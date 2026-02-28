# W8-B — HL7v2 Agent — Especificação Técnica

**Workstream:** W8-B
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (+ novo sub-módulo `hl7v2`)
**Status:** 📋 Especificação Técnica
**Data:** 2026-02-24
**Estimativa:** 42 dias

---

## 1. Arquitetura

### 1.1 Componentes

```
intellicare-grahame/
├── app/
│   ├── api/
│   │   └── hl7v2.py             # Endpoints HL7v2
│   ├── hl7v2/
│   │   ├── __init__.py
│   │   ├── parser.py            # HL7v2 parser core
│   │   ├── segments/            # Segment parsers
│   │   │   ├── __init__.py
│   │   │   ├── msh.py           # MSH (Message Header)
│   │   │   ├── pid.py           # PID (Patient Identification)
│   │   │   └── pv1.py           # PV1 (Patient Visit)
│   │   ├── messages/            # Message handlers
│   │   │   ├── __init__.py
│   │   │   └── adt_a04.py       # ADT^A04 (Register Patient)
│   │   ├── converters/          # HL7v2 → FHIR
│   │   │   ├── __init__.py
│   │   │   ├── patient.py       # PID → Patient
│   │   │   └── encounter.py     # PV1 → Encounter
│   │   ├── ack.py               # ACK generator
│   │   └── validators.py        # HL7v2 validation
│   └── events/
│       └── hl7v2_publisher.py   # Redis Stream publisher
├── tests/
│   ├── hl7v2/
│   │   ├── fixtures/            # HL7v2 messages reais
│   │   │   ├── pv_adt_a04.txt
│   │   │   ├── tasy_adt_a04.txt
│   │   │   ├── mv_adt_a04.txt
│   │   │   └── sysimal_adt_a04.txt
│   │   ├── test_parser.py
│   │   ├── test_segments.py
│   │   ├── test_messages.py
│   │   ├── test_converters.py
│   │   └── test_integration.py
│   └── benchmarks/
│       └── test_hl7v2_performance.py
└── requirements.txt              # + (nenhuma lib externa HL7v2)
```

### 1.2 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| **Parser** | Python nativo | HL7v2 é pipe-delimited, simples de parsear |
| **Encoding** | `encode` | Suporte ISO-8859-1 (brasileiro) |
| **Validation** | Regex + Pydantic | Validação de campos |
| **FHIR** | `fhir.resources` | Type-safe FHIR R4 models |
| **Events** | Redis Stream | Publicação para WANDA/Geralda |

---

## 2. Implementação Core

### 2.1 Parser HL7v2 Core

**File:** `app/hl7v2/parser.py`

```python
from typing import Optional
import re

from app.hl7v2.segments import MSHSegment, PIDSegment, PV1Segment

class HL7v2Parser:
    """
    Parse HL7v2 messages (pipe-delimited format).

    HL7v2 message structure:
    - Segments: MSH|PID|PV1|...
    - Fields: MSH|^~\\&|SENDING|RECEIVING|...
    - Components: Field^Component^Subcomponent
    - Subcomponents: Field^Component&Subcomponent

    Delimiters:
    - |: Field separator
    - ^: Component separator
    - ~: Subcomponent separator
    - \\: Escape character
    - &: Subfield separator

    Encoding: ASCII, UTF-8, ISO-8859-1
    """

    # Field separator (MSH-1)
    FIELD_SEP = "|"

    # Component separators (MSH-2)
    # Encoding characters: ^~\\&
    COMP_SEP = "^"      # Component separator
    SUBCOMP_SEP = "~"   # Subcomponent separator
    ESCAPE_CHAR = "\\"  # Escape character
    REP_SEP = "&"       # Repetition separator

    def __init__(self, raw_message: str):
        """
        Initialize parser with raw HL7v2 message.

        Args:
            raw_message: Raw HL7v2 message (string)
        """
        self.raw_message = raw_message.strip()
        self._segments: dict[str, list[str]] = {}
        self._parse()

    def _parse(self) -> None:
        """Parse raw message into segments."""
        lines = self.raw_message.split("\r")
        segments = []

        for line in lines:
            if not line:
                continue

            # First 3 characters are segment ID
            segment_id = line[:3]
            segment_fields = line[3:].split(self.FIELD_SEP)
            segments.append((segment_id, segment_fields))

        # Group by segment ID
        for seg_id, fields in segments:
            if seg_id not in self._segments:
                self._segments[seg_id] = []
            self._segments[seg_id].append(fields)

    def get_segment(self, segment_id: str, index: int = 0) -> Optional[list[str]]:
        """
        Get segment fields by ID.

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
        """
        Get field value from segment.

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

    def get_component(self, segment_id: str, field_position: int, component_position: int, index: int = 0) -> Optional[str]:
        """
        Get component from field.

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
```

