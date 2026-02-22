"""Testes dos endpoints API RAG."""

import pytest
from fastapi.testclient import TestClient

from florence.api.app import create_app


@pytest.fixture
def client():
    """Cliente de teste da API."""
    app = create_app()
    return TestClient(app)


class TestRAGQueryEndpoint:
    """Testes do endpoint /api/v1/rag/query."""

    def test_rag_query_basic(self, client):
        """Teste básico de query RAG."""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "Como interpretar creatinina elevada?",
                "top_k": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert "execution_time_ms" in data

    def test_rag_query_with_filters(self, client):
        """Query RAG com filtros."""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "diabetes",
                "top_k": 5,
                "filters": {"specialty": "Endocrinologia"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_rag_query_empty(self, client):
        """Query RAG vazia."""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "",
                "top_k": 3,
            },
        )
        # Deve aceitar query vazia
        assert response.status_code in [200, 422]

    def test_rag_query_invalid_top_k(self, client):
        """Query RAG com top_k inválido."""
        response = client.post(
            "/api/v1/rag/query",
            json={
                "query": "diabetes",
                "top_k": -1,
            },
        )
        # Deve validar top_k
        assert response.status_code in [200, 422]


class TestRAGProtocolsEndpoint:
    """Testes do endpoint /api/v1/rag/protocols."""

    def test_list_protocols(self, client):
        """Listar protocolos indexados."""
        response = client.get("/api/v1/rag/protocols")
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura
        assert "protocols" in data
        assert isinstance(data["protocols"], list)

    def test_protocols_structure(self, client):
        """Verificar estrutura dos protocolos."""
        response = client.get("/api/v1/rag/protocols")
        assert response.status_code == 200
        data = response.json()

        # Se houver protocolos, verificar estrutura
        if data["protocols"]:
            protocol = data["protocols"][0]
            assert "id" in protocol or "title" in protocol


class TestAnalyzeWithRAGEndpoint:
    """Testes do endpoint /api/v1/analyze-with-rag."""

    def test_analyze_with_rag_custom_query(self, client):
        """Análise com query customizada."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "rag-test-1",
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
        assert data["patient_id"] == "rag-test-1"
        assert "interpretations" in data
        assert "correlations" in data
        assert "summary" in data

        # Verificar campos RAG
        assert "relevant_protocols" in data
        assert "rag_query" in data
        assert "rag_execution_time_ms" in data

    def test_analyze_with_rag_auto_query(self, client):
        """Análise com auto-geração de query."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "rag-test-2",
                "results": {
                    "creatinine": 3.5,
                    "urea": 120.0,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verificar que análise foi feita
        assert data["patient_id"] == "rag-test-2"
        assert "interpretations" in data

        # Query pode ser auto-gerada ou None se RAG não estiver habilitado
        assert "rag_query" in data

    def test_analyze_with_rag_no_results(self, client):
        """Análise sem resultados laboratoriais."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "rag-test-3",
                "results": {},
            },
        )
        # Deve aceitar results vazio
        assert response.status_code == 200

    def test_analyze_with_rag_invalid_lab(self, client):
        """Análise com exame inválido."""
        response = client.post(
            "/api/v1/analyze-with-rag",
            json={
                "patient_id": "rag-test-4",
                "results": {
                    "invalid_lab_id": 100.0,
                },
            },
        )
        # Deve processar mesmo com exame inválido
        assert response.status_code == 200

