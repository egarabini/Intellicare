"""Testes do ContentLoader."""

import os
import tempfile

import pytest
import yaml

from geralda.engine.education.content_loader import ContentLoader


@pytest.fixture
def temp_data_dir():
    """Cria diretorio temporario com YAMLs de teste."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # CKD test file
        ckd_data = {
            "condition_code": "N18",
            "condition_name": "DRC",
            "materials": [
                {
                    "id": "ckd-001",
                    "title": "O que e DRC",
                    "reading_level": "basic",
                    "tags": ["renal", "introducao"],
                    "content": "Texto sobre DRC.",
                },
                {
                    "id": "ckd-002",
                    "title": "Alimentacao na DRC",
                    "reading_level": "basic",
                    "tags": ["dieta", "renal"],
                    "content": "Texto sobre dieta.",
                },
            ],
        }
        with open(os.path.join(tmpdir, "ckd.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(ckd_data, f, allow_unicode=True)

        # DM2 test file
        dm2_data = {
            "condition_code": "E11",
            "condition_name": "Diabetes Tipo 2",
            "materials": [
                {
                    "id": "dm2-001",
                    "title": "O que e Diabetes",
                    "reading_level": "basic",
                    "tags": ["diabetes", "glicose"],
                    "content": "Texto sobre diabetes.",
                },
                {
                    "id": "dm2-002",
                    "title": "Exames no Diabetes",
                    "reading_level": "intermediate",
                    "tags": ["exames", "hemoglobina"],
                    "content": "Texto sobre exames.",
                },
            ],
        }
        with open(os.path.join(tmpdir, "dm2.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(dm2_data, f, allow_unicode=True)

        yield tmpdir


@pytest.fixture
def loader(temp_data_dir):
    cl = ContentLoader(data_dir=temp_data_dir)
    cl.load()
    return cl


class TestLoad:
    def test_load_count(self, loader):
        assert loader.total_materials == 4

    def test_load_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cl = ContentLoader(data_dir=tmpdir)
            assert cl.load() == 0

    def test_load_nonexistent_dir(self):
        cl = ContentLoader(data_dir="/nonexistent/path")
        assert cl.load() == 0

    def test_auto_load_on_access(self, temp_data_dir):
        cl = ContentLoader(data_dir=temp_data_dir)
        # Should auto-load when first accessing
        assert cl.total_materials == 4


class TestGetMaterial:
    def test_get_existing(self, loader):
        m = loader.get_material("ckd-001")
        assert m is not None
        assert m.title == "O que e DRC"
        assert m.condition_code == "N18"

    def test_get_nonexistent(self, loader):
        assert loader.get_material("nope") is None


class TestGetByCondition:
    def test_get_ckd(self, loader):
        materials = loader.get_by_condition("N18")
        assert len(materials) == 2

    def test_get_dm2(self, loader):
        materials = loader.get_by_condition("E11")
        assert len(materials) == 2

    def test_filter_by_reading_level(self, loader):
        basic = loader.get_by_condition("E11", reading_level="basic")
        assert len(basic) == 1
        assert basic[0].id == "dm2-001"

    def test_filter_by_tag(self, loader):
        renal = loader.get_by_condition("N18", tag="renal")
        assert len(renal) == 2

    def test_nonexistent_condition(self, loader):
        assert loader.get_by_condition("X99") == []


class TestGetAllConditions:
    def test_list_conditions(self, loader):
        conditions = loader.get_all_conditions()
        assert len(conditions) == 2
        codes = [c["condition_code"] for c in conditions]
        assert "N18" in codes
        assert "E11" in codes

    def test_condition_count(self, loader):
        conditions = loader.get_all_conditions()
        for c in conditions:
            assert c["material_count"] == 2


class TestSearch:
    def test_search_title(self, loader):
        results = loader.search("diabetes")
        # Both dm2 materials have "Diabetes" in title
        assert len(results) == 2
        ids = [m.id for m in results]
        assert "dm2-001" in ids

    def test_search_tag(self, loader):
        results = loader.search("renal")
        assert len(results) == 2

    def test_search_no_results(self, loader):
        assert loader.search("xyz") == []

    def test_search_case_insensitive(self, loader):
        results = loader.search("DRC")
        # Both ckd materials have "DRC" in title
        assert len(results) == 2
