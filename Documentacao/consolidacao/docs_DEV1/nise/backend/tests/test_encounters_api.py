"""
============================================================================
NISE TRAINING MODULE - ENCOUNTER API TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Encounter API Integration Tests
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

SAMPLE_ENCOUNTER = {
    "resourceType": "Encounter",
    "id": str(uuid.uuid4()),
    "status": "finished",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory"
    },
    "subject": {
        "reference": "Patient/test-patient-123"
    },
    "period": {
        "start": "2026-03-20T09:00:00Z",
        "end": "2026-03-20T10:00:00Z"
    }
}

# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_encounter(client: AsyncClient):
    """Test creating a new encounter."""
    response = await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["resourceType"] == "Encounter"
    assert data["status"] == "finished"
    assert data["class"]["code"] == "AMB"


@pytest.mark.asyncio
async def test_get_encounter(client: AsyncClient):
    """Test retrieving an encounter by ID."""
    # Create encounter first
    create_response = await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    encounter_id = create_response.json()["id"]
    
    # Get encounter
    response = await client.get(f"/api/v1/encounters/{encounter_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == encounter_id


@pytest.mark.asyncio
async def test_update_encounter(client: AsyncClient):
    """Test updating an encounter."""
    # Create encounter first
    create_response = await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    encounter_id = create_response.json()["id"]
    
    # Update encounter
    updated_encounter = SAMPLE_ENCOUNTER.copy()
    updated_encounter["status"] = "in-progress"
    
    response = await client.put(f"/api/v1/encounters/{encounter_id}", json=updated_encounter)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "in-progress"


@pytest.mark.asyncio
async def test_delete_encounter(client: AsyncClient):
    """Test deleting an encounter."""
    # Create encounter first
    create_response = await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    encounter_id = create_response.json()["id"]
    
    # Delete encounter
    response = await client.delete(f"/api/v1/encounters/{encounter_id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion
    get_response = await client.get(f"/api/v1/encounters/{encounter_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_search_encounters_by_patient(client: AsyncClient):
    """Test searching encounters by patient."""
    # Create encounter first
    await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    
    # Search by patient
    response = await client.get("/api/v1/encounters/?patient=test-patient-123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"


@pytest.mark.asyncio
async def test_search_encounters_by_status(client: AsyncClient):
    """Test searching encounters by status."""
    # Create encounter first
    await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    
    # Search by status
    response = await client.get("/api/v1/encounters/?status=finished")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_search_encounters_by_class(client: AsyncClient):
    """Test searching encounters by class."""
    # Create encounter first
    await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    
    # Search by class
    response = await client.get("/api/v1/encounters/?class=AMB")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_search_encounters_by_date(client: AsyncClient):
    """Test searching encounters by date."""
    # Create encounter first
    await client.post("/api/v1/encounters/", json=SAMPLE_ENCOUNTER)
    
    # Search by date
    response = await client.get("/api/v1/encounters/?date=2026-03-20")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"

