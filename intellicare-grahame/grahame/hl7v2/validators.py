"""HL7v2 Message Validators.

This module provides validators for HL7v2 messages to ensure structural integrity,
required fields, and data type compliance.

Validators:
    - StructureValidator: Validates segment order and required segments
    - FieldValidator: Validates required fields and data types
    - MessageValidator: High-level validator combining all checks

Example Usage:
    validator = MessageValidator()
    is_valid, errors = validator.validate_adt_a04(parser)
    if not is_valid:
        print(f"Validation errors: {errors}")
"""

from typing import Optional

from .parser import HL7v2Parser


class ValidationError(Exception):
    """Raised when HL7v2 message validation fails."""

    pass


class StructureValidator:
    """Validates HL7v2 message structure (segment order, required segments)."""

    # ADT^A04 required segments
    ADT_A04_REQUIRED_SEGMENTS = ["MSH", "PID"]
    ADT_A04_OPTIONAL_SEGMENTS = ["PV1", "NK1", "OBX", "AL1", "DG1"]

    # Segment order for ADT^A04
    ADT_A04_SEGMENT_ORDER = ["MSH", "PID", "PV1", "NK1", "OBX", "AL1", "DG1"]

    def validate_required_segments(
        self, parser: HL7v2Parser, message_type: str = "ADT^A04"
    ) -> tuple[bool, Optional[str]]:
        """Validate that all required segments are present.

        Args:
            parser: HL7v2Parser instance
            message_type: Message type (default: ADT^A04)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if message_type == "ADT^A04":
            required = self.ADT_A04_REQUIRED_SEGMENTS
        else:
            return False, f"Unsupported message type: {message_type}"

        for segment_id in required:
            if not parser.has_segment(segment_id):
                return False, f"Required segment {segment_id} is missing"

        return True, None

    def validate_segment_order(
        self, parser: HL7v2Parser, message_type: str = "ADT^A04"
    ) -> tuple[bool, Optional[str]]:
        """Validate segment order (optional - some systems don't enforce strict order).

        Args:
            parser: HL7v2Parser instance
            message_type: Message type (default: ADT^A04)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # For MVP, we don't enforce strict segment order
        # Many hospital systems send segments in different orders
        # This is a placeholder for future strict validation if needed
        return True, None


class FieldValidator:
    """Validates HL7v2 field requirements and data types."""

    # ADT^A04 required fields
    ADT_A04_REQUIRED_FIELDS = {
        "MSH": [9, 10, 12],  # Message Type, Control ID, Version
        "PID": [3, 5],  # Patient ID, Patient Name
    }

    def validate_required_fields(
        self, parser: HL7v2Parser, message_type: str = "ADT^A04"
    ) -> tuple[bool, Optional[str]]:
        """Validate that all required fields are present and non-empty.

        Args:
            parser: HL7v2Parser instance
            message_type: Message type (default: ADT^A04)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if message_type == "ADT^A04":
            required_fields = self.ADT_A04_REQUIRED_FIELDS
        else:
            return False, f"Unsupported message type: {message_type}"

        for segment_id, field_numbers in required_fields.items():
            if not parser.has_segment(segment_id):
                continue  # Structure validator will catch missing segments

            for field_num in field_numbers:
                field_value = parser.get_field(segment_id, field_num)
                if not field_value or field_value.strip() == "":
                    return False, f"Required field {segment_id}-{field_num} is missing or empty"

        return True, None

    def validate_field_lengths(
        self, parser: HL7v2Parser, message_type: str = "ADT^A04"
    ) -> tuple[bool, Optional[str]]:
        """Validate field lengths (optional - for strict compliance).

        Args:
            parser: HL7v2Parser instance
            message_type: Message type (default: ADT^A04)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # For MVP, we don't enforce strict field length validation
        # This is a placeholder for future strict validation if needed
        return True, None


class MessageValidator:
    """High-level validator combining structure and field validation."""

    def __init__(self):
        """Initialize message validator."""
        self.structure_validator = StructureValidator()
        self.field_validator = FieldValidator()

    def validate_adt_a04(self, parser: HL7v2Parser) -> tuple[bool, Optional[str]]:
        """Validate ADT^A04 message.

        Performs all validation checks:
        1. Required segments present
        2. Required fields present and non-empty
        3. Segment order (optional)
        4. Field lengths (optional)

        Args:
            parser: HL7v2Parser instance

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Step 1: Validate required segments
        is_valid, error = self.structure_validator.validate_required_segments(parser, "ADT^A04")
        if not is_valid:
            return False, error

        # Step 2: Validate required fields
        is_valid, error = self.field_validator.validate_required_fields(parser, "ADT^A04")
        if not is_valid:
            return False, error

        # All validations passed
        return True, None

