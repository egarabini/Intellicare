# STEP-002 — WANDA Fase 2: Motor de Roteamento IA + Agregação Inteligente

**Data de conclusão:** 2026-02-17
**Versão:** 2.1.0
**Status:** ✅ Concluído

---

## Resumo

Implementação da Fase 2 do módulo `intellicare-wanda`, adicionando roteamento por intenção via LLM (EF-W003) e agregação inteligente de respostas multi-agente (EF-W004). Todos os componentes têm fallback gracioso para os componentes v1.0 existentes.

---

## Resultados

| Métrica | Fase 1 | Fase 2 |
|---------|--------|--------|
| Testes  | 246    | **318** (+72) |
| Cobertura | 90.26% | **89.74%** |
| Linhas de código | ~2.400 | ~3.200 |

---

## Componentes Implementados

### EF-W003 — Roteamento por Intenção (LLM)

#### `wanda/llm/` — Camada de Abstração LLM

| Arquivo | Descrição |
|---------|-----------|
| `provider.py` | `LLMProvider` (ABC) + `LLMResponse` (dataclass) |
| `ollama_provider.py` | `OllamaProvider` — POST `/api/chat` via `httpx.AsyncClient` |
| `exceptions.py` | `LLMUnavailableError`, `LLMTimeoutError`, `LLMParseError` |
| `__init__.py` | Exports públicos |

**OllamaProvider** — características:
- Usa `httpx.AsyncClient` diretamente (sem pacote `ollama`)
- `json_mode=True` → `"format": "json"` no payload
- `temperature=0.1` para respostas determinísticas
- Health check via `GET /api/tags`
- Exceções tipadas para timeout, conexão recusada e JSON inválido

#### `wanda/orchestrator/intent_extractor.py` — Extrator de Intenção (determinístico)

- 6 categorias: `care_management`, `clinical_analysis`, `chronic_disease`, `territorial`, `quality`, `general`
- Urgência: `normal` | `high` | `emergency`
- Sem LLM — regras baseadas em keywords
- `intent_to_modules()` mapeia intenção → módulo principal

#### `wanda/orchestrator/intent_router.py` — Roteador por Intenção

```
QueryRouter (v1.0, keyword)
     ↑ fallback automático
IntentRouter (v2.1, LLM)
```

**Fluxo de decisão:**
1. LLM (Ollama llama3.1:8b) → JSON estruturado com agentes + reasoning + confidence
2. Validação: agentes existem na lista disponível + `confidence >= 0.7`
3. Se qualquer falha (timeout, conexão, JSON inválido, confiança baixa) → fallback keyword

**Casos de fallback:**
- `LLMUnavailableError` — Ollama offline
- `LLMTimeoutError` — timeout 5s
- `LLMParseError` — JSON inválido
- `confidence < 0.7` — baixa confiança
- Agentes inventados (não na lista disponível)
- Qualquer exceção genérica

**Bug corrigido durante implementação:**
O `WANDA_ROUTING_SYSTEM_PROMPT` contém um exemplo JSON com `{` e `}`. Usar `.format()` fazia o Python interpretar `"primary_agents":` como campo template (erro: `KeyError: '\n    "primary_agents"'`). Fix: substituído por `.replace()` manual.

### EF-W004 — Agregação Inteligente (LLM)

#### `wanda/orchestrator/intelligent_aggregator.py`

```
ResponseAggregator (v1.0, concat simples)
          ↑ fallback automático
IntelligentAggregator (v2.1, LLM synthesis)
```

**Fluxo:**
1. 0-1 agentes com sucesso → passa para `ResponseAggregator` diretamente
2. `>max_agents_for_llm (5)` → fallback (contexto muito grande para LLM)
3. LLM call com síntese estruturada: `synthesis`, `key_points`, `recommended_actions`, `critical_alerts`
4. Anti-fabricação: síntese > 3× tamanho das respostas originais → fallback
5. Dois modos: `recipient_type="professional"` (clínico) | `"patient"` (linguagem acessível)

