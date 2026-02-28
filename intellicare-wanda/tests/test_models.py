"""Testes dos modelos de dados do Wanda."""

from wanda.discovery.models import (
    AggregatedResponse,
    ModuleInfo,
    ModuleResponse,
    ModuleStatus,
    OrchestrationResult,
    RoutingDecision,
)


class TestModuleInfo:
    def test_to_dict(self):
        m = ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            version="1.0.0",
            capabilities=["chronic-disease"],
            status=ModuleStatus.ONLINE,
        )
        d = m.to_dict()
        assert d["name"] == "intellicare-oswaldo"
        assert d["status"] == "online"
        assert "chronic-disease" in d["capabilities"]

    def test_default_offline(self):
        m = ModuleInfo(name="test", base_url="http://x")
        assert m.status == ModuleStatus.OFFLINE


class TestModuleResponse:
    def test_success(self):
        r = ModuleResponse(
            module_name="oswaldo",
            endpoint="/api/v1/health",
            status_code=200,
            data={"status": "healthy"},
        )
        assert r.success is True

    def test_failure_status(self):
        r = ModuleResponse(
            module_name="oswaldo",
            endpoint="/api/v1/health",
            status_code=500,
            error="Internal Error",
        )
        assert r.success is False

    def test_failure_error(self):
        r = ModuleResponse(
            module_name="oswaldo",
            endpoint="/api/v1/health",
            status_code=0,
            error="Connection refused",
        )
        assert r.success is False

    def test_to_dict(self):
        r = ModuleResponse(
            module_name="florence",
            endpoint="/api/v1/panels",
            status_code=200,
            data={"panels": []},
            duration_ms=45.67,
        )
        d = r.to_dict()
        assert d["success"] is True
        assert d["duration_ms"] == 45.7


class TestRoutingDecision:
    def test_to_dict(self):
        rd = RoutingDecision(
            target_modules=["intellicare-oswaldo"],
            reason="Keyword match",
            confidence=0.8,
        )
        d = rd.to_dict()
        assert d["confidence"] == 0.8
        assert "intellicare-oswaldo" in d["target_modules"]


class TestOrchestrationResult:
    def test_to_dict(self):
        resp = ModuleResponse(
            module_name="oswaldo", endpoint="/test", status_code=200, data={"ok": True}
        )
        result = OrchestrationResult(
            query="Como esta o paciente?",
            modules_used=["oswaldo"],
            responses=[resp],
            aggregated_response="Tudo bem.",
            safety_warnings=["IPS nao carregado"],
        )
        d = result.to_dict()
        assert d["query"] == "Como esta o paciente?"
        assert len(d["responses"]) == 1
        assert len(d["safety_warnings"]) == 1

    def test_empty_result(self):
        result = OrchestrationResult(
            query="teste",
            modules_used=[],
            responses=[],
        )
        d = result.to_dict()
        assert d["modules_used"] == []
        assert d["routing"] is None


class TestAggregatedResponse:
    def test_to_dict(self):
        ar = AggregatedResponse(
            synthesis="Paciente com DM2 controlada.",
            key_points=["HbA1c 6.8%", "sem complicações"],
            recommended_actions=["Manter metformina"],
            aggregation_method="llm",
            confidence=0.92,
        )
        d = ar.to_dict()
        assert d["synthesis"] == "Paciente com DM2 controlada."
        assert d["aggregation_method"] == "llm"
        assert d["confidence"] == 0.92
        assert "key_points" in d
        assert "recommended_actions" in d