### 2.2 Segment Parsers

**File:** `app/hl7v2/segments/msh.py`

```python
from pydantic import BaseModel
from typing import Optional

from app.hl7v2.parser import HL7v2Parser

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
```

**File:** `app/hl7v2/segments/pid.py`

```python
from pydantic import BaseModel
from typing import Optional, List

from app.hl7v2.parser import HL7v2Parser

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

        return cls(
            patient_id_list=patient_id_list,
            patient_name=patient_name,
            datetime_of_birth=datetime_of_birth,
            administrative_sex=administrative_sex,
            race=race,
            address=address,
            phone_number=phone_number,
        )

    @staticmethod
    def _parse_cx_list(cx_raw: str) -> List[dict]:
        """
        Parse CX datatype (Extended Composite ID).

        CX format: ID^AssigningAuthority^IdentifierTypeCode^...
        Example: 12345678900^CPF^BR
        """
        if not cx_raw:
            return []

        cx_list = []
        for cx in cx_raw.split("~"):  # Repetition separator
            parts = cx.split("^")
            cx_list.append({
                "id": parts[0] if len(parts) > 0 else None,
                "assigning_authority": parts[1] if len(parts) > 1 else None,
                "identifier_type": parts[2] if len(parts) > 2 else None,
            })
        return cx_list

    @staticmethod
    def _parse_xpn(xpn_raw: str) -> Optional[dict]:
        """
        Parse XPN datatype (Extended Person Name).

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
    def _ts_to_iso8601(ts: str) -> str:
        """
        Convert HL7 TS (timestamp) to ISO 8601.

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
```

**File:** `app/hl7v2/segments/pv1.py`

```python
from pydantic import BaseModel
from typing import Optional

from app.hl7v2.parser import HL7v2Parser

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
        """
        Map HL7 patient class to FHIR Encounter class.

        HL7 Patient Class:
        - I: Inpatient
        - O: Outpatient
        - E: Emergency
        - P: Preadmit
        """
        class_map = {
            "I": "imp",  # Inpatient
            "O": "amb",  # Ambulatory
            "E": "emerg",  # Emergency
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
```

### 2.3 Message Handler — ADT^A04

**File:** `app/hl7v2/messages/adt_a04.py`

```python
from fhir.resources.patient import Patient
from fhir.resources.encounter import Encounter

from app.hl7v2.parser import HL7v2Parser
from app.hl7v2.segments import MSHSegment, PIDSegment, PV1Segment
from app.hl7v2.converters import PatientConverter, EncounterConverter
from app.hl7v2.ack import ACKGenerator
from app.fhir.core import FHIRHandler
from app.events.hl7v2_publisher import HL7v2EventPublisher

class ADTA04Handler:
    """
    Handle HL7v2 ADT^A04 messages (Register Patient).

    Flow:
    1. Parse HL7v2 message
    2. Validate segments (MSH, PID, PV1)
    3. Convert to FHIR (Patient + Encounter)
    4. Persist FHIR resources
    5. Publish events (Redis Stream)
    6. Return ACK
    """

    def __init__(self, fhir_handler: FHIRHandler, event_publisher: HL7v2EventPublisher):
        self._fhir = fhir_handler
        self._events = event_publisher

    async def handle(self, raw_message: str) -> tuple[str, int]:
        """
        Handle ADT^A04 message.

        Returns:
            Tuple of (ACK message, HTTP status code)
        """
        try:
            # Parse message
            parser = HL7v2Parser(raw_message)

            # Validate message type
            if parser.message_type != "ADT^A04":
                return self._error_ack(
                    parser,
                    "E001",
                    "Unsupported message type"
                ), 400

            # Parse segments
            msh = MSHSegment.from_parser(parser)
            pid = PIDSegment.from_parser(parser)
            pv1 = PV1Segment.from_parser(parser)

            # Convert to FHIR
            patient_converter = PatientConverter()
            encounter_converter = EncounterConverter()

            patient = patient_converter.convert(pid, msh)
            encounter = encounter_converter.convert(pv1, msh, patient)

            # Persist FHIR resources
            created_patient = await self._fhir.create_resource(patient)
            created_encounter = await self._fhir.create_resource(encounter)

            # Publish events
            await self._events.publish_patient_created(created_patient)
            await self._events.publish_encounter_created(created_encounter)

            # Return ACK
            ack_gen = ACKGenerator()
            return ack_gen.generate_success(msh), 200

        except ValueError as e:
            # Validation error
            parser = HL7v2Parser(raw_message)
            msh = MSHSegment.from_parser(parser)
            return self._error_ack(msh, "E002", str(e)), 400

        except Exception as e:
            # Internal error
            parser = HL7v2Parser(raw_message)
            msh = MSHSegment.from_parser(parser)
            return self._error_ack(msh, "E999", f"Internal error: {e}"), 500

    def _error_ack(self, msh: MSHSegment, error_code: str, error_message: str) -> str:
        """Generate error ACK."""
        ack_gen = ACKGenerator()
        return ack_gen.generate_error(msh, error_code, error_message)
```

