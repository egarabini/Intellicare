"""E2E Validation script for W2-B Access Policies across 5 Personas. 
This script simulates the PolicyContext being injected into Grahame's FHIR routers 
to verify the First-Match-Wins logic, field filtering, and Exception mapping.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mock settings and imports to avoid DB connection issues during simple FastAPI test
import sys
from unittest.mock import MagicMock
sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
sys.modules['redis.asyncio'] = MagicMock()

from grahame.api.app import app
from grahame.api.deps import get_policy_context, PolicyContext, FHIRForbiddenError
from intellicare_core.access.policy_evaluator import PolicyEvaluator
from grahame.services.fhir_service import FHIRService

# Define 5 Persona Policies
POLICIES = {
    "admin": {
        "is_admin": True,
        "resource_rules": []
    },
    "doctor": {
        "is_admin": False,
        "resource_rules": [
            {"resource_type": "Patient", "interaction": ["read", "search"]},
            {"resource_type": "Observation", "interaction": ["read", "search", "create", "update"]}
        ]
    },
    "receptionist": {
        "is_admin": False,
        "resource_rules": [
            {
                "resource_type": "Patient", 
                "interaction": ["read", "search", "create", "update"],
                "hidden_fields": ["telecom"],
                "readonly_fields": ["birthDate"]
            }
            # No access to Observation
        ]
    },
    "bot": {
        "is_admin": False,
        "resource_rules": [
            {"resource_type": "Communication", "interaction": ["create"]}
        ]
    },
    "guest": {
        "is_admin": False,
        "resource_rules": [] # Deny all
    }
}

client = TestClient(app)

# Helper to override the dependency per-persona
def override_policy(persona: str):
    async def mock_get_policy_context():
        return PolicyContext(
            user_id=f"user_{persona}",
            tenant_id="default",
            policy=POLICIES[persona],
            evaluator=PolicyEvaluator()
        )
    app.dependency_overrides[get_policy_context] = mock_get_policy_context

# Mock the FHIRService DB calls to just return static models
class MockRow:
    def __init__(self, resource):
        self.resource = resource
        self.resource_type = resource.get("resourceType")
        self.fhir_id = resource.get("id", "123")

async def mock_get(self, resource_type, fhir_id):
    if resource_type == "Patient":
        return MockRow({"resourceType": "Patient", "id": fhir_id, "name": [{"given": ["John"]}], "telecom": [{"value": "555-1234"}]})
    return MockRow({"resourceType": resource_type, "id": fhir_id})

async def mock_search(self, resource_type, limit=100, offset=0):
    if resource_type == "Patient":
        return [MockRow({"resourceType": "Patient", "id": "1", "name": [{"given": ["John"]}], "telecom": [{"value": "555-1234"}]})]
    return []

async def mock_upsert(self, resource):
    return MockRow(resource)

async def mock_delete(self, resource_type, fhir_id):
    pass

FHIRService.get = mock_get
FHIRService.search = mock_search
FHIRService.upsert = mock_upsert
FHIRService.delete = mock_delete


def run_tests():
    print("Starting E2E Persona Validation for W2-B...")

    # 1. Admin Persona (Allowed everything)
    override_policy("admin")
    resp = client.get("/api/v1/Patient/123")
    assert resp.status_code == 200, "Admin should read Patient"
    resp = client.delete("/api/v1/Observation/456")
    assert resp.status_code == 204, "Admin should delete Observation"
    print("✅ Admin permissions verified.")

    # 2. Doctor Persona (Read Patient, Write Observation)
    override_policy("doctor")
    resp = client.get("/api/v1/Patient/123")
    assert resp.status_code == 200, "Doctor should read Patient"
    resp = client.delete("/api/v1/Patient/123")
    assert resp.status_code == 403, "Doctor should NOT delete Patient"
    assert resp.json()["issue"][0]["code"] == "forbidden"
    resp = client.post("/api/v1/Observation", json={"resourceType": "Observation", "status": "final"})
    assert resp.status_code == 201, "Doctor should create Observation"
    print("✅ Doctor permissions verified.")

    # 3. Receptionist Persona (Read/Write Patient, Hidden Telecom)
    override_policy("receptionist")
    resp = client.get("/api/v1/Patient/123")
    assert resp.status_code == 200, "Receptionist should read Patient"
    assert "telecom" not in resp.json(), "Telecom should be hidden from Receptionist"
    assert "name" in resp.json(), "Name should be visible"
    resp = client.get("/api/v1/Observation/456")
    assert resp.status_code == 403, "Receptionist should NOT read Observation"
    # Testing search filtering
    resp = client.get("/api/v1/Patient")
    assert resp.status_code == 200
    assert "telecom" not in resp.json()["entry"][0]["resource"], "Telecom should be hidden in Search Bundles"
    print("✅ Receptionist permissions and hidden_fields verified.")

    # 4. Bot Persona (Submit Communication only)
    override_policy("bot")
    resp = client.get("/api/v1/Patient/123")
    assert resp.status_code == 403, "Bot should NOT read Patient"
    resp = client.post("/api/v1/Communication", json={"resourceType": "Communication"})
    assert resp.status_code == 201, "Bot should create Communication"
    print("✅ Service Bot permissions verified.")

    # 5. Guest Persona (Deny All)
    override_policy("guest")
    resp = client.get("/api/v1/Patient/123")
    assert resp.status_code == 403, "Guest should NOT read Patient"
    resp = client.post("/api/v1/Patient", json={"resourceType": "Patient"})
    assert resp.status_code == 403, "Guest should NOT create Patient"
    print("✅ Guest (Deny-All) permissions verified.")
    print("\\nAll 5 Personas successfully evaluated. W2-B Engine is fully integrated with Grahame.")

if __name__ == "__main__":
    run_tests()
