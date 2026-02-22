"""
Quality assessment endpoints.

Provides REST API endpoints for calculating quality scores based on Donabedian framework.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from donabedian.api.dependencies import get_db
from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator, TriadDimension
from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.measurement import Measurement, MeasurementStatus
from donabedian.schemas.assessment import (
    QualityAssessmentRequest,
    QualityAssessmentResponse,
    PillarAssessmentResponse,
    TriadAssessmentResponse,
    PillarScore,
    TriadScore,
    IndicatorScore,
)
from donabedian.schemas.indicator import TriadDimensionSchema

# Keycloak authentication
from intellicare_auth import get_current_user

router = APIRouter()


# Score mapping: GREEN=100, YELLOW=50, RED=0
STATUS_SCORES = {
    MeasurementStatus.GREEN: 100.0,
    MeasurementStatus.YELLOW: 50.0,
    MeasurementStatus.RED: 0.0,
}


def calculate_indicator_score(measurements: List[Measurement], indicator_name: str, weight: float = 1.0) -> IndicatorScore:
    """
    Calculate score for a single indicator based on its measurements.
    
    Args:
        measurements: List of measurements for this indicator
        indicator_name: Name of the indicator
        weight: Weight of this indicator in the calculation
        
    Returns:
        IndicatorScore: Score details for the indicator
    """
    if not measurements:
        return IndicatorScore(
            indicator_id=0,
            indicator_name=indicator_name,
            score=0.0,
            weight=weight,
            measurement_count=0,
            green_count=0,
            yellow_count=0,
            red_count=0,
        )
    
    # Count by status
    green_count = sum(1 for m in measurements if m.status == MeasurementStatus.GREEN)
    yellow_count = sum(1 for m in measurements if m.status == MeasurementStatus.YELLOW)
    red_count = sum(1 for m in measurements if m.status == MeasurementStatus.RED)
    
    # Calculate average score
    total_score = sum(STATUS_SCORES[m.status] for m in measurements)
    avg_score = total_score / len(measurements)
    
    return IndicatorScore(
        indicator_id=measurements[0].indicator_id,
        indicator_name=indicator_name,
        score=avg_score,
        weight=weight,
        measurement_count=len(measurements),
        green_count=green_count,
        yellow_count=yellow_count,
        red_count=red_count,
    )


@router.post("/assess", response_model=QualityAssessmentResponse)
async def calculate_quality_assessment(
    request: QualityAssessmentRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> QualityAssessmentResponse:
    """
    Calculate overall quality assessment for a period.

    Calculates weighted scores for:
    - Each pillar (based on indicator weights)
    - Each triad dimension (structure, process, outcome)
    - Overall quality score

    **Authentication**: Required (any authenticated user)

    Args:
        request: Assessment request with period and optional filters
        user: Current authenticated user
        db: Database session
        
    Returns:
        QualityAssessmentResponse: Complete quality assessment
    """
    # Build query for measurements in period
    query = select(Measurement).where(
        and_(
            Measurement.period_start >= request.period_start,
            Measurement.period_end <= request.period_end,
        )
    )
    
    # Apply indicator filter if provided
    if request.indicator_ids:
        query = query.where(Measurement.indicator_id.in_(request.indicator_ids))
    
    # Get all measurements
    result = await db.execute(query)
    measurements = result.scalars().all()
    
    if not measurements:
        # Return empty assessment
        return QualityAssessmentResponse(
            period_start=request.period_start,
            period_end=request.period_end,
            overall_score=0.0,
            pillar_scores=[],
            triad_scores=[],
            total_indicators=0,
            total_measurements=0,
        )
    
    # Group measurements by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)
    
    # Get all indicators with their pillars and weights
    indicator_ids = list(measurements_by_indicator.keys())
    indicators_result = await db.execute(
        select(Indicator).where(Indicator.id.in_(indicator_ids))
    )
    indicators = {ind.id: ind for ind in indicators_result.scalars().all()}

    # Get indicator-pillar associations
    associations_result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.indicator_id.in_(indicator_ids))
    )
    associations = associations_result.scalars().all()

    # Apply pillar filter if provided
    if request.pillar_ids:
        associations = [a for a in associations if a.pillar_id in request.pillar_ids]

    # Get all pillars
    pillar_ids = list(set(a.pillar_id for a in associations))
    pillars_result = await db.execute(
        select(Pillar).where(Pillar.id.in_(pillar_ids))
    )
    pillars = {p.id: p for p in pillars_result.scalars().all()}

    # Calculate scores by pillar
    pillar_scores_dict: Dict[int, List[IndicatorScore]] = defaultdict(list)
    weights_by_pillar_indicator: Dict[tuple, float] = {}

    for assoc in associations:
        weights_by_pillar_indicator[(assoc.pillar_id, assoc.indicator_id)] = assoc.weight

        if assoc.indicator_id in measurements_by_indicator:
            indicator = indicators[assoc.indicator_id]
            indicator_measurements = measurements_by_indicator[assoc.indicator_id]

            indicator_score = calculate_indicator_score(
                indicator_measurements,
                indicator.name,
                assoc.weight
            )

            pillar_scores_dict[assoc.pillar_id].append(indicator_score)

    # Calculate weighted average for each pillar
    pillar_scores: List[PillarScore] = []
    for pillar_id, indicator_scores in pillar_scores_dict.items():
        if not indicator_scores:
            continue

        # Calculate weighted average
        total_weight = sum(ind_score.weight for ind_score in indicator_scores)
        if total_weight == 0:
            weighted_score = 0.0
        else:
            weighted_score = sum(
                ind_score.score * ind_score.weight for ind_score in indicator_scores
            ) / total_weight

        total_measurements = sum(ind_score.measurement_count for ind_score in indicator_scores)

        pillar_scores.append(PillarScore(
            pillar_id=pillar_id,
            pillar_name=pillars[pillar_id].name,
            score=weighted_score,
            indicator_scores=indicator_scores,
            total_measurements=total_measurements,
        ))

    # Calculate scores by triad dimension
    triad_scores_dict: Dict[TriadDimension, List[IndicatorScore]] = defaultdict(list)

    for indicator_id, indicator_measurements in measurements_by_indicator.items():
        indicator = indicators[indicator_id]

        indicator_score = calculate_indicator_score(
            indicator_measurements,
            indicator.name,
            weight=1.0  # Equal weight for triad calculation
        )

        triad_scores_dict[indicator.triad_dimension].append(indicator_score)

    # Calculate average for each triad dimension
    triad_scores: List[TriadScore] = []
    for dimension, indicator_scores in triad_scores_dict.items():
        if not indicator_scores:
            continue

        # Simple average (no weights for triad)
        avg_score = sum(ind_score.score for ind_score in indicator_scores) / len(indicator_scores)
        total_measurements = sum(ind_score.measurement_count for ind_score in indicator_scores)

        triad_scores.append(TriadScore(
            dimension=TriadDimensionSchema(dimension.value),
            score=avg_score,
            indicator_count=len(indicator_scores),
            measurement_count=total_measurements,
        ))

    # Calculate overall score (weighted average of pillar scores)
    if pillar_scores:
        overall_score = sum(p.score for p in pillar_scores) / len(pillar_scores)
    else:
        overall_score = 0.0

    return QualityAssessmentResponse(
        period_start=request.period_start,
        period_end=request.period_end,
        overall_score=overall_score,
        pillar_scores=pillar_scores,
        triad_scores=triad_scores,
        total_indicators=len(measurements_by_indicator),
        total_measurements=len(measurements),
    )


@router.get("/assess/pillar/{pillar_id}", response_model=PillarAssessmentResponse)
async def assess_pillar(
    pillar_id: int,
    period_start: str,
    period_end: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarAssessmentResponse:
    """
    Calculate quality assessment for a specific pillar.

    **Authentication**: Required (any authenticated user)

    Args:
        pillar_id: Pillar ID
        period_start: Start date (YYYY-MM-DD)
        period_end: End date (YYYY-MM-DD)
        user: Current authenticated user
        db: Database session

    Returns:
        PillarAssessmentResponse: Assessment for the pillar

    Raises:
        HTTPException: 404 if pillar not found
    """
    from datetime import date

    # Parse dates
    start_date = date.fromisoformat(period_start)
    end_date = date.fromisoformat(period_end)

    # Get pillar
    pillar_result = await db.execute(
        select(Pillar).where(Pillar.id == pillar_id)
    )
    pillar = pillar_result.scalar_one_or_none()

    if not pillar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar with id {pillar_id} not found"
        )

    # Get indicators for this pillar
    associations_result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.pillar_id == pillar_id)
    )
    associations = associations_result.scalars().all()

    if not associations:
        return PillarAssessmentResponse(
            pillar_id=pillar_id,
            pillar_name=pillar.name,
            period_start=start_date,
            period_end=end_date,
            score=0.0,
            indicator_scores=[],
            total_measurements=0,
        )

    indicator_ids = [a.indicator_id for a in associations]
    weights = {a.indicator_id: a.weight for a in associations}

    # Get measurements for these indicators in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.indicator_id.in_(indicator_ids),
                Measurement.period_start >= start_date,
                Measurement.period_end <= end_date,
            )
        )
    )
    measurements = measurements_result.scalars().all()

    # Group by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)

    # Get indicator names
    indicators_result = await db.execute(
        select(Indicator).where(Indicator.id.in_(indicator_ids))
    )
    indicators = {ind.id: ind for ind in indicators_result.scalars().all()}

    # Calculate scores
    indicator_scores: List[IndicatorScore] = []
    for indicator_id in indicator_ids:
        if indicator_id in measurements_by_indicator:
            indicator_measurements = measurements_by_indicator[indicator_id]
            indicator_name = indicators[indicator_id].name
            weight = weights[indicator_id]

            indicator_score = calculate_indicator_score(
                indicator_measurements,
                indicator_name,
                weight
            )
            indicator_scores.append(indicator_score)

    # Calculate weighted average
    if indicator_scores:
        total_weight = sum(ind_score.weight for ind_score in indicator_scores)
        if total_weight == 0:
            pillar_score = 0.0
        else:
            pillar_score = sum(
                ind_score.score * ind_score.weight for ind_score in indicator_scores
            ) / total_weight
    else:
        pillar_score = 0.0

    total_measurements = sum(ind_score.measurement_count for ind_score in indicator_scores)

    return PillarAssessmentResponse(
        pillar_id=pillar_id,
        pillar_name=pillar.name,
        period_start=start_date,
        period_end=end_date,
        score=pillar_score,
        indicator_scores=indicator_scores,
        total_measurements=total_measurements,
    )


@router.get("/assess/triad/{dimension}", response_model=TriadAssessmentResponse)
async def assess_triad_dimension(
    dimension: str,
    period_start: str,
    period_end: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TriadAssessmentResponse:
    """
    Calculate quality assessment for a specific triad dimension.

    **Authentication**: Required (any authenticated user)

    Args:
        dimension: Triad dimension (structure, process, outcome)
        period_start: Start date (YYYY-MM-DD)
        period_end: End date (YYYY-MM-DD)
        user: Current authenticated user
        db: Database session

    Returns:
        TriadAssessmentResponse: Assessment for the triad dimension

    Raises:
        HTTPException: 400 if invalid dimension
    """
    from datetime import date

    # Parse dates
    start_date = date.fromisoformat(period_start)
    end_date = date.fromisoformat(period_end)

    # Validate dimension
    try:
        triad_dimension = TriadDimension(dimension)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid triad dimension: {dimension}. Must be one of: structure, process, outcome"
        )

    # Get indicators for this dimension
    indicators_result = await db.execute(
        select(Indicator).where(Indicator.triad_dimension == triad_dimension)
    )
    indicators = indicators_result.scalars().all()

    if not indicators:
        return TriadAssessmentResponse(
            dimension=TriadDimensionSchema(dimension),
            period_start=start_date,
            period_end=end_date,
            score=0.0,
            indicator_scores=[],
            total_measurements=0,
        )

    indicator_ids = [ind.id for ind in indicators]
    indicators_dict = {ind.id: ind for ind in indicators}

    # Get measurements for these indicators in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.indicator_id.in_(indicator_ids),
                Measurement.period_start >= start_date,
                Measurement.period_end <= end_date,
            )
        )
    )
    measurements = measurements_result.scalars().all()

    # Group by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)

    # Calculate scores
    indicator_scores: List[IndicatorScore] = []
    for indicator_id, indicator_measurements in measurements_by_indicator.items():
        indicator = indicators_dict[indicator_id]

        indicator_score = calculate_indicator_score(
            indicator_measurements,
            indicator.name,
            weight=1.0  # Equal weight for triad
        )
        indicator_scores.append(indicator_score)

    # Calculate simple average
    if indicator_scores:
        triad_score = sum(ind_score.score for ind_score in indicator_scores) / len(indicator_scores)
    else:
        triad_score = 0.0

    total_measurements = sum(ind_score.measurement_count for ind_score in indicator_scores)

    return TriadAssessmentResponse(
        dimension=TriadDimensionSchema(dimension),
        period_start=start_date,
        period_end=end_date,
        score=triad_score,
        indicator_scores=indicator_scores,
        total_measurements=total_measurements,
    )

