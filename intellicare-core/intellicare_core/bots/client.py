"""IntelliCareClient — async FHIR client for use inside bot code.

Bots receive an instance of this client pre-authenticated for their tenant.
The client connects to intellicare-grahame's FHIR API.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx


class IntelliCareClient:
    """Minimal FHIR client scoped to a single tenant.

    Bot code receives this as ``client``:

        resource = await client.read("Patient", patient_id)
        obs = {"resourceType": "Observation", ...}
        created = await client.create(obs)
        results = await client.search("Observation", {"subject": "Patient/123"})
    """

    def __init__(
        self,
        tenant_id: str,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.base_url = (
            base_url
            or os.getenv("GRAHAME_URL", "http://intellicare-grahame:8000")
        ).rstrip("/")
        self._token = token
        self._headers = {
            "Content-Type": "application/fhir+json",
            "X-Tenant-ID": tenant_id,
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    # ── FHIR operations ────────────────────────────────────────────────────

    async def read(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        """Read a FHIR resource by type and id."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/{resource_type}/{resource_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def create(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Create a FHIR resource (upsert via grahame)."""
        resource_type = resource.get("resourceType", "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/{resource_type}",
                json=resource,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def update(self, resource: dict[str, Any]) -> dict[str, Any]:
        """Update (upsert) a FHIR resource."""
        return await self.create(resource)

    async def search(
        self,
        resource_type: str,
        params: Optional[dict[str, str]] = None,
    ) -> list[dict[str, Any]]:
        """Search FHIR resources. Returns list of resource dicts."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/{resource_type}",
                params=params or {},
                headers=self._headers,
            )
            resp.raise_for_status()
            bundle = resp.json()
            return [e["resource"] for e in bundle.get("entry", [])]

    async def send_notification(
        self,
        channel: str,
        to: str,
        message: str,
        *,
        severity: str = "medium",
    ) -> dict[str, Any]:
        """Send a clinical alert via intellicare-comunicacao.

        Args:
            channel: "rocketchat" | "email" | "whatsapp"
            to:      patient_id or recipient identifier
            message: alert message
        """
        comunicacao_url = os.getenv(
            "COMUNICACAO_URL", "http://intellicare-comunicacao:8000"
        ).rstrip("/")
        payload = {
            "patient_id": to,
            "source_module": "bot-engine",
            "alert_type": "bot_notification",
            "severity": severity,
            "message": message,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{comunicacao_url}/api/v1/events/clinical-alert",
                json=payload,
                headers={"X-Tenant-ID": self.tenant_id},
            )
            resp.raise_for_status()
            return resp.json()
