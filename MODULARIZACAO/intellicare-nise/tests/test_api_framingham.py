"""
Testes de API para Framingham endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from nise.api.app import app

client = TestClient(app)


class TestFraminghamAPI:
    """Testes para API de Framingham"""
    
    def test_calcular_risco_sucesso(self):
        """Testa cálculo de risco com sucesso"""
        payload = {
            "sexo": "M",
            "idade": 55,
            "colesterol_total": 220,
            "hdl": 45,
            "pa_sistolica": 140,
            "tabagismo": True,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos obrigatórios
        assert "risco_10_anos" in data
        assert "classificacao" in data
        assert "pontos_totais" in data
        assert "recomendacoes" in data
        
        # Verificar detalhamento
        assert "pontos_idade" in data
        assert "pontos_colesterol" in data
        assert "pontos_hdl" in data
        assert "pontos_pa" in data
        assert "pontos_tabagismo" in data
        assert "pontos_diabetes" in data
        
        # Verificar valores
        assert isinstance(data["risco_10_anos"], (int, float))
        assert data["classificacao"] in ["baixo", "intermediario", "alto"]
        assert isinstance(data["pontos_totais"], int)
        assert isinstance(data["recomendacoes"], list)
        assert len(data["recomendacoes"]) > 0
    
    def test_calcular_risco_baixo(self):
        """Testa cálculo de risco baixo"""
        payload = {
            "sexo": "M",
            "idade": 35,
            "colesterol_total": 180,
            "hdl": 55,
            "pa_sistolica": 115,
            "tabagismo": False,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["risco_10_anos"] < 10
        assert data["classificacao"] == "baixo"
    
    def test_calcular_risco_alto(self):
        """Testa cálculo de risco alto"""
        payload = {
            "sexo": "M",
            "idade": 70,
            "colesterol_total": 280,
            "hdl": 30,
            "pa_sistolica": 165,
            "tabagismo": True,
            "diabetes": True
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["risco_10_anos"] >= 20
        assert data["classificacao"] == "alto"
        assert any("RISCO ALTO" in r for r in data["recomendacoes"])
    
    def test_calcular_risco_mulher(self):
        """Testa cálculo de risco para mulher"""
        payload = {
            "sexo": "F",
            "idade": 50,
            "colesterol_total": 220,
            "hdl": 50,
            "pa_sistolica": 135,
            "tabagismo": False,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "risco_10_anos" in data
        assert data["classificacao"] in ["baixo", "intermediario", "alto"]
    
    def test_validacao_idade_minima(self):
        """Testa validação de idade mínima"""
        payload = {
            "sexo": "M",
            "idade": 25,  # Abaixo do mínimo
            "colesterol_total": 200,
            "hdl": 50,
            "pa_sistolica": 120,
            "tabagismo": False,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_validacao_idade_maxima(self):
        """Testa validação de idade máxima"""
        payload = {
            "sexo": "M",
            "idade": 80,  # Acima do máximo
            "colesterol_total": 200,
            "hdl": 50,
            "pa_sistolica": 120,
            "tabagismo": False,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_validacao_sexo_invalido(self):
        """Testa validação de sexo inválido"""
        payload = {
            "sexo": "X",  # Inválido
            "idade": 50,
            "colesterol_total": 200,
            "hdl": 50,
            "pa_sistolica": 120,
            "tabagismo": False,
            "diabetes": False
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_validacao_campos_obrigatorios(self):
        """Testa validação de campos obrigatórios"""
        payload = {
            "sexo": "M",
            "idade": 50,
            # Faltando campos obrigatórios
        }
        
        response = client.post("/api/v1/framingham/calcular", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @patch("nise.api.endpoints.framingham.get_oswaldo_client")
    async def test_calcular_risco_paciente_sucesso(self, mock_get_client):
        """Testa cálculo de risco para paciente do Oswaldo"""
        # Mock do cliente Oswaldo
        mock_client = AsyncMock()
        mock_client.get_paciente_resumo.return_value = {
            "sexo": "M",
            "idade": 55,
            "ultima_pa_sistolica": 140,
            "ultimo_lipidograma": {
                "colesterol_total": 220,
                "hdl": 45
            },
            "tabagismo": True,
            "tem_diabetes": False
        }
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/framingham/paciente/PAC001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "risco_10_anos" in data
        assert "classificacao" in data
        assert "pontos_totais" in data
    
    @patch("nise.api.endpoints.framingham.get_oswaldo_client")
    async def test_calcular_risco_paciente_nao_encontrado(self, mock_get_client):
        """Testa erro quando paciente não é encontrado"""
        # Mock do cliente Oswaldo
        mock_client = AsyncMock()
        mock_client.get_paciente_resumo.return_value = None
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/framingham/paciente/PAC999")
        
        assert response.status_code == 404
    
    @patch("nise.api.endpoints.framingham.get_oswaldo_client")
    async def test_calcular_risco_paciente_dados_insuficientes(self, mock_get_client):
        """Testa erro quando dados são insuficientes"""
        # Mock do cliente Oswaldo com dados incompletos
        mock_client = AsyncMock()
        mock_client.get_paciente_resumo.return_value = {
            "sexo": "M",
            "idade": 55,
            # Faltando PA e lipidograma
        }
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/v1/framingham/paciente/PAC001")
        
        assert response.status_code == 400

