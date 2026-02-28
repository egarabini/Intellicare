"""Testes para modelos de dados do Oswaldo."""

from datetime import datetime, timezone

from oswaldo.engine.models import (
    Alert,
    OswaldoPatientSummary,
    SeverityLevel,
    StagingResult,
    TrendDirection,
    TrendResult,
)


class TestStagingResult:
    def test_to_dict(self) -> None:
        result = StagingResult(
            disease_id="ckd",
            stage="G3a",
            stage_label="Moderately decreased",
            severity=SeverityLevel.WARNING,
            axes={"gfr": "G3a", "acr": "A1"},
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            observations_used={"egfr": 45.0, "acr": 20.0},
        )
        d = result.to_dict()
        assert d["disease_id"] == "ckd"
        assert d["stage"] == "G3a"
        assert d["severity"] == "warning"
        assert d["axes"]["gfr"] == "G3a"
        assert "2024-01-15" in d["timestamp"]


class TestTrendResult:
    def test_to_dict(self) -> None:
        result = TrendResult(
            observation_id="egfr",
            direction=TrendDirection.WORSENING,
            slope=-0.03,
            current_value=45.0,
            previous_value=55.0,
            change_percent=-18.2,
            period_days=90,
            data_points=5,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = result.to_dict()
        assert d["observation_id"] == "egfr"
        assert d["direction"] == "worsening"
        assert d["slope"] == -0.03
        assert d["data_points"] == 5

    def test_to_dict_with_none_values(self) -> None:
        result = TrendResult(
            observation_id="egfr",
            direction=TrendDirection.INSUFFICIENT_DATA,
            slope=None,
            current_value=None,
            previous_value=None,
            change_percent=None,
            period_days=90,
            data_points=0,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = result.to_dict()
        assert d["slope"] is None
        assert d["current_value"] is None


class TestAlert:
    def test_to_dict(self) -> None:
        alert = Alert(
            alert_id="egfr_critical",
            disease_id="ckd",
            alert_type="threshold",
            severity=SeverityLevel.CRITICAL,
            message="eGFR critico",
            observation_id="egfr",
            current_value=10.0,
            threshold_value=15.0,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = alert.to_dict()
        assert d["alert_id"] == "egfr_critical"
        assert d["severity"] == "critical"
        assert d["current_value"] == 10.0
        assert d["metadata"] == {}


class TestOswaldoPatientSummary:
    def test_to_dict(self) -> None:
        summary = OswaldoPatientSummary(
            patient_id="p-1",
            diseases=["ckd", "dm2"],
            staging_results={},
            trend_results={},
            alerts=[],
            last_updated=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = summary.to_dict()
        assert d["patient_id"] == "p-1"
        assert d["diseases"] == ["ckd", "dm2"]
        assert d["staging_results"] == {}
        assert d["alerts"] == []

    def test_to_dict_with_data(self) -> None:
        staging = StagingResult(
            disease_id="ckd",
            stage="G3a",
            stage_label="G3a",
            severity=SeverityLevel.WARNING,
            axes={},
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            observations_used={},
        )
        alert = Alert(
            alert_id="a1",
            disease_id="ckd",
            alert_type="threshold",
            severity=SeverityLevel.CRITICAL,
            message="test",
            observation_id="egfr",
            current_value=10.0,
            threshold_value=15.0,
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        summary = OswaldoPatientSummary(
            patient_id="p-1",
            diseases=["ckd"],
            staging_results={"ckd": staging},
            trend_results={},
            alerts=[alert],
            last_updated=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        d = summary.to_dict()
        assert "ckd" in d["staging_results"]
        assert len(d["alerts"]) == 1
        assert d["alerts"][0]["severity"] == "critical"


class TestEnums:
    def test_severity_values(self) -> None:
        assert SeverityLevel.INFO.value == "info"
        assert SeverityLevel.WARNING.value == "warning"
        assert SeverityLevel.CRITICAL.value == "critical"

    def test_trend_direction_values(self) -> None:
        assert TrendDirection.IMPROVING.value == "improving"
        assert TrendDirection.STABLE.value == "stable"
        assert TrendDirection.WORSENING.value == "worsening"
        assert TrendDirection.INSUFFICIENT_DATA.value == "insufficient_data"
