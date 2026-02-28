"""Tests for compartment extraction — 12 scenarios."""

from intellicare_core.fhir_storage.compartments import extract_compartments


def test_patient_owns_compartment() -> None:
    r = {"resourceType": "Patient", "id": "p-001"}
    compartments = extract_compartments(r)
    assert "Patient/p-001" in compartments


def test_organization_owns_compartment() -> None:
    r = {"resourceType": "Organization", "id": "org-a"}
    compartments = extract_compartments(r)
    assert "Organization/org-a" in compartments


def test_observation_extracts_patient_subject() -> None:
    r = {"resourceType": "Observation", "subject": {"reference": "Patient/p-001"}}
    compartments = extract_compartments(r)
    assert "Patient/p-001" in compartments


def test_encounter_extracts_subject() -> None:
    r = {"resourceType": "Encounter", "id": "enc-1", "subject": {"reference": "Patient/p-002"}}
    compartments = extract_compartments(r)
    assert "Patient/p-002" in compartments
    assert "Encounter/enc-1" in compartments


def test_managing_organization_extracted() -> None:
    r = {
        "resourceType": "Patient",
        "id": "p-003",
        "managingOrganization": {"reference": "Organization/org-b"},
    }
    compartments = extract_compartments(r)
    assert "Organization/org-b" in compartments
    assert "Patient/p-003" in compartments


def test_medication_request_extracts_subject() -> None:
    r = {
        "resourceType": "MedicationRequest",
        "subject": {"reference": "Patient/p-004"},
    }
    compartments = extract_compartments(r)
    assert "Patient/p-004" in compartments


def test_no_compartment_for_empty_resource() -> None:
    r = {"resourceType": "Device"}
    compartments = extract_compartments(r)
    assert compartments == []


def test_compartments_deduplicated() -> None:
    r = {
        "resourceType": "Observation",
        "subject": {"reference": "Patient/p-001"},
        "patient": {"reference": "Patient/p-001"},
    }
    compartments = extract_compartments(r)
    assert compartments.count("Patient/p-001") == 1


def test_non_patient_subject_not_added() -> None:
    r = {
        "resourceType": "Observation",
        "subject": {"reference": "Group/g-001"},
    }
    compartments = extract_compartments(r)
    # Group references are not currently indexed as compartments
    assert "Group/g-001" not in compartments


def test_missing_id_on_owner_not_added() -> None:
    r = {"resourceType": "Patient"}  # no id
    compartments = extract_compartments(r)
    assert compartments == []


def test_encounter_own_compartment() -> None:
    r = {"resourceType": "Encounter", "id": "e-99"}
    compartments = extract_compartments(r)
    assert "Encounter/e-99" in compartments


def test_performer_list_extracts_practitioner() -> None:
    r = {
        "resourceType": "Observation",
        "performer": [{"reference": "Practitioner/dr-001"}],
    }
    compartments = extract_compartments(r)
    assert "Practitioner/dr-001" in compartments
