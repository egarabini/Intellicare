"""
============================================================================
NISE TRAINING MODULE - PRACTITIONER API ENDPOINTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Practitioner FHIR R4 API Endpoints
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
from app.models.practitioner import Practitioner
from fhir.resources.practitioner import Practitioner as FHIRPractitioner
from fhir.resources.bundle import Bundle, BundleEntry

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

router = APIRouter(prefix="/practitioners", tags=["Practitioners"])
logger = logging.getLogger(__name__)

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=dict, status_code=201)
async def create_practitioner(
    practitioner_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new FHIR R4 Practitioner."""
    try:
        fhir_practitioner = FHIRPractitioner(**practitioner_data)
        
        practitioner = Practitioner(
            fhir_id=fhir_practitioner.id,
            fhir_resource=fhir_practitioner.dict()
        )
        
        db.add(practitioner)
        await db.commit()
        await db.refresh(practitioner)
        
        logger.info(f"Practitioner created: {practitioner.fhir_id}")
        
        return {
            "resourceType": "Practitioner",
            "id": practitioner.fhir_id,
            **fhir_practitioner.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating practitioner: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{practitioner_id}", response_model=dict)
async def get_practitioner(
    practitioner_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a Practitioner by ID."""
    result = await db.execute(
        select(Practitioner).where(Practitioner.fhir_id == practitioner_id)
    )
    practitioner = result.scalar_one_or_none()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    return practitioner.fhir_resource


@router.put("/{practitioner_id}", response_model=dict)
async def update_practitioner(
    practitioner_id: str,
    practitioner_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update a Practitioner."""
    result = await db.execute(
        select(Practitioner).where(Practitioner.fhir_id == practitioner_id)
    )
    practitioner = result.scalar_one_or_none()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    try:
        fhir_practitioner = FHIRPractitioner(**practitioner_data)
        practitioner.fhir_resource = fhir_practitioner.dict()
        await db.commit()
        await db.refresh(practitioner)
        
        logger.info(f"Practitioner updated: {practitioner_id}")
        return practitioner.fhir_resource
        
    except Exception as e:
        logger.error(f"Error updating practitioner: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{practitioner_id}", status_code=204)
async def delete_practitioner(
    practitioner_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a Practitioner."""
    result = await db.execute(
        select(Practitioner).where(Practitioner.fhir_id == practitioner_id)
    )
    practitioner = result.scalar_one_or_none()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    await db.delete(practitioner)
    await db.commit()
    
    logger.info(f"Practitioner deleted: {practitioner_id}")


@router.get("/", response_model=dict)
async def search_practitioners(
    name: Optional[str] = Query(None, description="Search by name"),
    identifier: Optional[str] = Query(None, description="Search by identifier (CRM)"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Search Practitioners with FHIR search parameters."""
    query = select(Practitioner)
    
    if name:
        query = query.where(
            func.lower(Practitioner.fhir_resource['name'][0]['family'].astext).contains(name.lower())
        )
    
    if identifier:
        query = query.where(
            Practitioner.fhir_resource['identifier'][0]['value'].astext == identifier
        )
    
    if specialty:
        query = query.where(
            Practitioner.fhir_resource['qualification'][0]['code']['coding'][0]['display'].astext.contains(specialty)
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.limit(_count).offset(_offset)
    result = await db.execute(query)
    practitioners = result.scalars().all()
    
    entries = [
        BundleEntry(
            fullUrl=f"Practitioner/{p.fhir_id}",
            resource=FHIRPractitioner(**p.fhir_resource)
        )
        for p in practitioners
    ]
    
    bundle = Bundle(type="searchset", total=total, entry=entries)
    return bundle.dict()

