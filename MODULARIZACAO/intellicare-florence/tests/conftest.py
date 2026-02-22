"""Fixtures compartilhadas para testes do Florence."""

from pathlib import Path

import pytest

from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector


REFERENCE_RANGES_DIR = Path(__file__).parent.parent / "florence" / "engine" / "reference_ranges" / "data"
CORRELATIONS_DIR = Path(__file__).parent.parent / "florence" / "engine" / "correlations" / "data"


@pytest.fixture
def ref_loader() -> ReferenceRangeLoader:
    loader = ReferenceRangeLoader(REFERENCE_RANGES_DIR)
    loader.load_all()
    return loader


@pytest.fixture
def corr_detector() -> CorrelationDetector:
    detector = CorrelationDetector(CORRELATIONS_DIR)
    detector.load_all()
    return detector


@pytest.fixture
def trend_detector() -> TrendDetector:
    return TrendDetector(min_data_points=3)


@pytest.fixture
def analyzer(
    ref_loader: ReferenceRangeLoader,
    corr_detector: CorrelationDetector,
    trend_detector: TrendDetector,
) -> ClinicalAnalyzer:
    return ClinicalAnalyzer(ref_loader, corr_detector, trend_detector)
