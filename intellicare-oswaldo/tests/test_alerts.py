"""Testes para regras de alerta."""

from oswaldo.engine.alerts.threshold_alert import ThresholdAlertRule
from oswaldo.engine.alerts.trend_alert import TrendAlertRule
from oswaldo.engine.models import SeverityLevel, TrendDirection, TrendResult
from oswaldo.profiles.models import AlertConfig
from datetime import datetime, timezone


class TestThresholdAlertRule:
    def test_fires_when_above(self) -> None:
        config = AlertConfig(
            id="test_alert",
            type="threshold",
            observation_id="egfr",
            condition="lt",
            threshold=15.0,
            severity="critical",
            message="eGFR critico",
        )
        rule = ThresholdAlertRule(config)
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={"egfr": 10.0},
        )
        assert alert is not None
        assert alert.severity == SeverityLevel.CRITICAL
        assert alert.current_value == 10.0

    def test_no_alert_when_normal(self) -> None:
        config = AlertConfig(
            id="test_alert",
            type="threshold",
            observation_id="egfr",
            condition="lt",
            threshold=15.0,
            severity="critical",
            message="eGFR critico",
        )
        rule = ThresholdAlertRule(config)
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={"egfr": 90.0},
        )
        assert alert is None

    def test_no_alert_when_missing(self) -> None:
        config = AlertConfig(
            id="test_alert",
            type="threshold",
            observation_id="egfr",
            condition="lt",
            threshold=15.0,
            severity="critical",
            message="eGFR critico",
        )
        rule = ThresholdAlertRule(config)
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={},
        )
        assert alert is None

    def test_gt_condition(self) -> None:
        config = AlertConfig(
            id="hba1c_high",
            type="threshold",
            observation_id="hba1c",
            condition="gt",
            threshold=9.0,
            severity="warning",
            message="HbA1c alta",
        )
        rule = ThresholdAlertRule(config)
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="dm2",
            observations={"hba1c": 10.5},
        )
        assert alert is not None
        assert alert.severity == SeverityLevel.WARNING


class TestTrendAlertRule:
    def test_fires_on_declining_trend(self) -> None:
        config = AlertConfig(
            id="egfr_decline",
            type="trend",
            observation_id="egfr",
            condition="lt",
            threshold=-5.0,
            severity="warning",
            message="eGFR em declinio",
        )
        rule = TrendAlertRule(config)
        trends = {
            "egfr": TrendResult(
                observation_id="egfr",
                direction=TrendDirection.WORSENING,
                slope=-0.03,  # -10.95/year
                current_value=45.0,
                previous_value=55.0,
                change_percent=-18.2,
                period_days=90,
                data_points=5,
                timestamp=datetime.now(timezone.utc),
            )
        }
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={},
            trends=trends,
        )
        assert alert is not None

    def test_no_alert_stable_trend(self) -> None:
        config = AlertConfig(
            id="egfr_decline",
            type="trend",
            observation_id="egfr",
            condition="lt",
            threshold=-5.0,
            severity="warning",
            message="eGFR em declinio",
        )
        rule = TrendAlertRule(config)
        trends = {
            "egfr": TrendResult(
                observation_id="egfr",
                direction=TrendDirection.STABLE,
                slope=-0.001,
                current_value=60.0,
                previous_value=60.5,
                change_percent=-0.8,
                period_days=90,
                data_points=5,
                timestamp=datetime.now(timezone.utc),
            )
        }
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={},
            trends=trends,
        )
        assert alert is None

    def test_no_alert_insufficient_data(self) -> None:
        config = AlertConfig(
            id="egfr_decline",
            type="trend",
            observation_id="egfr",
            condition="lt",
            threshold=-5.0,
            severity="warning",
            message="eGFR em declinio",
        )
        rule = TrendAlertRule(config)
        trends = {
            "egfr": TrendResult(
                observation_id="egfr",
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=None,
                current_value=45.0,
                previous_value=None,
                change_percent=None,
                period_days=90,
                data_points=1,
                timestamp=datetime.now(timezone.utc),
            )
        }
        alert = rule.evaluate(
            patient_id="p-1",
            disease_id="ckd",
            observations={},
            trends=trends,
        )
        assert alert is None
