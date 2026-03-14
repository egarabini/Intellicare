---
dem: DEM-010
titulo: SLM via OLLAMA — Implementação
tipo: IMPLEMENTACAO
status: concluído
criado: 2026-03-14
---

# DEM-010 · 03 — Implementação

## Arquivos Criados

| Arquivo | Papel |
|---------|-------|
| `modules/slm/__init__.py` | Marcador de pacote |
| `modules/slm/schemas.py` | 4 Pydantic models (AskRequest, AskResponse, SourceRef, ModelInfo) |
| `modules/slm/service.py` | `SLMService` — ask, stream_ask, list_models + _build_prompt |
| `modules/slm/router.py` | `APIRouter(/slm)` — 3 endpoints |
| `modules/slm/main.py` | `Module(BaseModule)` — contrato obrigatório |
| `tests/slm/__init__.py` | Pacote de testes |
| `tests/slm/test_slm.py` | 13 testes unitários — todos passando |

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/slm/health` | Health check |
| GET | `/slm/models` | Lista modelos instalados no OLLAMA |
| POST | `/slm/ask` | Pergunta clínica → resposta com fontes (suporta SSE streaming) |

## Fluxo de Operação

```
Query do Clínico
  → RAG: semantic_search (pgvector, schema do tenant)
  → Prompt: SYSTEM_PROMPT + contexto (chunks) + query
  → OLLAMA /api/generate (SLM_MODEL, temperature=0.1)
  → Resposta estruturada com sources citadas
```

## Configuração via Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OLLAMA_URL` | `http://ollama:11434` | URL do servidor OLLAMA |
| `SLM_MODEL` | `llama3.2:3b` | Modelo a usar para geração |
| `SLM_TIMEOUT_S` | `30` | Timeout em segundos |

## Tratamento de Erros

| Cenário | HTTP | Mensagem |
|---------|------|----------|
| OLLAMA indisponível | 503 | "OLLAMA indisponível" |
| Timeout > 30s | 504 | "OLLAMA timeout: modelo demorou mais de 30s" |
| Sem contexto RAG | 200 | Resposta honesta: "Não encontrei informações suficientes..." |

## Testes

```
tests/slm/test_slm.py — 13 passed
  ✓ test_ask_request_defaults
  ✓ test_ask_request_custom
  ✓ test_ask_request_query_too_short
  ✓ test_ask_request_limit_bounds
  ✓ test_ask_request_similarity_bounds
  ✓ test_source_ref
  ✓ test_ask_response
  ✓ test_model_info
  ✓ test_model_info_no_size
  ✓ test_build_prompt_single_chunk
  ✓ test_build_prompt_multiple_chunks
  ✓ test_system_prompt_contains_key_instructions
  ✓ test_default_model
```

## Dependências

- `intellicare-core` (DEM-003): `BaseModule`, `TenantContext`, `get_current_tenant`, `semantic_search`
- `DEM-009` (pgvector RAG): `semantic_search` busca chunks no schema do tenant
- `httpx`: cliente async para OLLAMA API
- OLLAMA server com modelo instalado (`ollama pull llama3.2:3b`)

