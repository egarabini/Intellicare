# EF-W009 — Rastreabilidade de Decisoes

> Audit trail completo e imutavel de todas as decisoes de roteamento e orquestracao da Wanda.

## 1. Objetivo

Implementar rastreabilidade completa das decisoes da Wanda:
- Registrar CADA decisao de roteamento (quem foi escolhido e por que)
- Registrar CADA chamada a agente (request/response/latencia)
- Registrar CADA falha e a decisao de fallback
- Exportar traces no formato FHIR AuditEvent (clinico) e OpenTelemetry (tecnico)
- Permitir auditoria retroativa de qualquer decisao

## 2. Justificativa

- **Responsabilizacao**: Se IA tomou decisao errada, deve ser rastreavel
- **Melhoria continua**: Analisar erros de routing para melhorar o sistema
- **Regulatorio**: ANS/ANVISA exigem auditoria de decisoes de IA clinica
- **Debugging**: Encontrar rapidamente onde uma falha ocorreu
- **Confianca**: Equipe confia mais no sistema quando sabe que e auditavel

## 3. Escopo

### 3.1 Trace de Decisao

```python
@dataclass
class DecisionTrace:
    """Registro completo de uma decisao de orquestracao."""
    trace_id: UUID
    execution_id: Optional[UUID]     # Vinculado a orchestration_execution

    # Request
    original_query: str
    patient_id: Optional[str]
    ips_loaded: bool
    ips_source: str                  # cache, fresh, stale, empty

    # Routing
    routing_method: str              # llm, keyword, direct, workflow
    routing_input: dict              # Query + contexto usado
    routing_output: dict             # Decisao do router
    routing_reasoning: Optional[str]  # Raciocinio do LLM (se usado)
    routing_latency_ms: int

    # Chamadas
    agent_calls: list[AgentCallTrace]

    # Agregacao
    aggregation_method: str          # llm, simple
    aggregation_latency_ms: int

    # Resultado
    success: bool
    final_response_preview: str      # Primeiros 200 chars da resposta
    total_latency_ms: int

    # Auditoria
    requested_by: str
    created_at: datetime


@dataclass
class AgentCallTrace:
    """Registro de uma chamada a agente especifico."""
    agent_name: str
    capability: str
    endpoint: str
    request_payload_hash: str       # Hash SHA256 do payload (privacidade)
    response_summary: str           # Resumo sem dados sensíveis
    status_code: int
    latency_ms: int
    success: bool
    error: Optional[str]
    circuit_breaker_state: str
    from_cache: bool
```

### 3.2 Rastreador de Decisoes

```python
class DecisionTracer:
    """
    Rastreia todas as decisoes e operacoes da Wanda.
    """

    def __init__(
        self,
        trace_store: TraceStore,
        fhir_client: Optional[FHIRClient],
        otel_tracer: Optional[Tracer],  # OpenTelemetry
    ):
        ...

    async def start_trace(
        self,
        query: str,
        patient_id: Optional[str],
        requested_by: str,
    ) -> TraceContext:
        """Inicia rastreamento de uma decisao."""

    async def record_routing(
        self,
        ctx: TraceContext,
        decision: RoutingDecision,
        latency_ms: int,
    ) -> None:
        """Registra decisao de roteamento."""

    async def record_agent_call(
        self,
        ctx: TraceContext,
        call: AgentCallTrace,
    ) -> None:
        """Registra chamada a agente."""

    async def complete_trace(
        self,
        ctx: TraceContext,
        result: OrchestratedResponse,
    ) -> DecisionTrace:
        """Finaliza trace e persiste."""

    async def fail_trace(
        self,
        ctx: TraceContext,
        error: Exception,
    ) -> DecisionTrace:
        """Registra trace de falha."""
```

### 3.3 Query de Traces

