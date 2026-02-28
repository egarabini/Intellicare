"""MSH Segment Parser — Message Header.

MSH segment contains message metadata:
- MSH-3: Sending Application
- MSH-4: Sending Facility
- MSH-5: Receiving Application
- MSH-6: Receiving Facility
- MSH-7: Date/Time of Message
- MSH-9: Message Type (e.g., "ADT^A04")
- MSH-10: Message Control ID
- MSH-12: Version ID (e.g., "2.5")
"""

from typing import Optional

from pydantic import BaseModel

from ..parser import HL7v2Parser


class MSHSegment(BaseModel):
    """HL7v2 MSH segment (Message Header)."""

    sending_application: Optional[str] = None      # MSH-3
    sending_facility: Optional[str] = None         # MSH-4
    receiving_application: Optional[str] = None    # MSH-5
    receiving_facility: Optional[str] = None       # MSH-6
    datetime: Optional[str] = None                 # MSH-7
    security: Optional[str] = None                 # MSH-8
    message_type: Optional[str] = None             # MSH-9 (e.g., "ADT^A04")
    message_control_id: Optional[str] = None       # MSH-10
    processing_id: Optional[str] = None            # MSH-11
    version: Optional[str] = None                  # MSH-12

    @classmethod
    def from_parser(cls, parser: HL7v2Parser) -> "MSHSegment":
        """Parse MSH segment from parser."""
        return cls(
            sending_application=parser.get_field("MSH", 3),
            sending_facility=parser.get_field("MSH", 4),
            receiving_application=parser.get_field("MSH", 5),
            receiving_facility=parser.get_field("MSH", 6),
            datetime=parser.get_field("MSH", 7),
            security=parser.get_field("MSH", 8),
            message_type=parser.get_field("MSH", 9),
            message_control_id=parser.get_field("MSH", 10),
            processing_id=parser.get_field("MSH", 11),
            version=parser.get_field("MSH", 12),
        )

    @property
    def trigger_event(self) -> Optional[str]:
        """Get trigger event from message type (e.g., "A04" from "ADT^A04")."""
        if self.message_type is None:
            return None
        parts = self.message_type.split("^")
        return parts[1] if len(parts) > 1 else None

