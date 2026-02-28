# EF-W008 — Circuit Breaker e Resiliencia

> Tolerancia a falhas de agentes com circuit breaker, retry inteligente e fallback gracioso.

## 1. Objetivo

Implementar padroes de resiliencia na Wanda para:
- Circuit Breaker: parar de chamar agente que esta falhando
- Retry: tentar novamente com backoff exponencial
- Timeout: nao esperar indefinidamente por agente lento
- Fallback: retornar resposta parcial quando agente indisponivel
- Bulkhead: isolar falha de um agente para nao afetar outros

## 2. Justificativa

- **Disponibilidade**: Wanda deve funcionar mesmo com 1-2 agentes fora
- **Cascata**: Agente lento nao pode travar todas as requisicoes
- **Auto-recovery**: Agente que volta deve ser detectado automaticamente
- **Experiencia**: Resposta parcial e melhor que erro total
- **SLA**: Wanda deve responder em < 5s independente do estado dos agentes

## 3. Escopo

### 3.1 Circuit Breaker por Agente

```python
class CircuitBreaker:
    """
    Implementa padrao Circuit Breaker para comunicacao com agentes.

    Estados:
    - CLOSED: Normal — chamadas passam normalmente
    - OPEN: Agente com falhas — chamadas bloqueadas
    - HALF_OPEN: Testando recuperacao — 1 chamada permitida
    """

    def __init__(
        self,
        agent_name: str,
        redis_client,
        failure_threshold: int = 5,        # Falhas para abrir
        success_threshold: int = 2,         # Sucessos para fechar (de HALF_OPEN)
        timeout: int = 60,                  # Segundos em OPEN antes de HALF_OPEN
        window_size: int = 60,             # Janela de contagem em segundos
    ):
        ...

    async def call(
        self,
        coro: Coroutine,
    ) -> Any:
        """
        Executa chamada com circuit breaker.

        CLOSED: executa normalmente
        OPEN: raise CircuitOpenError imediatamente
        HALF_OPEN: executa 1 chamada de teste
        """

    async def get_state(self) -> CircuitState:
        """Retorna estado atual do circuit breaker."""

    # Estados persistidos no Redis para resiliencia da propria Wanda
    # wanda:circuit:{agent_name}:state     → CLOSED/OPEN/HALF_OPEN
    # wanda:circuit:{agent_name}:failures  → contador (TTL window_size)
    # wanda:circuit:{agent_name}:successes → contador (TTL)
```

### 3.2 Retry com Backoff Exponencial

```python
class RetryPolicy:
    """Politica de retry configuravel por agente/endpoint."""

    POLICIES = {
        "default": RetryConfig(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
            backoff_factor=2.0,
            retry_on=[ConnectionError, TimeoutError, HTTP503],
            no_retry_on=[HTTP400, HTTP401, HTTP403, HTTP404],
        ),
        "critical": RetryConfig(
            max_attempts=5,
            initial_delay=0.2,
            max_delay=3.0,
            backoff_factor=1.5,
        ),
        "health_check": RetryConfig(
            max_attempts=2,
            initial_delay=1.0,
            max_delay=2.0,
            backoff_factor=2.0,
        ),
    }

    async def execute_with_retry(
        self,
        coro_factory: Callable,
        policy_name: str = "default",
    ) -> Any:
        """
        Executa chamada com retry.

        Delays: 0.5s, 1.0s, 2.0s (backoff_factor=2)
        Jitter: adiciona 0-20% de variacao aleatoria
        """
```

### 3.3 Timeout Manager

```python
class TimeoutManager:
    """
    Gerencia timeouts por agente e tipo de operacao.
    """

    TIMEOUTS = {
        # (agent, operation): timeout_seconds
        ("*", "health"): 2.0,
        ("*", "info"): 3.0,
        ("*", "analyze"): 30.0,
        ("florence", "analyze"): 45.0,    # Florence pode ser mais lento (RAG)
        ("wanda", "workflow"): 60.0,      # Workflows complexos
    }

    def get_timeout(
        self,
        agent: str,
        operation: str,
    ) -> float:
        """Retorna timeout configurado ou default."""
```

### 3.4 Fallback Manager

