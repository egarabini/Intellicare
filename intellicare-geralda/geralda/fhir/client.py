"""Cliente FHIR para comunicação com Grahame."""

import logging
from typing import Any, Optional

import httpx

from geralda.fhir.careplan_mapper import to_fhir_careplan, from_fhir_careplan
from geralda.models.care_plan import CarePlan
from geralda.models.care_task import CareTask


logger = logging.getLogger(__name__)


class GrahameFHIRClient:
    """
    Cliente HTTP assíncrono para Grahame (FHIR Server).

    Responsável por enviar/receber recursos FHIR CarePlan R4.
    """

    def __init__(self, base_url: str = "http://localhost:8012/api/v1/fhir", timeout: int = 30):
        """
        Inicializa cliente.

        Args:
            base_url: URL base do FHIR server
            timeout: Timeout para requisições em segundos
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Suporte para async context manager."""
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Suporte para async context manager."""
        if self._client:
            await self._client.aclose()

    async def is_available(self) -> bool:
        """
        Verifica se Grahame está disponível.

        Returns:
            True se Grahame responde, False caso contrário
        """
        try:
            async with self:
                response = await self._client.get(f"{self._base_url}/metadata")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Grahame unavailable: {e}")
            return False

    async def put_careplan(
        self,
        plan: CarePlan,
        tasks: list[CareTask],
    ) -> Optional[dict[str, Any]]:
        """
        Envia CarePlan para Grahame via FHIR.

        Args:
            plan: CarePlan do Geralda
            tasks: Lista de tarefas do plano

        Returns:
            Dict com resposta FHIR ou None se falhar

        Raises:
            httpx.HTTPError: Se houver erro de comunicação
        """
        try:
            async with self:
                # Converter para FHIR R4
                fhir_plan = to_fhir_careplan(plan, tasks, self._base_url)

                # Enviar para Grahame (PUT /CarePlan/{id})
                url = f"{self._base_url}/CarePlan/{fhir_plan['id']}"
                response = await self._client.put(url, json=fhir_plan)

                if response.status_code in (200, 201):
                    logger.info(f"CarePlan {plan.id} synced to Grahame FHIR")
                    return response.json()
                else:
                    logger.error(f"Failed to sync CarePlan: {response.status_code}")
                    return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error syncing CarePlan to Grahame: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error syncing CarePlan to Grahame: {e}")
            return None

    async def get_careplan(self, fhir_id: str) -> Optional[dict[str, Any]]:
        """
        Busca CarePlan do Grahame.

        Args:
            fhir_id: ID FHIR do plano

        Returns:
            Dict com recurso FHIR ou None se não encontrado
        """
        try:
            async with self:
                url = f"{self._base_url}/CarePlan/{fhir_id}"
                response = await self._client.get(url)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Error fetching CarePlan: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching CarePlan from Grahame: {e}")
            return None

    async def search_careplans(
        self,
        patient_id: str,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Busca todos os CarePlans de um paciente no Grahame.

        Args:
            patient_id: ID do paciente
            status: Filtro por status FHIR (opcional)

        Returns:
            Lista de recursos FHIR CarePlan
        """
        try:
            async with self:
                # Construir query FHIR
                query_parts = [f"Patient/{patient_id}"]
                if status:
                    query_parts.append(f"status={status}")

                search_query = "?".join(query_parts)
                url = f"{self._base_url}/CarePlan/{search_query}"

                response = await self._client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("entry", [])
                else:
                    logger.error(f"Error searching CarePlans: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error searching CarePlans in Grahame: {e}")
            return []

    async def delete_careplan(self, fhir_id: str) -> bool:
        """
        Deleta CarePlan do Grahame.

        Args:
            fhir_id: ID FHIR do plano

        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            async with self:
                url = f"{self._base_url}/CarePlan/{fhir_id}"
                response = await self._client.delete(url)

                return response.status_code in (200, 204)

        except Exception as e:
            logger.error(f"Error deleting CarePlan from Grahame: {e}")
            return False
