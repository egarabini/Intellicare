# W8-A — CCDA Parser/Import — Especificação Técnica

**Workstream:** W8-A
**Responsável:** DEV0
**Módulo:** `intellicare-grahame` (+ novo sub-módulo `ccda`)
**Status:** 📋 Especificação Técnica
**Data:** 2026-02-24
**Estimativa:** 30 dias

---

## 1. Arquitetura

### 1.1 Componentes

```
intellicare-grahame/
├── app/
│   ├── api/
│   │   └── ccda.py              # Endpoint $ccda-import
│   ├── ccda/
│   │   ├── __init__.py
│   │   ├── parser.py            # CCDAParser (main)
│   │   ├── validators.py        # Schema CDA R2 validator
│   │   ├── converters/          # CCDA → FHIR converters
│   │   │   ├── patient.py       # Patient converter
│   │   │   ├── condition.py     # Condition converter
│   │   │   ├── medication.py    # MedicationRequest converter
│   │   │   ├── observation.py   # Observation converter
│   │   │   ├── procedure.py     # Procedure converter
│   │   │   ├── immunization.py  # Immunization converter
│   │   │   └── encounter.py     # Encounter converter
│   │   ├── sections/            # CCDA section parsers
│   │   │   ├── __init__.py
│   │   │   ├── patient.py       # recordTarget parser
│   │   │   ├── problems.py      # problemListEntry section
│   │   │   ├── medications.py   # medicationActivity section
│   │   │   ├── results.py       # results section
│   │   │   ├── procedures.py    # procedures section
│   │   │   ├── immunizations.py # immunizations section
│   │   │   └── encounters.py    # encounters section
│   │   └── models.py            # Pydantic models (CCDA data)
│   └── fhir/
│       └── ccda_operations.py   # FHIR Operation $ccda-import
├── tests/
│   ├── ccda/
│   │   ├── fixtures/            # CCDA reais brasileiros
│   │   │   ├── pv_ccda.xml
│   │   │   ├── tasy_ccda.xml
│   │   │   ├── mv_ccda.xml
│   │   │   └── sysimal_ccda.xml
│   │   ├── test_parser.py
│   │   ├── test_validators.py
│   │   ├── test_converters.py
│   │   ├── test_sections.py
│   │   └── test_integration.py  # End-to-end tests
│   └── benchmarks/
│       └── test_ccda_performance.py
└── requirements.txt              # + lxml, xmlschema
```

### 1.2 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| **Parser XML** | `lxml` | Fast, secure, XXE protection built-in |
| **Schema Validator** | `xmlschema` | CDA R2 schema validation |
| **FHIR Converter** | `fhir.resources` | Type-safe FHIR R4 models |
| **Encoding** | `chardet` | Auto-detect ISO-8859-1, Windows-1252 |
| **Validation** | Pydantic v2 | Fast validation, type safety |

---

## 2. Implementação Core

### 2.1 Endpoint Principal

**File:** `app/api/ccda.py`

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.ccda.parser import CCDAParser
from app.ccda.validators import CDAValidator
from app.fhir.core import FHIRHandler

router = APIRouter(prefix="/fhir/DocumentReference", tags=["CCDA"])

class CCDAImportResponse(BaseModel):
    resourceType: str = "Bundle"
    type: str = "collection"
    entry: list[dict]
    meta: dict

