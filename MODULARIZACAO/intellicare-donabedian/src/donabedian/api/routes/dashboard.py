"""
Dashboard endpoints for consolidated data views.

Provides REST API endpoints for dashboard KPIs and summary statistics.
"""

from typing import Any, Dict, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from donabedian.api.dependencies import get_db
from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator, TriadDimension
from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.measurement import Measurement, MeasurementStatus
from donabedian.schemas.dashboard import (
    DashboardOverview,
    PillarsDashboard,
    IndicatorsDashboard,
    PillarSummary,
    IndicatorSummary,
    TriadSummary,
    StatusDistribution,
)
from donabedian.schemas.indicator import TriadDimensionSchema
from donabedian.schemas.measurement import MeasurementStatusSchema

# Keycloak authentication
from intellicare_auth import get_current_user

router = APIRouter()


# Score mapping: GREEN=100, YELLOW=50, RED=0
STATUS_SCORES = {
    MeasurementStatus.GREEN: 100.0,
    MeasurementStatus.YELLOW: 50.0,
    MeasurementStatus.RED: 0.0,
}


def calculate_status_distribution(measurements: List[Measurement]) -> StatusDistribution:
    """Calculate distribution of measurements by status."""
    if not measurements:
        return StatusDistribution(
            green=0,
            yellow=0,
            red=0,
            total=0,
            green_percent=0.0,
            yellow_percent=0.0,
            red_percent=0.0,
        )
    
    green = sum(1 for m in measurements if m.status == MeasurementStatus.GREEN)
    yellow = sum(1 for m in measurements if m.status == MeasurementStatus.YELLOW)
    red = sum(1 for m in measurements if m.status == MeasurementStatus.RED)
    total = len(measurements)
    
    return StatusDistribution(
        green=green,
        yellow=yellow,
        red=red,
        total=total,
        green_percent=(green / total * 100) if total > 0 else 0.0,
        yellow_percent=(yellow / total * 100) if total > 0 else 0.0,
        red_percent=(red / total * 100) if total > 0 else 0.0,
    )


def calculate_score(measurements: List[Measurement]) -> float:
    """Calculate average score from measurements."""
    if not measurements:
        return 0.0
    
    total_score = sum(STATUS_SCORES[m.status] for m in measurements)
    return total_score / len(measurements)


