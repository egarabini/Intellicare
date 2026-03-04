"""ChronicDiseaseEngine — motor generico de doencas cronicas."""

import logging
from datetime import datetime, timezone
from typing import Any

from oswaldo.datastore.fhir_datastore import FHIRDataStore
from oswaldo.engine.alerts.threshold_alert import ThresholdAlertRule
from oswaldo.engine.alerts.trend_alert import TrendAlertRule
from oswaldo.engine.models import Alert, OswaldoPatientSummary, StagingResult, TrendDirection, TrendResult
from oswaldo.engine.staging.factory import StagingStrategyFactory
from oswaldo.profiles.models import DiseaseProfile, ObservationConfig
from oswaldo.profiles.registry import DiseaseProfileRegistry

logger = logging.getLogger(__name__)


class ChronicDiseaseEngine:
    """Motor generico de monitoramento de doencas cronicas."""

    def __init__(self, datastore: FHIRDataStore, registry: DiseaseProfileRegistry) -> None:
        self.datastore = datastore
        self.registry = registry
        self.strategy_factory = StagingStrategyFactory()
        logger.info("ChronicDiseaseEngine inicializado com %d perfis", len(registry))

    def get_patient_summary(
        self, patient_id: str, disease_ids: list[str] | None = None
    ) -> OswaldoPatientSummary:
        patient = self.datastore.get_resource_by_type("Patient", patient_id)
        if not patient:
            raise ValueError(f"Paciente {patient_id} nao encontrado")

        if disease_ids is None:
            disease_ids = self.registry.list_ids()

        staging_results: dict[str, StagingResult] = {}
        trend_results: dict[str, TrendResult] = {}
        all_alerts: list[Alert] = []

        for disease_id in disease_ids:
            profile = self.registry.get(disease_id)
            if not profile:
                continue
            try:
                staging = self.calculate_staging(patient_id, disease_id, ctx=ctx)
                staging_results[disease_id] = staging
                trends = self.calculate_trends(patient_id, disease_id, ctx=ctx)
                trend_results.update(trends)
                alerts = self.generate_alerts(patient_id, disease_id, staging, trends, ctx=ctx)
                all_alerts.extend(alerts)
            except Exception as e:
                logger.error("Erro ao processar doenca '%s': %s", disease_id, e)

        return OswaldoPatientSummary(
            patient_id=patient_id,
            diseases=disease_ids,
            staging_results=staging_results,
            trend_results=trend_results,
            alerts=all_alerts,
            last_updated=datetime.now(timezone.utc),
        )

    def calculate_staging(self, patient_id: str, disease_id: str, ctx: Any = None) -> StagingResult:
        profile = self.registry.get(disease_id)
        if not profile:
            raise ValueError(f"Perfil '{disease_id}' nao encontrado")
        observations = self._get_observations(patient_id, profile)
        strategy = self.strategy_factory.create(profile)
        return strategy.calculate_stage(observations)

    def calculate_trends(
        self, patient_id: str, disease_id: str, period_days: int = 90
    ) -> dict[str, TrendResult]:
        profile = self.registry.get(disease_id)
        if not profile:
            raise ValueError(f"Perfil '{disease_id}' nao encontrado")

        trends: dict[str, TrendResult] = {}
        for obs_config in profile.observations:
            try:
                trends[obs_config.id] = self._calculate_observation_trend(patient_id, obs_config, period_days)
            except Exception:
                trends[obs_config.id] = TrendResult(
                    observation_id=obs_config.id,
                    direction=TrendDirection.INSUFFICIENT_DATA,
                    slope=None,
                    current_value=None,
                    previous_value=None,
                    change_percent=None,
                    period_days=period_days,
                    data_points=0,
                    timestamp=datetime.now(timezone.utc),
                )
        return trends

    def generate_alerts(
        self,
        patient_id: str,
        disease_id: str,
        staging: StagingResult,
        trends: dict[str, TrendResult],
    ) -> list[Alert]:
        profile = self.registry.get(disease_id)
        if not profile:
            return []

        alerts: list[Alert] = []
        for alert_config in profile.alerts:
            try:
                alert = self._evaluate_alert_config(patient_id, disease_id, alert_config, staging, trends)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                logger.warning("Erro ao avaliar alerta '%s': %s", alert_config.id, e)
        return alerts

    def _get_observations(self, patient_id: str, profile: DiseaseProfile) -> dict[str, Any]:
        observations: dict[str, Any] = {}
        for obs_config in profile.observations:
            fhir_obs = self.datastore.search_resources(
                "Observation", patient_id=patient_id, code=obs_config.loinc_code, limit=1, descending=True
            )
            if fhir_obs:
                observations[obs_config.id] = self._extract_observation_value(fhir_obs[0])
            else:
                observations[obs_config.id] = None
        return observations

    def _extract_observation_value(self, observation: dict[str, Any]) -> float | None:
        vq = observation.get("valueQuantity")
        if vq and "value" in vq:
            return float(vq["value"])
        for comp in observation.get("component", []):
            comp_value = comp.get("valueQuantity", {}).get("value")
            if comp_value is not None:
                return float(comp_value)
        return None

    def _calculate_observation_trend(
        self, patient_id: str, obs_config: ObservationConfig, period_days: int
    ) -> TrendResult:
        fhir_obs = self.datastore.search_resources(
            "Observation", patient_id=patient_id, code=obs_config.loinc_code, limit=100, descending=True
        )
        if len(fhir_obs) < 2:
            current_value = self._extract_observation_value(fhir_obs[0]) if fhir_obs else None
            return TrendResult(
                observation_id=obs_config.id,
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=None,
                current_value=current_value,
                previous_value=None,
                change_percent=None,
                period_days=period_days,
                data_points=len(fhir_obs),
                timestamp=datetime.now(timezone.utc),
            )

        current_value = self._extract_observation_value(fhir_obs[0])
        previous_value = self._extract_observation_value(fhir_obs[1])
        if current_value is None or previous_value is None:
            return TrendResult(
                observation_id=obs_config.id,
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=None,
                current_value=current_value,
                previous_value=previous_value,
                change_percent=None,
                period_days=period_days,
                data_points=len(fhir_obs),
                timestamp=datetime.now(timezone.utc),
            )

        change_percent = ((current_value - previous_value) / previous_value) * 100
        direction = self._determine_trend_direction(current_value, previous_value, obs_config.trend_direction)
        slope = (current_value - previous_value) / period_days

        return TrendResult(
            observation_id=obs_config.id,
            direction=direction,
            slope=slope,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            period_days=period_days,
            data_points=len(fhir_obs),
            timestamp=datetime.now(timezone.utc),
        )

    def _determine_trend_direction(self, current: float, previous: float, desired: str) -> TrendDirection:
        threshold = 0.05
        change_ratio = abs(current - previous) / previous if previous != 0 else 0
        if change_ratio < threshold:
            return TrendDirection.STABLE
        if desired == "higher_is_better":
            return TrendDirection.IMPROVING if current > previous else TrendDirection.WORSENING
        if desired == "lower_is_better":
            return TrendDirection.IMPROVING if current < previous else TrendDirection.WORSENING
        return TrendDirection.STABLE

    def _evaluate_alert_config(
        self,
        patient_id: str,
        disease_id: str,
        alert_config: Any,
        staging: StagingResult,
        trends: dict[str, TrendResult],
    ) -> Alert | None:
        profile = self.registry.get(disease_id)
        if not profile:
            return None
        observations = self._get_observations(patient_id, profile)

        if alert_config.type == "threshold":
            rule = ThresholdAlertRule(alert_config)
        elif alert_config.type == "trend":
            rule = TrendAlertRule(alert_config)
        else:
            return None

        return rule.evaluate(
            patient_id=patient_id,
            disease_id=disease_id,
            observations=observations,
            staging=staging,
            trends=trends,
        )