```python
class FallbackManager:
    """
    Gerencia respostas de fallback quando agente indisponivel.
    """

    async def get_fallback(
        self,
        agent: str,
        query: str,
        patient_id: Optional[str],
    ) -> FallbackResponse:
        """
        Retorna resposta de fallback.

        Estrategias por agente:
        - Florence: "Analise clinica indisponivel. Dados do IPS em cache."
        - Oswaldo: "Dados de DRC indisponivel. Verificar ultima analise."
        - Geralda: "Gestao de cuidado indisponivel. Verificar manual."
        - Zilda: "Dados territoriais indisponiveis."
        - Comunicacao: "Envio de mensagens temporariamente indisponivel."

        Se patient_id: incluir dados do cache (IPS)
        """

    async def get_partial_response(
        self,
        successful_responses: list[AgentResponse],
        failed_agents: list[str],
    ) -> AggregatedResponse:
        """
        Agrega respostas parciais (agentes que responderam).

        Marca claramente que alguns agentes falharam.
        """
```

### 3.5 Dashboard de Saude dos Agentes

```python
class HealthDashboard:
    """Visao em tempo real do estado de todos os agentes."""

    async def get_ecosystem_health(self) -> EcosystemHealth:
        """
        Estado de saude de todos os agentes.

        Returns:
            EcosystemHealth:
              - overall: healthy | degraded | critical
              - agents: {
                  "florence": {
                      "status": "healthy",
                      "circuit": "CLOSED",
                      "response_time_p95": 320,
                      "uptime_24h": 0.998,
                      "last_check": "2026-02-16T10:00:00Z"
                  },
                  ...
              }
              - last_updated: datetime
        """

    async def get_agent_metrics(
        self,
        agent: str,
        period: str = "1h",
    ) -> AgentMetrics:
        """
        Metricas detalhadas por agente.

        - Success rate
        - Error rate
        - Latencia (p50, p95, p99)
        - Circuit breaker state history
        - Retry counts
        """
```

### 3.6 Configuracao

```env
# Circuit Breaker
INTELLICARE_WANDA_CB_FAILURE_THRESHOLD=5
INTELLICARE_WANDA_CB_SUCCESS_THRESHOLD=2
INTELLICARE_WANDA_CB_TIMEOUT=60
INTELLICARE_WANDA_CB_WINDOW=60

# Retry
INTELLICARE_WANDA_RETRY_MAX_ATTEMPTS=3
INTELLICARE_WANDA_RETRY_INITIAL_DELAY=0.5
INTELLICARE_WANDA_RETRY_MAX_DELAY=5.0

# Timeout (segundos)
INTELLICARE_WANDA_TIMEOUT_HEALTH=2
INTELLICARE_WANDA_TIMEOUT_ANALYZE=30
INTELLICARE_WANDA_TIMEOUT_WORKFLOW=60
```

### 3.7 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/health/ecosystem` | Estado de todos os agentes |
| GET | `/api/v1/health/agents/{agent}` | Estado de um agente |
| POST | `/api/v1/circuit/{agent}/reset` | Resetar circuit breaker (admin) |

## 4. Testes

- CircuitBreaker: CLOSED→OPEN→HALF_OPEN→CLOSED (8 testes)
- RetryPolicy: sucesso, falha total, partial retry (6 testes)
- TimeoutManager: get_timeout, timeout expirado (4 testes)
- FallbackManager: cada agente, parcial (5 testes)
- HealthDashboard: healthy, degraded, critical (3 testes)
- Endpoints (3 testes)
- **Total**: 29+ testes

## 5. Criterios de Aceitacao

- [ ] Circuit Breaker 3 estados (CLOSED, OPEN, HALF_OPEN)
- [ ] Estado do circuit breaker persistido no Redis
- [ ] Retry com backoff exponencial e jitter
- [ ] Timeout configuravel por agente e operacao
- [ ] Fallback por agente com mensagem clara
- [ ] Resposta parcial quando agentes falham
- [ ] Dashboard de saude do ecossistema
- [ ] Auto-recovery (OPEN → HALF_OPEN apos timeout)
- [ ] Reset manual de circuit breaker (admin)
- [ ] 29+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~7
- **Arquivos modificados**: ~4 (orchestrator, agent_client, api, config)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~29
