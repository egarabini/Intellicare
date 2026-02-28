import pytest

from grahame.ccda.terminology import (
    map_condition_status,
    map_encounter_status,
    map_immunization_status,
    map_medication_request_status,
    map_observation_status,
    map_procedure_status,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("active", "active"),
        ("completed", "resolved"),
        ("inactive", "inactive"),
        ("cancelled", "inactive"),
        ("unknown", "active"),
    ],
)
def test_condition_status_matrix(raw, expected):
    assert map_condition_status(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("active", "active"),
        ("completed", "completed"),
        ("suspended", "on-hold"),
        ("aborted", "stopped"),
        ("cancelled", "cancelled"),
        ("new", "draft"),
    ],
)
def test_medication_status_matrix(raw, expected):
    assert map_medication_request_status(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("active", "preliminary"),
        ("new", "registered"),
        ("completed", "final"),
        ("amended", "amended"),
        ("cancelled", "cancelled"),
    ],
)
def test_observation_status_matrix(raw, expected):
    assert map_observation_status(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("new", "preparation"),
        ("active", "in-progress"),
        ("suspended", "on-hold"),
        ("aborted", "stopped"),
        ("completed", "completed"),
        ("cancelled", "not-done"),
    ],
)
def test_procedure_status_matrix(raw, expected):
    assert map_procedure_status(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("completed", "completed"),
        ("active", "completed"),
        ("cancelled", "not-done"),
        ("aborted", "not-done"),
        ("nullified", "entered-in-error"),
    ],
)
def test_immunization_status_matrix(raw, expected):
    assert map_immunization_status(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("new", "planned"),
        ("active", "in-progress"),
        ("arrived", "arrived"),
        ("triaged", "triaged"),
        ("completed", "finished"),
        ("cancelled", "cancelled"),
    ],
)
def test_encounter_status_matrix(raw, expected):
    assert map_encounter_status(raw) == expected
