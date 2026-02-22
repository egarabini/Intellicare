"""Testes End-to-End do Florence."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from florence.api.app import create_app


@pytest.fixture
def client():
    """Cliente de teste da API."""
    app = create_app()
    return TestClient(app)


class TestE2EFlowComplete:
    """Testes de fluxo completo E2E."""

    def test_e2e_simple_interpretation(self, client):
        """E2E: Interpretação simples de exames."""
        # 1. Verificar saúde da API
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "degraded"]

        # 2. Interpretar exames
        response = client.post(
            "/api/v1/interpret",
            json={
                "patient_id": "e2e-patient-1",
                "results": {
                    "glucose_fasting": 180.0,
                    "hba1c": 8.5,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()

        # 3. Validar resposta
        assert data["patient_id"] == "e2e-patient-1"
        assert len(data["interpretations"]) == 2
        assert data["significance"] in ["routine", "attention", "urgent", "critical"]

        # 4. Verificar interpretações
        glucose_interp = next(
            (i for i in data["interpretations"] if "Glicemia" in i["lab_name"]), None
        )
        assert glucose_interp is not None
        assert glucose_interp["value"] == 180.0
        assert glucose_interp["level"] == "high"

    def test_e2e_analysis_with_correlations(self, client):
        """E2E: Análise com detecção de correlações."""
        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "e2e-patient-2",
                "results": {
                    "creatinine": 3.5,
                    "urea": 120.0,
                    "potassium": 5.8,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar correlações detectadas
        assert len(data["correlations"]) > 0
        
        # Deve detectar comprometimento renal
        correlation_names = [c["pattern_name"] for c in data["correlations"]]
        assert any("renal" in name.lower() for name in correlation_names)

    def test_e2e_analysis_with_trends(self, client):
        """E2E: Análise com tendências históricas."""
        # Criar histórico de 6 meses
        now = datetime.now(timezone.utc)
        historical = {
            "glucose_fasting": [
                {
                    "timestamp": (now - timedelta(days=180)).isoformat(),
                    "value": 110.0,
                },
                {
                    "timestamp": (now - timedelta(days=120)).isoformat(),
                    "value": 130.0,
                },
                {
                    "timestamp": (now - timedelta(days=60)).isoformat(),
                    "value": 150.0,
                },
                {
                    "timestamp": (now - timedelta(days=30)).isoformat(),
                    "value": 170.0,
                },
            ]
        }

        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "e2e-patient-3",
                "results": {"glucose_fasting": 180.0},
                "historical": historical,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar tendências
        assert len(data["trends"]) > 0
        glucose_trend = data["trends"][0]
        assert glucose_trend["lab_id"] == "glucose_fasting"
        assert glucose_trend["direction"] in ["increasing", "decreasing", "stable"]

    def test_e2e_list_available_resources(self, client):
        """E2E: Listar recursos disponíveis."""
        # 1. Listar painéis
        response = client.get("/api/v1/panels")
        assert response.status_code == 200
        panels = response.json()
        assert len(panels) > 0
        assert any(p["id"] == "metabolic_panel" for p in panels)

        # 2. Listar exames
        response = client.get("/api/v1/labs")
        assert response.status_code == 200
        labs = response.json()
        assert len(labs) > 0
        assert any(l["id"] == "glucose_fasting" for l in labs)

        # 3. Verificar info do módulo
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        info = response.json()
        assert info["name"] == "intellicare-florence"
        assert "lab-interpretation" in info["capabilities"]

    def test_e2e_error_handling(self, client):
        """E2E: Tratamento de erros."""
        # 1. Exame inválido
        response = client.post(
            "/api/v1/interpret",
            json={
                "patient_id": "e2e-patient-4",
                "results": {
                    "invalid_lab": 100.0,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Deve retornar análise vazia ou com warnings
        assert "interpretations" in data

        # 2. Request malformado
        response = client.post(
            "/api/v1/interpret",
            json={
                "patient_id": "e2e-patient-5",
                # Faltando "results"
            },
        )
        assert response.status_code == 422  # Validation error


class TestE2ERAGIntegration:
    """Testes E2E de integração RAG."""

    def test_e2e_rag_query_direct(self, client):
        """E2E: Query direta ao RAG."""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "Como interpretar creatinina elevada?",
                "top_k": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura da resposta
        assert "query" in data
        assert "results" in data
        assert "total_results" in data

    def test_e2e_rag_list_protocols(self, client):
        """E2E: Listar protocolos indexados."""
        response = client.get("/api/v1/rag/protocols")
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura
        assert "protocols" in data
        assert isinstance(data["protocols"], list)

    def test_e2e_analyze_with_rag(self, client):
        """E2E: Análise clínica com RAG."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "e2e-patient-6",
                "results": {
                    "glucose_fasting": 180.0,
                    "hba1c": 8.5,
                },
                "query": "Como manejar diabetes tipo 2?",
                "top_k": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar campos básicos
        assert data["patient_id"] == "e2e-patient-6"
        assert "interpretations" in data
        assert "correlations" in data

        # Verificar campos RAG
        assert "relevant_protocols" in data
        assert "rag_query" in data
        assert data["rag_query"] == "Como manejar diabetes tipo 2?"

    def test_e2e_analyze_with_rag_auto_query(self, client):
        """E2E: Análise com auto-geração de query."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "e2e-patient-7",
                "results": {
                    "creatinine": 3.5,
                    "urea": 120.0,
                },
                # Sem query customizada - deve auto-gerar
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar que query foi auto-gerada
        assert "rag_query" in data
        if data["rag_query"]:  # Se RAG estiver habilitado
            assert len(data["rag_query"]) > 0


class TestE2EPerformance:
    """Testes E2E de performance."""

    def test_e2e_response_time_interpretation(self, client):
        """E2E: Tempo de resposta de interpretação."""
        import time

        start = time.time()
        response = client.post(
            "/api/v1/interpret",
            json={
                "patient_id": "perf-test-1",
                "results": {"glucose_fasting": 100.0},
            },
        )
        elapsed = (time.time() - start) * 1000  # ms

        assert response.status_code == 200
        assert elapsed < 200  # < 200ms

    def test_e2e_response_time_analysis(self, client):
        """E2E: Tempo de resposta de análise completa."""
        import time

        start = time.time()
        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "perf-test-2",
                "results": {
                    "glucose_fasting": 180.0,
                    "hba1c": 8.5,
                    "creatinine": 1.5,
                    "urea": 50.0,
                },
            },
        )
        elapsed = (time.time() - start) * 1000  # ms

        assert response.status_code == 200
        assert elapsed < 300  # < 300ms

    def test_e2e_concurrent_requests(self, client):
        """E2E: Requisições concorrentes."""
        import concurrent.futures

        def make_request(i):
            return client.post(
                "/api/v1/interpret",
                json={
                    "patient_id": f"concurrent-{i}",
                    "results": {"glucose_fasting": 100.0 + i},
                },
            )

        # 10 requisições concorrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Todas devem ter sucesso
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 10

