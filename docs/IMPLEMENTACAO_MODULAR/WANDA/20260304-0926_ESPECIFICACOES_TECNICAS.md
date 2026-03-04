# WANDA — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 3.0.0
**Modulo:** intellicare-wanda (porta 8004)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| AI Orchestration | LangGraph (langgraph>=0.2) |
| LLM | Ollama (llama4:scout ou qwen2.5:72b) |
| MCP Client | mcp (Anthropic MCP SDK) |
| Event Streaming | Redis Streams |
| Circuit Breaker | tenacity + custom |
| Tracing | OpenTelemetry |
| Testes | pytest + pytest-asyncio + langgraph testing |

---

## 2. LangGraph — Grafo Principal

```python
# wanda/agent/graph.py
from langgraph.graph import StateGraph, END

class WandaState(TypedDict):
    query: str
    patient_id: Optional[str]
    intent: Optional[str]
    patient_context: Optional[dict]   # IPS
    tools_results: list[dict]
    final_response: Optional[str]
    alert_triggered: bool

# Nos do grafo
graph = StateGraph(WandaState)
graph.add_node("intent_detector", detect_intent)
graph.add_node("context_builder", build_patient_context)    # IPS via GRAHAME
graph.add_node("tool_selector", select_tools)               # MCP tools
graph.add_node("parallel_executor", execute_tools_parallel) # PIERRE + MINERVA
graph.add_node("aggregator", aggregate_responses)           # LLM aggregation
graph.add_node("alert_dispatcher", dispatch_alerts)         # AlertHub
graph.add_node("responder", format_final_response)

# Arestas condicionais
graph.add_conditional_edges("intent_detector", route_by_intent, {
    "clinical_query": "context_builder",
    "document_upload": "tool_selector",
    "alert": "alert_dispatcher",
    "data_only": "aggregator"
})
```

---

## 3. MCP Client Integration

```python
# wanda/mcp/clients.py

class PierreClient(MCPClient):
    """Cliente MCP para PIERRE — busca cientifica"""
    server_url: str = "http://pierre:8009/mcp/sse"
    tools: ["search_pubmed", "search_bvs", "search_web", "synthesize"]

class MinervaClient(MCPClient):
    """Cliente MCP para MINERVA — extracao documental"""
    server_url: str = "http://minerva:8008/mcp/sse"
    tools: ["extract_text", "extract_lab_results", "extract_structured"]

# Inicializados no lifespan
async def lifespan(app: FastAPI):
    app.state.pierre = PierreClient()
    app.state.minerva = MinervaClient()
    await app.state.pierre.connect()
    await app.state.minerva.connect()
    yield
    await app.state.pierre.disconnect()
    await app.state.minerva.disconnect()
```

---

## 4. AlertHub

```python
# wanda/alerts/hub.py

class AlertHub:
    def __init__(self, redis_client, comunicacao_url: str):
        self.redis = redis_client
        self.comunicacao = ComunicacaoClient(comunicacao_url)

    async def publish(self, alert: ClinicalAlert):
        # 1. Persistir no Redis Stream "wanda:alerts"
        await self.redis.xadd("wanda:alerts", alert.dict())
        # 2. Categorizar urgencia
        if alert.severity == "critical":
            await self._dispatch_critical(alert)
        elif alert.severity == "urgent":
            await self._dispatch_urgent(alert)
        else:
            await self._queue_routine(alert)

    async def _dispatch_critical(self, alert: ClinicalAlert):
        # RC com @here + SMS medico responsavel (< 5s)
        await asyncio.gather(
            self.comunicacao.send_rocketchat(
                channel=alert.team_channel,
                message=f"🚨 CRITICO: {alert.message}",
                mention_all=True
            ),
            self.comunicacao.send_sms(
                to=alert.responsible_doctor_phone,
                message=f"CRITICO IntelliCare: {alert.message[:160]}"
            )
        )

class ClinicalAlert(BaseModel):
    patient_id: str
    source_module: str          # "grahame", "geralda", "donabedian"
    severity: str               # "critical", "urgent", "routine", "info"
    category: str               # "lab_value", "adherence", "medication", "quality"
    message: str
    data: dict                  # dados extras do alerta
    team_channel: str           # canal RC da equipe
    responsible_doctor_phone: Optional[str]
    created_at: datetime
```

---

## 5. IPS Builder (International Patient Summary)

```python
# wanda/context/ips_builder.py

class IPSBuilder:
    """Constroi o International Patient Summary de um paciente
    consultando GRAHAME (dados FHIR) e GERALDA (plano de cuidado)"""

    async def build(self, patient_id: str, tenant: str) -> PatientSummary:
        # Buscar em paralelo:
        grahame_data, geralda_data = await asyncio.gather(
            self.grahame.get_patient_everything(patient_id),
            self.geralda.get_active_careplan(patient_id),
            return_exceptions=True
        )
        # Montar IPS com graceful degradation
        return PatientSummary(
            patient=self._extract_patient(grahame_data),
            conditions=self._extract_conditions(grahame_data),
            medications=self._extract_medications(grahame_data),
            observations=self._extract_recent_obs(grahame_data),
            care_plan=geralda_data if not isinstance(geralda_data, Exception) else None,
            adherence_rate=geralda_data.adherence_rate if hasattr(geralda_data, 'adherence_rate') else None
        )
```

---

## 6. Endpoints

```
GET  /api/v1/health
GET  /api/v1/info
POST /api/v1/analyze          (BaseAgent — principal endpoint)
POST /api/v1/query            (alias para analyze)
POST /api/v1/upload           (upload documento + extracao MINERVA)

GET  /api/v1/alerts           (listar alertas recentes)
POST /api/v1/alerts           (publicar alerta no AlertHub)
GET  /api/v1/modules          (registry de modulos ativos)
GET  /api/v1/modules/{name}/health  (health de modulo especifico)
```

---

## 7. Configuracao

```env
# Modulos
GRAHAME_URL=http://grahame:8012/api/v1
GERALDA_URL=http://geralda:8006/api/v1
DONABEDIAN_URL=http://donabedian:8003/api/v1
FLORENCE_URL=http://florence:8001/api/v1
OSWALDO_URL=http://oswaldo:8002/api/v1
COMUNICACAO_URL=http://comunicacao:8005/api/v1
NISE_URL=http://nise:8013/api/v1
ZILDA_URL=http://zilda:8007/api/v1

# MCP Servers
PIERRE_MCP_URL=http://pierre:8009/mcp/sse
MINERVA_MCP_URL=http://minerva:8008/mcp/sse

# LLM
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:72b
INTENT_MODEL=qwen2.5:7b          # modelo menor para intent detection

# Infra
REDIS_URL=redis://redis:6379/0
PORT=8000
ENABLE_TRACING=true
OTEL_ENDPOINT=http://otel-collector:4317
```

---

*WANDA v3.0 — Especificacoes Tecnicas — 2026-03-04*
