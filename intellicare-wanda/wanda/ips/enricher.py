"""IPS Enricher — adds specialized agent data to IPS (EF-W002).

Enriches the base IPS with:
- Oswaldo: chronic disease staging (DRC G1-G5, DM2 control, HAS control)
- Geralda: care journey (macrostate E0-E7, adherence score, risk level)
"""

import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from wanda.ips.models import EnrichedIPS, IPSBundle

logger = logging.getLogger(__name__)


class IPSEnricher:
    """Enriches IPS with data from specialized agents."""

    def __init__(
        self,
        oswaldo_url: str = "http://localhost:8001",
        geralda_url: str = "http://localhost:8006",
        timeout: int = 10,
    ):
        self._oswaldo_url = oswaldo_url
        self._geralda_url = geralda_url
        self._timeout = timeout

    async def enrich(
        self,
        ips: IPSBundle,
        modules_available: Optional[list[str]] = None,
    ) -> EnrichedIPS:
        """Enrich IPS with data from Oswaldo and Geralda.

        Args:
            ips: Base IPS bundle.
            modules_available: List of available module names. If None, tries all.

        Returns:
            EnrichedIPS with staging and care data.
        """
        enriched = EnrichedIPS(ips=ips, enriched_at=datetime.now())
        available = modules_available or []

        # Enrich from Oswaldo (chronic disease staging)
        if not modules_available or "intellicare-oswaldo" in available:
            staging = await self._enrich_from_oswaldo(ips.patient_id)
            if staging:
                enriched.staging = staging
                enriched.enriched_sources.append("oswaldo")

        # Enrich from Geralda (care journey)
        if not modules_available or "intellicare-geralda" in available:
            care = await self._enrich_from_geralda(ips.patient_id)
            if care:
                enriched.care = care
                enriched.enriched_sources.append("geralda")

        return enriched

    async def _enrich_from_oswaldo(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Get staging data from Oswaldo."""
        url = f"{self._oswaldo_url}/api/v1/staging/{patient_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "chronic_conditions": data.get("chronic_conditions", []),
                        "drc_stage": data.get("drc_stage"),
                        "cv_risk_score": data.get("cv_risk_score"),
                        "dm2_control": data.get("dm2_control"),
                        "has_control": data.get("has_control"),
                    }
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("Failed to enrich from Oswaldo for %s: %s", patient_id, e)
        return None

    async def _enrich_from_geralda(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Get care journey data from Geralda."""
        url = f"{self._geralda_url}/api/v1/journey/{patient_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "macrostate": data.get("macrostate"),
                        "adherence_score": data.get("adherence_score"),
                        "active_plans": data.get("active_plans", []),
                        "risk_level": data.get("risk_level"),
                    }
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning("Failed to enrich from Geralda for %s: %s", patient_id, e)
        return None
