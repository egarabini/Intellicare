"""Testes para perfis de doencas e registry."""

from pathlib import Path

from oswaldo.profiles.loader import YAMLProfileLoader
from oswaldo.profiles.registry import DiseaseProfileRegistry


PROFILES_DIR = Path(__file__).parent.parent / "oswaldo" / "profiles" / "diseases"


class TestDiseaseProfileRegistry:
    def test_load_all(self, registry: DiseaseProfileRegistry) -> None:
        assert len(registry) >= 3
        assert registry.has("ckd")
        assert registry.has("dm2")
        assert registry.has("has")

    def test_list_ids(self, registry: DiseaseProfileRegistry) -> None:
        ids = registry.list_ids()
        assert "ckd" in ids
        assert "dm2" in ids
        assert "has" in ids

    def test_get_profile(self, registry: DiseaseProfileRegistry) -> None:
        ckd = registry.get("ckd")
        assert ckd is not None
        assert ckd.name == "Chronic Kidney Disease"
        assert ckd.snomed_code == "709044004"
        assert len(ckd.observations) >= 5
        assert ckd.staging.strategy == "kdigo"

    def test_get_nonexistent(self, registry: DiseaseProfileRegistry) -> None:
        assert registry.get("nonexistent") is None

    def test_contains(self, registry: DiseaseProfileRegistry) -> None:
        assert "ckd" in registry
        assert "xyz" not in registry

    def test_get_all(self, registry: DiseaseProfileRegistry) -> None:
        all_profiles = registry.get_all()
        assert len(all_profiles) >= 3

    def test_clear(self) -> None:
        reg = DiseaseProfileRegistry(PROFILES_DIR)
        reg.load_all()
        assert len(reg) >= 3
        reg.clear()
        assert len(reg) == 0


class TestYAMLProfileLoader:
    def test_load_ckd(self) -> None:
        loader = YAMLProfileLoader()
        profile = loader.load_from_file(PROFILES_DIR / "ckd.yaml")
        assert profile.id == "ckd"
        assert profile.version == "1.0.0"

    def test_load_dm2(self) -> None:
        loader = YAMLProfileLoader()
        profile = loader.load_from_file(PROFILES_DIR / "dm2.yaml")
        assert profile.id == "dm2"
        assert profile.staging.strategy == "ada"

    def test_load_has(self) -> None:
        loader = YAMLProfileLoader()
        profile = loader.load_from_file(PROFILES_DIR / "has.yaml")
        assert profile.id == "has"
        assert profile.staging.strategy == "escesh"

    def test_observations_have_loinc(self) -> None:
        loader = YAMLProfileLoader()
        profile = loader.load_from_file(PROFILES_DIR / "ckd.yaml")
        for obs in profile.observations:
            assert obs.loinc_code, f"Observacao {obs.id} sem LOINC"

    def test_profile_roundtrip(self) -> None:
        loader = YAMLProfileLoader()
        profile = loader.load_from_file(PROFILES_DIR / "ckd.yaml")
        data = profile.to_dict()
        from oswaldo.profiles.models import DiseaseProfile
        profile2 = DiseaseProfile.from_dict(data)
        assert profile.id == profile2.id
        assert len(profile.observations) == len(profile2.observations)
        assert len(profile.alerts) == len(profile2.alerts)

    def test_file_not_found(self) -> None:
        loader = YAMLProfileLoader()
        import pytest
        with pytest.raises(FileNotFoundError):
            loader.load_from_file(Path("/nonexistent/file.yaml"))


class TestCKDProfile:
    def test_egfr_observation(self, registry: DiseaseProfileRegistry) -> None:
        ckd = registry.get("ckd")
        egfr = ckd.get_observation("egfr")
        assert egfr is not None
        assert egfr.loinc_code == "33914-3"
        assert egfr.unit == "mL/min/1.73m²"
        assert egfr.trend_direction == "higher_is_better"

    def test_acr_observation(self, registry: DiseaseProfileRegistry) -> None:
        ckd = registry.get("ckd")
        acr = ckd.get_observation("acr")
        assert acr is not None
        assert acr.loinc_code == "14958-3"
        assert acr.trend_direction == "lower_is_better"

    def test_staging_axes(self, registry: DiseaseProfileRegistry) -> None:
        ckd = registry.get("ckd")
        assert len(ckd.staging.axes) == 2
        assert ckd.staging.axes[0].id == "gfr"
        assert ckd.staging.axes[1].id == "acr"

    def test_alerts_count(self, registry: DiseaseProfileRegistry) -> None:
        ckd = registry.get("ckd")
        assert len(ckd.alerts) >= 8
