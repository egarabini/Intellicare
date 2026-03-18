"""Adapter HTTP para Kestra."""
from __future__ import annotations

import httpx

from ..config import CareplannerSettings


class KestraAdapter:
    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings

    def _headers(self) -> dict[str, str]:
        if not self._settings.kestra_api_key:
            return {}
        return {"Authorization": f"Bearer {self._settings.kestra_api_key}"}

    async def resume_execution(self, execution_id: str, payload: dict | None = None) -> dict:
        async with httpx.AsyncClient(
            base_url=self._settings.kestra_url.rstrip("/"),
            timeout=self._settings.kestra_timeout,
        ) as client:
            response = await client.post(
                f"/api/v1/executions/{execution_id}/resume",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_execution(self, execution_id: str) -> dict:
        async with httpx.AsyncClient(
            base_url=self._settings.kestra_url.rstrip("/"),
            timeout=self._settings.kestra_timeout,
        ) as client:
            response = await client.get(
                f"/api/v1/executions/{execution_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(
                base_url=self._settings.kestra_url.rstrip("/"),
                timeout=self._settings.kestra_timeout,
            ) as client:
                response = await client.get("/health", headers=self._headers())
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def trigger_flow(
        self,
        namespace: str,
        flow_id: str,
        inputs: dict | None = None,
    ) -> dict:
        """Dispara uma nova execution de um flow Kestra.

        Args:
            namespace: Namespace Kestra, ex. 'intellicare.careplanner'.
            flow_id: ID do flow, ex. 'careplanner_jornada_basica'.
            inputs: Dicionário de inputs conforme declarados no flow YAML.

        Returns:
            Objeto execution do Kestra com campos: id, state, namespace, flowId.

        Raises:
            httpx.HTTPStatusError: Em caso de 4xx/5xx do Kestra.
        """
        async with httpx.AsyncClient(
            base_url=self._settings.kestra_url.rstrip("/"),
            timeout=self._settings.kestra_timeout,
        ) as client:
            response = await client.post(
                f"/api/v1/executions/{namespace}/{flow_id}",
                json=inputs or {},
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