### 2.4 FHIR Converters

**File:** `app/hl7v2/converters/patient.py`

```python
from fhir.resources.patient import (
    Patient,
    PatientIdentifier,
    HumanName,
    Address,
    ContactPoint,
)
from fhir.resources.extension import Extension

from app.hl7v2.segments import PIDSegment, MSHSegment

class PatientConverter:
    """Convert HL7v2 PID segment to FHIR Patient resource."""

    def convert(self, pid: PIDSegment, msh: MSHSegment) -> Patient:
        """Convert PID to FHIR Patient."""

        # Build identifiers (PID-3)
        identifiers = []
        for cx in pid.patient_id_list:
            if cx["id"]:
                identifiers.append(PatientIdentifier(
                    use="usual",
                    system=self._map_identifier_system(cx["identifier_type"]),
                    value=cx["id"],
                ))

        # Build name (PID-5)
        name_elem = pid.patient_name or {}
        name = HumanName(
            use="official",
            family=name_elem.get("family"),
            given=[name_elem.get("given")] if name_elem.get("given") else [],
        )

        # Build address (PID-11)
        address = None
        if pid.address:
            address = Address(
                use="home",
                line=[pid.address["street"]] if pid.address["street"] else [],
                city=pid.address["city"],
                state=pid.address["state"],
                postalCode=pid.address["postal_code"],
                country=pid.address["country"],
            )

        # Build phone (PID-13)
        telecom = None
        if pid.phone_number:
            telecom = [ContactPoint(
                system="phone",
                value=pid.phone_number["number"],
                use=pid.phone_number["use"] or "home",
            )]

        # Build extension (race)
        extension = None
        if pid.race:
            extension = [
                Extension(
                    url="http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                    extension=[
                        Extension(
                            url="ombCategory",
                            valueCoding={
                                "system": pid.race.get("system"),
                                "code": pid.race.get("code"),
                                "display": pid.race.get("text"),
                            },
                        )
                    ],
                )
            ]

        return Patient(
            identifier=identifiers,
            name=[name],
            gender=pid.administrative_sex or "unknown",
            birthDate=pid.datetime_of_birth,
            address=[address] if address else None,
            telecom=telecom,
            extension=extension,
        )

    @staticmethod
    def _map_identifier_system(identifier_type: str) -> str:
        """Map HL7 identifier type to FHIR system."""
        type_map = {
            "CPF": "urn:oid:2.16.840.1.113883.4.578",  # Brazil CPF
            "CNS": "urn:oid:2.16.840.1.113883.4.578",  # Brazil CNS
            "RG": "urn:oid:2.16.840.1.113883.4.578",   # Brazil RG
        }
        return type_map.get(identifier_type, "urn:oid:2.16.840.1.113883.4.578")
```

**File:** `app/hl7v2/converters/encounter.py`