@router.post("/$ccda-import")
async def ccda_import(
    file: UploadFile = File(..., description="CCDA XML document")
) -> CCDAImportResponse:
    """
    Import CCDA document and convert to FHIR R4 resources.

    Accepts: application/xml, application/pdf+ccda
    Returns: FHIR Bundle with imported resources
    """
    # Detect encoding
    raw_content = await file.read()
    encoding = _detect_encoding(raw_content)

    # Parse CCDA
    parser = CCDAParser()
    try:
        ccda_doc = parser.parse(raw_content.decode(encoding))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CCDA parsing failed: {e}")

    # Validate against CDA R2 schema
    validator = CDAValidator()
    validation_result = validator.validate(ccda_doc)
    if not validation_result.valid:
        return JSONResponse(
            status_code=400,
            content={
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "structure",
                        "diagnostics": err
                    }
                    for err in validation_result.errors
                ]
            }
        )

    # Convert to FHIR
    fhir_handler = FHIRHandler()
    resources = fhir_handler.convert_ccda_to_fhir(ccda_doc)

    # Persist resources
    persisted = []
    for resource in resources:
        persisted_resource = await fhir_handler.create_resource(resource)
        persisted.append(persisted_resource)

    return CCDAImportResponse(
        resourceType="Bundle",
        type="collection",
        entry=[{"resource": r.dict()} for r in persisted],
        meta={
            "importedAt": datetime.now().isoformat(),
            "sourceFormat": "ccda",
            "resourcesImported": len(persisted),
            "processingTimeMs": parser.processing_time_ms
        }
    )

def _detect_encoding(raw_content: bytes) -> str:
    """Detect encoding from XML declaration or BOM."""
    import chardet
    result = chardet.detect(raw_content)
    return result["encoding"] or "utf-8"
```

### 2.2 CCDA Parser Core

**File:** `app/ccda/parser.py`

```python
from lxml import etree
from typing import Optional
import time

from app.ccda.models import CCDADocument
from app.ccda.sections import (
    PatientSectionParser,
    ProblemsSectionParser,
    MedicationsSectionParser,
    ResultsSectionParser,
    ProceduresSectionParser,
    ImmunizationsSectionParser,
    EncountersSectionParser,
)

class CCDAParser:
    """
    Parse CCDA (CDA R2) documents and extract clinical data.

    Security:
    - XXE protection: Disable DTD, entities, XIncludes
    - Safe parsing: Only allow CDA R2 schema
    """

    # CDA R2 namespace
    NS = {"cda": "urn:hl7-org:v3"}

    # Section templates (CDA R2)
    SECTION_TEMPLATES = {
        "problemListEntry": "2.16.840.1.113883.10.20.22.2.5.1",
        "medicationActivity": "2.16.840.1.113883.10.20.22.4.16",
        "results": "2.16.840.1.113883.10.20.22.2.3.1",
        "procedures": "2.16.840.1.113883.10.20.22.2.7.1",
        "immunizations": "2.16.840.1.113883.10.20.22.2.2.1",
        "encounters": "2.16.840.1.113883.10.20.22.2.22.1",
    }

    def __init__(self):
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def parse(self, xml_content: str) -> CCDADocument:
        """Parse CCDA XML and extract all clinical sections."""
        self._start_time = time.time()

        # Secure XML parsing (XXE protection)
        parser = etree.XMLParser(
            resolve_entities=False,      # Disable entity expansion
            remove_comments=True,         # Remove comments
            remove_pis=True,              # Remove processing instructions
            dtd_validation=False,         # Disable DTD
            load_dtd=False,               # Don't load DTD
            no_network=True,              # Disable network access
        )

        try:
            root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML: {e}")

        # Validate CDA root
        if root.tag != "{urn:hl7-org:v3}ClinicalDocument":
            raise ValueError("Root element must be ClinicalDocument")

        # Extract sections
        document = CCDADocument()

        # Patient section
        patient_parser = PatientSectionParser(self.NS)
        document.patient = patient_parser.parse(root)

        # Problems section
        if self._has_section(root, "problemListEntry"):
            problems_parser = ProblemsSectionParser(self.NS)
            document.conditions = problems_parser.parse(root)

        # Medications section
        if self._has_section(root, "medicationActivity"):
            meds_parser = MedicationsSectionParser(self.NS)
            document.medications = meds_parser.parse(root)

        # Results section
        if self._has_section(root, "results"):
            results_parser = ResultsSectionParser(self.NS)
            document.observations = results_parser.parse(root)

        # Procedures section
        if self._has_section(root, "procedures"):
            proc_parser = ProceduresSectionParser(self.NS)
            document.procedures = proc_parser.parse(root)

        # Immunizations section
        if self._has_section(root, "immunizations"):
            imm_parser = ImmunizationsSectionParser(self.NS)
            document.immunizations = imm_parser.parse(root)

        # Encounters section
        if self._has_section(root, "encounters"):
            enc_parser = EncountersSectionParser(self.NS)
            document.encounters = enc_parser.parse(root)

        self._end_time = time.time()
        return document

    def _has_section(self, root: etree.Element, section_name: str) -> bool:
        """Check if CCDA has a specific section."""
        template_id = self.SECTION_TEMPLATES.get(section_name)
        if not template_id:
            return False

        xpath = f".//cda:section[cda:templateId/@root='{template_id}']"
        sections = root.xpath(xpath, namespaces=self.NS)
        return len(sections) > 0

    @property
    def processing_time_ms(self) -> float:
        """Return processing time in milliseconds."""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time) * 1000
        return 0.0
