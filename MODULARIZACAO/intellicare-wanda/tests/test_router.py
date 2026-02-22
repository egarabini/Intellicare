"""Testes do QueryRouter."""

from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.orchestrator.router import QueryRouter


class TestRouteByKeyword:
    def test_route_to_oswaldo(self, router, online_modules):
        decision = router.route("Como esta a funcao renal do paciente?", online_modules)
        assert "intellicare-oswaldo" in decision.target_modules
        assert decision.confidence > 0

    def test_route_to_florence(self, router, online_modules):
        decision = router.route("Quais os resultados dos exames de laboratorio?", online_modules)
        assert "intellicare-florence" in decision.target_modules

    def test_route_to_zilda(self, router, online_modules):
        decision = router.route("Quais UBS existem na regiao?", online_modules)
        assert "intellicare-zilda" in decision.target_modules

    def test_route_to_geralda(self, router, online_modules):
        decision = router.route("Qual o plano de cuidado e os lembretes?", online_modules)
        assert "intellicare-geralda" in decision.target_modules

    def test_route_diabetes(self, router, online_modules):
        decision = router.route("Paciente com diabetes tipo 2", online_modules)
        assert "intellicare-oswaldo" in decision.target_modules

    def test_route_multiple_modules(self, router, online_modules):
        decision = router.route(
            "Analise os exames do paciente com doenca renal cronica", online_modules
        )
        # Should match both oswaldo (renal, cronica) and florence (exames)
        assert len(decision.target_modules) >= 2

    def test_max_modules_limit(self, online_modules):
        router = QueryRouter(max_modules=1)
        decision = router.route(
            "exames do paciente renal com diabetes", online_modules
        )
        assert len(decision.target_modules) == 1

    def test_no_match_fallback(self, router, online_modules):
        decision = router.route("Bom dia", online_modules)
        # Should fall back to capability-based
        assert len(decision.target_modules) > 0 or decision.confidence <= 0.3

    def test_empty_modules(self, router):
        decision = router.route("qualquer coisa", [])
        assert decision.target_modules == []
        assert decision.confidence == 0.0


class TestRouteWithAvailability:
    def test_only_available_modules(self, router):
        # Only Oswaldo is online
        modules = [
            ModuleInfo(
                name="intellicare-oswaldo",
                base_url="http://localhost:8001",
                capabilities=["chronic-disease"],
                status=ModuleStatus.ONLINE,
            ),
        ]
        decision = router.route("Resultado dos exames de laboratorio", modules)
        # Florence would be ideal but is offline — should not route to it
        assert all(m in ["intellicare-oswaldo"] for m in decision.target_modules)

    def test_single_module_fallback(self, router):
        # Capability "general" is NOT in CAPABILITY_MAPPING, so capability fallback
        # yields nothing → triggers last-resort single-module path (router.py:112)
        modules = [
            ModuleInfo(
                name="intellicare-custom",
                base_url="http://localhost:8099",
                capabilities=["general"],
                status=ModuleStatus.ONLINE,
            ),
        ]
        decision = router.route("Bom dia", modules)
        # Only one module available with unmapped capability → route to it
        assert decision.target_modules == ["intellicare-custom"]
        assert decision.reason == "Unico modulo disponivel"


class TestClinicalIntent:
    def test_clinical_query(self, router):
        assert router.detect_clinical_intent("Como esta o paciente?") is True

    def test_clinical_exame(self, router):
        assert router.detect_clinical_intent("Resultados do exame") is True

    def test_clinical_medicamento(self, router):
        assert router.detect_clinical_intent("Quais medicamentos?") is True

    def test_non_clinical(self, router):
        assert router.detect_clinical_intent("Bom dia") is False

    def test_non_clinical_greeting(self, router):
        assert router.detect_clinical_intent("Ola, tudo bem?") is False
