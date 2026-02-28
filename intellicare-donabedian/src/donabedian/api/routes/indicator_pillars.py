"""
IndicatorPillar CRUD endpoints.

Provides REST API endpoints for managing indicator-pillar associations with weights.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.api.dependencies import get_db
from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.indicator import Indicator
from donabedian.models.pillar import Pillar
from donabedian.schemas.indicator_pillar import (
    IndicatorPillarCreate,
    IndicatorPillarUpdate,
    IndicatorPillarRead,
    IndicatorPillarList,
    IndicatorPillarWithNames,
)
from donabedian.schemas.common import PaginatedResponse, MessageResponse

# Keycloak authentication - optional dependency
try:
    from intellicare_auth import get_current_user, requires_role
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    # Dummy implementations for when auth is not available
    async def get_current_user():
        return {"sub": "anonymous", "preferred_username": "anonymous"}

    def requires_role(role: str):
        def decorator(func):
            return func
        return decorator

router = APIRouter()


@router.get("/indicator-pillars", response_model=PaginatedResponse[IndicatorPillarList])
async def list_indicator_pillars(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    indicator_id: int | None = Query(None, description="Filter by indicator ID"),
    pillar_id: int | None = Query(None, description="Filter by pillar ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[IndicatorPillarList]:
    """
    List indicator-pillar associations with pagination and optional filtering.

    **Authentication**: Required (any authenticated user)

    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page (max 100)
        indicator_id: Optional filter by indicator ID
        pillar_id: Optional filter by pillar ID
        user: Current authenticated user
        db: Database session

    Returns:
        PaginatedResponse[IndicatorPillarList]: Paginated list of associations
    """
    # Build query
    query = select(IndicatorPillar)
    count_query = select(func.count()).select_from(IndicatorPillar)
    
    if indicator_id:
        query = query.where(IndicatorPillar.indicator_id == indicator_id)
        count_query = count_query.where(IndicatorPillar.indicator_id == indicator_id)
    
    if pillar_id:
        query = query.where(IndicatorPillar.pillar_id == pillar_id)
        count_query = count_query.where(IndicatorPillar.pillar_id == pillar_id)
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    
    # Get paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        query
        .order_by(IndicatorPillar.id)
        .limit(page_size)
        .offset(offset)
    )
    associations = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[IndicatorPillarList.model_validate(a) for a in associations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/indicator-pillars/{association_id}", response_model=IndicatorPillarRead)
async def get_indicator_pillar(
    association_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorPillarRead:
    """
    Get a specific indicator-pillar association by ID.

    **Authentication**: Required (any authenticated user)

    Args:
        association_id: Association ID
        user: Current authenticated user
        db: Database session

    Returns:
        IndicatorPillarRead: Association details

    Raises:
        HTTPException: 404 if association not found
    """
    result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.id == association_id)
    )
    association = result.scalar_one_or_none()
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IndicatorPillar with id {association_id} not found"
        )
    
    return IndicatorPillarRead.model_validate(association)


@router.post("/indicator-pillars", response_model=IndicatorPillarRead, status_code=status.HTTP_201_CREATED)
@requires_role("intellicare_admin")
async def create_indicator_pillar(
    association_data: IndicatorPillarCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorPillarRead:
    """
    Create a new indicator-pillar association.

    Validates that both indicator and pillar exist before creating the association.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        association_data: Association creation data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        IndicatorPillarRead: Created association
        
    Raises:
        HTTPException: 404 if indicator or pillar not found
    """
    # Validate indicator exists
    indicator_result = await db.execute(
        select(Indicator).where(Indicator.id == association_data.indicator_id)
    )
    if not indicator_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {association_data.indicator_id} not found"
        )
    
    # Validate pillar exists
    pillar_result = await db.execute(
        select(Pillar).where(Pillar.id == association_data.pillar_id)
    )
    if not pillar_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar with id {association_data.pillar_id} not found"
        )
    
    # Create association
    association = IndicatorPillar(**association_data.model_dump())
    
    db.add(association)
    await db.commit()
    await db.refresh(association)

    return IndicatorPillarRead.model_validate(association)


@router.put("/indicator-pillars/{association_id}", response_model=IndicatorPillarRead)
@requires_role("intellicare_admin")
async def update_indicator_pillar(
    association_id: int,
    association_data: IndicatorPillarUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorPillarRead:
    """
    Update an existing indicator-pillar association.

    Typically used to update the weight of the association.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        association_id: Association ID
        association_data: Association update data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        IndicatorPillarRead: Updated association

    Raises:
        HTTPException: 404 if association not found
    """
    # Get existing association
    result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.id == association_id)
    )
    association = result.scalar_one_or_none()

    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IndicatorPillar with id {association_id} not found"
        )

    # Update fields (only non-None values)
    update_data = association_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(association, field, value)

    await db.commit()
    await db.refresh(association)

    return IndicatorPillarRead.model_validate(association)


@router.delete("/indicator-pillars/{association_id}", response_model=MessageResponse)
@requires_role("intellicare_admin")
async def delete_indicator_pillar(
    association_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete an indicator-pillar association.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        association_id: Association ID
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: 404 if association not found
    """
    # Get existing association
    result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.id == association_id)
    )
    association = result.scalar_one_or_none()

    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IndicatorPillar with id {association_id} not found"
        )

    await db.delete(association)
    await db.commit()

    return MessageResponse(message=f"IndicatorPillar {association_id} deleted successfully")

