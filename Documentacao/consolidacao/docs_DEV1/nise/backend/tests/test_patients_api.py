"""
============================================================================
NISE TRAINING MODULE - PATIENT API TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Patient API Integration Tests
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

SAMPLE_PATIENT = {
    "resourceType": "Patient",
    "id": str(uuid.uuid4()),
    "identifier": [
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "value": "12345678901"
        },
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns",
            "value": "123456789012345"
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Silva",
            "given": ["João", "Pedro"]
        }
    ],
    "gender": "male",
    "birthDate": "1980-01-15",
    "address": [
        {
            "use": "home",
            "city": "São Paulo",
            "state": "SP",
            "country": "BR"
        }
    ]
}

# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_patient(client: AsyncClient):
    """Test creating a new patient."""
    response = await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["resourceType"] == "Patient"
    assert data["id"] == SAMPLE_PATIENT["id"]
    assert data["name"][0]["family"] == "Silva"


@pytest.mark.asyncio
async def test_get_patient(client: AsyncClient):
    """Test retrieving a patient by ID."""
    # Create patient first
    create_response = await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    patient_id = create_response.json()["id"]
    
    # Get patient
    response = await client.get(f"/api/v1/patients/{patient_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == patient_id
    assert data["name"][0]["family"] == "Silva"


@pytest.mark.asyncio
async def test_get_patient_not_found(client: AsyncClient):
    """Test retrieving a non-existent patient."""
    response = await client.get(f"/api/v1/patients/{uuid.uuid4()}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_patient(client: AsyncClient):
    """Test updating a patient."""
    # Create patient first
    create_response = await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    patient_id = create_response.json()["id"]
    
    # Update patient
    updated_patient = SAMPLE_PATIENT.copy()
    updated_patient["name"][0]["family"] = "Santos"
    
    response = await client.put(f"/api/v1/patients/{patient_id}", json=updated_patient)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"][0]["family"] == "Santos"


@pytest.mark.asyncio
async def test_delete_patient(client: AsyncClient):
    """Test deleting a patient."""
    # Create patient first
    create_response = await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    patient_id = create_response.json()["id"]
    
    # Delete patient
    response = await client.delete(f"/api/v1/patients/{patient_id}")
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion
    get_response = await client.get(f"/api/v1/patients/{patient_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_search_patients_by_name(client: AsyncClient):
    """Test searching patients by name."""
    # Create patient first
    await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    
    # Search by name
    response = await client.get("/api/v1/patients/?name=Silva")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_patients_by_gender(client: AsyncClient):
    """Test searching patients by gender."""
    # Create patient first
    await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    
    # Search by gender
    response = await client.get("/api/v1/patients/?gender=male")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_patients_pagination(client: AsyncClient):
    """Test patient search pagination."""
    # Create multiple patients
    for i in range(5):
        patient = SAMPLE_PATIENT.copy()
        patient["id"] = str(uuid.uuid4())
        await client.post("/api/v1/patients/", json=patient)
    
    # Test pagination
    response = await client.get("/api/v1/patients/?_count=2&_offset=0")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["entry"]) <= 2


@pytest.mark.asyncio
async def test_patient_everything_operation(client: AsyncClient):
    """Test $everything operation."""
    # Create patient first
    create_response = await client.post("/api/v1/patients/", json=SAMPLE_PATIENT)
    patient_id = create_response.json()["id"]
    
    # Get everything
    response = await client.get(f"/api/v1/patients/{patient_id}/$everything")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["total"] >= 1