#### `wanda/orchestrator/contradiction_detector.py`

- Detecta conflitos entre respostas de múltiplos agentes
- Retorna lista de `Contradiction(field, agent_a, value_a, agent_b, value_b, severity)`
- Degradação graciosa: retorna `[]` em qualquer falha LLM

### Novos Endpoints API

#### `wanda/api/routing_routes.py`

```
POST /api/v1/routing/explain   → Preview de roteamento sem chamar módulos
GET  /api/v1/routing/method    → Método ativo (llm/keyword) + disponibilidade LLM
```

#### `wanda/api/aggregation_routes.py`

```
POST /api/v1/aggregate         → Debug: agrega respostas mock
```

---

## Configuração

### Novas vars em `wanda/config.py`

```python
# EF-W003
enable_ollama: bool = False           # Desabilitado por padrão
ollama_url: str = "http://localhost:11434"
ollama_routing_model: str = "llama3.1:8b"
ollama_routing_timeout_seconds: int = 5
routing_method: str = "auto"          # auto | llm | keyword
llm_confidence_min: float = 0.7

# EF-W004
ollama_aggregation_model: str = "llama3.1:8b"
ollama_aggregation_timeout_seconds: int = 15
max_agents_for_llm_aggregation: int = 5
```

### Ativação (`.env`)

```bash
INTELLICARE_ENABLE_OLLAMA=true
INTELLICARE_OLLAMA_URL=http://localhost:11434
INTELLICARE_OLLAMA_ROUTING_MODEL=llama3.1:8b
```

---

## Testes (72 novos)

| Arquivo | Testes | Foco |
|---------|--------|------|
| `test_llm_provider.py` | 12 | OllamaProvider, exceções, LLMResponse |
| `test_intent_extractor.py` | 13 | Categorias, urgência, mapeamento módulos |
| `test_intent_router.py` | 13 | LLM ok, fallback, JSON inválido, confiança baixa |
| `test_intelligent_aggregator.py` | 16 | Pass-through, LLM, fallback, anti-fabricação |
| `test_contradiction_detector.py` | 6 | Sem contradição, com contradição, LLM down |
| `test_routing_routes.py` | 5 | Endpoints routing/explain, routing/method |
| `test_aggregation_routes.py` | 3 | Endpoint aggregate |
| `test_repository.py` (Fase 1) | 31 | Cobertura repositório SQLAlchemy |
| **Total novos** | **99** | |

---

## Arquitetura Final (v2.1)

```
wanda/
├── llm/                          # NOVO Fase 2
│   ├── provider.py               # Abstract LLMProvider + LLMResponse
│   ├── ollama_provider.py        # Implementação Ollama via httpx
│   └── exceptions.py             # Exceções tipadas LLM
├── orchestrator/
│   ├── router.py                 # v1.0 QueryRouter (keyword) — fallback
│   ├── aggregator.py             # v1.0 ResponseAggregator — fallback
│   ├── intent_extractor.py       # NOVO Fase 2 — determinístico
│   ├── intent_router.py          # NOVO Fase 2 — LLM + fallback keyword
│   ├── intelligent_aggregator.py # NOVO Fase 2 — LLM + fallback simple
│   ├── contradiction_detector.py # NOVO Fase 2 — detecção de conflitos
│   └── orchestrator.py           # Pipeline principal v2.1
├── api/
│   ├── routing_routes.py         # NOVO Fase 2 — /routing/explain + /method
│   └── aggregation_routes.py     # NOVO Fase 2 — /aggregate debug
└── ...
```

---

## Princípio de Design

> **"LLM quando disponível, keyword quando não"**

Todos os componentes LLM são opcionais e inicializados apenas quando `enable_ollama=True`. O sistema mantém 100% de funcionalidade mesmo sem Ollama, garantindo que nenhuma regressão afete a Fase 1.
