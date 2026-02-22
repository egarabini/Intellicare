"""Trend Detector — analise de tendencias em series temporais de laboratoriais."""

from datetime import datetime

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - fallback para ambientes sem numpy
    np = None

from florence.engine.models import TrendAnalysis, TrendDirection


class TrendDetector:
    """Detecta tendencias em series temporais de resultados laboratoriais."""

    def __init__(self, min_data_points: int = 3, significance_threshold: float = 0.05) -> None:
        self._min_data_points = min_data_points
        self._significance_threshold = significance_threshold

    def analyze(
        self,
        lab_id: str,
        lab_name: str,
        values: list[float],
        timestamps: list[datetime],
    ) -> TrendAnalysis:
        """Analisa a tendencia de uma serie temporal de valores."""
        n = len(values)
        if n == 0:
            return self._insufficient_data(lab_id, lab_name, 0)

        current_value = values[-1]

        if n < self._min_data_points:
            return TrendAnalysis(
                lab_id=lab_id,
                lab_name=lab_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=None,
                current_value=current_value,
                previous_value=values[-2] if n >= 2 else None,
                change_percent=None,
                period_days=self._calc_period_days(timestamps),
                data_points=n,
                values=values,
                timestamps=[t.isoformat() for t in timestamps],
                message=f"Dados insuficientes para tendencia ({n} pontos, minimo {self._min_data_points})",
            )

        previous_value = values[-2]
        period_days = self._calc_period_days(timestamps)

        # Regressao linear para slope
        slope = self._calculate_slope(values, timestamps)

        # Change percent
        change_percent = self._calc_change_percent(current_value, previous_value)

        # Classificar direcao
        direction = self._classify_direction(values, slope)

        message = self._generate_message(lab_name, direction, change_percent, period_days)

        return TrendAnalysis(
            lab_id=lab_id,
            lab_name=lab_name,
            direction=direction,
            slope=slope,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            period_days=period_days,
            data_points=n,
            values=values,
            timestamps=[t.isoformat() for t in timestamps],
            message=message,
        )

    def _calculate_slope(self, values: list[float], timestamps: list[datetime]) -> float:
        """Calcula slope via regressao linear simples."""
        if len(values) < 2:
            return 0.0

        # Converter timestamps em dias relativos ao primeiro
        t0 = timestamps[0]
        x = [(t - t0).total_seconds() / 86400.0 for t in timestamps]
        y = [float(v) for v in values]

        if np is not None:
            x_arr = np.array(x)
            y_arr = np.array(y, dtype=float)
            x_mean = float(np.mean(x_arr))
            y_mean = float(np.mean(y_arr))
            denominator = float(np.sum((x_arr - x_mean) ** 2))
            if denominator == 0:
                return 0.0
            return float(np.sum((x_arr - x_mean) * (y_arr - y_mean)) / denominator)

        # Regressao linear manual: slope = covariance(x,y) / variance(x)
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        if denominator == 0:
            return 0.0
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        slope = float(numerator / denominator)
        return slope

    def _classify_direction(self, values: list[float], slope: float) -> TrendDirection:
        """Classifica a direcao da tendencia com base na mudanca percentual total."""
        if len(values) < 2:
            return TrendDirection.STABLE

        first_value = values[0]
        last_value = values[-1]
        if first_value == 0:
            return TrendDirection.STABLE

        # Mudanca percentual total (inicio -> fim)
        total_change_pct = abs(last_value - first_value) / abs(first_value)

        if total_change_pct < self._significance_threshold:
            return TrendDirection.STABLE

        # Diferenciamos improving/worsening na camada superior (clinical_analyzer)
        # Aqui retornamos a direcao bruta
        if slope > 0:
            return TrendDirection.WORSENING  # Pode ser invertido por lab (ex: eGFR)
        return TrendDirection.IMPROVING

    def _calc_period_days(self, timestamps: list[datetime]) -> int:
        """Calcula o periodo em dias."""
        if len(timestamps) < 2:
            return 0
        delta = timestamps[-1] - timestamps[0]
        return max(1, int(delta.total_seconds() / 86400))

    def _calc_change_percent(self, current: float, previous: float) -> float | None:
        """Calcula percentual de mudanca."""
        if previous == 0:
            return None
        return ((current - previous) / abs(previous)) * 100

    def _generate_message(
        self, lab_name: str, direction: TrendDirection, change_percent: float | None, period_days: int
    ) -> str:
        """Gera mensagem descritiva da tendencia."""
        if direction == TrendDirection.STABLE:
            return f"{lab_name} estavel nos ultimos {period_days} dias"
        if direction == TrendDirection.INSUFFICIENT_DATA:
            return f"{lab_name}: dados insuficientes para analise de tendencia"
        pct = f" ({change_percent:+.1f}%)" if change_percent is not None else ""
        direction_pt = "em alta" if direction == TrendDirection.WORSENING else "em queda"
        return f"{lab_name} {direction_pt}{pct} nos ultimos {period_days} dias"

    def _insufficient_data(self, lab_id: str, lab_name: str, n: int) -> TrendAnalysis:
        return TrendAnalysis(
            lab_id=lab_id,
            lab_name=lab_name,
            direction=TrendDirection.INSUFFICIENT_DATA,
            slope=None,
            current_value=0.0,
            previous_value=None,
            change_percent=None,
            period_days=0,
            data_points=n,
            message=f"{lab_name}: sem dados para analise",
        )
