"""Tests for FieldFilter — 15 scenarios."""

import pytest

from intellicare_core.access.field_filter import FieldFilter


@pytest.fixture
def ff() -> type[FieldFilter]:
    return FieldFilter


# ── apply_hidden ──────────────────────────────────────────────────────────────


def test_apply_hidden_removes_single_field(ff) -> None:
    resource = {"id": "p-1", "meta": {"versionId": "1"}, "active": True}
    result = ff.apply_hidden(resource, ["meta"])
    assert "meta" not in result
    assert result["id"] == "p-1"


def test_apply_hidden_removes_multiple_fields(ff) -> None:
    resource = {"id": "p-1", "meta": {}, "text": "note", "active": True}
    result = ff.apply_hidden(resource, ["meta", "text"])
    assert "meta" not in result
    assert "text" not in result
    assert "active" in result


def test_apply_hidden_no_effect_on_absent_field(ff) -> None:
    resource = {"id": "p-1", "active": True}
    result = ff.apply_hidden(resource, ["meta", "extension"])
    assert result == {"id": "p-1", "active": True}


def test_apply_hidden_empty_list_returns_copy(ff) -> None:
    resource = {"id": "p-1", "active": True}
    result = ff.apply_hidden(resource, [])
    assert result == resource
    assert result is not resource


def test_apply_hidden_nested_dot_path(ff) -> None:
    """meta.security should remove only the 'security' key inside 'meta'."""
    resource = {
        "id": "p-1",
        "meta": {"versionId": "1", "security": [{"code": "R"}]},
    }
    result = ff.apply_hidden(resource, ["meta.security"])
    assert "meta" in result
    assert "security" not in result["meta"]
    assert result["meta"]["versionId"] == "1"


def test_apply_hidden_returns_new_dict(ff) -> None:
    resource = {"id": "p-1"}
    result = ff.apply_hidden(resource, ["x"])
    assert result is not resource


# ── get_readonly_fields ────────────────────────────────────────────────────────


def test_get_readonly_fields_returns_present_fields(ff) -> None:
    resource = {"id": "p-1", "status": "final", "category": "lab", "value": 42}
    result = ff.get_readonly_fields(resource, ["status", "category"])
    assert result == {"status": True, "category": True}


def test_get_readonly_fields_skips_absent_fields(ff) -> None:
    resource = {"id": "p-1", "status": "final"}
    result = ff.get_readonly_fields(resource, ["status", "extension"])
    assert result == {"status": True}
    assert "extension" not in result


def test_get_readonly_fields_empty_list(ff) -> None:
    resource = {"id": "p-1"}
    assert ff.get_readonly_fields(resource, []) == {}


# ── apply_meta_extension ──────────────────────────────────────────────────────


def test_apply_meta_extension_adds_extensions(ff) -> None:
    resource = {"id": "p-1", "status": "active"}
    result = ff.apply_meta_extension(resource, ["status"])
    assert "meta" in result
    extensions = result["meta"]["extension"]
    assert any(
        e["url"] == "urn:intellicare:readonly-field" and e["valueString"] == "status"
        for e in extensions
    )


def test_apply_meta_extension_preserves_existing_meta(ff) -> None:
    resource = {"id": "p-1", "meta": {"versionId": "3"}, "status": "active"}
    result = ff.apply_meta_extension(resource, ["status"])
    assert result["meta"]["versionId"] == "3"
    assert result["meta"]["extension"]


def test_apply_meta_extension_multiple_fields(ff) -> None:
    resource = {"id": "p-1"}
    result = ff.apply_meta_extension(resource, ["status", "category"])
    url = "urn:intellicare:readonly-field"
    fields = {e["valueString"] for e in result["meta"]["extension"] if e["url"] == url}
    assert "status" in fields
    assert "category" in fields


def test_apply_meta_extension_empty_fields_unchanged(ff) -> None:
    resource = {"id": "p-1"}
    result = ff.apply_meta_extension(resource, [])
    assert result == resource


def test_apply_meta_extension_preserves_original(ff) -> None:
    resource = {"id": "p-1", "status": "active"}
    result = ff.apply_meta_extension(resource, ["status"])
    # Original should not be mutated
    assert "meta" not in resource