```python
from fhir.resources.encounter import (
    Encounter,
    EncounterIdentifier,
    EncounterLocation,
    EncounterHospitalization,
)
from fhir.resources.reference import Reference

from app.hl7v2.segments import PV1Segment, MSHSegment
from app.hl7v2.converters.patient import PatientConverter

class EncounterConverter:
    """Convert HL7v2 PV1 segment to FHIR Encounter resource."""

    def convert(self, pv1: PV1Segment, msh: MSHSegment, patient: Patient) -> Encounter:
        """Convert PV1 to FHIR Encounter."""

        # Build identifier (MSH-10 + PV1-1)
        identifiers = []
        if msh.message_control_id:
            identifiers.append(EncounterIdentifier(
                use="official",
                system=f"urn:hl7:{msh.sending_application}:{msh.sending_facility}",
                value=msh.message_control_id,
            ))
        if pv1.set_id:
            identifiers.append(EncounterIdentifier(
                use="usual",
                value=pv1.set_id,
            ))

        # Build class (PV1-2)
        class_code = pv1.patient_class or "amb"

        # Build location (PV1-3)
        location = None
        if pv1.assigned_location:
            location = [EncounterLocation(
                location=Reference(
                    reference="Location/unknown",
                    display=pv1.assigned_location.get("point_of_care"),
                ),
            )]

        # Build hospitalization (PV1-4)
        hospitalization = None
        if pv1.admission_type:
            hospitalization = EncounterHospitalization(
                admitSource={
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0007",
                        "code": pv1.admission_type["code"],
                    }],
                }
            )

        return Encounter(
            identifier=identifiers,
            class_=class_code,
            subject=Reference(reference=f"Patient/{patient.id}"),
            location=location,
            hospitalization=hospitalization,
            period={
                "start": pv1.admit_datetime,
            },
        )
```

### 2.5 ACK Generator

**File:** `app/hl7v2/ack.py`

```python
from datetime import datetime

from app.hl7v2.segments import MSHSegment

class ACKGenerator:
    """
    Generate HL7v2 ACK messages.

    ACK message format:
    MSH|^~\\&|RECEIVING|RECEIVING_FACILITY|SENDING|SENDING_FACILITY|TIMESTAMP||ACK^A04|MSG_CONTROL_ID|P|2.5
    MSA|AA|MSG_CONTROL_ID
    """

    def generate_success(self, msh: MSHSegment) -> str:
        """
        Generate success ACK (ACK^A04 with MSA|AA).

        Args:
            msh: Original MSH segment

        Returns:
            ACK message string
        """
        # Build MSH for ACK
        ack_msh = [
            "MSH",
            "^~\\&",  # Encoding characters
            msh.receiving_application or "GRAHAME",
            msh.receiving_facility or "INTELLICARE",
            msh.sending_application or "UNKNOWN",
            msh.sending_facility or "UNKNOWN",
            datetime.now().strftime("%Y%m%d%H%M%S"),  # MSH-7 (timestamp)
            "",  # MSH-8 (security)
            f"ACK^{msh.trigger_event or 'A04'}",  # MSH-9
            msh.message_control_id or "0",  # MSH-10
            "P",  # MSH-11 (Processing ID)
            msh.version or "2.5",  # MSH-12
        ]

        # Build MSA (Message Acknowledgment)
        msa = [
            "MSA",
            "AA",  # Application Accept
            msh.message_control_id or "0",
        ]

        # Join with field separator
        return "|".join(ack_msh) + "\r" + "|".join(msa)

    def generate_error(self, msh: MSHSegment, error_code: str, error_message: str) -> str:
        """
        Generate error ACK (ACK^AE with MSA|AE).

        Args:
            msh: Original MSH segment
            error_code: Error code (e.g., "E001")
            error_message: Human-readable error message

        Returns:
            ACK message string with error
        """
        # Build MSH for ACK (same as success, but with ACK^AE)
        ack_msh = [
            "MSH",
            "^~\\&",
            msh.receiving_application or "GRAHAME",
            msh.receiving_facility or "INTELLICARE",
            msh.sending_application or "UNKNOWN",
            msh.sending_facility or "UNKNOWN",
            datetime.now().strftime("%Y%m%d%H%M%S"),
            "",
            f"ACK^{msh.trigger_event or 'A04'}",
            msh.message_control_id or "0",
            "P",
            msh.version or "2.5",
        ]

        # Build MSA with error
        msa = [
            "MSA",
            "AE",  # Application Error
            msh.message_control_id or "0",
        ]

        # Build ERR segment
        err = [
            "ERR",
            "",
            "",
            error_message,
        ]

        # Join with field separator
        return "|".join(ack_msh) + "\r" + "|".join(msa) + "\r" + "|".join(err)
```

### 2.6 Endpoint HL7v2

**File:** `app/api/hl7v2.py`

