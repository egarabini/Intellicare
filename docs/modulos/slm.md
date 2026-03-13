---
tipo: nota-modulo
modulo: slm
porto: TBD
fase: 3
sprint: "3.x"
status: pendente
dem_principal: DEM-010
tags: [fase-3, slm, ollama, rag, ia]
---

# Módulo: slm

**Responsabilidade:** Geração de respostas clínicas em linguagem natural via SLM local (OLLAMA), fundamentadas em chunks RAG da knowledge_base.

---

## Propósito

Fecha o ciclo RAG: recebe uma pergunta clínica, busca chunks relevantes via `semantic_search` (pgvector), monta prompt com contexto e system prompt em PT-BR, e envia ao OLLAMA para gerar resposta. Suporta modo síncrono e streaming (SSE). Sem dependência de APIs externas (LGPD, latência, custo).

---

## Endpoints Principais

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/slm/health` | Health check | any |
| POST | `/slm/ask` | Pergunta clínica → resposta com fontes | autenticado |
| GET | `/slm/models` | Lista modelos disponíveis no OLLAMA | autenticado |

### Payload `POST /slm/ask`

```json
{
  "query": "Qual o protocolo de triagem para hipertensão?",
  "limit": 5,
  "min_similarity": 0.5,
  "stream": false
}
```

### Resposta

```json
{
  "answer": "De acordo com os protocolos da unidade...",
  "sources": [
    {"title": "Protocolo HAS", "source_path": "protocolos/has.pdf", "similarity": 0.87}
  ],
  "model": "llama3.2:3b",
  "latency_ms": 1240
}
```

---

## Modelos Suportados

| Modelo | Parâmetros | Uso |
|--------|------------|-----|
| `llama3.2:3b` | 3B | Default — rápido, roda em CPU |
| `phi4-mini` | 3.8B | Melhor em PT-BR e texto médico |
| `mistral:7b` | 7B | Maior qualidade, requer GPU |

Configurável via variável de ambiente `SLM_MODEL`.

---

## System Prompt

```
Você é um assistente clínico do IntelliCare.
Responda APENAS com base no contexto clínico fornecido abaixo.
Responda sempre em português do Brasil. Nunca invente dados clínicos.
```

---

## Restrições e Segurança

- Sem dados de pacientes no prompt — apenas texto de protocolos e guidelines
- Timeout 30s → HTTP 504 com mensagem clara
- OLLAMA indisponível → HTTP 503
- Sem cache de resposta (dados clínicos são sensíveis)
- Isolamento: chunks buscados sempre do schema do tenant autenticado

---

## Roles Autorizados

- **Qualquer autenticado** — acesso a todos os endpoints
- O isolamento de dados é garantido pelo `TenantContext` (schema do tenant)

---

## Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OLLAMA_URL` | `http://ollama:11434` | URL do serviço OLLAMA |
| `SLM_MODEL` | `llama3.2:3b` | Modelo para geração |
| `SLM_TIMEOUT_S` | `30` | Timeout em segundos |

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/slm`)
- httpx (client assíncrono para OLLAMA API)
- `semantic_search()` do intellicare_core/vector/search.py (DEM-009)
- OLLAMA rodando localmente (container Docker)
- [[decisoes/ADR-003-rag-slm-pgvector]]

---

## DEMs relacionadas

- **DEM-010**: SLM via OLLAMA (geração de resposta, streaming SSE)
- **DEM-009**: Pipeline RAG (busca semântica consumida pelo SLM)
- **DEM-013**: Cuidado backend (endpoint `/encounters/{eid}/ask` delega ao SLM)

