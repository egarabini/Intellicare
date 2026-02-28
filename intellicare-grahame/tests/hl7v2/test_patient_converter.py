"""Tests for Patient Converter (PID → FHIR Patient)."""

import pytest

from grahame.hl7v2.converters.patient import PatientConverter
from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment, PIDSegment


@pytest.fixture
def sample_adt_message() -> str:
    """Sample ADT^A04 message with complete PID segment."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||Silva^João^Carlos^Jr^Dr||19800101|M||"
        "2106-3^White^HL70005|Rua Teste, 123^^São Paulo^SP^01234-567^BR||5511999999999|||||||||2135-2^Hispanic^HL70189\r"
    )


@pytest.fixture
def minimal_adt_message() -> str:
    """Minimal ADT^A04 message with only required PID fields."""
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||Silva^João||19800101|M\r"
    )


def test_convert_complete_patient(sample_adt_message):
    """Test converting complete PID segment to FHIR Patient."""
    parser = HL7v2Parser(sample_adt_message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)

    converter = PatientConverter()
    patient = converter.convert(pid, msh)

    # Verify resource type
    assert patient["resourceType"] == "Patient"

    # Verify meta source
    assert "meta" in patient
    assert patient["meta"]["source"] == "urn:hl7:HOSPITAL:FACILITY"

    # Verify identifier
    assert "identifier" in patient
    assert len(patient["identifier"]) == 1
    assert patient["identifier"][0]["value"] == "12345678900"
    assert patient["identifier"][0]["use"] == "usual"

    # Verify name
    assert "name" in patient
    assert len(patient["name"]) == 1
    assert patient["name"][0]["family"] == "Silva"
    assert patient["name"][0]["given"] == ["João", "Carlos"]
    assert patient["name"][0]["prefix"] == ["Dr"]
    assert patient["name"][0]["suffix"] == ["Jr"]

    # Verify birthDate
    assert patient["birthDate"] == "1980-01-01"

    # Verify gender
    assert patient["gender"] == "male"

    # Verify address
    assert "address" in patient
    assert len(patient["address"]) == 1
    assert patient["address"][0]["line"] == ["Rua Teste, 123"]
    assert patient["address"][0]["city"] == "São Paulo"
    assert patient["address"][0]["state"] == "SP"
    assert patient["address"][0]["postalCode"] == "01234-567"
    assert patient["address"][0]["country"] == "BR"

    # Verify telecom
    assert "telecom" in patient
    assert len(patient["telecom"]) == 1
    assert patient["telecom"][0]["system"] == "phone"
    assert patient["telecom"][0]["value"] == "5511999999999"

    # Verify extensions (race and ethnicity)
    assert "extension" in patient
    assert len(patient["extension"]) == 2


def test_convert_minimal_patient(minimal_adt_message):
    """Test converting minimal PID segment to FHIR Patient."""
    parser = HL7v2Parser(minimal_adt_message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)

    converter = PatientConverter()
    patient = converter.convert(pid, msh)

    # Verify required fields
    assert patient["resourceType"] == "Patient"
    assert patient["identifier"][0]["value"] == "12345678900"
    assert patient["name"][0]["family"] == "Silva"
    assert patient["name"][0]["given"] == ["João"]
    assert patient["birthDate"] == "1980-01-01"
    assert patient["gender"] == "male"

    # Verify optional fields are not present
    assert "address" not in patient or not patient.get("address")
    assert "extension" not in patient or not patient.get("extension")


def test_identifier_with_cpf():
    """Test identifier mapping for CPF (Brazilian tax ID)."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^CPF||Silva^João||19800101|M\r"
    )
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)

    converter = PatientConverter()
    patient = converter.convert(pid, msh)

    # Verify CPF identifier system
    assert patient["identifier"][0]["system"] == "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf"
    assert patient["identifier"][0]["type"]["coding"][0]["code"] == "CPF"


def test_name_without_middle_name():
    """Test name conversion without middle name."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||12345678900^^^HOSPITAL^MR||Silva^João||||M\r"
    )
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)

    converter = PatientConverter()
    patient = converter.convert(pid, msh)

    # Verify name has only first name
    assert patient["name"][0]["family"] == "Silva"
    assert patient["name"][0]["given"] == ["João"]
    assert "prefix" not in patient["name"][0]
    assert "suffix" not in patient["name"][0]


def test_gender_mapping():
    """Test gender mapping from HL7v2 to FHIR."""
    test_cases = [
        ("M", "male"),
        ("F", "female"),
        ("U", "unknown"),
        ("O", "other"),
    ]

    for hl7_gender, fhir_gender in test_cases:
        message = (
            f"MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
            f"PID|1||12345678900^^^HOSPITAL^MR||Silva^João||19800101|{hl7_gender}\r"
        )
        parser = HL7v2Parser(message)
        msh = MSHSegment.from_parser(parser)
        pid = PIDSegment.from_parser(parser)

        converter = PatientConverter()
        patient = converter.convert(pid, msh)

        assert patient["gender"] == fhir_gender


def test_patient_without_identifier():
    """Test patient conversion when identifier is missing."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PID|1||||Silva^João||19800101|M\r"
    )
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pid = PIDSegment.from_parser(parser)

    converter = PatientConverter()
    patient = converter.convert(pid, msh)

    # Should still create patient without identifier
    assert patient["resourceType"] == "Patient"
    assert "identifier" not in patient or not patient.get("identifier")

