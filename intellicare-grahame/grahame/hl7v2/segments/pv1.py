"""PV1 Segment Parser — Patient Visit.

PV1 segment contains patient visit/encounter data:
- PV1-1: Set ID
- PV1-2: Patient Class (I=Inpatient, O=Outpatient, E=Emergency)
- PV1-3: Assigned Patient Location (PL datatype)
- PV1-4: Admission Type (IS datatype)
- PV1-44: Admit Date/Time (TS datatype)
"""

from typing import Optional

from pydantic import BaseModel

from ..parser import HL7v2Parser
from .pid import PIDSegment


class PV1Segment(BaseModel):
    """HL7v2 PV1 segment (Patient Visit)."""

    set_id: Optional[str] = None                   # PV1-1
    patient_class: Optional[str] = None            # PV1-2 (e.g., "I" = Inpatient)
    assigned_location: Optional[dict] = None       # PV1-3
    admission_type: Optional[dict] = None          # PV1-4
    admit_datetime: Optional[str] = None           # PV1-44

    @classmethod
    def from_parser(cls, parser: HL7v2Parser) -> "PV1Segment":
        """Parse PV1 segment from parser."""
        # PV1-2 (Patient Class) - IS datatype
        patient_class = parser.get_field("PV1", 2)
        if patient_class:
            patient_class = cls._map_patient_class(patient_class)

        # PV1-3 (Assigned Location) - PL datatype
        location_raw = parser.get_field("PV1", 3) or ""
        assigned_location = cls._parse_pl(location_raw)

        # PV1-4 (Admission Type) - IS datatype
        admit_type_raw = parser.get_field("PV1", 4) or ""
        admission_type = cls._parse_is(admit_type_raw)

        # PV1-44 (Admit DateTime) - TS datatype
        admit_datetime = parser.get_field("PV1", 44)
        if admit_datetime:
            admit_datetime = PIDSegment._ts_to_iso8601(admit_datetime)

        return cls(
            set_id=parser.get_field("PV1", 1),
            patient_class=patient_class,
            assigned_location=assigned_location,
            admission_type=admission_type,
            admit_datetime=admit_datetime,
        )

    @staticmethod
    def _map_patient_class(cls_code: str) -> str:
        """Map HL7 patient class to FHIR Encounter class.

        HL7 Patient Class:
        - I: Inpatient
        - O: Outpatient
        - E: Emergency
        - P: Preadmit
        """
        class_map = {
            "I": "imp",  # Inpatient
            "O": "amb",  # Ambulatory
            "E": "emer",  # Emergency
            "P": "imp",  # Preadmit (treat as inpatient)
        }
        return class_map.get(cls_code, "amb")

    @staticmethod
    def _parse_pl(pl_raw: str) -> Optional[dict]:
        """Parse PL datatype (Person Location)."""
        if not pl_raw:
            return None

        parts = pl_raw.split("^")
        return {
            "point_of_care": parts[0] if len(parts) > 0 else None,
            "room": parts[1] if len(parts) > 1 else None,
            "bed": parts[2] if len(parts) > 2 else None,
            "facility": parts[3] if len(parts) > 3 else None,
        }

    @staticmethod
    def _parse_is(is_raw: str) -> Optional[dict]:
        """Parse IS datatype (Identifier String)."""
        if not is_raw:
            return None

        return {
            "code": is_raw,
        }

