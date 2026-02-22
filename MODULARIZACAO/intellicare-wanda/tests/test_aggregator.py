"""Testes do ResponseAggregator."""

from wanda.discovery.models import ModuleResponse, RoutingDecision
from wanda.orchestrator.aggregator import ResponseAggregator


class TestAggregate:
    def test_single_success(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-oswaldo",
                endpoint="/api/v1/analyze",
                status_code=200,
                data={"data": {"staging": "3b", "risk": "alto"}},
            ),
        ]
        result = aggregator.aggregate("Como esta?", responses)
        assert len(result.modules_used) == 1
        assert "Oswaldo" in result.aggregated_response

    def test_multiple_success(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-oswaldo",
                endpoint="/api/v1/analyze",
                status_code=200,
                data={"data": {"staging": "3b"}},
            ),
            ModuleResponse(
                module_name="intellicare-florence",
                endpoint="/api/v1/panels",
                status_code=200,
                data={"data": [{"panel": "renal", "status": "alto"}]},
            ),
        ]
        result = aggregator.aggregate("analise completa", responses)
        assert len(result.modules_used) == 2
        assert "Oswaldo" in result.aggregated_response
        assert "Florence" in result.aggregated_response

    def test_with_failure(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-oswaldo",
                endpoint="/api/v1/analyze",
                status_code=200,
                data={"data": "ok"},
            ),
            ModuleResponse(
                module_name="intellicare-florence",
                endpoint="/api/v1/analyze",
                status_code=0,
                error="Timeout",
            ),
        ]
        result = aggregator.aggregate("analise", responses)
        assert len(result.modules_used) == 1
        assert "falha" in result.aggregated_response.lower()

    def test_all_failed(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-oswaldo",
                endpoint="/api/v1/analyze",
                status_code=0,
                error="Connection refused",
            ),
        ]
        result = aggregator.aggregate("teste", responses)
        assert result.modules_used == []
        assert "falha" in result.aggregated_response.lower()

    def test_empty_responses(self, aggregator):
        result = aggregator.aggregate("teste", [])
        assert "Nenhum modulo" in result.aggregated_response

    def test_with_routing_and_warnings(self, aggregator):
        routing = RoutingDecision(
            target_modules=["intellicare-oswaldo"],
            reason="Keyword match",
            confidence=0.9,
        )
        result = aggregator.aggregate(
            "teste",
            [],
            routing=routing,
            safety_warnings=["IPS nao carregado"],
        )
        assert len(result.safety_warnings) == 1
        assert result.routing_decision is not None

    def test_list_data(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-florence",
                endpoint="/api/v1/panels",
                status_code=200,
                data={"data": [
                    {"name": "Painel Renal", "exams": 5},
                    {"name": "Painel Hepatico", "exams": 4},
                ]},
            ),
        ]
        result = aggregator.aggregate("paineis", responses)
        assert "Painel Renal" in result.aggregated_response

    def test_string_data(self, aggregator):
        responses = [
            ModuleResponse(
                module_name="intellicare-geralda",
                endpoint="/api/v1/education",
                status_code=200,
                data={"data": "Material educativo sobre DRC."},
            ),
        ]
        result = aggregator.aggregate("educacao", responses)
        assert "Material educativo" in result.aggregated_response
