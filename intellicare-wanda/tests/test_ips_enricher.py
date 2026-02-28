"""Tests for IPSEnricher (EF-W002)."""

import pytest
import httpx
import respx

from wanda.ips.models import IPSBundle
from wanda.ips.enricher import IPSEnricher


@pytest.fixture
def enricher():
    return IPSEnricher(
        oswaldo_url="http://localhost:8001",
        geralda_url="http://localhost:8006",
        timeout=5,
    )


@pytest.fixture
def sample_ips():
    return IPSBundle(
        patient_id="P001",
        patient_name="João Silva",
        conditions=[{"code": "E11", "display": "DM2"}],
        medications=[{"code": "A10", "display": "Metformin"}],
        source="florence",
    )


def _oswaldo_staging():
    return {
        "chronic_conditions": [{"code": "E11", "stage": "controlled"}],
        "drc_stage": "G2",
        "cv_risk_score": 12.5,
        "dm2_control": "adequate",
        "has_control": "controlled",
    }


def _geralda_journey():
    return {
        "macrostate": "E3",
        "adherence_score": 0.85,
        "active_plans": [{"id": "CP001", "type": "DM2"}],
        "risk_level": "moderate",
    }


class TestEnrichBothSources:
    @pytest.mark.asyncio
    @respx.mock
    async def test_enrich_all(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            return_value=httpx.Response(200, json=_oswaldo_staging())
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            return_value=httpx.Response(200, json=_geralda_journey())
        )

        enriched = await enricher.enrich(sample_ips)

        assert enriched.ips.patient_id == "P001"
        assert "oswaldo" in enriched.enriched_sources
        assert "geralda" in enriched.enriched_sources
        assert enriched.staging["drc_stage"] == "G2"
        assert enriched.care["macrostate"] == "E3"
        assert enriched.enriched_at is not None


class TestEnrichOswaldoOnly:
    @pytest.mark.asyncio
    @respx.mock
    async def test_oswaldo_only(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            return_value=httpx.Response(200, json=_oswaldo_staging())
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            side_effect=httpx.ConnectError("down")
        )

        enriched = await enricher.enrich(sample_ips)
        assert "oswaldo" in enriched.enriched_sources
        assert "geralda" not in enriched.enriched_sources
        assert enriched.staging["dm2_control"] == "adequate"
        assert enriched.care == {}


class TestEnrichGeraldaOnly:
    @pytest.mark.asyncio
    @respx.mock
    async def test_geralda_only(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            return_value=httpx.Response(200, json=_geralda_journey())
        )

        enriched = await enricher.enrich(sample_ips)
        assert "geralda" in enriched.enriched_sources
        assert "oswaldo" not in enriched.enriched_sources
        assert enriched.care["adherence_score"] == 0.85


class TestEnrichNoSources:
    @pytest.mark.asyncio
    @respx.mock
    async def test_both_down(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            side_effect=httpx.ConnectError("down")
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            side_effect=httpx.ConnectError("down")
        )

        enriched = await enricher.enrich(sample_ips)
        assert enriched.enriched_sources == []
        assert enriched.staging == {}
        assert enriched.care == {}
        # Original IPS unchanged
        assert enriched.ips.patient_id == "P001"


class TestModuleFiltering:
    @pytest.mark.asyncio
    @respx.mock
    async def test_filter_to_oswaldo_only(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            return_value=httpx.Response(200, json=_oswaldo_staging())
        )
        # Geralda should NOT be called
        enriched = await enricher.enrich(
            sample_ips, modules_available=["intellicare-oswaldo"]
        )
        assert "oswaldo" in enriched.enriched_sources
        assert "geralda" not in enriched.enriched_sources
        # Verify Geralda was never called
        assert respx.calls.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_filter_none_passes_all(self, enricher, sample_ips):
        """When modules_available=None, tries all sources."""
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            return_value=httpx.Response(200, json=_oswaldo_staging())
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            return_value=httpx.Response(200, json=_geralda_journey())
        )

        enriched = await enricher.enrich(sample_ips, modules_available=None)
        assert len(enriched.enriched_sources) == 2


class TestEnrichToDict:
    @pytest.mark.asyncio
    @respx.mock
    async def test_to_dict_has_enrichment(self, enricher, sample_ips):
        respx.get("http://localhost:8001/api/v1/staging/P001").mock(
            return_value=httpx.Response(200, json=_oswaldo_staging())
        )
        respx.get("http://localhost:8006/api/v1/journey/P001").mock(
            return_value=httpx.Response(200, json=_geralda_journey())
        )

        enriched = await enricher.enrich(sample_ips)
        d = enriched.to_dict()
        assert "staging" in d
        assert "care" in d
        assert "enriched_sources" in d
        assert "patient_id" in d
