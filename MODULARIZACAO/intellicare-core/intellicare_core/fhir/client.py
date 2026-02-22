"""Cliente HTTP para servidores FHIR R4.

Extraido e simplificado do fhir_mcp_server.py do monolito.
Fornece acesso padronizado a recursos FHIR para todos os modulos.

Exemplo:
    client = FHIRClient("http://localhost:8080/fhir")
    patient = await client.get_patient("patient-123")
    observations = await client.get_observations("patient-123", code="2160-0")
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from intellicare_core.fhir.models import (
    AllergySummary,
    ConditionSummary,
    MedicationSummary,
    ObservationValue,
    PatientSummary,
)

logger = logging.getLogger(__name__)


class FHIRClientError(Exception):
    """Erro de comunicacao com o servidor FHIR."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FHIRClient:
    """Cliente HTTP assincrono para servidores FHIR R4."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        auth_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers: dict[str, str] = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        if auth_token:
            self._headers["Authorization"] = f"Bearer {auth_token}"

    def _build_url(self, resource_type: str, resource_id: str = "") -> str:
        if resource_id:
            return f"{self.base_url}/{resource_type}/{resource_id}"
        return f"{self.base_url}/{resource_type}"

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Faz requisicao HTTP ao servidor FHIR."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise FHIRClientError(f"Timeout ao acessar {url}", status_code=408)
            except httpx.HTTPStatusError as e:
                raise FHIRClientError(
                    f"Erro HTTP {e.response.status_code}: {e.response.text[:200]}",
                    status_code=e.response.status_code,
                )
            except httpx.RequestError as e:
                raise FHIRClientError(f"Erro de conexao: {e}")

    async def get_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> dict[str, Any]:
        """Busca um recurso FHIR por tipo e ID."""
        url = self._build_url(resource_type, resource_id)
        return await self._request("GET", url)

    async def search(
        self,
        resource_type: str,
        params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Busca recursos FHIR com parametros de busca. Retorna lista de entries."""
        url = self._build_url(resource_type)
        result = await self._request("GET", url, params=params)
        entries = result.get("entry", [])
        return [e.get("resource", e) for e in entries]

    async def get_patient(self, patient_id: str) -> dict[str, Any]:
        """Busca paciente por ID FHIR."""
        return await self.get_resource("Patient", patient_id)

    async def search_patient_by_cpf(self, cpf: str) -> list[dict[str, Any]]:
        """Busca pacientes por CPF."""
        return await self.search("Patient", {"identifier": cpf})

    async def get_observations(
        self,
        patient_id: str,
        code: str | None = None,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Busca observacoes clinicas de um paciente."""
        params: dict[str, str] = {
            "patient": patient_id,
            "_count": str(count),
            "_sort": "-date",
        }
        if code:
            params["code"] = code
        return await self.search("Observation", params)

    async def get_conditions(self, patient_id: str) -> list[dict[str, Any]]:
        """Busca condicoes clinicas (diagnosticos) de um paciente."""
        return await self.search("Condition", {"patient": patient_id})

    async def get_allergies(self, patient_id: str) -> list[dict[str, Any]]:
        """Busca alergias de um paciente."""
        return await self.search("AllergyIntolerance", {"patient": patient_id})

    async def get_medications(self, patient_id: str) -> list[dict[str, Any]]:
        """Busca medicamentos em uso de um paciente."""
        return await self.search("MedicationRequest", {"patient": patient_id})

    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        """Gera um resumo consolidado do paciente (IPS simplificado).

        Busca Patient + Conditions + Observations + Allergies + Medications
        e retorna um PatientSummary unificado.
        """
        patient_data = await self.get_patient(patient_id)

        # Extrair dados basicos do paciente
        name = ""
        if patient_data.get("name"):
            name_obj = patient_data["name"][0]
            given = " ".join(name_obj.get("given", []))
            family = name_obj.get("family", "")
            name = f"{given} {family}".strip()

        cpf = ""
        for identifier in patient_data.get("identifier", []):
            system = identifier.get("system", "")
            if "cpf" in system.lower() or "br-cpf" in system.lower():
                cpf = identifier.get("value", "")
                break

        birth_date = None
        if patient_data.get("birthDate"):
            from datetime import date as date_type

            try:
                birth_date = date_type.fromisoformat(patient_data["birthDate"])
            except ValueError:
                pass

        # Buscar dados clinicos em paralelo
        conditions_raw = await self.get_conditions(patient_id)
        observations_raw = await self.get_observations(patient_id)
        allergies_raw = await self.get_allergies(patient_id)
        medications_raw = await self.get_medications(patient_id)

        # Converter para modelos simplificados
        conditions = self._parse_conditions(conditions_raw)
        observations = self._parse_observations(observations_raw)
        allergies = self._parse_allergies(allergies_raw)
        medications = self._parse_medications(medications_raw)

        return PatientSummary(
            patient_id=patient_id,
            name=name,
            birth_date=birth_date,
            gender=patient_data.get("gender", ""),
            cpf=cpf,
            conditions=conditions,
            observations=observations,
            allergies=allergies,
            medications=medications,
        )

    @staticmethod
    def _parse_conditions(raw: list[dict[str, Any]]) -> list[ConditionSummary]:
        result = []
        for item in raw:
            code_obj = item.get("code", {})
            coding = code_obj.get("coding", [{}])[0] if code_obj.get("coding") else {}
            result.append(
                ConditionSummary(
                    code=coding.get("code", "unknown"),
                    display=coding.get("display", code_obj.get("text", "")),
                    clinical_status=item.get("clinicalStatus", {})
                    .get("coding", [{}])[0]
                    .get("code", "active")
                    if isinstance(item.get("clinicalStatus"), dict)
                    else "active",
                )
            )
        return result

    @staticmethod
    def _parse_observations(raw: list[dict[str, Any]]) -> list[ObservationValue]:
        result = []
        for item in raw:
            code_obj = item.get("code", {})
            coding = code_obj.get("coding", [{}])[0] if code_obj.get("coding") else {}

            value = None
            unit = ""
            vq = item.get("valueQuantity", {})
            if vq:
                value = vq.get("value")
                unit = vq.get("unit", "")

            obs_date = None
            if item.get("effectiveDateTime"):
                from datetime import datetime as dt

                try:
                    obs_date = dt.fromisoformat(
                        item["effectiveDateTime"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            ref_low = None
            ref_high = None
            for ref_range in item.get("referenceRange", []):
                if ref_range.get("low"):
                    ref_low = ref_range["low"].get("value")
                if ref_range.get("high"):
                    ref_high = ref_range["high"].get("value")

            result.append(
                ObservationValue(
                    code=coding.get("code", "unknown"),
                    display=coding.get("display", ""),
                    value=value,
                    unit=unit,
                    date=obs_date,
                    reference_low=ref_low,
                    reference_high=ref_high,
                )
            )
        return result

    @staticmethod
    def _parse_allergies(raw: list[dict[str, Any]]) -> list[AllergySummary]:
        result = []
        for item in raw:
            code_obj = item.get("code", {})
            substance = code_obj.get("text", "")
            if not substance and code_obj.get("coding"):
                substance = code_obj["coding"][0].get("display", "")

            reaction = ""
            if item.get("reaction"):
                manifestations = item["reaction"][0].get("manifestation", [])
                if manifestations:
                    reaction = manifestations[0].get("coding", [{}])[0].get(
                        "display", ""
                    )

            result.append(
                AllergySummary(
                    substance=substance,
                    reaction=reaction,
                    severity=item.get("reaction", [{}])[0].get("severity", "")
                    if item.get("reaction")
                    else "",
                )
            )
        return result

    @staticmethod
    def _parse_medications(raw: list[dict[str, Any]]) -> list[MedicationSummary]:
        result = []
        for item in raw:
            med_obj = item.get("medicationCodeableConcept", {})
            name = med_obj.get("text", "")
            if not name and med_obj.get("coding"):
                name = med_obj["coding"][0].get("display", "")

            code = ""
            if med_obj.get("coding"):
                code = med_obj["coding"][0].get("code", "")

            dosage = ""
            if item.get("dosageInstruction"):
                dose_obj = item["dosageInstruction"][0]
                dosage = dose_obj.get("text", "")

            result.append(
                MedicationSummary(
                    name=name,
                    code=code,
                    dosage=dosage,
                    status=item.get("status", "active"),
                )
            )
        return result

    async def check_connection(self) -> bool:
        """Verifica se o servidor FHIR esta acessivel."""
        try:
            url = f"{self.base_url}/metadata"
            await self._request("GET", url)
            return True
        except FHIRClientError:
            return False
