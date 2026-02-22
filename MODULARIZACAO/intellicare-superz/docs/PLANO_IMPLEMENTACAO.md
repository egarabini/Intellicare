# intellicare-superz — Plano de Implementacao

**Modulo:** `intellicare-superz` (Super Z / PIERRE)
**Versao:** 1.0 (IntelliCare V5)
**Data:** 2026-02-16
**Status:** EM IMPLEMENTACAO

---

## 1. Visao Geral

Implementacao completa do MCP Server de inteligencia externa do IntelliCare. O modulo expoe 6 tools MCP para busca web em tempo real (Tavily), literatura medica indexada (PubMed, BVS/BIREME, SciELO), verificacao regulatoria (ANVISA/ANS/CFM), analise de texto (Qwen2.5 via Ollama), resumo de documentos e traducao medica PT-BR.

---

## 2. Fases de Implementacao

### Fase 1 — Estrutura Base & Configuracao
**Prioridade:** CRITICA (tudo depende disso)
**Arquivos:**
- `pyproject.toml` — dependencias e metadata
- `superz/__init__.py` — package init
- `superz/config.py` — `SuperZConfig` dataclass com `from_env()`
- `superz/models.py` — dataclasses de output (WebSearchResult, MedicalArticle, etc.)
- `Dockerfile` — imagem Python 3.11-slim
- `docker-compose.yml` — superz + redis
- `.env.example` — variaveis de ambiente documentadas
- `.gitignore`

**Criterios de conclusao:**
- [x] `SuperZConfig.from_env()` funciona
- [x] Todos os 10 dataclasses/enums do models.py validados
- [x] Docker build sem erros

---

### Fase 2 — Cache Redis & Rate Limiter
**Prioridade:** ALTA (Tavily e pago — cache e rate limiter economizam $$$)
**Arquivos:**
- `superz/cache/__init__.py`
- `superz/cache/search_cache.py` — `SearchCache` com TTLs diferenciados
- `superz/rate_limiter/__init__.py`
- `superz/rate_limiter/limiter.py` — `TavilyRateLimiter` (token bucket)

**Criterios de conclusao:**
- [x] Cache get/set com TTL diferenciado (6h tavily, 24h pubmed, 12h regulatory)
- [x] Cache funciona sem Redis (graceful degradation)
- [x] Rate limiter bloqueia apos N requests/hora
- [x] Rate limiter status endpoint funciona

---

### Fase 3 — Clientes de Busca
**Prioridade:** ALTA (core do modulo)
**Arquivos:**
- `superz/search/__init__.py`
- `superz/search/tavily_client.py` — `TavilySearchClient`
- `superz/search/pubmed_client.py` — `PubMedClient` (NCBI E-utilities)
- `superz/search/bireme_client.py` — `BIREMEClient` (BVS API)
- `superz/search/scielo_client.py` — `SciELOClient`
- `superz/search/regulatory_client.py` — `RegulatoryClient` (ANVISA via Tavily)

**Criterios de conclusao:**
- [x] Tavily retorna WebSearchResponse com cache e rate limit
- [x] PubMed esearch → efetch pipeline funciona com filtros
- [x] BIREME retorna artigos em PT-BR
- [x] SciELO busca funcional
- [x] Regulatory busca ANVISA com resultado estruturado
- [x] Todos os clientes com `is_available()` para health check

---

### Fase 4 — Cliente LLM (Qwen/Ollama)
**Prioridade:** ALTA (analyze_text, summarize, translate dependem)
**Arquivos:**
- `superz/llm/__init__.py`
- `superz/llm/qwen_client.py` — `QwenClient` com fallback 72b→7b
- `superz/llm/prompts.py` — system prompts em PT-BR (analyze, summarize, translate)
- `superz/llm/url_fetcher.py` — `URLFetcher` (busca HTML de URL para summarize)

**Criterios de conclusao:**
- [x] analyze() produz TextAnalysisResult
- [x] summarize() produz SummaryResult
- [x] translate() produz TranslationResult
- [x] Fallback 72b→7b automatico
- [x] Graceful degradation sem Ollama
- [x] URL fetcher extrai texto limpo de paginas web

---

