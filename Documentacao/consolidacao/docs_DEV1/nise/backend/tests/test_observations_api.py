"""
============================================================================
NISE TRAINING MODULE - OBSERVATION API TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Observation API Integration Tests
Versão: 1.0
Data: 20/03/2026
Responsável: DEV2
============================================================================
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

# ============================================================================
# TEST DATA
# ============================================================================

SAMPLE_OBSERVATION = {
    "resourceType": "Observation",
    "id": str(uuid.uuid4()),
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "2339-0",
                "display": "Glucose [Mass/volume] in Blood"
            }
        ]
    },
    "subject": {
        "reference": "Patient/test-patient-123"
    },
    "effectiveDateTime": "2026-03-20T10:00:00Z",
    "valueQuantity": {
        "value": 95,
        "unit": "mg/dL",
        "system": "http://unitsofmeasure.org",
        "code": "mg/dL"
    }
}

# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_observation(client: AsyncClient):
    """Test creating a new observation."""
    response = await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["resourceType"] == "Observation"
    assert data["status"] == "final"
    assert data["code"]["coding"][0]["code"] == "2339-0"


@pytest.mark.asyncio
async def test_get_observation(client: AsyncClient):
    """Test retrieving an observation by ID."""
    # Create observation first
    create_response = await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    observation_id = create_response.json()["id"]
    
    # Get observation
    response = await client.get(f"/api/v1/observations/{observation_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == observation_id
    assert data["status"] == "final"


@pytest.mark.asyncio
async def test_update_observation(client: AsyncClient):
    """Test updating an observation."""
    # Create observation first
    create_response = await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    observation_id = create_response.json()["id"]
    
    # Update observation
    updated_observation = SAMPLE_OBSERVATION.copy()
    updated_observation["status"] = "amended"
    
    response = await client.put(f"/api/v1/observations/{observation_id}", json=updated_observation)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "amended"


@pytest.mark.asyncio
async def test_delete_observation(client: AsyncClient):
    """Test deleting an observation."""
    # Create observation first
    create_response = await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    observation_id = create_response.json()["id"]
    
    # Delete observation
    response = await client.delete(f"/api/v1/observations/{observation_id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion
    get_response = await client.get(f"/api/v1/observations/{observation_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_search_observations_by_patient(client: AsyncClient):
    """Test searching observations by patient."""
    # Create observation first
    await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    
    # Search by patient
    response = await client.get("/api/v1/observations/?patient=test-patient-123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"


@pytest.mark.asyncio
async def test_search_observations_by_code(client: AsyncClient):
    """Test searching observations by LOINC code."""
    # Create observation first
    await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    
    # Search by code
    response = await client.get("/api/v1/observations/?code=2339-0")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_search_observations_by_status(client: AsyncClient):
    """Test searching observations by status."""
    # Create observation first
    await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    
    # Search by status
    response = await client.get("/api/v1/observations/?status=final")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_get_patient_observations(client: AsyncClient):
    """Test getting all observations for a patient."""
    # Create observation first
    await client.post("/api/v1/observations/", json=SAMPLE_OBSERVATION)
    
    # Get patient observations
    response = await client.get("/api/v1/observations/patient/test-patient-123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"

