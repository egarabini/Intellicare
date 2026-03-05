"""
IntelliCareClient for IntelliCare Bots.
Provides a simplified, tenant-scoped API to access FHIR data and trigger internal actions.
"""

from typing import Any, Dict, List, Optional
import httpx
import json

class IntelliCareClient:
    """
    Client injected into Bot executions.
    This encapsulates HTTP requests to the internal API or direct database 
    access depending on the configuration, but strictly scoping data to `tenant_id`.
    """

    def __init__(self, tenant_id: str, api_base_url: str = "http://intellicare-grahame:8000/api/v1"):
        self.tenant_id = tenant_id
        self.api_base_url = api_base_url
        self._headers = {"X-Tenant-Id": self.tenant_id}

    def create(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a FHIR resource in the current tenant."""
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("Resource must have a 'resourceType'")

        url = f"{self.api_base_url}/fhir/{resource_type}"
        response = httpx.post(url, json=resource, headers=self._headers, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def read(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """Reads a FHIR resource by ID."""
        url = f"{self.api_base_url}/fhir/{resource_type}/{resource_id}"
        response = httpx.get(url, headers=self._headers, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def update(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing FHIR resource."""
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            raise ValueError("Resource must have 'resourceType' and 'id' to be updated")

        url = f"{self.api_base_url}/fhir/{resource_type}/{resource_id}"
        response = httpx.put(url, json=resource, headers=self._headers, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def search(self, resource_type: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Searches for resources of a given type."""
        url = f"{self.api_base_url}/fhir/{resource_type}"
        response = httpx.get(url, params=params, headers=self._headers, timeout=10.0)
        response.raise_for_status()
        bundle = response.json()
        
        if bundle.get("resourceType") == "Bundle" and "entry" in bundle:
            return [entry.get("resource") for entry in bundle["entry"] if "resource" in entry]
        return []

    def send_notification(self, channel: str, to: str, message: str, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Triggers the communication module. 
        Requires that the communication microservice is reachable.
        """
        url = "http://intellicare-comunicacao:8000/api/v1/dispatch"
        payload = {
            "channel": channel,    # e.g., "sms", "email"
            "recipient": to,
            "message": message
        }
        if subject:
            payload["subject"] = subject

        response = httpx.post(url, json=payload, headers=self._headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
