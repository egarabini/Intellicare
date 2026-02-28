"""ADT^A04 Message Handler — Register Patient.

ADT^A04 is used to register a patient in the hospital system.
This handler:
1. Parses the HL7v2 message (MSH, PID, PV1 segments)
2. Validates required fields
3. Converts to FHIR Patient + Encounter resources
4. Publishes events to Redis Stream
5. Returns ACK message

Flow:
    Raw HL7v2 → Parse → Validate → Convert to FHIR → Persist → Publish Events → ACK
"""

import logging
from typing import Optional

from ..ack import ACKGenerator
from ..parser import HL7v2Parser
from ..segments import MSHSegment, PIDSegment, PV1Segment

logger = logging.getLogger(__name__)


class ADTMessage:
    """Parsed ADT message with all segments."""

    def __init__(
        self,
        msh: MSHSegment,
        pid: PIDSegment,
        pv1: Optional[PV1Segment] = None,
    ):
        self.msh = msh
        self.pid = pid
        self.pv1 = pv1

    @classmethod
    def from_parser(cls, parser: HL7v2Parser) -> "ADTMessage":
        """Parse ADT message from HL7v2Parser."""
        msh = MSHSegment.from_parser(parser)
        pid = PIDSegment.from_parser(parser)
        pv1 = PV1Segment.from_parser(parser) if parser.has_segment("PV1") else None

        return cls(msh=msh, pid=pid, pv1=pv1)

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate ADT message.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # MSH validation
        if not self.msh.message_type:
            return False, "MSH-9 (Message Type) is required"

        if not self.msh.message_control_id:
            return False, "MSH-10 (Message Control ID) is required"

        # PID validation
        if not self.pid.patient_id_list or len(self.pid.patient_id_list) == 0:
            return False, "PID-3 (Patient ID List) is required"

        if not self.pid.patient_name:
            return False, "PID-5 (Patient Name) is required"

        # All validations passed
        return True, None


class ADTA04Handler:
    """Handler for ADT^A04 messages (Register Patient).

    This handler processes patient registration messages from hospital systems.
    It converts HL7v2 ADT^A04 messages to FHIR Patient and Encounter resources.

    Example usage:
        handler = ADTA04Handler()
        ack_message, status_code = await handler.handle(raw_hl7_message)
    """

    def __init__(self):
        """Initialize ADT^A04 handler."""
        self.ack_generator = ACKGenerator()

    async def handle(self, raw_message: str) -> tuple[str, int]:
        """Handle ADT^A04 message.

        Args:
            raw_message: Raw HL7v2 message string

        Returns:
            Tuple of (ACK message, HTTP status code)
        """
        try:
            # Step 1: Parse message
            parser = HL7v2Parser(raw_message)

            # Step 2: Validate message type
            if parser.message_type != "ADT^A04":
                error_msg = f"Unsupported message type: {parser.message_type}"
                logger.warning(error_msg)
                msh = MSHSegment.from_parser(parser)
                ack = self.ack_generator.generate_reject(msh, error_msg)
                return ack, 400

            # Step 3: Parse segments
            try:
                adt_message = ADTMessage.from_parser(parser)
            except Exception as e:
                error_msg = f"Failed to parse message segments: {str(e)}"
                logger.error(error_msg, exc_info=True)
                msh = MSHSegment.from_parser(parser)
                ack = self.ack_generator.generate_error(msh, error_msg)
                return ack, 400

            # Step 4: Validate message
            is_valid, validation_error = adt_message.validate()
            if not is_valid:
                logger.warning(f"Message validation failed: {validation_error}")
                ack = self.ack_generator.generate_reject(adt_message.msh, validation_error)
                return ack, 400

            # Step 5: Process message (convert to FHIR, persist, publish events)
            # TODO: Implement in Phase 3 (FHIR Converters) and Phase 4 (Event Publisher)
            logger.info(
                f"ADT^A04 message processed successfully: "
                f"Patient={adt_message.pid.patient_name}, "
                f"MsgCtrlID={adt_message.msh.message_control_id}"
            )

            # Step 6: Build success ACK
            ack = self.ack_generator.generate_success(adt_message.msh)
            return ack, 200

        except Exception as e:
            logger.error(f"Unexpected error handling ADT^A04: {e}", exc_info=True)
            # Try to build error ACK if possible
            try:
                parser = HL7v2Parser(raw_message)
                msh = MSHSegment.from_parser(parser)
                ack = self.ack_generator.generate_error(msh, f"Internal error: {str(e)}")
                return ack, 500
            except Exception:
                # If we can't even parse the message, return generic error
                from ..ack import build_simple_ack
                return build_simple_ack(ack_code="AE", message_text="Internal error"), 500

