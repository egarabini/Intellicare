"""
Indicator CRUD endpoints.

Provides REST API endpoints for managing quality indicators.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.api.dependencies import get_db
from donabedian.models.indicator import Indicator
from donabedian.schemas.indicator import (
    IndicatorCreate,
    IndicatorUpdate,
    IndicatorRead,
    IndicatorList,
)
from donabedian.schemas.common import PaginatedResponse, MessageResponse

# Keycloak authentication
from intellicare_auth import get_current_user, requires_role

router = APIRouter()


@router.get("/indicators", response_model=PaginatedResponse[IndicatorList])
async def list_indicators(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[IndicatorList]:
    """
    List indicators with pagination.

    **Authentication**: Required (any authenticated user)

    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page (max 100)
        user: Current authenticated user
        db: Database session

    Returns:
        PaginatedResponse[IndicatorList]: Paginated list of indicators
    """
    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Indicator))
    total = count_result.scalar_one()
    
    # Get paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Indicator)
        .order_by(Indicator.name)
        .limit(page_size)
        .offset(offset)
    )
    indicators = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[IndicatorList.model_validate(i) for i in indicators],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/indicators/{indicator_id}", response_model=IndicatorRead)
async def get_indicator(
    indicator_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorRead:
    """
    Get a specific indicator by ID.

    **Authentication**: Required (any authenticated user)

    Args:
        indicator_id: Indicator ID
        user: Current authenticated user
        db: Database session

    Returns:
        IndicatorRead: Indicator details

    Raises:
        HTTPException: 404 if indicator not found
    """
    result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    
    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found"
        )
    
    return IndicatorRead.model_validate(indicator)


@router.post("/indicators", response_model=IndicatorRead, status_code=status.HTTP_201_CREATED)
@requires_role("intellicare_admin")
async def create_indicator(
    indicator_data: IndicatorCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorRead:
    """
    Create a new indicator.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        indicator_data: Indicator creation data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        IndicatorRead: Created indicator
    """
    # Create new indicator
    indicator = Indicator(**indicator_data.model_dump())
    
    db.add(indicator)
    await db.commit()
    await db.refresh(indicator)
    
    return IndicatorRead.model_validate(indicator)


@router.put("/indicators/{indicator_id}", response_model=IndicatorRead)
@requires_role("intellicare_admin")
async def update_indicator(
    indicator_id: int,
    indicator_data: IndicatorUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorRead:
    """
    Update an existing indicator.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        indicator_id: Indicator ID
        indicator_data: Indicator update data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        IndicatorRead: Updated indicator

    Raises:
        HTTPException: 404 if indicator not found
    """
    # Get existing indicator
    result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    
    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found"
        )
    
    # Update fields (only non-None values)
    update_data = indicator_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(indicator, field, value)
    
    await db.commit()
    await db.refresh(indicator)

    return IndicatorRead.model_validate(indicator)


@router.delete("/indicators/{indicator_id}", response_model=MessageResponse)
@requires_role("intellicare_admin")
async def delete_indicator(
    indicator_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete an indicator.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        indicator_id: Indicator ID
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: 404 if indicator not found
    """
    # Get existing indicator
    result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found"
        )

    await db.delete(indicator)
    await db.commit()

    return MessageResponse(message=f"Indicator {indicator_id} deleted successfully")

