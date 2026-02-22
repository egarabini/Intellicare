"""
============================================================================
NISE TRAINING MODULE - OBSERVATION API ENDPOINTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Observation FHIR R4 API Endpoints
Versão: 1.0
Data: 18/03/2026
Responsável: DEV2
============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import logging

from app.database import get_db
from app.models.observation import Observation
from fhir.resources.observation import Observation as FHIRObservation
from fhir.resources.bundle import Bundle, BundleEntry

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

router = APIRouter(prefix="/observations", tags=["Observations"])
logger = logging.getLogger(__name__)

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=dict, status_code=201)
async def create_observation(
    observation_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new FHIR R4 Observation.
    
    Args:
        observation_data: FHIR R4 Observation resource (JSON)
        db: Database session
    
    Returns:
        dict: Created observation with ID
    
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Validate FHIR R4
        fhir_observation = FHIRObservation(**observation_data)
        
        # Extract patient reference
        patient_id = None
        if fhir_observation.subject and fhir_observation.subject.reference:
            patient_id = fhir_observation.subject.reference.split('/')[-1]
        
        # Create database record
        observation = Observation(
            fhir_id=fhir_observation.id,
            patient_id=patient_id,
            fhir_resource=fhir_observation.dict()
        )
        
        db.add(observation)
        await db.commit()
        await db.refresh(observation)
        
        logger.info(f"Observation created: {observation.fhir_id}")
        
        return {
            "resourceType": "Observation",
            "id": observation.fhir_id,
            **fhir_observation.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating observation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{observation_id}", response_model=dict)
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get an Observation by ID.
    
    Args:
        observation_id: FHIR Observation ID
        db: Database session
    
    Returns:
        dict: FHIR R4 Observation resource
    
    Raises:
        HTTPException: 404 if not found
    """
    result = await db.execute(
        select(Observation).where(Observation.fhir_id == observation_id)
    )
    observation = result.scalar_one_or_none()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    return observation.fhir_resource


@router.put("/{observation_id}", response_model=dict)
async def update_observation(
    observation_id: str,
    observation_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an Observation.
    
    Args:
        observation_id: FHIR Observation ID
        observation_data: Updated FHIR R4 Observation resource
        db: Database session
    
    Returns:
        dict: Updated observation
    
    Raises:
        HTTPException: 404 if not found, 400 if validation fails
    """
    result = await db.execute(
        select(Observation).where(Observation.fhir_id == observation_id)
    )
    observation = result.scalar_one_or_none()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    try:
        # Validate FHIR R4
        fhir_observation = FHIRObservation(**observation_data)
        
        # Update patient reference
        patient_id = None
        if fhir_observation.subject and fhir_observation.subject.reference:
            patient_id = fhir_observation.subject.reference.split('/')[-1]
        
        # Update
        observation.patient_id = patient_id
        observation.fhir_resource = fhir_observation.dict()
        await db.commit()
        await db.refresh(observation)
        
        logger.info(f"Observation updated: {observation_id}")
        
        return observation.fhir_resource
        
    except Exception as e:
        logger.error(f"Error updating observation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{observation_id}", status_code=204)
async def delete_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an Observation (logical delete).

    Args:
        observation_id: FHIR Observation ID
        db: Database session

    Raises:
        HTTPException: 404 if not found
    """
    result = await db.execute(
        select(Observation).where(Observation.fhir_id == observation_id)
    )
    observation = result.scalar_one_or_none()

    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    await db.delete(observation)
    await db.commit()

    logger.info(f"Observation deleted: {observation_id}")


@router.get("/", response_model=dict)
async def search_observations(
    patient: Optional[str] = Query(None, description="Filter by patient ID"),
    code: Optional[str] = Query(None, description="Filter by LOINC code"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    _count: int = Query(20, ge=1, le=100, description="Number of results"),
    _offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search Observations with FHIR search parameters.

    Args:
        patient: Patient ID (reference)
        code: LOINC code
        status: Observation status (registered, preliminary, final, amended)
        date: Observation date
        category: Category (laboratory, vital-signs, etc.)
        _count: Results per page
        _offset: Pagination offset
        db: Database session

    Returns:
        dict: FHIR Bundle with search results
    """
    # Build query
    query = select(Observation)

    # Apply filters
    if patient:
        query = query.where(Observation.patient_id == patient)

    if code:
        query = query.where(
            Observation.fhir_resource['code']['coding'][0]['code'].astext == code
        )

    if status:
        query = query.where(Observation.fhir_resource['status'].astext == status)

    if date:
        query = query.where(
            Observation.fhir_resource['effectiveDateTime'].astext.like(f"{date}%")
        )

    if category:
        query = query.where(
            Observation.fhir_resource['category'][0]['coding'][0]['code'].astext == category
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.limit(_count).offset(_offset)

    # Execute
    result = await db.execute(query)
    observations = result.scalars().all()

    # Build FHIR Bundle
    entries = [
        BundleEntry(
            fullUrl=f"Observation/{obs.fhir_id}",
            resource=FHIRObservation(**obs.fhir_resource)
        )
        for obs in observations
    ]

    bundle = Bundle(
        type="searchset",
        total=total,
        entry=entries
    )

    return bundle.dict()


@router.get("/patient/{patient_id}", response_model=dict)
async def get_patient_observations(
    patient_id: str,
    code: Optional[str] = Query(None, description="Filter by LOINC code"),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all Observations for a specific patient.

    Args:
        patient_id: Patient ID
        code: Optional LOINC code filter
        _count: Results per page
        _offset: Pagination offset
        db: Database session

    Returns:
        dict: FHIR Bundle with patient's observations
    """
    # Build query
    query = select(Observation).where(Observation.patient_id == patient_id)

    if code:
        query = query.where(
            Observation.fhir_resource['code']['coding'][0]['code'].astext == code
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.limit(_count).offset(_offset)

    # Execute
    result = await db.execute(query)
    observations = result.scalars().all()

    # Build FHIR Bundle
    entries = [
        BundleEntry(
            fullUrl=f"Observation/{obs.fhir_id}",
            resource=FHIRObservation(**obs.fhir_resource)
        )
        for obs in observations
    ]

    bundle = Bundle(
        type="searchset",
        total=total,
        entry=entries
    )

    return bundle.dict()