```python
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.hl7v2.messages.adt_a04 import ADTA04Handler
from app.fhir.core import FHIRHandler
from app.events.hl7v2_publisher import HL7v2EventPublisher

router = APIRouter(prefix="/hl7v2", tags=["HL7v2"])

# Handlers
_adt_a04_handler: ADTA04Handler = None

def init_handlers(fhir_handler: FHIRHandler, event_publisher: HL7v2EventPublisher):
    """Initialize HL7v2 message handlers."""
    global _adt_a04_handler
    _adt_a04_handler = ADTA04Handler(fhir_handler, event_publisher)

@router.post("/adt-a04", response_class=PlainTextResponse)
async def adt_a04(
    request: Request,
    x_api_key: str = Header(..., description="API Key for authentication"),
) -> str:
    """
    Receive HL7v2 ADT^A04 message (Register Patient).

    Returns:
        HL7v2 ACK message (text/plain)
    """
    # Authenticate API Key
    if not _validate_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # Get raw message
    raw_message = await request.body()

    # Validate encoding
    try:
        message_text = raw_message.decode("utf-8")
    except UnicodeDecodeError:
        # Try ISO-8859-1 (Brazilian legacy)
        message_text = raw_message.decode("iso-8859-1")

    # Handle message
    ack_message, status_code = await _adt_a04_handler.handle(message_text)

    return PlainTextResponse(
        content=ack_message,
        status_code=status_code,
        media_type="application/x-hl7-v2",
    )

def _validate_api_key(api_key: str) -> bool:
    """Validate API Key."""
    # TODO: Implement proper API key validation
    # For MVP, accept any non-empty key
    return bool(api_key)
```

---

## 3. Event Publisher (Redis Stream)

**File:** `app/events/hl7v2_publisher.py`

```python
import json
import aioredis

from fhir.resources.patient import Patient
from fhir.resources.encounter import Encounter

class HL7v2EventPublisher:
    """
    Publish HL7v2 events to Redis Stream.

    Streams:
    - hl7v2:patient-created
    - hl7v2:encounter-created
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: aioredis.Redis = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = await aioredis.from_url(self._redis_url)

    async def publish_patient_created(self, patient: Patient) -> None:
        """Publish patient created event."""
        event = {
            "event_type": "patient.created",
            "resource_type": "Patient",
            "resource_id": patient.id,
            "timestamp": datetime.now().isoformat(),
        }
        await self._redis.xadd("hl7v2:patient-created", event)
        await self._redis.publish("hl7v2:patient-created", json.dumps(event))

    async def publish_encounter_created(self, encounter: Encounter) -> None:
        """Publish encounter created event."""
        event = {
            "event_type": "encounter.created",
            "resource_type": "Encounter",
            "resource_id": encounter.id,
            "subject_id": encounter.subject.reference.split("/")[1],
            "timestamp": datetime.now().isoformat(),
        }
        await self._redis.xadd("hl7v2:encounter-created", event)
        await self._redis.publish("hl7v2:encounter-created", json.dumps(event))
```

---

## 4. Testes

### 4.1 Testes de Parser

**File:** `tests/hl7v2/test_parser.py`

```python
import pytest

from app.hl7v2.parser import HL7v2Parser

@pytest.fixture
def sample_adt_a04() -> str:
    """Sample ADT^A04 message."""
    return """MSH|^~\\&|INTELLICARE|GRAHAME|20260224100000||ADT^A04|MSG00001|P|2.5|||ER|AL||UNICODE
PID|1||12345678900^CPF^BR||19800101|M|||Rua Teste, 123^^São Paulo^SP^^BR||5511999999999|PT|BR
PV1|1|I|2000^01^Hospital Central^^^^BR|||||||||||||||||||||||||||||||||||"""

def test_parse_msh():
    """Test MSH segment parsing."""
    parser = HL7v2Parser(sample_adt_a04())

    assert parser.message_type == "ADT^A04"
    assert parser.message_control_id == "MSG00001"
    assert parser.timestamp == "20260224100000"

def test_parse_pid():
    """Test PID segment parsing."""
    from app.hl7v2.segments.pid import PIDSegment

    parser = HL7v2Parser(sample_adt_a04())
    pid = PIDSegment.from_parser(parser)

    assert len(pid.patient_id_list) == 1
    assert pid.patient_id_list[0]["id"] == "12345678900"
    assert pid.patient_name["family"] == "Silva"
    assert pid.administrative_sex == "male"
    assert pid.datetime_of_birth == "1980-01-01"

def test_parse_pv1():
    """Test PV1 segment parsing."""
    from app.hl7v2.segments.pv1 import PV1Segment

    parser = HL7v2Parser(sample_adt_a04())
    pv1 = PV1Segment.from_parser(parser)

    assert pv1.set_id == "1"
    assert pv1.patient_class == "imp"

def test_parse_invalid_encoding():
    """Test parsing with ISO-8859-1 encoding."""
    adt_win1252 = "MSH|^~\\&|HOSPITAL|GRAHAME|20260224100000||ADT^A04|MSG00002|P|2.5\rPID|1||12345678900^CPF^BR|São Paulo^João^Maria|19800101|M|||".encode("iso-8859-1")

    parser = HL7v2Parser(adt_win1252.decode("iso-8859-1"))
    pid = PIDSegment.from_parser(parser)

    assert pid.patient_name["given"] == "João"
```

