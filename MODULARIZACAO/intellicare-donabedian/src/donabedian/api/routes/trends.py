"""
Trends endpoints for temporal analysis.

Provides REST API endpoints for analyzing trends over time.
"""

from typing import Any, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from donabedian.api.dependencies import get_db
from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator
from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.measurement import Measurement, MeasurementStatus
from donabedian.schemas.trends import (
    IndicatorTrend,
    PillarTrend,
    DataPoint,
    TrendAnalysis,
    TrendDirection,
)

# Keycloak authentication
from intellicare_auth import get_current_user

router = APIRouter()


# Score mapping: GREEN=100, YELLOW=50, RED=0
STATUS_SCORES = {
    MeasurementStatus.GREEN: 100.0,
    MeasurementStatus.YELLOW: 50.0,
    MeasurementStatus.RED: 0.0,
}


def analyze_trend(data_points: List[DataPoint]) -> TrendAnalysis:
    """
    Analyze trend from data points.
    
    Args:
        data_points: List of data points sorted by date
        
    Returns:
        TrendAnalysis: Trend analysis result
    """
    if not data_points:
        return TrendAnalysis(
            direction=TrendDirection.INSUFFICIENT_DATA,
            slope=None,
            change_percent=None,
            data_points=0,
            first_value=None,
            last_value=None,
            average_value=None,
            min_value=None,
            max_value=None,
        )
    
    if len(data_points) < 2:
        return TrendAnalysis(
            direction=TrendDirection.INSUFFICIENT_DATA,
            slope=None,
            change_percent=None,
            data_points=len(data_points),
            first_value=data_points[0].value,
            last_value=data_points[0].value,
            average_value=data_points[0].value,
            min_value=data_points[0].value,
            max_value=data_points[0].value,
        )
    
    # Sort by date
    sorted_points = sorted(data_points, key=lambda p: p.measurement_date)
    
    # Calculate statistics
    values = [p.value for p in sorted_points]
    first_value = values[0]
    last_value = values[-1]
    average_value = sum(values) / len(values)
    min_value = min(values)
    max_value = max(values)
    
    # Calculate change
    change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0.0
    
    # Calculate slope (simple linear regression)
    n = len(sorted_points)
    days_diff = (sorted_points[-1].date - sorted_points[0].date).days
    slope = (last_value - first_value) / days_diff if days_diff > 0 else 0.0
    
    # Determine direction
    if abs(change_percent) < 5:  # Less than 5% change is considered stable
        direction = TrendDirection.STABLE
    elif change_percent > 0:
        direction = TrendDirection.IMPROVING
    else:
        direction = TrendDirection.DECLINING
    
    return TrendAnalysis(
        direction=direction,
        slope=slope,
        change_percent=change_percent,
        data_points=n,
        first_value=first_value,
        last_value=last_value,
        average_value=average_value,
        min_value=min_value,
        max_value=max_value,
    )


@router.get("/trends/{indicator_id}", response_model=IndicatorTrend)
async def get_indicator_trend(
    indicator_id: int,
    period_days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorTrend:
    """
    Get temporal trend for a specific indicator.

    **Authentication**: Required (any authenticated user)

    Args:
        indicator_id: Indicator ID
        period_days: Number of days to look back (default: 90)
        user: Current authenticated user
        db: Database session

    Returns:
        IndicatorTrend: Trend analysis for the indicator
        
    Raises:
        HTTPException: 404 if indicator not found
    """
    # Get indicator
    indicator_result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    indicator = indicator_result.scalar_one_or_none()
    
    if not indicator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator with id {indicator_id} not found"
        )
    
    # Calculate period
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)

    # Get measurements for this indicator in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.indicator_id == indicator_id,
                Measurement.period_start >= period_start,
                Measurement.period_end <= period_end,
            )
        ).order_by(Measurement.period_end)
    )
    measurements = measurements_result.scalars().all()

    # Build time series
    time_series: List[DataPoint] = []
    for m in measurements:
        time_series.append(DataPoint(
            measurement_date=m.period_end,
            value=m.value,
            score=STATUS_SCORES[m.status],
            status_label=m.status.value,
        ))

    # Analyze trend
    trend_analysis = analyze_trend(time_series)

    # Calculate current score
    if measurements:
        current_score = sum(STATUS_SCORES[m.status] for m in measurements) / len(measurements)
    else:
        current_score = 0.0

    return IndicatorTrend(
        indicator_id=indicator_id,
        indicator_name=indicator.name,
        period_start=period_start,
        period_end=period_end,
        target_value=indicator.target_value,
        time_series=time_series,
        trend_analysis=trend_analysis,
        current_score=current_score,
    )