@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DashboardOverview:
    """
    Get complete dashboard overview with all KPIs.

    **Authentication**: Required (any authenticated user)

    Args:
        period_days: Number of days to look back (default: 30)
        user: Current authenticated user
        db: Database session

    Returns:
        DashboardOverview: Complete dashboard with all statistics
    """
    # Calculate period
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)
    
    # Get all measurements in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.period_start >= period_start,
                Measurement.period_end <= period_end,
            )
        )
    )
    measurements = measurements_result.scalars().all()
    
    # Get all pillars
    pillars_result = await db.execute(select(Pillar).order_by(Pillar.display_order))
    pillars = {p.id: p for p in pillars_result.scalars().all()}
    
    # Get all indicators
    indicators_result = await db.execute(select(Indicator))
    indicators = {ind.id: ind for ind in indicators_result.scalars().all()}
    
    # Get all indicator-pillar associations
    associations_result = await db.execute(select(IndicatorPillar))
    associations = associations_result.scalars().all()
    
    # Group measurements by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)
    
    # Group associations by pillar
    associations_by_pillar: Dict[int, List[IndicatorPillar]] = defaultdict(list)
    for assoc in associations:
        associations_by_pillar[assoc.pillar_id].append(assoc)
    
    # Calculate overall status distribution
    overall_distribution = calculate_status_distribution(measurements)
    
    # Calculate pillar summaries
    pillar_summaries: List[PillarSummary] = []
    for pillar_id, pillar in pillars.items():
        pillar_associations = associations_by_pillar.get(pillar_id, [])
        
        # Get measurements for this pillar's indicators
        pillar_measurements = []
        for assoc in pillar_associations:
            if assoc.indicator_id in measurements_by_indicator:
                pillar_measurements.extend(measurements_by_indicator[assoc.indicator_id])
        
        pillar_score = calculate_score(pillar_measurements)
        pillar_distribution = calculate_status_distribution(pillar_measurements)
        
        pillar_summaries.append(PillarSummary(
            pillar_id=pillar_id,
            pillar_name=pillar.name,
            pillar_description=pillar.description,
            indicator_count=len(pillar_associations),
            measurement_count=len(pillar_measurements),
            current_score=pillar_score,
            status_distribution=pillar_distribution,
        ))

    # Calculate triad summaries
    measurements_by_triad: Dict[TriadDimension, List[Measurement]] = defaultdict(list)
    indicators_by_triad: Dict[TriadDimension, List[int]] = defaultdict(list)

    for indicator_id, indicator in indicators.items():
        indicators_by_triad[indicator.triad_dimension].append(indicator_id)
        if indicator_id in measurements_by_indicator:
            measurements_by_triad[indicator.triad_dimension].extend(measurements_by_indicator[indicator_id])

    triad_summaries: List[TriadSummary] = []
    for dimension in TriadDimension:
        triad_measurements = measurements_by_triad.get(dimension, [])
        triad_score = calculate_score(triad_measurements)
        triad_distribution = calculate_status_distribution(triad_measurements)

        triad_summaries.append(TriadSummary(
            dimension=TriadDimensionSchema(dimension.value),
            indicator_count=len(indicators_by_triad.get(dimension, [])),
            measurement_count=len(triad_measurements),
            current_score=triad_score,
            status_distribution=triad_distribution,
        ))

    # Calculate indicator scores for top/bottom performers
    indicator_scores: List[tuple[int, float]] = []
    for indicator_id, indicator_measurements in measurements_by_indicator.items():
        score = calculate_score(indicator_measurements)
        indicator_scores.append((indicator_id, score))

    # Sort by score
    indicator_scores.sort(key=lambda x: x[1], reverse=True)

    # Get top 5 and bottom 5
    top_5_ids = [ind_id for ind_id, _ in indicator_scores[:5]]
    bottom_5_ids = [ind_id for ind_id, _ in indicator_scores[-5:]]

    # Build indicator summaries
    def build_indicator_summary(indicator_id: int) -> IndicatorSummary:
        indicator = indicators[indicator_id]
        indicator_measurements = measurements_by_indicator[indicator_id]

        # Get pillar count
        pillar_count = sum(1 for assoc in associations if assoc.indicator_id == indicator_id)

        # Get latest measurement
        latest_measurement = max(indicator_measurements, key=lambda m: m.period_end) if indicator_measurements else None

        return IndicatorSummary(
            indicator_id=indicator_id,
            indicator_name=indicator.name,
            triad_dimension=TriadDimensionSchema(indicator.triad_dimension.value),
            pillar_count=pillar_count,
            measurement_count=len(indicator_measurements),
            current_score=calculate_score(indicator_measurements),
            latest_value=latest_measurement.value if latest_measurement else None,
            latest_status=MeasurementStatusSchema(latest_measurement.status.value) if latest_measurement else None,
            target_value=indicator.target_value,
        )

    top_performers = [build_indicator_summary(ind_id) for ind_id in top_5_ids]
    bottom_performers = [build_indicator_summary(ind_id) for ind_id in bottom_5_ids]

    # Calculate overall score
    overall_score = sum(p.current_score for p in pillar_summaries) / len(pillar_summaries) if pillar_summaries else 0.0

    return DashboardOverview(
        period_start=period_start,
        period_end=period_end,
        overall_score=overall_score,
        total_pillars=len(pillars),
        total_indicators=len(indicators),
        total_measurements=len(measurements),
        status_distribution=overall_distribution,
        pillar_summaries=pillar_summaries,
        triad_summaries=triad_summaries,
        top_performers=top_performers,
        bottom_performers=bottom_performers,
    )


