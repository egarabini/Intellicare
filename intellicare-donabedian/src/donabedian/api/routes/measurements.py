"""
Measurement CRUD endpoints.

Provides REST API endpoints for managing quality measurements with auto-calculated status.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.api.dependencies import get_db
from donabedian.models.measurement import Measurement, MeasurementStatus
from donabedian.models.indicator import Indicator, TargetOperator
from donabedian.schemas.measurement import (
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementRead,
    MeasurementList,
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


def calculate_status(value: float, target_value: float, target_operator: TargetOperator) -> MeasurementStatus:
    """
    Calculate measurement status based on target.
    
    Args:
        value: Measured value
        target_value: Target value
        target_operator: Comparison operator (>=, <=, ==)
        
    Returns:
        MeasurementStatus: GREEN (met), YELLOW (close), or RED (not met)
    """
    if target_operator == TargetOperator.GREATER_EQUAL:
        if value >= target_value:
            return MeasurementStatus.GREEN
        elif value >= target_value * 0.9:  # Within 90% of target
            return MeasurementStatus.YELLOW
        else:
            return MeasurementStatus.RED
    
    elif target_operator == TargetOperator.LESS_EQUAL:
        if value <= target_value:
            return MeasurementStatus.GREEN
        elif value <= target_value * 1.1:  # Within 110% of target
            return MeasurementStatus.YELLOW
        else:
            return MeasurementStatus.RED
    
    else:  # EQUAL
        tolerance = target_value * 0.05  # 5% tolerance
        if abs(value - target_value) <= tolerance:
            return MeasurementStatus.GREEN
        elif abs(value - target_value) <= tolerance * 2:
            return MeasurementStatus.YELLOW
        else:
            return MeasurementStatus.RED


@router.get("/measurements", response_model=PaginatedResponse[MeasurementList])
async def list_measurements(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    indicator_id: int | None = Query(None, description="Filter by indicator ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[MeasurementList]:
    """
    List measurements with pagination and optional filtering.

    **Authentication**: Required (any authenticated user)

    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page (max 100)
        indicator_id: Optional filter by indicator ID
        user: Current authenticated user
        db: Database session

    Returns:
        PaginatedResponse[MeasurementList]: Paginated list of measurements
    """
    # Build query
    query = select(Measurement)
    if indicator_id:
        query = query.where(Measurement.indicator_id == indicator_id)
    
    # Get total count
    count_query = select(func.count()).select_from(Measurement)
    if indicator_id:
        count_query = count_query.where(Measurement.indicator_id == indicator_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    
    # Get paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        query
        .order_by(Measurement.period_start.desc())
        .limit(page_size)
        .offset(offset)
    )
    measurements = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=[MeasurementList.model_validate(m) for m in measurements],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/measurements/{measurement_id}", response_model=MeasurementRead)
async def get_measurement(
    measurement_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MeasurementRead:
    """
    Get a specific measurement by ID.

    **Authentication**: Required (any authenticated user)

    Args:
        measurement_id: Measurement ID
        user: Current authenticated user
        db: Database session

    Returns:
        MeasurementRead: Measurement details

    Raises:
        HTTPException: 404 if measurement not found
    """
    result = await db.execute(
        select(Measurement).where(Measurement.id == measurement_id)
    )
    measurement = result.scalar_one_or_none()
    
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement with id {measurement_id} not found"
        )
    
    return MeasurementRead.model_validate(measurement)


@router.post("/measurements", response_model=MeasurementRead, status_code=status.HTTP_201_CREATED)
@requires_role("intellicare_admin")
async def create_measurement(
    measurement_data: MeasurementCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MeasurementRead:
    """
    Create a new measurement with auto-calculated status.

    The status (GREEN/YELLOW/RED) is automatically calculated based on the
    indicator's target_value and target_operator.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        measurement_data: Measurement creation data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MeasurementRead: Created measurement with calculated status

    Raises:
        HTTPException: 404 if indicator not found
    """
    # Get indicator to calculate status
    result = await db.execute(
        select(Indicator).where(Indicator.id == measurement_data.indicator_id)
    )
    indicator = result.scalar_one_or_none()
    
    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {measurement_data.indicator_id} not found"
        )
    
    # Calculate status
    calculated_status = calculate_status(
        measurement_data.value,
        indicator.target_value,
        indicator.target_operator
    )
    
    # Create measurement with calculated status
    measurement = Measurement(
        **measurement_data.model_dump(),
        status=calculated_status
    )
    
    db.add(measurement)
    await db.commit()
    await db.refresh(measurement)

    return MeasurementRead.model_validate(measurement)


@router.put("/measurements/{measurement_id}", response_model=MeasurementRead)
@requires_role("intellicare_admin")
async def update_measurement(
    measurement_id: int,
    measurement_data: MeasurementUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MeasurementRead:
    """
    Update an existing measurement.

    If the value is updated, the status is automatically recalculated.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        measurement_id: Measurement ID
        measurement_data: Measurement update data
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MeasurementRead: Updated measurement

    Raises:
        HTTPException: 404 if measurement not found
    """
    # Get existing measurement
    result = await db.execute(
        select(Measurement).where(Measurement.id == measurement_id)
    )
    measurement = result.scalar_one_or_none()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement with id {measurement_id} not found"
        )

    # Update fields (only non-None values)
    update_data = measurement_data.model_dump(exclude_unset=True)

    # If value is being updated, recalculate status
    if "value" in update_data:
        # Get indicator
        indicator_result = await db.execute(
            select(Indicator).where(Indicator.id == measurement.indicator_id)
        )
        indicator = indicator_result.scalar_one()

        # Recalculate status
        new_status = calculate_status(
            update_data["value"],
            indicator.target_value,
            indicator.target_operator
        )
        update_data["status"] = new_status

    # Apply updates
    for field, value in update_data.items():
        setattr(measurement, field, value)

    await db.commit()
    await db.refresh(measurement)

    return MeasurementRead.model_validate(measurement)


@router.delete("/measurements/{measurement_id}", response_model=MessageResponse)
@requires_role("intellicare_admin")
async def delete_measurement(
    measurement_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Delete a measurement.

    **Authentication**: Required
    **Authorization**: Role `intellicare_admin` required

    Args:
        measurement_id: Measurement ID
        user: Current authenticated user (must be admin)
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: 404 if measurement not found
    """
    # Get existing measurement
    result = await db.execute(
        select(Measurement).where(Measurement.id == measurement_id)
    )
    measurement = result.scalar_one_or_none()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement with id {measurement_id} not found"
        )

    await db.delete(measurement)
    await db.commit()

    return MessageResponse(message=f"Measurement {measurement_id} deleted successfully")

