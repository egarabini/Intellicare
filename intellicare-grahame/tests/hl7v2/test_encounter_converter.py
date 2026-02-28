"""Tests for Encounter Converter (PV1 → FHIR Encounter)."""

import pytest

from grahame.hl7v2.parser import HL7v2Parser
from grahame.hl7v2.segments import MSHSegment, PV1Segment
from grahame.hl7v2.converters import EncounterConverter


@pytest.fixture
def sample_adt_message() -> str:
    """Sample ADT^A04 message with complete PV1 segment."""
    # PV1 has 44 fields, so we need to pad with empty fields to reach field 44
    pv1_fields = ["1", "I", "2000^01^Hospital Central^^^^BR", "E"] + [""] * 39 + ["20260224100000"]
    pv1_segment = "PV1|" + "|".join(pv1_fields)
    
    return (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        + pv1_segment
    )


def test_convert_complete_encounter(sample_adt_message):
    """Test complete PV1 to Encounter conversion."""
    parser = HL7v2Parser(sample_adt_message)
    msh = MSHSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)
    
    converter = EncounterConverter()
    encounter = converter.convert(pv1, msh, patient_id="patient-123")
    
    # Basic structure
    assert encounter["resourceType"] == "Encounter"
    assert encounter["status"] == "in-progress"
    assert encounter["meta"]["source"] == "urn:hl7:HOSPITAL:FACILITY"
    
    # Identifiers (MSH-10 + PV1-1)
    assert len(encounter["identifier"]) == 2
    assert encounter["identifier"][0]["use"] == "official"
    assert encounter["identifier"][0]["system"] == "urn:hl7:HOSPITAL:FACILITY"
    assert encounter["identifier"][0]["value"] == "MSG00001"
    assert encounter["identifier"][1]["use"] == "usual"
    assert encounter["identifier"][1]["value"] == "1"
    
    # Class (PV1-2: I → imp)
    assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    assert encounter["class"]["code"] == "imp"
    
    # Subject (Patient reference)
    assert encounter["subject"]["reference"] == "Patient/patient-123"
    
    # Location (PV1-3)
    assert len(encounter["location"]) == 1
    assert encounter["location"][0]["location"]["reference"] == "Location/unknown"
    assert encounter["location"][0]["location"]["display"] == "2000"
    
    # Hospitalization (PV1-4)
    assert encounter["hospitalization"]["admitSource"]["coding"][0]["system"] == \
        "http://terminology.hl7.org/CodeSystem/v2-0007"
    assert encounter["hospitalization"]["admitSource"]["coding"][0]["code"] == "E"
    
    # Period (PV1-44)
    assert encounter["period"]["start"] == "2026-02-24T10:00:00"


def test_convert_minimal_encounter():
    """Test minimal PV1 to Encounter conversion (only required fields)."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PV1|1|O"
    )
    
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)
    
    converter = EncounterConverter()
    encounter = converter.convert(pv1, msh)
    
    # Basic structure
    assert encounter["resourceType"] == "Encounter"
    assert encounter["status"] == "in-progress"
    
    # Class (PV1-2: O → amb)
    assert encounter["class"]["code"] == "amb"
    
    # Subject (default to unknown)
    assert encounter["subject"]["reference"] == "Patient/unknown"
    
    # No location, hospitalization, or period
    assert "location" not in encounter
    assert "hospitalization" not in encounter
    assert "period" not in encounter


def test_encounter_class_mapping():
    """Test patient class mapping (I→imp, O→amb, E→emer, P→imp)."""
    test_cases = [
        ("I", "imp"),   # Inpatient
        ("O", "amb"),   # Outpatient/Ambulatory
        ("E", "emer"),  # Emergency
        ("P", "imp"),   # Preadmit (treated as inpatient)
    ]
    
    for hl7_class, fhir_class in test_cases:
        message = (
            f"MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
            f"PV1|1|{hl7_class}"
        )
        
        parser = HL7v2Parser(message)
        msh = MSHSegment.from_parser(parser)
        pv1 = PV1Segment.from_parser(parser)
        
        converter = EncounterConverter()
        encounter = converter.convert(pv1, msh)
        
        assert encounter["class"]["code"] == fhir_class


def test_encounter_with_location():
    """Test encounter with assigned location (PV1-3)."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PV1|1|I|Emergency Room^ER-01^Bed 5"
    )
    
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)
    
    converter = EncounterConverter()
    encounter = converter.convert(pv1, msh)
    
    assert len(encounter["location"]) == 1
    assert encounter["location"][0]["location"]["display"] == "Emergency Room"


def test_encounter_without_location():
    """Test encounter without assigned location."""
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        "PV1|1|O"
    )
    
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)
    
    converter = EncounterConverter()
    encounter = converter.convert(pv1, msh)
    
    assert "location" not in encounter


def test_encounter_with_admit_datetime():
    """Test encounter with admit datetime (PV1-44)."""
    # PV1 with 44 fields
    pv1_fields = ["1", "I"] + [""] * 41 + ["20260315143000"]
    pv1_segment = "PV1|" + "|".join(pv1_fields)
    
    message = (
        "MSH|^~\\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5\r"
        + pv1_segment
    )
    
    parser = HL7v2Parser(message)
    msh = MSHSegment.from_parser(parser)
    pv1 = PV1Segment.from_parser(parser)
    
    converter = EncounterConverter()
    encounter = converter.convert(pv1, msh)
    
    assert encounter["period"]["start"] == "2026-03-15T14:30:00"

