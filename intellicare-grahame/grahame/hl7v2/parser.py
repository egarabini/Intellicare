"""HL7v2 Parser Core — Parse pipe-delimited HL7v2 messages.

HL7v2 message structure:
- Segments: MSH|PID|PV1|...
- Fields: MSH|^~\\&|SENDING|RECEIVING|...
- Components: Field^Component^Subcomponent
- Subcomponents: Field^Component&Subcomponent

Delimiters:
- |: Field separator
- ^: Component separator
- ~: Subcomponent separator (repetition separator)
- \\: Escape character
- &: Subfield separator

Encoding: ASCII, UTF-8, ISO-8859-1
"""

from typing import Optional


class HL7v2Parser:
    """Parse HL7v2 messages (pipe-delimited format)."""

    # Field separator (MSH-1)
    FIELD_SEP = "|"

    # Component separators (MSH-2)
    # Encoding characters: ^~\\&
    COMP_SEP = "^"      # Component separator
    SUBCOMP_SEP = "~"   # Subcomponent separator (also repetition separator)
    ESCAPE_CHAR = "\\"  # Escape character
    REP_SEP = "&"       # Repetition separator

    def __init__(self, raw_message: str):
        """Initialize parser with raw HL7v2 message.

        Args:
            raw_message: Raw HL7v2 message (string)
        """
        self.raw_message = raw_message.strip()
        self._segments: dict[str, list[list[str]]] = {}
        self._parse()

    def _parse(self) -> None:
        """Parse raw message into segments."""
        lines = self.raw_message.split("\r")
        if not lines or len(lines) == 1:
            lines = self.raw_message.split("\n")

        for line in lines:
            if not line or len(line) < 3:
                continue

            # First 3 characters are segment ID
            segment_id = line[:3]

            # Special handling for MSH segment
            if segment_id == "MSH":
                # MSH has special structure: MSH|^~\&|SENDING|RECEIVING|...
                # Position 3 is field separator |
                # Position 4-7 is encoding characters ^~\&
                # Fields start at position 8
                # We need to insert the encoding characters as field 1
                rest = line[8:]  # Skip "MSH|^~\&"
                segment_fields = ["^~\\&"] + rest.split(self.FIELD_SEP)
            else:
                # For other segments, skip segment ID and field separator
                segment_fields = line[4:].split(self.FIELD_SEP)

            # Group by segment ID (allow multiple occurrences)
            if segment_id not in self._segments:
                self._segments[segment_id] = []
            self._segments[segment_id].append(segment_fields)

    def has_segment(self, segment_id: str) -> bool:
        """Check if segment exists in message.

        Args:
            segment_id: Segment ID (e.g., "MSH", "PID", "PV1")

        Returns:
            True if segment exists, False otherwise
        """
        return segment_id in self._segments and len(self._segments[segment_id]) > 0

    def get_segment(self, segment_id: str, index: int = 0) -> Optional[list[str]]:
        """Get segment fields by ID.

        Args:
            segment_id: Segment ID (e.g., "MSH", "PID", "PV1")
            index: Segment index (default: 0, first occurrence)

        Returns:
            List of segment fields or None if not found
        """
        segments = self._segments.get(segment_id, [])
        if index >= len(segments):
            return None
        return segments[index]

    def get_field(self, segment_id: str, field_position: int, index: int = 0) -> Optional[str]:
        """Get field value from segment.

        Args:
            segment_id: Segment ID (e.g., "MSH", "PID")
            field_position: Field position (1-indexed)
            index: Segment index (default: 0)

        Returns:
            Field value or None if not found
        """
        segment = self.get_segment(segment_id, index)
        if segment is None:
            return None

        # Field position is 1-indexed
        if field_position < 1 or field_position > len(segment):
            return None

        return segment[field_position - 1]

    def get_component(
        self, segment_id: str, field_position: int, component_position: int, index: int = 0
    ) -> Optional[str]:
        """Get component from field.

        Args:
            segment_id: Segment ID
            field_position: Field position (1-indexed)
            component_position: Component position (1-indexed)
            index: Segment index (default: 0)

        Returns:
            Component value or None if not found
        """
        field = self.get_field(segment_id, field_position, index)
        if field is None:
            return None

        components = field.split(self.COMP_SEP)
        if component_position < 1 or component_position > len(components):
            return None

        return components[component_position - 1]

    @property
    def message_type(self) -> Optional[str]:
        """Get message type from MSH-9."""
        msh = self.get_segment("MSH")
        if msh is None or len(msh) < 9:
            return None
        return msh[8]  # MSH-9 (1-indexed, so index 8)

    @property
    def message_control_id(self) -> Optional[str]:
        """Get message control ID from MSH-10."""
        return self.get_field("MSH", 10)

    @property
    def timestamp(self) -> Optional[str]:
        """Get timestamp from MSH-7."""
        return self.get_field("MSH", 7)

