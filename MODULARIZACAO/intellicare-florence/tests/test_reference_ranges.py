"""Testes para ReferenceRangeLoader."""

from florence.engine.reference_ranges.loader import ReferenceRangeLoader


class TestReferenceRangeLoader:
    def test_load_all(self, ref_loader: ReferenceRangeLoader) -> None:
        assert len(ref_loader) >= 20  # 6 panels, ~25 labs total

    def test_get_creatinine(self, ref_loader: ReferenceRangeLoader) -> None:
        ref = ref_loader.get("creatinine")
        assert ref is not None
        assert ref.loinc_code == "2160-0"
        assert ref.unit == "mg/dL"
        assert ref.normal_min == 0.7
        assert ref.normal_max == 1.3

    def test_get_by_loinc(self, ref_loader: ReferenceRangeLoader) -> None:
        ref = ref_loader.get_by_loinc("4548-4")  # HbA1c
        assert ref is not None
        assert ref.lab_id == "hba1c"

    def test_get_nonexistent(self, ref_loader: ReferenceRangeLoader) -> None:
        assert ref_loader.get("nonexistent") is None

    def test_get_by_loinc_nonexistent(self, ref_loader: ReferenceRangeLoader) -> None:
        assert ref_loader.get_by_loinc("99999-9") is None

    def test_list_panels(self, ref_loader: ReferenceRangeLoader) -> None:
        panels = ref_loader.list_panels()
        assert "renal_panel" in panels
        assert "metabolic_panel" in panels
        assert "hematologic_panel" in panels
        assert "hepatic_panel" in panels
        assert "thyroid_panel" in panels
        assert "inflammatory_panel" in panels

    def test_get_panel(self, ref_loader: ReferenceRangeLoader) -> None:
        renal = ref_loader.get_panel("renal_panel")
        assert len(renal) >= 5
        lab_ids = [r.lab_id for r in renal]
        assert "creatinine" in lab_ids
        assert "egfr" in lab_ids
        assert "potassium" in lab_ids

    def test_list_labs(self, ref_loader: ReferenceRangeLoader) -> None:
        labs = ref_loader.list_labs()
        assert "creatinine" in labs
        assert "hemoglobin" in labs
        assert "hba1c" in labs
        assert "tsh" in labs

    def test_contains(self, ref_loader: ReferenceRangeLoader) -> None:
        assert "creatinine" in ref_loader
        assert "xyz" not in ref_loader

    def test_potassium_ranges(self, ref_loader: ReferenceRangeLoader) -> None:
        ref = ref_loader.get("potassium")
        assert ref is not None
        assert ref.normal_min == 3.5
        assert ref.normal_max == 5.0
        assert ref.critical_low == 2.5
        assert ref.critical_high == 6.5
        assert ref.panic_low == 2.0
        assert ref.panic_high == 7.0

    def test_hemoglobin_gender_specific(self, ref_loader: ReferenceRangeLoader) -> None:
        ref = ref_loader.get("hemoglobin")
        assert ref is not None
        assert ref.gender_specific is True
