"""
============================================================================
NISE TRAINING MODULE - PRACTITIONER API TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Practitioner API Integration Tests
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

SAMPLE_PRACTITIONER = {
    "resourceType": "Practitioner",
    "id": str(uuid.uuid4()),
    "identifier": [
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
            "value": "CRM-SP-123456"
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Santos",
            "given": ["Maria", "Clara"],
            "prefix": ["Dra."]
        }
    ],
    "qualification": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                        "code": "MD",
                        "display": "Cardiologia"
                    }
                ]
            }
        }
    ]
}

# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_practitioner(client: AsyncClient):
    """Test creating a new practitioner."""
    response = await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["resourceType"] == "Practitioner"
    assert data["name"][0]["family"] == "Santos"


@pytest.mark.asyncio
async def test_get_practitioner(client: AsyncClient):
    """Test retrieving a practitioner by ID."""
    # Create practitioner first
    create_response = await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    practitioner_id = create_response.json()["id"]
    
    # Get practitioner
    response = await client.get(f"/api/v1/practitioners/{practitioner_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == practitioner_id


@pytest.mark.asyncio
async def test_update_practitioner(client: AsyncClient):
    """Test updating a practitioner."""
    # Create practitioner first
    create_response = await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    practitioner_id = create_response.json()["id"]
    
    # Update practitioner
    updated_practitioner = SAMPLE_PRACTITIONER.copy()
    updated_practitioner["name"][0]["family"] = "Silva"
    
    response = await client.put(f"/api/v1/practitioners/{practitioner_id}", json=updated_practitioner)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"][0]["family"] == "Silva"


@pytest.mark.asyncio
async def test_delete_practitioner(client: AsyncClient):
    """Test deleting a practitioner."""
    # Create practitioner first
    create_response = await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    practitioner_id = create_response.json()["id"]
    
    # Delete practitioner
    response = await client.delete(f"/api/v1/practitioners/{practitioner_id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion
    get_response = await client.get(f"/api/v1/practitioners/{practitioner_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_search_practitioners_by_name(client: AsyncClient):
    """Test searching practitioners by name."""
    # Create practitioner first
    await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    
    # Search by name
    response = await client.get("/api/v1/practitioners/?name=Santos")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"


@pytest.mark.asyncio
async def test_search_practitioners_by_identifier(client: AsyncClient):
    """Test searching practitioners by identifier (CRM)."""
    # Create practitioner first
    await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    
    # Search by identifier
    response = await client.get("/api/v1/practitioners/?identifier=CRM-SP-123456")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"


@pytest.mark.asyncio
async def test_search_practitioners_by_specialty(client: AsyncClient):
    """Test searching practitioners by specialty."""
    # Create practitioner first
    await client.post("/api/v1/practitioners/", json=SAMPLE_PRACTITIONER)
    
    # Search by specialty
    response = await client.get("/api/v1/practitioners/?specialty=Cardiologia")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"

