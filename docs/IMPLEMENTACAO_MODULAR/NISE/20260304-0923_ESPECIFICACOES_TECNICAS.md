# NISE — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-nise (porta 8013)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| LLM Workflow | Flowise (externo, http://flowise:3100) |
| Vector DB | ChromaDB (intellicare-conhecimento) |
| LLM | Ollama (qwen2.5:7b via Flowise) |
| BD | PostgreSQL (historico de conversas) |
| Streaming | Server-Sent Events (SSE) para chat em tempo real |
| Testes | pytest + respx |

---

## 2. Arquitetura

```
[Portal / WhatsApp] → [NISE API] → [Flowise]
                           │              │
                           │         [ChromaDB] (protocolos)
                           │         [Ollama] (LLM)
                           │
                    [PostgreSQL]   (sessoes + historico)
                    [Redis]        (sessoes ativas)
```

---

## 3. Endpoints

```
GET  /api/v1/health
GET  /api/v1/info
POST /api/v1/analyze          (BaseAgent)

POST /api/v1/chat             → ChatResponse (conversa)
GET  /api/v1/chat/{session_id}/history → List[ChatMessage]
DELETE /api/v1/chat/{session_id}  → 204 (encerrar sessao)

POST /api/v1/triage           → TriageResult (score de risco)
GET  /api/v1/flows            → List[FlowInfo] (flows Flowise)
GET  /api/v1/flows/{flow_id}/status → FlowStatus
```

---

## 4. Integracao Flowise

```python
# nise/services/flowise_client.py
class FlowiseClient:
    base_url: str   # http://flowise:3100

    async def chat(self, flow_id: str, message: str,
                   session_id: str, context: dict = {}) -> str:
        payload = {
            "question": message,
            "overrideConfig": {
                "sessionId": session_id,
                **context  # paciente_id, profissional_id, etc.
            }
        }
        response = await self.http.post(
            f"{self.base_url}/api/v1/prediction/{flow_id}",
            json=payload
        )
        return response["text"]

    async def list_chatflows(self) -> list[dict]:
        return await self.http.get(f"{self.base_url}/api/v1/chatflows")
```

---

## 5. Modelos

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: UUID (PK)
    flow_id: str            # ID do flow Flowise
    user_id: Optional[str]  # profissional ou paciente
    patient_id: Optional[str]
    session_type: str       # "clinical", "triage", "training"
    started_at: datetime
    ended_at: Optional[datetime]
    tenant_id: str

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: UUID (PK)
    session_id: UUID (FK)
    role: str               # "user" ou "assistant"
    content: str
    sources: Optional[list] # JSONB - citacoes de protocolo
    created_at: datetime

class TriageResult(Base):
    __tablename__ = "triage_results"
    id: UUID (PK)
    patient_id: str
    symptoms: list          # JSONB
    risk_score: int         # 1-5 (Manchester adaptado)
    classification: str     # "emergência", "urgente", "pouco_urgente", "nao_urgente"
    recommended_action: str
    created_at: datetime
    tenant_id: str
```

---

## 6. Triagem (Manchester Simplificado)

```python
# nise/services/triage_service.py
RISK_THRESHOLDS = {
    # sintomas -> score
    "dor_peito": 5,          # emergencia
    "falta_ar_grave": 5,
    "sangramento_ativo": 4,  # urgente
    "febre_alta": 3,         # pouco urgente
    "dor_leve": 2,
    "sintomas_cronicos": 1   # nao urgente
}

CLASSIFICATION_MAP = {
    5: ("emergencia", "Ir imediatamente para UPA/PS"),
    4: ("urgente", "Consulta em ate 2h na UBS"),
    3: ("pouco_urgente", "Consulta hoje na UBS"),
    2: ("nao_urgente", "Consulta em ate 3 dias"),
    1: ("eletivo", "Agendar consulta de rotina")
}
```

---

## 7. Configuracao

```env
FLOWISE_URL=http://flowise:3100
FLOWISE_API_KEY=             # opcional
CLINICAL_FLOW_ID=            # ID do flow clinico no Flowise
TRIAGE_FLOW_ID=              # ID do flow de triagem
TRAINING_FLOW_ID=            # ID do flow de treinamento
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379/0
PORT=8000
```

---

## 8. Fallback sem Flowise

Se Flowise estiver offline, NISE responde com:
```json
{
  "text": "Assistente temporariamente indisponivel. Para duvidas urgentes, consulte um profissional de saude.",
  "sources": [],
  "flowise_available": false
}
```

Nao retorna erro 503 — retorna resposta de fallback com flag `flowise_available: false`.

---

*NISE v2.0 — Especificacoes Tecnicas — 2026-03-04*
