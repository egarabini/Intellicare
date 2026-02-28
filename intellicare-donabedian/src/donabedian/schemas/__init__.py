"""
Schemas package - Pydantic schemas for request/response validation.

This package contains all Pydantic schemas used for:
- Request validation
- Response serialization
- Data validation
- API documentation (OpenAPI/Swagger)
"""

# Common schemas
from donabedian.schemas.common import (
    PaginatedResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    InfoResponse,
    MessageResponse,
)

# Pillar schemas
from donabedian.schemas.pillar import (
    PillarBase,
    PillarCreate,
    PillarUpdate,
    PillarRead,
    PillarList,
)

# Indicator schemas
from donabedian.schemas.indicator import (
    TriadDimensionSchema,
    TargetOperatorSchema,
    IndicatorBase,
    IndicatorCreate,
    IndicatorUpdate,
    IndicatorRead,
    IndicatorList,
)

# IndicatorPillar schemas
from donabedian.schemas.indicator_pillar import (
    IndicatorPillarBase,
    IndicatorPillarCreate,
    IndicatorPillarUpdate,
    IndicatorPillarRead,
    IndicatorPillarWithNames,
    IndicatorPillarList,
)

# Measurement schemas
from donabedian.schemas.measurement import (
    PeriodTypeSchema,
    MeasurementStatusSchema,
    MeasurementBase,
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementRead,
    MeasurementList,
    MeasurementWithIndicator,
)

# Assessment schemas
from donabedian.schemas.assessment import (
    IndicatorScore,
    PillarScore,
    TriadScore,
    QualityAssessmentRequest,
    QualityAssessmentResponse,
    PillarAssessmentResponse,
    TriadAssessmentResponse,
)

# Dashboard schemas
from donabedian.schemas.dashboard import (
    StatusDistribution,
    PillarSummary,
    IndicatorSummary,
    TriadSummary,
    DashboardOverview,
    PillarsDashboard,
    IndicatorsDashboard,
)

# Trends schemas
from donabedian.schemas.trends import (
    TrendDirection,
    DataPoint,
    TrendAnalysis,
    IndicatorTrend,
    PillarTrend,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "InfoResponse",
    "MessageResponse",
    # Pillar
    "PillarBase",
    "PillarCreate",
    "PillarUpdate",
    "PillarRead",
    "PillarList",
    # Indicator
    "TriadDimensionSchema",
    "TargetOperatorSchema",
    "IndicatorBase",
    "IndicatorCreate",
    "IndicatorUpdate",
    "IndicatorRead",
    "IndicatorList",
    # IndicatorPillar
    "IndicatorPillarBase",
    "IndicatorPillarCreate",
    "IndicatorPillarUpdate",
    "IndicatorPillarRead",
    "IndicatorPillarWithNames",
    "IndicatorPillarList",
    # Measurement
    "PeriodTypeSchema",
    "MeasurementStatusSchema",
    "MeasurementBase",
    "MeasurementCreate",
    "MeasurementUpdate",
    "MeasurementRead",
    "MeasurementList",
    "MeasurementWithIndicator",
    # Assessment
    "IndicatorScore",
    "PillarScore",
    "TriadScore",
    "QualityAssessmentRequest",
    "QualityAssessmentResponse",
    "PillarAssessmentResponse",
    "TriadAssessmentResponse",
    # Dashboard
    "StatusDistribution",
    "PillarSummary",
    "IndicatorSummary",
    "TriadSummary",
    "DashboardOverview",
    "PillarsDashboard",
    "IndicatorsDashboard",
    # Trends
    "TrendDirection",
    "DataPoint",
    "TrendAnalysis",
    "IndicatorTrend",
    "PillarTrend",
]