@router.get("/dashboard/pillars", response_model=PillarsDashboard)
async def get_pillars_dashboard(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PillarsDashboard:
    """
    Get dashboard focused on pillars.

    **Authentication**: Required (any authenticated user)

    Args:
        period_days: Number of days to look back (default: 30)
        user: Current authenticated user
        db: Database session

    Returns:
        PillarsDashboard: Dashboard with pillar summaries
    """
    # Calculate period
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)

    # Get all measurements in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.period_start >= period_start,
                Measurement.period_end <= period_end,
            )
        )
    )
    measurements = measurements_result.scalars().all()

    # Get all pillars
    pillars_result = await db.execute(select(Pillar).order_by(Pillar.display_order))
    pillars = {p.id: p for p in pillars_result.scalars().all()}

    # Get all indicator-pillar associations
    associations_result = await db.execute(select(IndicatorPillar))
    associations = associations_result.scalars().all()

    # Group measurements by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)

    # Group associations by pillar
    associations_by_pillar: Dict[int, List[IndicatorPillar]] = defaultdict(list)
    for assoc in associations:
        associations_by_pillar[assoc.pillar_id].append(assoc)

    # Calculate pillar summaries
    pillar_summaries: List[PillarSummary] = []
    for pillar_id, pillar in pillars.items():
        pillar_associations = associations_by_pillar.get(pillar_id, [])

        # Get measurements for this pillar's indicators
        pillar_measurements = []
        for assoc in pillar_associations:
            if assoc.indicator_id in measurements_by_indicator:
                pillar_measurements.extend(measurements_by_indicator[assoc.indicator_id])

        pillar_score = calculate_score(pillar_measurements)
        pillar_distribution = calculate_status_distribution(pillar_measurements)

        pillar_summaries.append(PillarSummary(
            pillar_id=pillar_id,
            pillar_name=pillar.name,
            pillar_description=pillar.description,
            indicator_count=len(pillar_associations),
            measurement_count=len(pillar_measurements),
            current_score=pillar_score,
            status_distribution=pillar_distribution,
        ))

    # Calculate overall score
    overall_score = sum(p.current_score for p in pillar_summaries) / len(pillar_summaries) if pillar_summaries else 0.0

    return PillarsDashboard(
        period_start=period_start,
        period_end=period_end,
        pillar_summaries=pillar_summaries,
        overall_score=overall_score,
    )


@router.get("/dashboard/indicators", response_model=IndicatorsDashboard)
async def get_indicators_dashboard(
    period_days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> IndicatorsDashboard:
    """
    Get dashboard focused on indicators.

    **Authentication**: Required (any authenticated user)

    Args:
        period_days: Number of days to look back (default: 30)
        user: Current authenticated user
        db: Database session

    Returns:
        IndicatorsDashboard: Dashboard with indicator summaries
    """
    # Calculate period
    period_end = date.today()
    period_start = period_end - timedelta(days=period_days)

    # Get all measurements in period
    measurements_result = await db.execute(
        select(Measurement).where(
            and_(
                Measurement.period_start >= period_start,
                Measurement.period_end <= period_end,
            )
        )
    )
    measurements = measurements_result.scalars().all()

    # Get all indicators
    indicators_result = await db.execute(select(Indicator).order_by(Indicator.name))
    indicators = {ind.id: ind for ind in indicators_result.scalars().all()}

    # Get all indicator-pillar associations
    associations_result = await db.execute(select(IndicatorPillar))
    associations = associations_result.scalars().all()

    # Group measurements by indicator
    measurements_by_indicator: Dict[int, List[Measurement]] = defaultdict(list)
    for m in measurements:
        measurements_by_indicator[m.indicator_id].append(m)

    # Count pillars per indicator
    pillars_per_indicator: Dict[int, int] = defaultdict(int)
    for assoc in associations:
        pillars_per_indicator[assoc.indicator_id] += 1

    # Build indicator summaries
    indicator_summaries: List[IndicatorSummary] = []
    by_triad: Dict[str, List[IndicatorSummary]] = {
        "structure": [],
        "process": [],
        "outcome": [],
    }

    for indicator_id, indicator in indicators.items():
        indicator_measurements = measurements_by_indicator.get(indicator_id, [])

        # Get latest measurement
        latest_measurement = max(indicator_measurements, key=lambda m: m.period_end) if indicator_measurements else None

        summary = IndicatorSummary(
            indicator_id=indicator_id,
            indicator_name=indicator.name,
            triad_dimension=TriadDimensionSchema(indicator.triad_dimension.value),
            pillar_count=pillars_per_indicator.get(indicator_id, 0),
            measurement_count=len(indicator_measurements),
            current_score=calculate_score(indicator_measurements),
            latest_value=latest_measurement.value if latest_measurement else None,
            latest_status=MeasurementStatusSchema(latest_measurement.status.value) if latest_measurement else None,
            target_value=indicator.target_value,
        )

        indicator_summaries.append(summary)
        by_triad[indicator.triad_dimension.value].append(summary)

    return IndicatorsDashboard(
        period_start=period_start,
        period_end=period_end,
        indicator_summaries=indicator_summaries,
        by_triad=by_triad,
        total_indicators=len(indicators),
    )

