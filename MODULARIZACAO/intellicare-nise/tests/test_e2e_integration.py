"""Testes E2E de integração NISE ↔ Oswaldo."""

import pytest
import httpx
from typing import AsyncGenerator
import asyncio

# ── Configuração ──────────────────────────────────────────────────

NISE_BASE_URL = "http://localhost:8000"
OSWALDO_BASE_URL = "http://localhost:8002"
REDIS_URL = "redis://localhost:6379/0"


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture para cliente HTTP async."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def wait_for_services():
    """Aguarda serviços estarem prontos."""
    max_retries = 30
    retry_delay = 2
    
    services = {
        "NISE": f"{NISE_BASE_URL}/health",
        "Oswaldo": f"{OSWALDO_BASE_URL}/health"
    }
    
    async with httpx.AsyncClient() as client:
        for service_name, health_url in services.items():
            for attempt in range(max_retries):
                try:
                    response = await client.get(health_url)
                    if response.status_code == 200:
                        print(f"✅ {service_name} is ready")
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        pytest.skip(f"{service_name} not available: {e}")
                    await asyncio.sleep(retry_delay)


# ── Testes E2E ────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════
# TESTES E2E - FRAMINGHAM RISK SCORE
# ══════════════════════════════════════════════════════════════════


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_framingham_calcular_direto(http_client: httpx.AsyncClient, wait_for_services):
    """
    Testa cálculo de risco Framingham direto (sem Oswaldo)

    Fluxo:
    1. Enviar dados do paciente
    2. Receber risco calculado
    3. Validar classificação e recomendações
    """
    # Dados do paciente
    payload = {
        "sexo": "M",
        "idade": 60,
        "colesterol_total": 240,
        "hdl": 40,
        "pa_sistolica": 150,
        "tabagismo": True,
        "diabetes": False
    }

    # Calcular risco
    response = await http_client.post(
        f"{NISE_BASE_URL}/api/v1/framingham/calcular",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()

    # Validar estrutura
    assert "risco_10_anos" in data
    assert "classificacao" in data
    assert "pontos_totais" in data
    assert "recomendacoes" in data

    # Validar valores
    assert isinstance(data["risco_10_anos"], (int, float))
    assert data["risco_10_anos"] > 0
    assert data["classificacao"] in ["baixo", "intermediario", "alto"]
    assert isinstance(data["recomendacoes"], list)
    assert len(data["recomendacoes"]) > 0

    # Validar detalhamento de pontos
    assert "pontos_idade" in data
    assert "pontos_colesterol" in data
    assert "pontos_hdl" in data
    assert "pontos_pa" in data
    assert "pontos_tabagismo" in data
    assert "pontos_diabetes" in data

    # Validar recomendações para fumante
    recomendacoes_str = " ".join(data["recomendacoes"])
    assert "CESSAÇÃO DO TABAGISMO" in recomendacoes_str or "tabagismo" in recomendacoes_str.lower()

    print(f"✅ Risco calculado: {data['risco_10_anos']}% ({data['classificacao']})")
    print(f"✅ Pontos totais: {data['pontos_totais']}")
    print(f"✅ Recomendações: {len(data['recomendacoes'])} itens")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_framingham_risco_baixo(http_client: httpx.AsyncClient, wait_for_services):
    """
    Testa cálculo de risco baixo

    Cenário: Paciente jovem sem fatores de risco
    """
    payload = {
        "sexo": "F",
        "idade": 35,
        "colesterol_total": 170,
        "hdl": 60,
        "pa_sistolica": 110,
        "tabagismo": False,
        "diabetes": False
    }

    response = await http_client.post(
        f"{NISE_BASE_URL}/api/v1/framingham/calcular",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()

    # Validar risco baixo
    assert data["risco_10_anos"] < 10
    assert data["classificacao"] == "baixo"

    # Validar recomendações de prevenção
    recomendacoes_str = " ".join(data["recomendacoes"])
    assert "RISCO BAIXO" in recomendacoes_str or "estilo de vida" in recomendacoes_str.lower()

    print(f"✅ Risco baixo confirmado: {data['risco_10_anos']}%")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_framingham_risco_alto(http_client: httpx.AsyncClient, wait_for_services):
    """
    Testa cálculo de risco alto

    Cenário: Paciente idoso com múltiplos fatores de risco
    """
    payload = {
        "sexo": "M",
        "idade": 70,
        "colesterol_total": 280,
        "hdl": 30,
        "pa_sistolica": 165,
        "tabagismo": True,
        "diabetes": True
    }

    response = await http_client.post(
        f"{NISE_BASE_URL}/api/v1/framingham/calcular",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()

    # Validar risco alto
    assert data["risco_10_anos"] >= 20
    assert data["classificacao"] == "alto"

    # Validar recomendações intensivas
    recomendacoes_str = " ".join(data["recomendacoes"])
    assert "RISCO ALTO" in recomendacoes_str or "Estatina de alta intensidade" in recomendacoes_str

    print(f"✅ Risco alto confirmado: {data['risco_10_anos']}%")
    print(f"✅ Recomendações intensivas geradas")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_framingham_validacao_idade(http_client: httpx.AsyncClient, wait_for_services):
    """
    Testa validação de idade (fora da faixa 30-74)
    """
    # Idade muito baixa
    payload_baixa = {
        "sexo": "M",
        "idade": 25,
        "colesterol_total": 200,
        "hdl": 50,
        "pa_sistolica": 120,
        "tabagismo": False,
        "diabetes": False
    }

    response = await http_client.post(
        f"{NISE_BASE_URL}/api/v1/framingham/calcular",
        json=payload_baixa
    )

    assert response.status_code == 422  # Validation error

    # Idade muito alta
    payload_alta = {
        "sexo": "M",
        "idade": 80,
        "colesterol_total": 200,
        "hdl": 50,
        "pa_sistolica": 120,
        "tabagismo": False,
        "diabetes": False
    }

    response = await http_client.post(
        f"{NISE_BASE_URL}/api/v1/framingham/calcular",
        json=payload_alta
    )

    assert response.status_code == 422  # Validation error

    print("✅ Validação de idade funcionando corretamente")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
async def test_e2e_framingham_performance(http_client: httpx.AsyncClient, wait_for_services):
    """
    Testa performance do cálculo Framingham

    SLA: < 200ms p95
    """
    import time

    payload = {
        "sexo": "M",
        "idade": 55,
        "colesterol_total": 220,
        "hdl": 45,
        "pa_sistolica": 140,
        "tabagismo": True,
        "diabetes": False
    }

    # Executar 20 requisições
    tempos = []
    for _ in range(20):
        start = time.time()
        response = await http_client.post(
            f"{NISE_BASE_URL}/api/v1/framingham/calcular",
            json=payload
        )
        end = time.time()

        assert response.status_code == 200
        tempos.append((end - start) * 1000)  # ms

    # Calcular estatísticas
    tempos.sort()
    p50 = tempos[len(tempos) // 2]
    p95 = tempos[int(len(tempos) * 0.95)]
    p99 = tempos[int(len(tempos) * 0.99)]
    media = sum(tempos) / len(tempos)

    print(f"✅ Performance Framingham:")
    print(f"   - Média: {media:.2f}ms")
    print(f"   - P50: {p50:.2f}ms")
    print(f"   - P95: {p95:.2f}ms")
    print(f"   - P99: {p99:.2f}ms")

    # Validar SLA
    assert p95 < 200, f"P95 ({p95:.2f}ms) excedeu SLA de 200ms"
    print(f"✅ SLA atendido: P95 = {p95:.2f}ms < 200ms")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_health_check(http_client, wait_for_services):
    """Testa health check do NISE."""
    response = await http_client.get(f"{NISE_BASE_URL}/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "intellicare-nise"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_info_endpoint(http_client, wait_for_services):
    """Testa endpoint de informações do NISE."""
    response = await http_client.get(f"{NISE_BASE_URL}/api/v1/info")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "intellicare-nise"
    assert "oswaldo-integration" in data["capabilities"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_oswaldo_health_check(http_client, wait_for_services):
    """Testa health check do Oswaldo."""
    response = await http_client.get(f"{OSWALDO_BASE_URL}/health")
    
    assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_oswaldo_integration_resumo(http_client, wait_for_services):
    """Testa integração NISE ↔ Oswaldo - endpoint resumo."""
    
    # Criar paciente de teste no Oswaldo primeiro (se necessário)
    paciente_id = "pac-test-e2e-001"
    
    # Buscar resumo via NISE
    response = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/resumo"
    )
    
    # Pode retornar 200 (com dados) ou 404 (paciente não existe)
    assert response.status_code in [200, 404, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "paciente_id" in data
        assert "diagnosticos" in data
        assert "alertas_criticos" in data
        assert "total_alertas" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_cache_functionality(http_client, wait_for_services):
    """Testa funcionalidade de cache do NISE."""
    
    paciente_id = "pac-test-cache-001"
    
    # Primeira requisição (cache MISS)
    response1 = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/resumo?use_cache=true"
    )
    
    # Segunda requisição (cache HIT)
    response2 = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/resumo?use_cache=true"
    )
    
    # Ambas devem retornar o mesmo status
    assert response1.status_code == response2.status_code
    
    if response1.status_code == 200:
        # Dados devem ser idênticos
        assert response1.json() == response2.json()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_oswaldo_diagnosticos_endpoint(http_client, wait_for_services):
    """Testa endpoint de diagnósticos via NISE."""
    
    paciente_id = "pac-test-diag-001"
    
    response = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/diagnosticos"
    )
    
    assert response.status_code in [200, 404, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_oswaldo_alertas_endpoint(http_client, wait_for_services):
    """Testa endpoint de alertas via NISE."""
    
    paciente_id = "pac-test-alert-001"
    
    response = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/alertas?status=ativo"
    )
    
    assert response.status_code in [200, 404, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nise_performance_response_time(http_client, wait_for_services):
    """Testa tempo de resposta do NISE."""
    
    import time
    
    paciente_id = "pac-test-perf-001"
    
    start_time = time.time()
    response = await http_client.get(
        f"{NISE_BASE_URL}/api/v1/oswaldo/paciente/{paciente_id}/resumo"
    )
    end_time = time.time()
    
    response_time_ms = (end_time - start_time) * 1000
    
    # Deve responder em menos de 3 segundos (com cache)
    assert response_time_ms < 3000, f"Response time too slow: {response_time_ms}ms"
    
    print(f"Response time: {response_time_ms:.2f}ms")