### 4.2 Testes de Integração

**File:** `tests/hl7v2/test_integration.py`

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.hl7v2.fixtures import PV_ADT_A04, TASY_ADT_A04

client = TestClient(app)

def test_adt_a04_success():
    """Test ADT^A04 message success."""
    response = client.post(
        "/hl7v2/adt-a04",
        content=PV_ADT_A04,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    ack = response.text
    assert "MSA|AA" in ack  # Application Accept

def test_adt_a04_invalid_api_key():
    """Test ADT^A04 with invalid API key."""
    response = client.post(
        "/hl7v2/adt-a04",
        content=PV_ADT_A04,
    )

    assert response.status_code == 401

def test_adt_a04_missing_pid():
    """Test ADT^A04 with missing PID segment."""
    invalid_adt = "MSH|^~\\&|HOSPITAL|GRAHAME|20260224100000||ADT^A04|MSG00003|P|2.5\r"

    response = client.post(
        "/hl7v2/adt-a04",
        content=invalid_adt,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 400
    ack = response.text
    assert "MSA|AE" in ack  # Application Error

def test_adt_a04_performance(benchmark):
    """Benchmark ADT^A04 processing (target: < 100ms)."""
    response = client.post(
        "/hl7v2/adt-a04",
        content=PV_ADT_A04,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    # Benchmark target: < 100ms p99
```

---

## 5. Deploy

### 5.1 Docker Compose (Redis)

```yaml
services:
  grahame:
    # ... existing config ...
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## 6. Troubleshooting

### 6.1 Encoding Issues

**Problem:** Acentos brasileiros (ã, ç, é) corrompidos.

**Solution:** Detect encoding e tente UTF-8 → ISO-8859-1:

```python
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    text = raw.decode("iso-8859-1")
```

### 6.2 Variações de Hospital

**Problem:** PV usa formatação diferente de TASY.

**Solution:** Parser é flexível com campos opcionais:

```python
pid.patient_name["given"] or ""
```

### 6.3 ACK Sempre Retorna 200

**Problem:** Erro de validação retorna HTTP 200 com ACK^AE.

**Solution:** Por design. ACK^AE indica erro de **negócio** (validação HL7), não erro HTTP. Erros HTTP (500, 503) indicam falhas de **infraestrutura**.

---

## 7. Timeline

| Fase | Dias | Responsável |
|------|------|-------------|
| **Fase 1:** Parser Core | 5 | DEV1 |
| - HL7v2 parser base | | |
| - MSH, PID, PV1 segment parsers | | |
| **Fase 2:** Message Handlers | 7 | DEV1 |
| - ADT^A04 handler | | |
| - ACK generator | | |
| **Fase 3:** FHIR Converters | 8 | DEV1 |
| - Patient converter | | |
| - Encounter converter | | |
| **Fase 4:** Event Publisher | 5 | DEV1 |
| - Redis Stream publisher | | |
| - Integration with subscriptions | | |
| **Fase 5:** Validation + Tests | 10 | DEV1 |
| - HL7v2 validator | | |
| - 30+ testes com mensagens reais | | |
| - Performance benchmarks | | |
| **Fase 6:** Integração + Deploy | 7 | DEV1 |
| - Endpoint /hl7v2/adt-a04 | | |
| - API Key authentication | | |
| - CI/CD + docker | | |

**Total: 42 dias**

---

## 8. Referências

- **Medplum HL7v2:** `packages/hl7/src/parse.ts`
- **HL7 2.5:** https://hl7.org/documentcenter/publictemp/27B5F2E3-28C1-4E55-AAB3-3F8EB37C4A6D/HL7v2.5_2007.pdf
- **HL7 Brasil:** http://www.hl7brasil.org.br/