```python
class TraceQueryService:
    """Consulta e analise de traces."""

    async def get_trace(
        self,
        trace_id: UUID,
    ) -> DecisionTrace:
        """Trace especifico com todos os detalhes."""

    async def search_traces(
        self,
        patient_id: Optional[str] = None,
        agent: Optional[str] = None,
        routing_method: Optional[str] = None,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[DecisionTrace]:
        """Busca traces com filtros."""

    async def analyze_routing_patterns(
        self,
        period_days: int = 30,
    ) -> RoutingAnalysis:
        """
        Analisa padroes de roteamento.

        - Distribuicao de metodo (LLM vs keyword)
        - Confianca media do LLM
        - Agentes mais requisitados
        - Queries que mais falharam
        - Latencia media por agente
        """

    async def find_anomalies(
        self,
        period_days: int = 7,
    ) -> list[RoutingAnomaly]:
        """
        Detecta anomalias no roteamento.

        - Query que sempre rota para agente inesperado
        - Confianca LLM em queda
        - Latencia em aumento
        """
```

### 3.4 Exportacao FHIR AuditEvent

```python
class FHIRAuditExporter:
    """
    Exporta traces no formato FHIR AuditEvent.

    Necessario para conformidade com regulatorios de saude.
    """

    async def export_decision(
        self,
        trace: DecisionTrace,
    ) -> dict:
        """
        Gera FHIR AuditEvent para decisao de orquestracao.

        Formato:
        {
            "resourceType": "AuditEvent",
            "type": {"system": "intellicare", "code": "orchestration"},
            "action": "E",
            "period": {"start": "...", "end": "..."},
            "outcome": "0",
            "agent": [{"requestor": true, "name": "wanda"}],
            "source": {"site": "intellicare-wanda"},
            "entity": [
                {"role": {"code": "query"}, "detail": [...]},
                {"role": {"code": "patient"}, "reference": {...}},
            ]
        }
        """
```

### 3.5 OpenTelemetry Integration

```python
class OTelInstrumentation:
    """
    Instrumentacao OpenTelemetry para traces tecnicos.
    """

    def instrument_agent_call(
        self,
        span: Span,
        agent: str,
        operation: str,
        attributes: dict,
    ) -> None:
        """
        Adiciona spans OTel para cada chamada de agente.

        Compativel com Jaeger, Zipkin, Grafana Tempo.
        """
```

### 3.6 Tabelas

```sql
-- Traces de decisao
CREATE TABLE decision_traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id UUID UNIQUE NOT NULL,
    execution_id UUID,
    original_query TEXT NOT NULL,
    patient_id VARCHAR(64),
    ips_loaded BOOLEAN DEFAULT FALSE,
    ips_source VARCHAR(20),
    routing_method VARCHAR(20),
    routing_reasoning TEXT,
    routing_latency_ms INTEGER,
    agent_calls JSONB DEFAULT '[]',
    aggregation_method VARCHAR(20),
    aggregation_latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    final_response_preview TEXT,
    total_latency_ms INTEGER,
    requested_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_traces_patient ON decision_traces(patient_id);
CREATE INDEX idx_traces_date ON decision_traces(created_at);
CREATE INDEX idx_traces_method ON decision_traces(routing_method);
CREATE INDEX idx_traces_success ON decision_traces(success);

-- Particionar por mes para escala
-- CREATE TABLE decision_traces_2026_02 PARTITION OF decision_traces
--     FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### 3.7 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/traces/{trace_id}` | Trace especifico |
| GET | `/api/v1/traces` | Busca com filtros |
| GET | `/api/v1/traces/patterns` | Analise de padroes |
| GET | `/api/v1/traces/anomalies` | Anomalias detectadas |
| GET | `/api/v1/traces/{trace_id}/fhir` | Exportar como FHIR AuditEvent |

## 4. Testes

- DecisionTracer: start, record, complete, fail (6 testes)
- TraceQueryService: get, search, patterns, anomalies (6 testes)
- FHIRAuditExporter: formato correto (3 testes)
- Hash de payload (privacidade) (2 testes)
- Endpoints (5 testes)
- **Total**: 22+ testes

## 5. Criterios de Aceitacao

- [ ] Trace completo de cada decisao (query → routing → calls → aggregation)
- [ ] Hash SHA256 de payloads (privacidade do paciente)
- [ ] Exportacao FHIR AuditEvent
- [ ] Integracao OpenTelemetry (opcional)
- [ ] Analise de padroes de routing
- [ ] Deteccao de anomalias
- [ ] 5 endpoints funcionais
- [ ] 22+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~7
- **Arquivos modificados**: ~3 (orchestrator, api, config)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~22