@router.get("/trends/pillar/{pillar_id}", response_model=PillarTrend)
async def get_pillar_trend(
    pillar_id: int,
    period_days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarTrend:
    """
    Get temporal trend for a specific pillar (aggregated from its indicators).

    **Authentication**: Required (any authenticated user)

    Args:
        pillar_id: Pillar ID
        period_days: Number of days to look back (default: 90)
        user: Current authenticated user
        db: Database session

    Returns:
        PillarTrend: Trend analysis for the pillar

    Raises:
        HTTPException: 404 if pillar not found
    """
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

    # Calculate period
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)

    # Get indicators for this pillar
    associations_result = await db.execute(
        select(IndicatorPillar).where(IndicatorPillar.pillar_id == pillar_id)
    )
    associations = associations_result.scalars().all()

    if not associations:
        return PillarTrend(
            pillar_id=pillar_id,
            pillar_name=pillar.name,
            period_start=period_start,
            period_end=period_end,
            indicator_trends=[],
            aggregated_time_series=[],
            trend_analysis=TrendAnalysis(
                direction=TrendDirection.INSUFFICIENT_DATA,
                slope=None,
                change_percent=None,
                data_points=0,
                first_value=None,
                last_value=None,
                average_value=None,
                min_value=None,
                max_value=None,
            ),
            current_score=0.0,
        )

    indicator_ids = [a.indicator_id for a in associations]
    weights = {a.indicator_id: a.weight for a in associations}

    # Get indicators
    indicators_result = await db.execute(
        select(Indicator).where(Indicator.id.in_(indicator_ids))
    )
    indicators = {ind.id: ind for ind in indicators_result.scalars().all()}

    # Get all measurements for these indicators in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.indicator_id.in_(indicator_ids),
                Measurement.period_start >= period_start,
                Measurement.period_end <= period_end,
            )
        ).order_by(Measurement.period_end)
    )
    measurements = measurements_result.scalars().all()

    # Group by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)

    # Build indicator trends
    indicator_trends: List[IndicatorTrend] = []
    for indicator_id in indicator_ids:
        if indicator_id not in measurements_by_indicator:
            continue

        indicator = indicators[indicator_id]
        indicator_measurements = measurements_by_indicator[indicator_id]

        # Build time series
        time_series: List[DataPoint] = []
        for m in indicator_measurements:
            time_series.append(DataPoint(
                measurement_date=m.period_end,
                value=m.value,
                score=STATUS_SCORES[m.status],
                status_label=m.status.value,
            ))

        # Analyze trend
        trend_analysis = analyze_trend(time_series)

        # Calculate current score
        current_score = sum(STATUS_SCORES[m.status] for m in indicator_measurements) / len(indicator_measurements)

        indicator_trends.append(IndicatorTrend(
            indicator_id=indicator_id,
            indicator_name=indicator.name,
            period_start=period_start,
            period_end=period_end,
            target_value=indicator.target_value,
            time_series=time_series,
            trend_analysis=trend_analysis,
            current_score=current_score,
        ))

    # Aggregate time series (weighted average by date)
    dates_scores: Dict[date, List[tuple[float, float]]] = defaultdict(list)  # date -> [(score, weight), ...]

    for indicator_id, indicator_measurements in measurements_by_indicator.items():
        weight = weights[indicator_id]
        for m in indicator_measurements:
            score = STATUS_SCORES[m.status]
            dates_scores[m.period_end].append((score, weight))

    # Calculate weighted average for each date
    aggregated_time_series: List[DataPoint] = []
    for measurement_date in sorted(dates_scores.keys()):
        scores_weights = dates_scores[measurement_date]
        total_weight = sum(w for _, w in scores_weights)
        if total_weight > 0:
            weighted_score = sum(s * w for s, w in scores_weights) / total_weight
        else:
            weighted_score = 0.0

        # Determine status from score
        if weighted_score >= 75:
            status = "green"
        elif weighted_score >= 25:
            status = "yellow"
        else:
            status = "red"

        aggregated_time_series.append(DataPoint(
            measurement_date=measurement_date,
            value=weighted_score,  # Using score as value for aggregated view
            score=weighted_score,
            status_label=status,
        ))

    # Analyze aggregated trend
    aggregated_trend = analyze_trend(aggregated_time_series)

    # Calculate current pillar score
    if aggregated_time_series:
        current_score = aggregated_time_series[-1].score
    else:
        current_score = 0.0

    return PillarTrend(
        pillar_id=pillar_id,
        pillar_name=pillar.name,
        period_start=period_start,
        period_end=period_end,
        indicator_trends=indicator_trends,
        aggregated_time_series=aggregated_time_series,
        trend_analysis=aggregated_trend,
        current_score=current_score,
    )

