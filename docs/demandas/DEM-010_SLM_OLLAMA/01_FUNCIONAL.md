---
dem: DEM-010
titulo: SLM via OLLAMA — Geração de Resposta Clínica
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-009]
---

# DEM-010 · 01 — Especificação Funcional

## Contexto e Motivação

O pipeline RAG (DEM-009) entrega chunks relevantes da `knowledge_base`. A DEM-010 fecha o ciclo:
usa um SLM local via OLLAMA para **gerar resposta em linguagem natural** fundamentada nesses chunks
— sem depender de APIs externas (LGPD, latência, custo).

## Modelo de Operação

```
Query do Clinico
  → RAG: top-k chunks relevantes (DEM-009)
  → Prompt: system_prompt + contexto (chunks) + query
  → OLLAMA SLM: gerar resposta em PT-BR
  → Resposta estruturada com fontes citadas
```

## Modelos Suportados

| Modelo | Parâmetros | Uso recomendado |
|---|---|---|
| `llama3.2:3b` | 3B | Default — rápido, roda em CPU |
| `phi4-mini` | 3.8B | Melhor em PT-BR e texto médico |
| `mistral:7b` | 7B | Maior qualidade, requer GPU |

Configurável via `SLM_MODEL` no `.env`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/slm/ask` | Pergunta clínica → resposta com fontes |
| GET | `/slm/models` | Lista modelos disponíveis no OLLAMA |
| GET | `/slm/health` | Health check do módulo |

## Payload e Resposta

**Request** `POST /slm/ask`:
```json
{
  "query": "Qual o protocolo de triagem para hipertensão?",
  "limit": 5,
  "min_similarity": 0.5,
  "stream": false
}
```

**Response**:
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

## System Prompt Padrão

```
Você é um assistente clínico do IntelliCare. Responda APENAS com base no contexto fornecido.
Responda sempre em português do Brasil. Seja objetivo e cite as fontes pelo título.
Se o contexto não contiver informação suficiente, diga explicitamente.
Nunca invente dados clínicos, doses, diagnósticos ou condutas.
```

## Restrições e Segurança

- Sem dados de pacientes no prompt — apenas texto de protocolos e guidelines
- Timeout 30s; se ultrapassado → 504 Gateway Timeout com mensagem clara
- Sem cache de resposta por padrão (dados clínicos são sensíveis)
- Isolamento de tenant: chunks buscados sempre do schema do tenant autenticado

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | POST `/slm/ask` com query válida → resposta em PT-BR com campo `sources` |
| AC-2 | Resposta cita `source_path` dos chunks usados como contexto |
| AC-3 | Latência total (RAG + geração) < 30s com `llama3.2:3b` |
| AC-4 | `stream: true` → resposta via Server-Sent Events (chunks progressivos) |
| AC-5 | OLLAMA indisponível → HTTP 503 com mensagem (sem travar a API principal) |
| AC-6 | GET `/slm/models` lista modelos instalados no OLLAMA |
| AC-7 | Query sem contexto suficiente → resposta honesta ("Não encontrei informações...") |
