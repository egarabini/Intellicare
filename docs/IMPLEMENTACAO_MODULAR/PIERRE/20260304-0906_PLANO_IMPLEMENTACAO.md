# PIERRE — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 1.0.0
**Estimativa Total:** 2-3 dias
**Prioridade:** ONDA 1 — Quick Win (pos-ZILDA)

---

## Estado Atual

Estrutura de pastas criada, sem implementacao core. Os arquivos existentes
sao scaffolding inicial. Toda a logica de negocio precisa ser implementada.

```
intellicare-pierre/
├── pierre/api/app.py       # Scaffolding OK
├── pierre/api/routes/      # health, info, analyze — implementar
├── tests/                  # Estrutura existe, testes a criar
└── pyproject.toml          # Verificar dependencias
```

---

## Fase 1 — Setup e Dependencias (Dia 1, manha) — ~2h

### Tarefa 1.1 — Atualizar pyproject.toml
```toml
[project]
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]",
    "httpx>=0.27",
    "mcp>=1.0",         # Anthropic MCP SDK
    "pydantic>=2.0",
    "pydantic-settings",
    "redis[hiredis]",
    "biopython",        # Para Entrez API (opcional, pode usar httpx direto)
    "tavily-python",    # Tavily SDK (opcional, fallback se sem key)
    "intellicare-core @ ../intellicare-core",
]
```

- [ ] Atualizar `pyproject.toml`
- [ ] `pip install -e ".[dev]"` sem erros
- [ ] `pytest --co -q` sem erros de coleta

### Tarefa 1.2 — Criar config.py
```python
# pierre/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ncbi_api_key: str = ""
    tavily_api_key: str = ""
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout: int = 30
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_pubmed: int = 3600
    port: int = 8000
    log_level: str = "INFO"
```

- [ ] Criar `pierre/config.py`
- [ ] Criar `pierre/__init__.py` e `pierre/api/__init__.py`

---

## Fase 2 — Implementar Servicos (Dia 1, tarde + Dia 2, manha) — ~6h

### Tarefa 2.1 — PubMed Service (~2h)
```python
# pierre/services/pubmed_service.py
import httpx
from pierre.models.article import PubMedArticle

class PubMedService:
    ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    async def search(self, query: str, max_results: int = 5,
                    years_back: int = 5) -> list[PubMedArticle]:
        # 1. esearch → lista de PMIDs
        # 2. efetch → abstracts dos PMIDs
        # 3. Parsear XML/JSON em PubMedArticle
        # 4. Cache Redis
        ...
```

- [ ] Implementar `pubmed_service.py` com cache Redis
- [ ] Testar manualmente: `asyncio.run(service.search("hipertensao tratamento"))`

### Tarefa 2.2 — BVS Service (~1h)
```python
# pierre/services/bvs_service.py
async def search(self, query: str, lang: str = "pt",
                max_results: int = 5) -> list[WebResult]:
    url = "https://api.bvsalud.org/v1/search"
    # params: q={query}, lang={lang}, count={max_results}
    ...
```

- [ ] Implementar `bvs_service.py`
- [ ] Testar: busca em portugues retorna resultados

### Tarefa 2.3 — Web Search Service (~1h)
```python
# pierre/services/tavily_service.py
async def search(self, query: str, focus: str = "guidelines") -> list[WebResult]:
    if self.tavily_key:
        # Usar Tavily SDK com include_domains medicos
        ...
    else:
        # Fallback: DuckDuckGo via httpx
        ...
```

- [ ] Implementar `tavily_service.py` com fallback DuckDuckGo
- [ ] Testar com e sem TAVILY_API_KEY

### Tarefa 2.4 — Synthesis Service (~1h)
```python
# pierre/services/synthesis_service.py
async def synthesize(self, question: str, sources: list) -> SynthesisResult:
    if not await self.ollama_available():
        # Graceful degradation: retornar fontes sem sintese
        return SynthesisResult(synthesis="[Sintese indisponivel]", sources=sources, ...)

    prompt = self._build_prompt(question, sources)
    # POST http://ollama:11434/api/generate
    response = await self.ollama_client.generate(prompt)
    ...
```

- [ ] Implementar `synthesis_service.py` com graceful degradation
- [ ] Testar com Ollama mockado

---

## Fase 3 — MCP Server (Dia 2, tarde) — ~3h

### Tarefa 3.1 — Implementar MCP Server
```python
# pierre/mcp/server.py
from mcp.server import Server
from mcp.server.sse import SseServerTransport

server = Server("pierre")

# Registrar tools (ver spec tecnica para schemas completos)
@server.list_tools() → retorna 4 tools
@server.call_tool()  → roteamento para servicos
```

- [ ] Criar `pierre/mcp/server.py` com 4 tools registradas
- [ ] Criar `pierre/mcp/tools/pubmed.py`, `bvs.py`, `web_search.py`, `synthesize.py`

### Tarefa 3.2 — Integrar MCP no FastAPI
```python
# pierre/api/app.py
@app.get("/mcp/sse")
async def mcp_sse(request: Request):
    transport = SseServerTransport("/mcp/message")
    await server.run(transport)

@app.post("/mcp/message")
async def mcp_message(request: Request):
    ...
```

- [ ] Endpoint SSE `/mcp/sse` respondendo
- [ ] Testar conexao MCP: `curl http://localhost:8009/mcp/sse`

---

## Fase 4 — Testes e Empacotamento (Dia 3) — ~4h

### Tarefa 4.1 — Suite de testes completa
```bash
pytest tests/ -v --cov=pierre --cov-report=term-missing
```
- [ ] `test_pubmed_service.py` — 4 testes (ver spec tecnica)
- [ ] `test_mcp_tools.py` — 3 testes
- [ ] `test_routes.py` — 3 testes (health, info, analyze)
- [ ] Meta: >= 75% cobertura, 0 falhas

### Tarefa 4.2 — Docker smoke test
```bash
docker compose up --build -d
curl http://localhost:8009/api/v1/health
```
- [ ] Container sobe sem erros
- [ ] Health check passa

### Tarefa 4.3 — Smoke test global
- [ ] Adicionar PIERRE ao `scripts/smoke_tests.py`

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| `pytest -q` → 0 falhas, >= 75% cobertura | [ ] |
| `docker compose up` → healthy | [ ] |
| `GET /api/v1/health` → 200 OK | [ ] |
| `POST /api/v1/analyze` → artigos retornados | [ ] |
| `/mcp/sse` → SSE stream ativo | [ ] |
| WANDA consegue listar tools MCP do PIERRE | [ ] |
| smoke_tests.py inclui PIERRE | [ ] |

---

## Sequencia de Dependencias

```
PIERRE RODA EM PARALELO COM ZILDA (confirmado — sem dependencia entre si).
COMUNICACAO inicia apos ZILDA ou PIERRE terminar (o que vier primeiro).
PIERRE e prerequisito para:
  - WANDA MCP integration (FASE 3.1 do roadmap)
  - Qualquer busca de evidencia do WANDA
```

---

*PIERRE v1.0 — Plano de Implementacao — 2026-03-04*
