"""HL7v2 ACK Message Generator.

This module generates HL7v2 ACK (Acknowledgment) messages in response to received messages.

ACK Message Structure:
    MSH|^~\\&|RECEIVING|RECEIVING_FACILITY|SENDING|SENDING_FACILITY|TIMESTAMP||ACK^A04|MSG_CONTROL_ID|P|2.5
    MSA|AA|MSG_CONTROL_ID|Message accepted

ACK Codes (MSA-1):
    - AA (Application Accept): Message accepted and processed successfully
    - AR (Application Reject): Message rejected due to validation error
    - AE (Application Error): Message rejected due to internal error

Example Usage:
    generator = ACKGenerator()
    ack = generator.generate_success(msh_segment)
    ack = generator.generate_error(msh_segment, "AR", "Invalid patient ID")
"""

from datetime import datetime
from typing import Optional

from .segments import MSHSegment


class ACKGenerator:
    """Generate HL7v2 ACK messages.

    This class creates properly formatted ACK messages following HL7v2 specification.
    It handles success (AA), rejection (AR), and error (AE) acknowledgments.
    """

    FIELD_SEP = "|"
    SEGMENT_SEP = "\r"

    def generate_success(self, msh: MSHSegment, message: str = "Message accepted") -> str:
        """Generate success ACK (AA - Application Accept).

        Args:
            msh: Original MSH segment from the received message
            message: Optional success message (default: "Message accepted")

        Returns:
            Complete ACK message string with AA code
        """
        return self._build_ack(msh, "AA", message)

    def generate_reject(self, msh: MSHSegment, error_message: str) -> str:
        """Generate rejection ACK (AR - Application Reject).

        Used when the message is rejected due to validation errors or business rules.

        Args:
            msh: Original MSH segment from the received message
            error_message: Description of why the message was rejected

        Returns:
            Complete ACK message string with AR code
        """
        return self._build_ack(msh, "AR", error_message)

    def generate_error(self, msh: MSHSegment, error_message: str) -> str:
        """Generate error ACK (AE - Application Error).

        Used when the message cannot be processed due to internal system errors.

        Args:
            msh: Original MSH segment from the received message
            error_message: Description of the internal error

        Returns:
            Complete ACK message string with AE code
        """
        return self._build_ack(msh, "AE", error_message)

    def _build_ack(self, msh: MSHSegment, ack_code: str, message_text: str) -> str:
        """Build ACK message.

        Args:
            msh: Original MSH segment
            ack_code: ACK code (AA, AR, or AE)
            message_text: Message text for MSA-3

        Returns:
            Complete ACK message string
        """
        # Build MSH segment for ACK
        # Swap sender/receiver from original message
        ack_msh_fields = [
            "MSH",
            "^~\\&",  # Encoding characters
            msh.receiving_application or "GRAHAME",  # MSH-3: Sending App (was receiving)
            msh.receiving_facility or "INTELLICARE",  # MSH-4: Sending Facility
            msh.sending_application or "UNKNOWN",  # MSH-5: Receiving App (was sending)
            msh.sending_facility or "UNKNOWN",  # MSH-6: Receiving Facility
            datetime.now().strftime("%Y%m%d%H%M%S"),  # MSH-7: Timestamp
            "",  # MSH-8: Security (empty)
            f"ACK^{msh.trigger_event or 'A04'}",  # MSH-9: Message Type
            self._generate_control_id(),  # MSH-10: Message Control ID (new for ACK)
            "P",  # MSH-11: Processing ID (P=Production)
            msh.version or "2.5",  # MSH-12: Version
        ]

        # Build MSA segment (Message Acknowledgment)
        msa_fields = [
            "MSA",
            ack_code,  # MSA-1: Acknowledgment Code (AA/AR/AE)
            msh.message_control_id or "UNKNOWN",  # MSA-2: Original Message Control ID
            message_text,  # MSA-3: Text Message
        ]

        # Join fields and segments
        msh_line = self.FIELD_SEP.join(ack_msh_fields)
        msa_line = self.FIELD_SEP.join(msa_fields)

        return f"{msh_line}{self.SEGMENT_SEP}{msa_line}"

    def _generate_control_id(self) -> str:
        """Generate unique message control ID for ACK.

        Returns:
            Message control ID in format: ACK-YYYYMMDDHHMMSS-MICROSECONDS
        """
        now = datetime.now()
        return f"ACK-{now.strftime('%Y%m%d%H%M%S')}-{now.microsecond:06d}"


def build_simple_ack(
    message_control_id: Optional[str] = None,
    ack_code: str = "AA",
    message_text: str = "Message accepted",
) -> str:
    """Build a simple ACK message without requiring MSH segment.

    This is a convenience function for cases where you don't have a parsed MSH segment.
    Use ACKGenerator class for full-featured ACK generation.

    Args:
        message_control_id: Original message control ID (default: "UNKNOWN")
        ack_code: ACK code (AA, AR, or AE) (default: "AA")
        message_text: Message text (default: "Message accepted")

    Returns:
        Simple ACK message string
    """
    msg_ctrl_id = message_control_id or "UNKNOWN"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    msh = f"MSH|^~\\&|GRAHAME|INTELLICARE|||{timestamp}||ACK||P|2.5"
    msa = f"MSA|{ack_code}|{msg_ctrl_id}|{message_text}"

    return f"{msh}\r{msa}"