```

### 2.3 Patient Section Parser

**File:** `app/ccda/sections/patient.py`

```python
from lxml import etree
from typing import Optional

from app.ccda.models import PatientInfo

class PatientSectionParser:
    """Extract patient demographic data from recordTarget."""

    def __init__(self, ns: dict):
        self.ns = ns

    def parse(self, root: etree.Element) -> PatientInfo:
        """Parse patient data from recordTarget/patientRole."""

        # XPath to patient role
        patient_role = root.find(".//cda:recordTarget/cda:patientRole", self.ns)
        if patient_role is None:
            raise ValueError("Missing recordTarget/patientRole")

        patient = patient_role.find("cda:patient", self.ns)
        if patient is None:
            raise ValueError("Missing patient element")

        # Extract identifiers
        identifiers = self._parse_identifiers(patient_role)

        # Extract name
        name = self._parse_name(patient)

        # Extract gender
        gender = self._parse_gender(patient)

        # Extract birthdate
        birthdate = self._parse_birthdate(patient)

        # Extract race
        race = self._parse_race(patient)

        # Extract address
        address = self._parse_address(patient)

        # Extract phone
        phone = self._parse_phone(patient_role)

        return PatientInfo(
            identifiers=identifiers,
            name=name,
            gender=gender,
            birthDate=birthdate,
            race=race,
            address=address,
            phone=phone,
        )

    def _parse_identifiers(self, patient_role: etree.Element) -> list[dict]:
        """Parse patient ID list (II)."""
        identifiers = []

        for ii in patient_role.findall("cda:id", self.ns):
            identifiers.append({
                "system": ii.get("root"),
                "value": ii.get("extension"),
                "assigner": ii.get("assigningAuthorityName"),
            })

        return identifiers

    def _parse_name(self, patient: etree.Element) -> dict:
        """Parse patient name (EN)."""
        name_elem = patient.find("cda:name", self.ns)
        if name_elem is None:
            return {"use": "official", "text": "Unknown"}

        given = []
        for given_elem in name_elem.findall("cda:given", self.ns):
            given.append(given_elem.text or "")

        family_elem = name_elem.find("cda:family", self.ns)
        family = family_elem.text if family_elem is not None else ""

        return {
            "use": "official",
            "given": given,
            "family": family,
            "text": " ".join(given + [family]),
        }

    def _parse_gender(self, patient: etree.Element) -> str:
        """Parse administrative gender (M/F/U)."""
        gender_elem = patient.find("cda:administrativeGenderCode", self.ns)
        if gender_elem is None:
            return "unknown"

        code = gender_elem.get("code")
        gender_map = {"M": "male", "F": "female", "U": "unknown"}
        return gender_map.get(code, "unknown")

    def _parse_birthdate(self, patient: etree.Element) -> str:
        """Parse birth time (TS)."""
        birth_elem = patient.find("cda:birthTime", self.ns)
        if birth_elem is None:
            return None

        # HL7 TS format -> ISO 8601
        value = birth_elem.get("value")
        return self._ts_to_iso8601(value)

    def _parse_race(self, patient: etree.Element) -> Optional[dict]:
        """Parse raceCode (US extension)."""
        race_elem = patient.find("cda:raceCode", self.ns)
        if race_elem is None:
            return None

        return {
            "system": "urn:oid:2.16.840.1.113883.6.238",  # CDC Race
            "code": race_elem.get("code"),
            "display": race_elem.get("displayName"),
        }

    def _parse_address(self, patient: etree.Element) -> Optional[dict]:
        """Parse patient address (AD)."""
        addr_elem = patient.find("cda:addr", self.ns)
        if addr_elem is None:
            return None

        street_line = addr_elem.find("cda:streetAddressLine", self.ns)
        city = addr_elem.find("cda:city", self.ns)
        state = addr_elem.find("cda:state", self.ns)
        postal = addr_elem.find("cda:postalCode", self.ns)
        country = addr_elem.find("cda:country", self.ns)

        lines = []
        if street_line is not None and street_line.text:
            lines.append(street_line.text)

        return {
            "use": "home",
            "type": "both",
            "line": lines,
            "city": city.text if city is not None else None,
            "state": state.text if state is not None else None,
            "postalCode": postal.text if postal is not None else None,
            "country": country.text if country is not None else None,
        }

    def _parse_phone(self, patient_role: etree.Element) -> Optional[dict]:
        """Parse phone number (TEL)."""
        phone_elem = patient_role.find("cda:telecom", self.ns)
        if phone_elem is None:
            return None

        value = phone_elem.get("value")
        # Convert tel: to tel:
        if value and value.startswith("tel:"):
            value = value[4:]

        return {
            "system": "phone",
            "value": value,
            "use": "mobile",
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
```

### 2.4 FHIR Converter — Patient

**File:** `app/ccda/converters/patient.py`

```python
from fhir.resources.patient import Patient, PatientIdentifier, HumanName, Address, ContactPoint
from fhir.resources.extension import Extension

from app.ccda.models import PatientInfo

class PatientConverter:
    """Convert CCDA patient data to FHIR Patient resource."""

    def convert(self, patient_info: PatientInfo) -> Patient:
        """Convert CCDA PatientInfo to FHIR Patient."""

        # Build identifiers
        identifiers = []
        for ident in patient_info.identifiers:
            identifiers.append(PatientIdentifier(
                use="usual",
                system=ident["system"],
                value=ident["value"],
            ))

        # Build name
        name = HumanName(
            use=patient_info.name["use"],
            given=patient_info.name["given"],
            family=patient_info.name["family"],
        )

        # Build address
        address = None
        if patient_info.address:
            address = Address(
                use=patient_info.address["use"],
                type=patient_info.address["type"],
                line=patient_info.address["line"],
                city=patient_info.address["city"],
                state=patient_info.address["state"],
                postalCode=patient_info.address["postalCode"],
                country=patient_info.address["country"],
            )

        # Build phone
        telecom = None
        if patient_info.phone:
            telecom = [ContactPoint(
                system=patient_info.phone["system"],
                value=patient_info.phone["value"],
                use=patient_info.phone["use"],
            )]

        # Build extensions (race)
        extension = None
        if patient_info.race:
            extension = [
                Extension(
                    url="http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                    extension=[
                        Extension(
                            url="ombCategory",
                            valueCoding={
                                "system": patient_info.race["system"],
                                "code": patient_info.race["code"],
                                "display": patient_info.race["display"],
                            },
                        )
                    ],
                )
            ]

        return Patient(
            identifier=identifiers,
            name=[name],
            gender=patient_info.gender,
            birthDate=patient_info.birthDate,
            address=[address] if address else None,
            telecom=telecom,
            extension=extension,
        )
