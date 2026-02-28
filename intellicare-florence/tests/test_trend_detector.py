"""Testes para TrendDetector."""

from datetime import datetime, timedelta, timezone

from florence.engine.models import TrendDirection
from florence.engine.trend_detector import TrendDetector


class TestTrendDetector:
    def test_insufficient_data_empty(self, trend_detector: TrendDetector) -> None:
        result = trend_detector.analyze("creatinine", "Creatinina", [], [])
        assert result.direction == TrendDirection.INSUFFICIENT_DATA
        assert result.data_points == 0

    def test_insufficient_data_one_point(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        result = trend_detector.analyze("creatinine", "Creatinina", [1.2], [now])
        assert result.direction == TrendDirection.INSUFFICIENT_DATA
        assert result.data_points == 1

    def test_insufficient_data_two_points(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        result = trend_detector.analyze(
            "creatinine", "Creatinina",
            [1.0, 1.2],
            [now - timedelta(days=30), now],
        )
        assert result.direction == TrendDirection.INSUFFICIENT_DATA
        assert result.data_points == 2

    def test_stable_trend(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(4, -1, -1)]
        values = [1.0, 1.01, 0.99, 1.0, 1.01]
        result = trend_detector.analyze("creatinine", "Creatinina", values, timestamps)
        assert result.direction == TrendDirection.STABLE
        assert "estavel" in result.message

    def test_increasing_trend(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(4, -1, -1)]
        values = [1.0, 1.5, 2.0, 2.5, 3.0]
        result = trend_detector.analyze("creatinine", "Creatinina", values, timestamps)
        assert result.direction == TrendDirection.WORSENING
        assert result.slope is not None
        assert result.slope > 0

    def test_decreasing_trend(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(4, -1, -1)]
        values = [3.0, 2.5, 2.0, 1.5, 1.0]
        result = trend_detector.analyze("creatinine", "Creatinina", values, timestamps)
        assert result.direction == TrendDirection.IMPROVING
        assert result.slope is not None
        assert result.slope < 0

    def test_change_percent(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(4, -1, -1)]
        values = [100.0, 110.0, 120.0, 130.0, 150.0]
        result = trend_detector.analyze("glucose_fasting", "Glicemia", values, timestamps)
        assert result.change_percent is not None
        # 150 vs 130 = +15.4%
        assert result.change_percent > 10.0

    def test_period_days(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=90), now - timedelta(days=60), now - timedelta(days=30), now]
        values = [1.0, 1.1, 1.2, 1.3]
        result = trend_detector.analyze("creatinine", "Creatinina", values, timestamps)
        assert result.period_days == 90

    def test_data_points_count(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 15) for i in range(5, -1, -1)]
        values = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        result = trend_detector.analyze("urea", "Ureia", values, timestamps)
        assert result.data_points == 6

    def test_to_dict(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(4, -1, -1)]
        values = [1.0, 1.5, 2.0, 2.5, 3.0]
        result = trend_detector.analyze("creatinine", "Creatinina", values, timestamps)
        d = result.to_dict()
        assert d["lab_id"] == "creatinine"
        assert d["direction"] == "worsening"
        assert "slope" in d

    def test_custom_min_data_points(self) -> None:
        detector = TrendDetector(min_data_points=5)
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(3, -1, -1)]
        values = [1.0, 2.0, 3.0, 4.0]
        result = detector.analyze("creatinine", "Creatinina", values, timestamps)
        assert result.direction == TrendDirection.INSUFFICIENT_DATA

    def test_zero_previous_value(self, trend_detector: TrendDetector) -> None:
        now = datetime.now(timezone.utc)
        timestamps = [now - timedelta(days=i * 30) for i in range(3, -1, -1)]
        values = [0.0, 0.0, 0.0, 1.0]
        result = trend_detector.analyze("crp", "PCR", values, timestamps)
        assert result.change_percent is None or result.data_points >= 3
