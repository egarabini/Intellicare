"""Testes para os contratos padrao IntelliCare."""

from datetime import datetime, timezone

from intellicare_core.contracts.module_info import ModuleInfo
from intellicare_core.contracts.health import HealthCheck, DependencyStatus
from intellicare_core.contracts.base_agent import (
    AnalysisRequest,
    AnalysisResponse,
    BaseAgent,
)


class TestModuleInfo:
    def test_minimal(self) -> None:
        info = ModuleInfo(name="test-module", version="1.0.0")
        assert info.name == "test-module"
        assert info.version == "1.0.0"
        assert info.status == "healthy"
        assert info.capabilities == []
        assert info.fhir_version == "R4"

    def test_full(self) -> None:
        info = ModuleInfo(
            name="intellicare-oswaldo",
            version="1.0.0",
            status="healthy",
            capabilities=["chronic-disease-monitoring", "staging", "alerts"],
            description="Motor de doencas cronicas",
            metadata={"diseases": ["ckd", "dm2", "has"]},
        )
        assert len(info.capabilities) == 3
        assert info.metadata["diseases"] == ["ckd", "dm2", "has"]

    def test_json_roundtrip(self) -> None:
        info = ModuleInfo(name="test", version="0.1.0", capabilities=["a", "b"])
        data = info.model_dump()
        info2 = ModuleInfo(**data)
        assert info == info2


class TestHealthCheck:
    def test_defaults(self) -> None:
        health = HealthCheck()
        assert health.status == "healthy"
        assert health.is_healthy is True
        assert health.uptime_seconds == 0.0
        assert health.dependencies == []

    def test_with_dependencies(self) -> None:
        health = HealthCheck(
            status="degraded",
            module_name="test-module",
            version="1.0.0",
            uptime_seconds=3600.0,
            dependencies=[
                DependencyStatus(name="database", status="connected", latency_ms=5.2),
                DependencyStatus(name="fhir", status="disconnected"),
            ],
        )
        assert health.is_healthy is False
        assert len(health.dependencies) == 2
        assert health.dependencies[0].latency_ms == 5.2
        assert health.dependencies[1].status == "disconnected"

    def test_timestamp_is_utc(self) -> None:
        health = HealthCheck()
        assert health.timestamp.tzinfo is not None


class TestDependencyStatus:
    def test_minimal(self) -> None:
        dep = DependencyStatus(name="db", status="connected")
        assert dep.name == "db"
        assert dep.latency_ms is None
        assert dep.details == ""

    def test_full(self) -> None:
        dep = DependencyStatus(
            name="fhir",
            status="degraded",
            latency_ms=250.5,
            details="Timeout intermitente",
        )
        assert dep.latency_ms == 250.5


class TestAnalysisRequest:
    def test_minimal(self) -> None:
        req = AnalysisRequest(patient_id="p-123")
        assert req.patient_id == "p-123"
        assert req.query == ""
        assert req.parameters == {}

    def test_full(self) -> None:
        req = AnalysisRequest(
            patient_id="p-123",
            query="estadiamento renal",
            parameters={"diseases": ["ckd"]},
        )
        assert req.query == "estadiamento renal"


class TestAnalysisResponse:
    def test_defaults(self) -> None:
        resp = AnalysisResponse()
        assert resp.success is True
        assert resp.confidence == 0.0
        assert resp.recommendations == []
        assert resp.alerts == []

    def test_confidence_bounds(self) -> None:
        resp = AnalysisResponse(confidence=0.95)
        assert resp.confidence == 0.95

    def test_full(self) -> None:
        resp = AnalysisResponse(
            success=True,
            patient_id="p-123",
            analysis={"stage": "G3a", "egfr": 52.3},
            recommendations=["Encaminhar a nefrologista"],
            alerts=[{"severity": "urgent", "message": "eGFR em queda"}],
            confidence=0.92,
            source="intellicare-oswaldo",
        )
        assert resp.source == "intellicare-oswaldo"
        assert len(resp.alerts) == 1