```

### 2.5 CDA R2 Validator

**File:** `app/ccda/validators.py`

```python
from xmlschema import XMLSchema
from xmlschema.exceptions import XMLSchemaValidationError
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CDAValidator:
    """
    Validate CCDA documents against CDA R2 schema.

    Schema: https://www.cdaeucal.org/schema/CDA.r2.xsd
    """

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with CDA R2 schema.

        Args:
            schema_path: Path to CDA.r2.xsd (default: bundled schema)
        """
        if schema_path is None:
            # Use bundled schema
            schema_path = Path(__file__).parent / "schemas" / "CDA.r2.xsd"

        if not schema_path.exists():
            logger.warning(f"CDA schema not found at {schema_path}, validation disabled")
            self._schema = None
        else:
            try:
                self._schema = XMLSchema(str(schema_path))
            except Exception as e:
                logger.error(f"Failed to load CDA schema: {e}")
                self._schema = None

    def validate(self, ccda_doc: str) -> "ValidationResult":
        """
        Validate CCDA document against CDA R2 schema.

        Returns:
            ValidationResult with errors/warnings
        """
        if self._schema is None:
            # Schema not loaded, skip validation
            return ValidationResult(valid=True, warnings=["Schema validation disabled"])

        try:
            self._schema.validate(ccda_doc)
            return ValidationResult(valid=True, errors=[], warnings=[])
        except XMLSchemaValidationError as e:
            return ValidationResult(
                valid=False,
                errors=[str(e)],
                warnings=[],
            )

class ValidationResult:
    """Validation result from CDA R2 schema validation."""

    def __init__(
        self,
        valid: bool,
        errors: list[str],
        warnings: list[str],
    ):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
```

### 2.6 Pydantic Models

**File:** `app/ccda/models.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class PatientInfo(BaseModel):
    """Patient demographic data from CCDA."""
    identifiers: List[dict]
    name: dict
    gender: str
    birthDate: Optional[str]
    race: Optional[dict]
    address: Optional[dict]
    phone: Optional[dict]

class ConditionInfo(BaseModel):
    """Problem/condition from CCDA problemListEntry."""
    code: dict
    status: str
    onset: Optional[str]
    severity: Optional[dict]

class MedicationInfo(BaseModel):
    """Medication from CCDA medicationActivity."""
    medication_code: dict
    dosage: dict
    route: Optional[dict]
    frequency: Optional[dict]

class ObservationInfo(BaseModel):
    """Lab result from CCDA results section."""
    code: dict
    value: Optional[dict]
    unit: Optional[str]
    effective: Optional[str]
    reference_range: Optional[dict]

class ProcedureInfo(BaseModel):
    """Procedure from CCDA procedures section."""
    code: dict
    performed: Optional[str]
    status: str

class ImmunizationInfo(BaseModel):
    """Immunization from CCDA immunizations section."""
    vaccine_code: dict
    occurrence: Optional[str]
    lot_number: Optional[str]
    expiration: Optional[str]

class EncounterInfo(BaseModel):
    """Encounter from CCDA encounters section."""
    class_code: dict
    period: dict
    location: Optional[dict]
    discharge_disposition: Optional[dict]

class CCDADocument(BaseModel):
    """Complete CCDA document with all sections."""
    patient: PatientInfo
    conditions: List[ConditionInfo] = []
    medications: List[MedicationInfo] = []
    observations: List[ObservationInfo] = []
    procedures: List[ProcedureInfo] = []
    immunizations: List[ImmunizationInfo] = []
    encounters: List[EncounterInfo] = []
```

---

## 3. Testes

### 3.1 Testes de Parser

**File:** `tests/ccda/test_parser.py`

```python
import pytest
from lxml import etree

from app.ccda.parser import CCDAParser
from app.ccda.models import CCDADocument

@pytest.fixture
def sample_ccda() -> str:
    """Sample CCDA document (minimal)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id extension="12345" root="1.2.840.113619.21.1.12345"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of episode note"/>
  <title>CCDA Sample</title>
  <effectiveTime value="20260101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id extension="12345678900" root="2.16.840.1.113883.4.6"/>
      <patient>
        <name>
          <given>João</given>
          <family>Silva</family>
        </name>
        <administrativeGenderCode code="M"/>
        <birthTime value="19800101"/>
        <raceCode code="2106-3" displayName="White" codeSystem="2.16.840.1.113883.6.238"/>
      </patient>
    </patientRole>
  </recordTarget>