### Fase 5 — MCP Server & 6 Tools
**Prioridade:** CRITICA (ponto de integracao com WANDA)
**Arquivos:**
- `superz/mcp/__init__.py`
- `superz/mcp/server.py` — `SuperZMCPServer` com 6 tools
- `superz/mcp/schemas.py` — JSON Schemas para cada tool
- `superz/mcp/tools/__init__.py`
- `superz/mcp/tools/web_search.py`
- `superz/mcp/tools/search_medical_literature.py`
- `superz/mcp/tools/check_regulatory.py`
- `superz/mcp/tools/analyze_text.py`
- `superz/mcp/tools/summarize_document.py`
- `superz/mcp/tools/translate_to_portuguese.py`

**Criterios de conclusao:**
- [x] `list_tools()` retorna 6 tools com JSON Schema correto
- [x] `call_tool()` roteia para handler correto
- [x] Cada tool retorna TextContent com JSON serializado
- [x] Erros tratados — nunca crash, sempre resposta estruturada

---

### Fase 6 — FastAPI REST & Endpoints
**Prioridade:** ALTA (health, info, MCP transport)
**Arquivos:**
- `superz/api/__init__.py`
- `superz/api/app.py` — FastAPI app com /health, /info, MCP SSE

**Criterios de conclusao:**
- [x] `GET /api/v1/health` retorna status de cada componente
- [x] `GET /api/v1/info` retorna metadata do modulo
- [x] MCP over SSE transport funcional
- [x] CORS configurado para integracao com portal

---

### Fase 7 — Testes (>= 25)
**Prioridade:** OBRIGATORIA (criterio de aceitacao)
**Arquivos:**
- `tests/__init__.py`
- `tests/conftest.py` — fixtures globais (mock Tavily, mock Ollama, mock Redis)
- `tests/test_tavily_client.py` (4 testes)
- `tests/test_pubmed_client.py` (4 testes)
- `tests/test_bireme_client.py` (2 testes)
- `tests/test_qwen_client.py` (5 testes)
- `tests/test_mcp_tools.py` (6 testes)
- `tests/test_api.py` (3 testes)
- `tests/test_cache.py` (3 testes)
- `tests/test_rate_limiter.py` (2 testes)
- **Total: 29 testes**

**Criterios de conclusao:**
- [x] >= 25 testes passando
- [x] Cobertura >= 80%
- [x] Testes rodam sem dependencias externas (Redis, Tavily, Ollama mockados)

---

## 3. Dependencias e Riscos

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| Tavily API key nao configurada | web_search e check_regulatory indisponiveis | Graceful degradation com mensagem clara |
| Ollama nao instalado/modelo nao baixado | analyze, summarize, translate falham | Fallback 72b→7b + mensagem de erro estruturada |
| Redis indisponivel | Cache perde funcao | Cache bypassed automaticamente — funciona sem Redis |
| PubMed/BIREME fora | Literatura indisponivel | Retorna resultado parcial + aviso de qual base falhou |
| Python < 3.11 | Type hints modernas falham | Dockerfile garante 3.11-slim |

---

## 4. Checklist Final

- [ ] 6 MCP Tools implementadas e documentadas com JSON Schema
- [ ] `web_search` retorna resultados via Tavily com relevance_score e URL
- [ ] `search_medical_literature` busca PubMed e BVS com filtros
- [ ] `check_regulatory` retorna status ANVISA/ANS
- [ ] `analyze_text` usa Qwen2.5 local via Ollama (graceful degradation sem Ollama)
- [ ] `summarize_document` suporta texto direto e URL
- [ ] `translate_to_portuguese` com terminologia medica preservada
- [ ] Sem Tavily: graceful degradation com mensagem clara
- [ ] `GET /api/v1/health` e `GET /api/v1/info` funcionando
- [ ] `docker compose up` standalone
- [ ] >= 25 testes
- [ ] Cobertura >= 80%

---

## 5. Notas de Implementacao

1. **MCP SDK**: usar `mcp` package (Anthropic) — SSE transport sobre HTTP
2. **Tavily**: usar `tavily-python` SDK — sync client wrapped em asyncio.to_thread()
3. **PubMed XML**: parsear com `lxml.etree` — mais rapido que BeautifulSoup para XML
4. **Cache Hash**: SHA256 de (query + params_normalizados) como chave Redis
5. **Token Bucket**: rate limiter em memoria (nao precisa de Redis) — simplifica deploy
6. **Retry**: usar `tenacity` com exponential backoff para APIs externas
7. **URL Fetcher**: httpx GET + BeautifulSoup para extrair texto de paginas web
