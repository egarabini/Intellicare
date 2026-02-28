"""Tests for FHIR search parser — 18 scenarios."""

from intellicare_core.fhir_search.parser import parse_search_params
from intellicare_core.fhir_search.models import SearchRequest


def test_empty_params_returns_defaults() -> None:
    req = parse_search_params("Patient", {})
    assert req.resource_type == "Patient"
    assert req.filters == []
    assert req.count == 100
    assert req.offset == 0


def test_simple_filter() -> None:
    req = parse_search_params("Patient", {"status": "active"})
    assert len(req.filters) == 1
    f = req.filters[0]
    assert f.code == "status"
    assert f.op == "eq"
    assert f.value == "active"


def test_prefix_gt_operator() -> None:
    req = parse_search_params("Patient", {"birthdate": "gt1990-01-01"})
    f = req.filters[0]
    assert f.op == "gt"
    assert f.value == "1990-01-01"


def test_prefix_le_operator() -> None:
    req = parse_search_params("Observation", {"value-quantity": "le100"})
    f = req.filters[0]
    assert f.op == "le"
    assert f.value == "100"


def test_prefix_ge_operator() -> None:
    req = parse_search_params("Observation", {"value-quantity": "ge50"})
    f = req.filters[0]
    assert f.op == "ge"
    assert f.value == "50"


def test_modifier_contains() -> None:
    req = parse_search_params("Patient", {"name:contains": "silva"})
    f = req.filters[0]
    assert f.code == "name"
    assert f.modifier == "contains"
    assert f.op == "co"


def test_modifier_exact() -> None:
    req = parse_search_params("Patient", {"family:exact": "Silva"})
    f = req.filters[0]
    assert f.code == "family"
    assert f.modifier == "exact"
    assert f.op == "eq"


def test_token_system_pipe() -> None:
    req = parse_search_params("Patient", {"identifier": "http://cpf.gov.br|12345678901"})
    f = req.filters[0]
    assert f.system == "http://cpf.gov.br"
    assert f.value == "12345678901"


def test_count_param() -> None:
    req = parse_search_params("Patient", {"_count": "20"})
    assert req.count == 20


def test_count_clamped_to_1000() -> None:
    req = parse_search_params("Patient", {"_count": "9999"})
    assert req.count == 1000


def test_offset_param() -> None:
    req = parse_search_params("Patient", {"_offset": "50"})
    assert req.offset == 50


def test_sort_param_single() -> None:
    req = parse_search_params("Patient", {"_sort": "name"})
    assert "name" in req.sort


def test_sort_param_descending() -> None:
    req = parse_search_params("Patient", {"_sort": "-birthdate"})
    assert "-birthdate" in req.sort


def test_include_param() -> None:
    req = parse_search_params("Observation", {"_include": "Observation:subject"})
    assert "Observation:subject" in req.include


def test_summary_param() -> None:
    req = parse_search_params("Patient", {"_summary": "true"})
    assert req.summary == "true"


def test_unknown_underscore_param_ignored() -> None:
    req = parse_search_params("Patient", {"_unknown": "value", "status": "active"})
    assert len(req.filters) == 1
    assert req.filters[0].code == "status"


def test_multiple_filters() -> None:
    req = parse_search_params("Patient", {"status": "active", "gender": "female"})
    codes = {f.code for f in req.filters}
    assert "status" in codes
    assert "gender" in codes


def test_id_filter() -> None:
    req = parse_search_params("Patient", {"_id": "p-001"})
    f = req.filters[0]
    assert f.code == "_id"
    assert f.value == "p-001"
