"""
Pillar CRUD endpoints.

Provides REST API endpoints for managing the 7 Donabedian quality pillars.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.api.dependencies import get_db
from donabedian.models.pillar import Pillar
from donabedian.schemas.pillar import (
    PillarCreate,
    PillarUpdate,
    PillarRead,
    PillarList,
)
from donabedian.schemas.common import MessageResponse

# Keycloak authentication
from intellicare_auth import get_current_user, requires_role

router = APIRouter()


@router.get("/pillars", response_model=List[PillarList])
async def list_pillars(
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[PillarList]:
    """
    List all 7 Donabedian quality pillars.

    Returns pillars ordered by display_order.

    **Authentication**: Required (any authenticated user)

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List[PillarList]: List of all pillars
    """
    result = await db.execute(
        select(Pillar).order_by(Pillar.display_order)
    )
    pillars = result.scalars().all()
    return [PillarList.model_validate(p) for p in pillars]


@router.get("/pillars/{pillar_id}", response_model=PillarRead)
async def get_pillar(
    pillar_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarRead:
    """
    Get a specific pillar by ID.

    **Authentication**: Required (any authenticated user)

    Args:
        pillar_id: Pillar ID
        user: Current authenticated user
        db: Database session

    Returns:
        PillarRead: Pillar details

    Raises:
        HTTPException: 404 if pillar not found
    """
    result = await db.execute(
        select(Pillar).where(Pillar.id == pillar_id)
    )
    pillar = result.scalar_one_or_none()

    if not pillar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar with id {pillar_id} not found"
        )

    return PillarRead.model_validate(pillar)


@router.post("/pillars", response_model=PillarRead, status_code=status.HTTP_201_CREATED)
@requires_role("intellicare_admin")
async def create_pillar(
    pillar_data: PillarCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarRead:
    """
    Create a new pillar.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        pillar_data: Pillar creation data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        PillarRead: Created pillar
    """
    # Create new pillar
    pillar = Pillar(**pillar_data.model_dump())

    db.add(pillar)
    await db.commit()
    await db.refresh(pillar)

    return PillarRead.model_validate(pillar)


@router.put("/pillars/{pillar_id}", response_model=PillarRead)
@requires_role("intellicare_admin")
async def update_pillar(
    pillar_id: int,
    pillar_data: PillarUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarRead:
    """
    Update an existing pillar.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        pillar_id: Pillar ID
        pillar_data: Pillar update data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        PillarRead: Updated pillar

    Raises:
        HTTPException: 404 if pillar not found
    """
    # Get existing pillar
    result = await db.execute(
        select(Pillar).where(Pillar.id == pillar_id)
    )
    pillar = result.scalar_one_or_none()

    if not pillar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar with id {pillar_id} not found"
        )

    # Update fields (only non-None values)
    update_data = pillar_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pillar, field, value)

    await db.commit()
    await db.refresh(pillar)

    return PillarRead.model_validate(pillar)


@router.delete("/pillars/{pillar_id}", response_model=MessageResponse)
@requires_role("intellicare_admin")
async def delete_pillar(
    pillar_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete a pillar.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        pillar_id: Pillar ID
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: 404 if pillar not found
    """
    # Get existing pillar
    result = await db.execute(
        select(Pillar).where(Pillar.id == pillar_id)
    )
    pillar = result.scalar_one_or_none()

    if not pillar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar with id {pillar_id} not found"
        )

    await db.delete(pillar)
    await db.commit()

    return MessageResponse(message=f"Pillar {pillar_id} deleted successfully")

