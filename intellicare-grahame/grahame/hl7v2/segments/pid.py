"""PID Segment Parser — Patient Identification.

PID segment contains patient demographic data:
- PID-3: Patient Identifier List (CX datatype)
- PID-5: Patient Name (XPN datatype)
- PID-7: Date/Time of Birth (TS datatype)
- PID-8: Administrative Sex (IS datatype)
- PID-10: Race (CE datatype)
- PID-11: Patient Address (XAD datatype)
- PID-13: Phone Number (XTN datatype)
- PID-22: Ethnic Group (CE datatype)
"""

from typing import List, Optional

from pydantic import BaseModel

from ..parser import HL7v2Parser


class PIDSegment(BaseModel):
    """HL7v2 PID segment (Patient Identification)."""

    patient_id_list: List[dict] = []               # PID-3 (CX list)
    patient_name: Optional[dict] = None             # PID-5
    mother_maiden_name: Optional[str] = None        # PID-6
    datetime_of_birth: Optional[str] = None         # PID-7
    administrative_sex: Optional[str] = None        # PID-8
    race: Optional[dict] = None                     # PID-10
    address: Optional[dict] = None                  # PID-11
    phone_number: Optional[dict] = None             # PID-13
    ethnicity: Optional[dict] = None                # PID-22

    @classmethod
    def from_parser(cls, parser: HL7v2Parser) -> "PIDSegment":
        """Parse PID segment from parser."""
        # PID-3 (Patient ID List) - CX datatype (repeating)
        patient_id_list_raw = parser.get_field("PID", 3) or ""
        patient_id_list = cls._parse_cx_list(patient_id_list_raw)

        # PID-5 (Patient Name) - XPN datatype
        patient_name_raw = parser.get_field("PID", 5) or ""
        patient_name = cls._parse_xpn(patient_name_raw)

        # PID-7 (Datetime of Birth) - TS datatype
        datetime_of_birth = parser.get_field("PID", 7)
        if datetime_of_birth:
            datetime_of_birth = cls._ts_to_iso8601(datetime_of_birth)

        # PID-8 (Administrative Sex) - IS datatype
        administrative_sex = parser.get_field("PID", 8)
        if administrative_sex:
            administrative_sex = cls._map_gender(administrative_sex)

        # PID-10 (Race) - CE datatype
        race_raw = parser.get_field("PID", 10) or ""
        race = cls._parse_ce(race_raw)

        # PID-11 (Address) - XAD datatype
        address_raw = parser.get_field("PID", 11) or ""
        address = cls._parse_xad(address_raw)

        # PID-13 (Phone Number) - XTN datatype
        phone_raw = parser.get_field("PID", 13) or ""
        phone_number = cls._parse_xtn(phone_raw)

        # PID-22 (Ethnic Group) - CE datatype
        ethnicity_raw = parser.get_field("PID", 22) or ""
        ethnicity = cls._parse_ce(ethnicity_raw)

        return cls(
            patient_id_list=patient_id_list,
            patient_name=patient_name,
            datetime_of_birth=datetime_of_birth,
            administrative_sex=administrative_sex,
            race=race,
            address=address,
            phone_number=phone_number,
            ethnicity=ethnicity,
        )

    @staticmethod
    def _parse_cx_list(cx_raw: str) -> List[dict]:
        """Parse CX datatype (Extended Composite ID).

        CX format: ID^CheckDigit^CheckDigitScheme^AssigningAuthority^IdentifierTypeCode^...
        Example: 12345678900^^^HOSPITAL^CPF
        """
        if not cx_raw:
            return []

        cx_list = []
        for cx in cx_raw.split("~"):  # Repetition separator
            parts = cx.split("^")
            cx_list.append({
                "id": parts[0] if len(parts) > 0 else None,
                "check_digit": parts[1] if len(parts) > 1 else None,
                "check_digit_scheme": parts[2] if len(parts) > 2 else None,
                "assigning_authority": parts[3] if len(parts) > 3 else None,
                "identifier_type": parts[4] if len(parts) > 4 else None,
            })
        return cx_list

    @staticmethod
    def _parse_xpn(xpn_raw: str) -> Optional[dict]:
        """Parse XPN datatype (Extended Person Name).

        XPN format: FamilyName^GivenName^SecondName^Suffix^Prefix...
        Example: Silva^João^Maria
        """
        if not xpn_raw:
            return None

        parts = xpn_raw.split("^")
        return {
            "family": parts[0] if len(parts) > 0 else None,
            "given": parts[1] if len(parts) > 1 else None,
            "middle": parts[2] if len(parts) > 2 else None,
            "suffix": parts[3] if len(parts) > 3 else None,
            "prefix": parts[4] if len(parts) > 4 else None,
        }

    @staticmethod
    def _ts_to_iso8601(ts: str) -> Optional[str]:
        """Convert HL7 TS (timestamp) to ISO 8601.

        HL7 TS: 20260101120000
        ISO 8601: 2026-01-01T12:00:00
        """
        if not ts or len(ts) < 8:
            return None

        year = ts[0:4]
        month = ts[4:6]
        day = ts[6:8]

        time_part = ""
        if len(ts) >= 14:
            hour = ts[8:10]
            minute = ts[10:12]
            second = ts[12:14]
            time_part = f"T{hour}:{minute}:{second}"

        return f"{year}-{month}-{day}{time_part}"

    @staticmethod
    def _map_gender(sex: str) -> str:
        """Map HL7 administrative sex to FHIR gender."""
        gender_map = {
            "M": "male",
            "F": "female",
            "A": "other",
            "U": "unknown",
            "O": "other",
        }
        return gender_map.get(sex, "unknown")

    @staticmethod
    def _parse_ce(ce_raw: str) -> Optional[dict]:
        """Parse CE datatype (Coded Element)."""
        if not ce_raw:
            return None

        parts = ce_raw.split("^")
        return {
            "code": parts[0] if len(parts) > 0 else None,
            "text": parts[1] if len(parts) > 1 else None,
            "system": parts[2] if len(parts) > 2 else None,
        }

    @staticmethod
    def _parse_xad(xad_raw: str) -> Optional[dict]:
        """Parse XAD datatype (Extended Address)."""
        if not xad_raw:
            return None

        parts = xad_raw.split("^")
        return {
            "street": parts[0] if len(parts) > 0 else None,
            "city": parts[2] if len(parts) > 2 else None,
            "state": parts[3] if len(parts) > 3 else None,
            "postal_code": parts[4] if len(parts) > 4 else None,
            "country": parts[5] if len(parts) > 5 else None,
        }

    @staticmethod
    def _parse_xtn(xtn_raw: str) -> Optional[dict]:
        """Parse XTN datatype (Extended Telecommunication Number)."""
        if not xtn_raw:
            return None

        # Remove "tel:" prefix if present
        if xtn_raw.startswith("tel:"):
            xtn_raw = xtn_raw[4:]

        parts = xtn_raw.split("^")
        return {
            "number": parts[0] if len(parts) > 0 else None,
            "use": parts[2] if len(parts) > 2 else None,
        }