</ClinicalDocument>
"""

def test_parse_ccda(sample_ccda: str):
    """Test basic CCDA parsing."""
    parser = CCDAParser()
    doc = parser.parse(sample_ccda)

    assert isinstance(doc, CCDADocument)
    assert doc.patient.name["given"] == ["João"]
    assert doc.patient.name["family"] == "Silva"
    assert doc.patient.gender == "male"
    assert doc.patient.birthDate == "1980-01-01"
    assert parser.processing_time_ms > 0

def test_parse_ccda_with_encoding():
    """Test CCDA with Windows-1252 encoding."""
    # Portuguese characters
    ccda_win1252 = "<?xml version='1.0' encoding='Windows-1252'?>...".encode("windows-1252")

    parser = CCDAParser()
    doc = parser.parse(ccda_win1252.decode("windows-1252"))

    assert doc.patient.name["given"]  # Should parse correctly

def test_parse_invalid_xml():
    """Test that invalid XML raises error."""
    parser = CCDAParser()

    with pytest.raises(ValueError, match="Invalid XML"):
        parser.parse("not xml")

def test_parse_missing_record_target():
    """Test that missing recordTarget raises error."""
    ccda_no_patient = """<?xml version="1.0"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <!-- Missing recordTarget -->
</ClinicalDocument>
"""

    parser = CCDAParser()
    with pytest.raises(ValueError, match="recordTarget"):
        parser.parse(ccda_no_patient)
```

### 3.2 Testes de Integração

**File:** `tests/ccda/test_integration.py`

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.ccda.fixtures import PV_CCDA, TASY_CCDA, MV_CCDA

client = TestClient(app)

def test_ccda_import_pv():
    """Test CCDA import from PV system."""
    response = client.post(
        "/fhir/DocumentReference/$ccda-import",
        files={"file": ("pv_ccda.xml", PV_CCDA, "application/xml")}
    )

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["meta"]["sourceFormat"] == "ccda"
    assert len(bundle["entry"]) > 0

    # Check Patient resource
    patient_entry = [e for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient"][0]
    assert patient_entry["resource"]["name"][0]["family"] == "Silva"

def test_ccda_import_invalid_schema():
    """Test CCDA with invalid schema."""
    invalid_ccda = "<ClinicalDocument></ClinicalDocument>"

    response = client.post(
        "/fhir/DocumentReference/$ccda-import",
        files={"file": ("invalid.xml", invalid_ccda, "application/xml")}
    )

    assert response.status_code == 400
    assert response.json()["resourceType"] == "OperationOutcome"

def test_ccda_import_performance(benchmark):
    """Benchmark CCDA parsing performance."""
    # 100-page CCDA should process in < 10s
    large_ccda = load_large_ccda_fixture()

    parser = CCDAParser()
    doc = benchmark(parser.parse, large_ccda)

    assert parser.processing_time_ms < 10000  # 10 seconds
```

---

## 4. Performance Benchmarks

### 4.1 Benchmark Script

**File:** `tests/benchmarks/test_ccda_performance.py`

```python
import pytest
import time
from pathlib import Path

from app.ccda.parser import CCDAParser

@pytest.mark.benchmark
def test_ccda_parsing_performance():
    """
    Benchmark: CCDA parsing should be < 10s for 100-page document.

    Target:
    - Small CCDA (10 pages): < 1s
    - Medium CCDA (50 pages): < 5s
    - Large CCDA (100 pages): < 10s
    """
    fixtures = Path(__file__).parent.parent / "ccda" / "fixtures"

    # Test small CCDA
    small_ccda = (fixtures / "small_ccda.xml").read_text()
    start = time.time()
    parser = CCDAParser()
    parser.parse(small_ccda)
    small_time = (time.time() - start) * 1000
    assert small_time < 1000  # < 1s

    # Test medium CCDA
    medium_ccda = (fixtures / "medium_ccda.xml").read_text()
    start = time.time()
    parser.parse(medium_ccda)
    medium_time = (time.time() - start) * 1000
    assert medium_time < 5000  # < 5s

    # Test large CCDA
    large_ccda = (fixtures / "large_ccda.xml").read_text()
    start = time.time()
    parser.parse(large_ccda)
    large_time = (time.time() - start) * 1000
    assert large_time < 10000  # < 10s

    print(f"Small CCDA: {small_time:.0f}ms")
    print(f"Medium CCDA: {medium_time:.0f}ms")
    print(f"Large CCDA: {large_time:.0f}ms")
```

---

## 5. Deploy

### 5.1 Dependências

**File:** `requirements.txt` (adicionar)

```txt
# CCDA Parser
lxml>=5.1.0              # Fast XML parsing with XXE protection
xmlschema>=3.0.0         # CDA R2 schema validation
chardet>=5.2.0           # Encoding detection
```

### 5.2 Dockerfile Update

```dockerfile
# ... existing stages ...

# Install CCDA dependencies
RUN pip install --no-cache-dir lxml xmlschema chardet

# Copy CDA R2 schema
COPY app/ccda/schemas /app/app/ccda/schemas
```

---

## 6. Troubleshooting

### 6.1 XXE Attack Prevention

**Problem:** Malicious CCDA with XXE payload.

**Solution:** Parser disables entities, DTD, network access:

```python
parser = etree.XMLParser(
    resolve_entities=False,  # Prevent XXE
    no_network=True,         # Prevent external entity loading
    load_dtd=False,          # Don't load DTD
)
```

### 6.2 Encoding Issues

**Problem:** CCDA with ISO-8859-1 encoding (acentos brasileiros).

**Solution:** Auto-detect encoding with chardet:

```python
import chardet
raw_content = await file.read()
encoding = chardet.detect(raw_content)["encoding"] or "utf-8"
text = raw_content.decode(encoding)
```

### 6.3 Missing Sections

**Problem:** CCDA doesn't have all sections (graceful degradation).

**Solution:** Check for section presence before parsing:

```python
if self._has_section(root, "problemListEntry"):
    document.conditions = problems_parser.parse(root)
```

---

## 7. Timeline

| Fase | Dias | Responsável |
|------|------|-------------|
| **Fase 1:** Parser Core | 5 | DEV0 |
| - Parser base, security, XXE protection | | |
| - Patient section parser | | |
| **Fase 2:** Section Parsers | 10 | DEV0 |
| - Problems, medications, results | | |
| - Procedures, immunizations, encounters | | |
| **Fase 3:** FHIR Converters | 8 | DEV0 |
| - Patient, Condition, MedicationRequest | | |
| - Observation, Procedure, Immunization, Encounter | | |
| **Fase 4:** Validation + Tests | 5 | DEV0 |
| - CDA R2 schema validator | | |
| - 50+ tests com CCDA reais | | |
| - Performance benchmarks | | |
| **Fase 5:** Integração + Deploy | 2 | DEV0 |
| - Endpoint $ccda-import | | |
| - CI/CD + docker | | |

**Total: 30 dias**

---

## 8. Referências

- **Medplum CCDA:** `packages/ccda/src/parse.ts`
- **CDA R2 Schema:** https://www.cdaeucal.org/schema/CDA.r2.xsd
- **ANS/DT:** Padrão brasileiro CCDA
