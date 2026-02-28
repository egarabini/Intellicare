# EF-F009 — Monitoramento Prometheus e Feedback RAG

> Ativar coleta de metricas Prometheus nos endpoints da Florence e implementar o loop de feedback do RAG — permitindo que medicos avaliem a qualidade dos protocolos retornados e que o sistema melhore continuamente.

## 1. Objetivo

Dois objetivos complementares que compartilham infraestrutura de dados:

### Monitoramento Prometheus
- Coletar metricas de latencia, throughput e erros em todos os endpoints
- Expor `/metrics` no formato Prometheus
- Alertas automaticos quando latencia > 500ms ou error rate > 5%

### Feedback RAG
- Medico avalia (polegar cima/baixo) se o protocolo retornado foi util
- Feedback persiste no banco para analise
- Dashboard mostra quais protocolos tem menor utilidade (candidatos a revisao)
- Feedback loop: protocolos mais avaliados positivamente sobem no ranking

## 2. Justificativa

- `prometheus-client` ja instalado mas sem coleta ativa nos endpoints
- Alertas YAML estruturados mas sem disparador
- `RAGFeedback` model definido em `florence/engine/rag/models.py` mas sem UI ou endpoint
- Sem feedback, nao ha como saber se os 10 protocolos sao de fato uteis
- Observabilidade e requisito para producao hospitalar (ON-CALL, SLA, RCA)

## 3. Escopo

### 3.1 FlorenceMetrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

class FlorenceMetrics:
    """
    Coleta de metricas Prometheus para a Florence.
    Singleton — instanciado uma vez na startup.

    Metricas coletadas:
    - florence_requests_total: contador de requests por endpoint + status
    - florence_request_duration_seconds: histograma de latencia por endpoint
    - florence_critical_values_total: contador de valores criticos detectados
    - florence_rag_queries_total: contador de queries RAG
    - florence_rag_latency_seconds: latencia especifica do RAG
    - florence_cache_hit_rate: taxa de hit do cache Redis
    - florence_active_analyses: gauge de analises em andamento
    - florence_llm_requests_total: requests ao Ollama + status
    """

    # Latencia por endpoint
    REQUEST_DURATION = Histogram(
        "florence_request_duration_seconds",
        "Latencia de requests por endpoint",
        ["method", "endpoint", "status"],
        buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0],
    )

    # Contador de requests
    REQUESTS_TOTAL = Counter(
        "florence_requests_total",
        "Total de requests",
        ["method", "endpoint", "status"],
    )

    # Valores criticos detectados
    CRITICAL_VALUES = Counter(
        "florence_critical_values_total",
        "Valores criticos detectados por lab_id",
        ["lab_id", "level"],
    )

    # RAG
    RAG_QUERIES = Counter(
        "florence_rag_queries_total",
        "Queries ao RAG por resultado",
        ["protocol_found", "cache_hit"],
    )

    RAG_LATENCY = Histogram(
        "florence_rag_latency_seconds",
        "Latencia do RAG (ChromaDB)",
        ["cache_hit"],
        buckets=[0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0],
    )

    # LLM
    LLM_REQUESTS = Counter(
        "florence_llm_requests_total",
        "Requests ao Ollama",
        ["status"],   # "success" | "timeout" | "unavailable" | "fallback"
    )

    # RAG Feedback
    RAG_FEEDBACK = Counter(
        "florence_rag_feedback_total",
        "Feedback de protocolos RAG",
        ["protocol_id", "rating"],   # rating: "positive" | "negative"
    )

    def instrument_fastapi(self, app: FastAPI) -> None:
        """
        Adiciona middleware de instrumentacao ao FastAPI.
        Coleta REQUEST_DURATION e REQUESTS_TOTAL automaticamente.
        """
