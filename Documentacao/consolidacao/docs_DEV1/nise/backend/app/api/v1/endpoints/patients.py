"""
============================================================================
NISE TRAINING MODULE - PATIENT API ENDPOINTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Patient FHIR R4 API Endpoints
Versão: 1.0
Data: 17/03/2026
Responsável: DEV2
============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import logging

from app.database import get_db
from app.models.patient import Patient
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.bundle import Bundle, BundleEntry

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

router = APIRouter(prefix="/patients", tags=["Patients"])
logger = logging.getLogger(__name__)

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=dict, status_code=201)
async def create_patient(
    patient_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new FHIR R4 Patient.
    
    Args:
        patient_data: FHIR R4 Patient resource (JSON)
        db: Database session
    
    Returns:
        dict: Created patient with ID
    
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Validate FHIR R4
        fhir_patient = FHIRPatient(**patient_data)
        
        # Create database record
        patient = Patient(
            fhir_id=fhir_patient.id,
            fhir_resource=fhir_patient.dict()
        )
        
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        
        logger.info(f"Patient created: {patient.fhir_id}")
        
        return {
            "resourceType": "Patient",
            "id": patient.fhir_id,
            **fhir_patient.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{patient_id}", response_model=dict)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a Patient by ID.
    
    Args:
        patient_id: FHIR Patient ID
        db: Database session
    
    Returns:
        dict: FHIR R4 Patient resource
    
    Raises:
        HTTPException: 404 if not found
    """
    result = await db.execute(
        select(Patient).where(Patient.fhir_id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient.fhir_resource


@router.put("/{patient_id}", response_model=dict)
async def update_patient(
    patient_id: str,
    patient_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a Patient.
    
    Args:
        patient_id: FHIR Patient ID
        patient_data: Updated FHIR R4 Patient resource
        db: Database session
    
    Returns:
        dict: Updated patient
    
    Raises:
        HTTPException: 404 if not found, 400 if validation fails
    """
    result = await db.execute(
        select(Patient).where(Patient.fhir_id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    try:
        # Validate FHIR R4
        fhir_patient = FHIRPatient(**patient_data)
        
        # Update
        patient.fhir_resource = fhir_patient.dict()
        await db.commit()
        await db.refresh(patient)
        
        logger.info(f"Patient updated: {patient_id}")
        
        return patient.fhir_resource
        
    except Exception as e:
        logger.error(f"Error updating patient: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a Patient (logical delete).
    
    Args:
        patient_id: FHIR Patient ID
        db: Database session
    
    Raises:
        HTTPException: 404 if not found
    """
    result = await db.execute(
        select(Patient).where(Patient.fhir_id == patient_id)
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    await db.delete(patient)
    await db.commit()

    logger.info(f"Patient deleted: {patient_id}")


@router.get("/", response_model=dict)
async def search_patients(
    name: Optional[str] = Query(None, description="Search by name"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    birthdate: Optional[str] = Query(None, description="Filter by birthdate"),
    identifier: Optional[str] = Query(None, description="Search by identifier (CPF/CNS)"),
    _count: int = Query(20, ge=1, le=100, description="Number of results"),
    _offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search Patients with FHIR search parameters.

    Args:
        name: Patient name (partial match)
        gender: Gender (male, female, other, unknown)
        birthdate: Birth date (YYYY-MM-DD)
        identifier: CPF or CNS
        _count: Results per page
        _offset: Pagination offset
        db: Database session

    Returns:
        dict: FHIR Bundle with search results
    """
    # Build query
    query = select(Patient)

    # Apply filters using JSONB queries
    if name:
        query = query.where(
            func.lower(Patient.fhir_resource['name'][0]['family'].astext).contains(name.lower())
        )

    if gender:
        query = query.where(Patient.fhir_resource['gender'].astext == gender)

    if birthdate:
        query = query.where(Patient.fhir_resource['birthDate'].astext == birthdate)

    if identifier:
        query = query.where(
            or_(
                Patient.fhir_resource['identifier'][0]['value'].astext == identifier,
                Patient.fhir_resource['identifier'][1]['value'].astext == identifier
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.limit(_count).offset(_offset)

    # Execute
    result = await db.execute(query)
    patients = result.scalars().all()

    # Build FHIR Bundle
    entries = [
        BundleEntry(
            fullUrl=f"Patient/{p.fhir_id}",
            resource=FHIRPatient(**p.fhir_resource)
        )
        for p in patients
    ]

    bundle = Bundle(
        type="searchset",
        total=total,
        entry=entries
    )

    return bundle.dict()


@router.get("/{patient_id}/$everything", response_model=dict)
async def get_patient_everything(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Patient with all related resources (FHIR $everything operation).

    Args:
        patient_id: FHIR Patient ID
        db: Database session

    Returns:
        dict: FHIR Bundle with Patient and related resources

    Raises:
        HTTPException: 404 if not found
    """
    # Get patient
    result = await db.execute(
        select(Patient).where(Patient.fhir_id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # TODO: Get related resources (Observations, Encounters, etc.)
    # For now, return only patient

    entries = [
        BundleEntry(
            fullUrl=f"Patient/{patient.fhir_id}",
            resource=FHIRPatient(**patient.fhir_resource)
        )
    ]

    bundle = Bundle(
        type="searchset",
        total=1,
        entry=entries
    )

    return bundle.dict()

