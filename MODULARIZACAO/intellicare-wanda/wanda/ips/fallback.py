"""IPS Fallback Strategy — graceful degradation (EF-W002).

Provides IPS data when Florence is unavailable:
1. Stale cache (expired but available)
2. Basic data from Oswaldo/Geralda
3. Empty structured IPS (last resort)
"""

import logging
from typing import Any, Optional

import httpx

from wanda.ips.models import IPSBundle

logger = logging.getLogger(__name__)


class IPSFallbackStrategy:
    """Fallback strategy when Florence is unavailable."""

    def __init__(
        self,
        oswaldo_url: str = "http://localhost:8001",
        geralda_url: str = "http://localhost:8006",
        timeout: int = 5,
    ):
        self._oswaldo_url = oswaldo_url
        self._geralda_url = geralda_url
        self._timeout = timeout

    async def get_minimal_ips(
        self,
        patient_id: str,
        stale_ips: Optional[IPSBundle] = None,
    ) -> IPSBundle:
        """Build minimal IPS without Florence.

        Priority:
        1. Stale cache (if provided)
        2. Data from Oswaldo (basic patient info)
        3. Data from Geralda (basic care info)
        4. Empty IPS (last resort)

        Marks the IPS as 'degraded' so agents know data may be incomplete.
        """
        # Option 1: Use stale cache
        if stale_ips:
            stale_ips.is_degraded = True
            stale_ips.source = "stale"
            logger.info("Using stale IPS for %s", patient_id)
            return stale_ips

        # Option 2: Try to get basic data from Oswaldo
        oswaldo_data = await self._get_basic_from_oswaldo(patient_id)
        if oswaldo_data:
            ips = IPSBundle(
                patient_id=patient_id,
                patient_name=oswaldo_data.get("patient_name", ""),
                conditions=oswaldo_data.get("conditions", []),
                source="oswaldo-fallback",
                is_degraded=True,
            )
            logger.info("Built fallback IPS from Oswaldo for %s", patient_id)
            return ips

        # Option 3: Try Geralda
        geralda_data = await self._get_basic_from_geralda(patient_id)
        if geralda_data:
            ips = IPSBundle(
                patient_id=patient_id,
                patient_name=geralda_data.get("patient_name", ""),
                conditions=geralda_data.get("conditions", []),
                medications=geralda_data.get("medications", []),
                source="geralda-fallback",
                is_degraded=True,
            )
            logger.info("Built fallback IPS from Geralda for %s", patient_id)
            return ips

        # Option 4: Empty IPS
        logger.warning("All fallback sources failed for %s, returning empty IPS", patient_id)
        return self.build_empty_ips(patient_id)

    def build_empty_ips(self, patient_id: str) -> IPSBundle:
        """Create an empty structured IPS.

        Used when all sources fail. Allows the query to continue with warnings.
        """
        return IPSBundle.empty(patient_id)

    async def _get_basic_from_oswaldo(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Get basic patient data from Oswaldo."""
        url = f"{self._oswaldo_url}/api/v1/patient/{patient_id}/basic"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        return None

    async def _get_basic_from_geralda(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Get basic patient data from Geralda."""
        url = f"{self._geralda_url}/api/v1/patient/{patient_id}/basic"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        return None