```

### 3.2 Endpoint `/metrics`

```python
# GET /metrics
# Retorna: metricas Prometheus em texto (Content-Type: text/plain)
# Exemplo de saida:
"""
# HELP florence_request_duration_seconds Latencia de requests por endpoint
# TYPE florence_request_duration_seconds histogram
florence_request_duration_seconds_bucket{endpoint="/api/v1/analyze",le="0.1"} 842
florence_request_duration_seconds_bucket{endpoint="/api/v1/analyze",le="0.3"} 1204
...

# HELP florence_critical_values_total Valores criticos detectados por lab_id
# TYPE florence_critical_values_total counter
florence_critical_values_total{lab_id="potassium",level="critical_high"} 47
florence_critical_values_total{lab_id="troponin_i",level="critical_high"} 12
...

# HELP florence_rag_queries_total Queries ao RAG
# TYPE florence_rag_queries_total counter
florence_rag_queries_total{protocol_found="true",cache_hit="true"} 1847
florence_rag_queries_total{protocol_found="true",cache_hit="false"} 623
...
"""
```

### 3.3 Alertas Prometheus (AlertManager)

```yaml
# florence/monitoring/alerts.yaml
# Compativel com Prometheus AlertManager

groups:
  - name: florence_alerts
    rules:
      - alert: FlorenceHighLatency
        expr: histogram_quantile(0.95, florence_request_duration_seconds_bucket) > 0.5
        for: 5m
        labels:
          severity: warning
          module: florence
        annotations:
          summary: "Florence latencia p95 > 500ms"
          description: "p95 = {{ $value }}s — verificar ChromaDB e Ollama"

      - alert: FlorenceCriticalValuesSpike
        expr: rate(florence_critical_values_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
          module: florence
        annotations:
          summary: "Alta taxa de valores criticos — verificar qualidade dos dados"

      - alert: FlorenceLLMUnavailable
        expr: rate(florence_llm_requests_total{status="unavailable"}[5m]) > 0
        for: 3m
        labels:
          severity: warning
          module: florence
        annotations:
          summary: "Ollama indisponivel — Florence operando sem narrativas LLM"

      - alert: FlorenceLowRAGFeedback
        expr: (florence_rag_feedback_total{rating="negative"} / florence_rag_feedback_total) > 0.3
        for: 1d
        labels:
          severity: info
          module: florence
        annotations:
          summary: "Mais de 30% de feedbacks negativos nos protocolos RAG"
```

### 3.4 Sistema de Feedback RAG

```python
# Modelos (estendendo RAGFeedback existente em rag/models.py)

@dataclass
class RAGFeedbackRequest:
    """Enviado pelo medico/UI ao avaliar um protocolo."""
    analysis_id: str               # ID da analise que gerou o protocolo
    protocol_id: str               # ID do protocolo avaliado
    query: str                     # Query usada para buscar o protocolo
    chunk_text: str                # Chunk especifico avaliado
    rating: str                    # "positive" | "negative"
    comment: Optional[str] = None  # Comentario livre (opcional)
    user_id: Optional[str] = None  # Quem avaliou


@dataclass
class RAGProtocolStats:
    """Estatisticas agregadas por protocolo."""
    protocol_id: str
    protocol_name: str
    total_retrievals: int
    total_feedbacks: int
    positive_count: int
    negative_count: int
    feedback_rate: float           # total_feedbacks / total_retrievals
    approval_rate: float           # positive / total_feedbacks
    last_positive_at: Optional[str]
    last_negative_at: Optional[str]
    recommendation: str            # "manter" | "revisar" | "substituir"
```

```sql
-- Tabela de feedback RAG
CREATE TABLE florence_rag_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID,             -- Referencia florence_analyses (EF-F002)
    protocol_id VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    chunk_text TEXT,
    rating VARCHAR(20) NOT NULL,  -- "positive" | "negative"
    comment TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_protocol ON florence_rag_feedback (protocol_id, rating);
```

### 3.5 Endpoints Novos

```python
# GET /metrics
# Metricas Prometheus

# POST /api/v1/rag/feedback
# Body: RAGFeedbackRequest
# Registra feedback de um protocolo RAG
# Retorna: {feedback_id, protocol_id, rating}

# GET /api/v1/rag/protocols/stats
# Retorna: list[RAGProtocolStats] com aprovacao por protocolo
# Ordenado por approval_rate ASC (piores primeiro — candidatos a revisao)

# GET /api/v1/monitoring/health-detailed
# Retorna health check estendido:
{
    "status": "healthy",
    "modules": {
        "clinical_analyzer": {"status": "ok", "avg_latency_ms": 180},
        "rag": {"status": "ok", "indexed_protocols": 10, "avg_latency_ms": 320},
        "llm": {"status": "degraded", "reason": "Ollama unavailable — using fallback"},
        "redis": {"status": "ok", "hit_rate": 0.71},
        "database": {"status": "ok", "total_analyses": 4821},
    },
    "version": "2.0.0",
    "uptime_seconds": 86400,
}
```

### 3.6 Atualizacao da UI Streamlit — Pagina de RAG

```python
# florence/ui/pages/4_🤖_RAG.py — adicionar secao de feedback

# Abaixo de cada protocolo retornado:
col1, col2 = st.columns(2)
with col1:
    if st.button("👍 Util", key=f"pos_{chunk_id}"):
        api_client.post("/api/v1/rag/feedback", {
            "analysis_id": analysis_id,
            "protocol_id": protocol_id,
            "rating": "positive",
        })
        st.success("Obrigado pelo feedback!")

with col2:
    if st.button("👎 Nao util", key=f"neg_{chunk_id}"):
        # Pede comentario opcional
        comment = st.text_input("O que estava errado?")
        api_client.post("/api/v1/rag/feedback", {
            "analysis_id": analysis_id,
            "protocol_id": protocol_id,
            "rating": "negative",
            "comment": comment,
        })
```

### 3.7 Configuracao

```env
FLORENCE_METRICS_ENABLED=true
FLORENCE_METRICS_PATH=/metrics
FLORENCE_RAG_FEEDBACK_ENABLED=true
FLORENCE_ALERTMANAGER_URL=http://alertmanager:9093  # Para alertas
```

## 4. Testes

- FlorenceMetrics.instrument_fastapi: metricas coletadas apos request (2 testes)
- /metrics: endpoint retorna formato Prometheus valido (1 teste)
- RAGFeedback: POST feedback persiste, GET stats calcula approval_rate (2 testes)
- RAGProtocolStats: protocolo com > 30% negativos marcado como "revisar" (1 teste)
- /api/v1/monitoring/health-detailed: retorna status de todos os modulos (1 teste)
- Alerta: latencia alta detectada pela regra Prometheus (1 teste — unitario da regra PromQL)
- **Total**: 8+ testes novos

## 5. Criterios de Aceitacao

- [ ] `GET /metrics` retorna metricas Prometheus validas
- [ ] Latencia de todos os endpoints monitorada via histogram
- [ ] Valores criticos contados por lab_id
- [ ] `POST /api/v1/rag/feedback` persiste avaliacao de protocolo
- [ ] `GET /api/v1/rag/protocols/stats` mostra approval_rate por protocolo
- [ ] UI Streamlit tem botoes de feedback na pagina RAG
- [ ] Alerta `FlorenceHighLatency` definido e documentado
- [ ] `/api/v1/monitoring/health-detailed` consolida status de todos os modulos
- [ ] 198 testes existentes continuam passando
- [ ] 8+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/metrics/prometheus.py`, `florence/monitoring/alerts.yaml`, `alembic/versions/004_rag_feedback.py`
- **Arquivos modificados**: `florence/api/app.py` (instrumentar endpoints + 4 novos endpoints), `florence/ui/pages/4_🤖_RAG.py` (botoes feedback), `florence/config.py`
- **Linhas estimadas**: ~350
- **Testes novos**: ~8
