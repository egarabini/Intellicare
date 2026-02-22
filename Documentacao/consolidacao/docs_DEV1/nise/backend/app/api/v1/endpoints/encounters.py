"""
============================================================================
NISE TRAINING MODULE - ENCOUNTER API ENDPOINTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Encounter FHIR R4 API Endpoints
Versão: 1.0
Data: 18/03/2026
Responsável: DEV2
============================================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.database import get_db
from app.models.encounter import Encounter
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.bundle import Bundle, BundleEntry

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

router = APIRouter(prefix="/encounters", tags=["Encounters"])
logger = logging.getLogger(__name__)

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=dict, status_code=201)
async def create_encounter(
    encounter_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new FHIR R4 Encounter."""
    try:
        fhir_encounter = FHIREncounter(**encounter_data)
        
        # Extract patient reference
        patient_id = None
        if fhir_encounter.subject and fhir_encounter.subject.reference:
            patient_id = fhir_encounter.subject.reference.split('/')[-1]
        
        encounter = Encounter(
            fhir_id=fhir_encounter.id,
            patient_id=patient_id,
            fhir_resource=fhir_encounter.dict()
        )
        
        db.add(encounter)
        await db.commit()
        await db.refresh(encounter)
        
        logger.info(f"Encounter created: {encounter.fhir_id}")
        
        return {
            "resourceType": "Encounter",
            "id": encounter.fhir_id,
            **fhir_encounter.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating encounter: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{encounter_id}", response_model=dict)
async def get_encounter(
    encounter_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get an Encounter by ID."""
    result = await db.execute(
        select(Encounter).where(Encounter.fhir_id == encounter_id)
    )
    encounter = result.scalar_one_or_none()
    
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    return encounter.fhir_resource


@router.put("/{encounter_id}", response_model=dict)
async def update_encounter(
    encounter_id: str,
    encounter_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update an Encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.fhir_id == encounter_id)
    )
    encounter = result.scalar_one_or_none()
    
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    try:
        fhir_encounter = FHIREncounter(**encounter_data)
        
        patient_id = None
        if fhir_encounter.subject and fhir_encounter.subject.reference:
            patient_id = fhir_encounter.subject.reference.split('/')[-1]
        
        encounter.patient_id = patient_id
        encounter.fhir_resource = fhir_encounter.dict()
        await db.commit()
        await db.refresh(encounter)
        
        logger.info(f"Encounter updated: {encounter_id}")
        return encounter.fhir_resource
        
    except Exception as e:
        logger.error(f"Error updating encounter: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{encounter_id}", status_code=204)
async def delete_encounter(
    encounter_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an Encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.fhir_id == encounter_id)
    )
    encounter = result.scalar_one_or_none()
    
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    await db.delete(encounter)
    await db.commit()
    
    logger.info(f"Encounter deleted: {encounter_id}")


@router.get("/", response_model=dict)
async def search_encounters(
    patient: Optional[str] = Query(None, description="Filter by patient ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    class_code: Optional[str] = Query(None, alias="class", description="Filter by class (AMB, EMER, etc.)"),
    date: Optional[str] = Query(None, description="Filter by date"),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Search Encounters with FHIR search parameters."""
    query = select(Encounter)
    
    if patient:
        query = query.where(Encounter.patient_id == patient)
    
    if status:
        query = query.where(Encounter.fhir_resource['status'].astext == status)
    
    if class_code:
        query = query.where(Encounter.fhir_resource['class']['code'].astext == class_code)
    
    if date:
        query = query.where(
            Encounter.fhir_resource['period']['start'].astext.like(f"{date}%")
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.limit(_count).offset(_offset)
    result = await db.execute(query)
    encounters = result.scalars().all()
    
    entries = [
        BundleEntry(
            fullUrl=f"Encounter/{enc.fhir_id}",
            resource=FHIREncounter(**enc.fhir_resource)
        )
        for enc in encounters
    ]
    
    bundle = Bundle(type="searchset", total=total, entry=entries)
    return bundle.dict()

