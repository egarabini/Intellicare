# PIERRE — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-pierre (porta 8009)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| MCP Server | mcp (Anthropic MCP SDK) |
| PubMed | Entrez API (biopython ou requests direto) |
| Web Search | Tavily SDK (com fallback httpx + DuckDuckGo) |
| LLM Sintese | httpx → Ollama (qwen2.5:7b) |
| Cache | Redis (intellicare-core) |
| Testes | pytest + respx (mock HTTP) |

---

## 2. Estrutura de Diretorios

```
intellicare-pierre/
├── pierre/
│   ├── api/
│   │   ├── app.py              # FastAPI + MCP SSE endpoint
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       └── analyze.py      # BaseAgent contract
│   ├── mcp/
│   │   ├── server.py           # MCP Server com tools registradas
│   │   └── tools/
│   │       ├── pubmed.py       # search_pubmed tool
│   │       ├── web_search.py   # search_web tool
│   │       ├── bvs.py          # search_bvs tool
│   │       └── synthesize.py   # synthesize tool
│   ├── services/
│   │   ├── pubmed_service.py   # NCBI Entrez API client
│   │   ├── tavily_service.py   # Tavily + fallback
│   │   ├── bvs_service.py      # BVS/BIREME API client
│   │   └── synthesis_service.py # Ollama LLM synthesis
│   ├── models/
│   │   ├── article.py          # PubMedArticle, WebResult
│   │   └── synthesis.py        # SynthesisResult
│   └── config.py
├── tests/
│   ├── conftest.py
│   ├── test_pubmed_service.py
│   ├── test_bvs_service.py
│   ├── test_synthesis_service.py
│   ├── test_mcp_tools.py
│   └── test_routes.py
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## 3. MCP Server — Definicao das Tools

```python
# pierre/mcp/server.py
from mcp import Server
from mcp.types import Tool, TextContent

server = Server("pierre")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_pubmed",
            description="Busca artigos cientificos no PubMed/MEDLINE",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query de busca"},
                    "max_results": {"type": "integer", "default": 5},
                    "years_back": {"type": "integer", "default": 5,
                                  "description": "Filtrar artigos dos ultimos N anos"},
                    "study_types": {
                        "type": "array",
                        "items": {"type": "string",
                                  "enum": ["meta-analysis", "systematic-review",
                                           "randomized-controlled-trial", "review"]},
                        "description": "Tipos de estudo preferidos"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_bvs",
            description="Busca na Biblioteca Virtual em Saude (literatura brasileira/latina)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "language": {"type": "string", "default": "pt",
                                "enum": ["pt", "es", "en"]},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_web",
            description="Busca em portais medicos confiáveis (diretrizes, protocolos)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "focus": {"type": "string",
                             "enum": ["guidelines", "protocols", "general"],
                             "default": "guidelines"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="synthesize",
            description="Sintetiza evidencias de multiplas fontes em resposta clinica",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string",
                                "description": "Pergunta clinica original"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Lista de artigos/resultados para sintetizar"
                    }
                },
                "required": ["question", "sources"]
            }
        )
    ]
```

---

## 4. Endpoints FastAPI

```
GET  /api/v1/health          → HealthCheck
GET  /api/v1/info            → ModuleInfo
POST /api/v1/analyze         → AnalysisResponse (BaseAgent)
GET  /mcp/sse                → SSE stream (MCP protocol)
POST /mcp/message            → MCP message handler
```

---

## 5. Servicos Externos

### 5.1 NCBI Entrez (PubMed)
```python
# Base URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
# Endpoints:
#   esearch.fcgi?db=pubmed&term={query}&retmax={n}&sort=relevance
#   efetch.fcgi?db=pubmed&id={pmids}&rettype=abstract&retmode=json
# API Key (opcional): NCBI_API_KEY — eleva rate limit de 3 para 10 req/s
# Cache: Redis TTL 3600 (1h)
```

### 5.2 BVS/BIREME
```python
# Base URL: https://api.bvsalud.org/v1/
# Endpoint: /search?q={query}&lang={lang}&count={n}
# Sem auth necessaria
# Cache: Redis TTL 3600 (1h)
```

### 5.3 Tavily (Web Search)
```python
# SDK: from tavily import TavilyClient
# Fallback se TAVILY_API_KEY nao configurada:
#   DuckDuckGo via httpx (sem auth, rate limited)
# Include domains: cochrane.org, scielo.br, cfm.org.br, sbc.org.br, sbdiabetes.org.br
# Exclude domains: wikipedia.org, news sites
```

### 5.4 Ollama (Sintese)
```python
# URL: http://ollama:11434
# Modelo: qwen2.5:7b (default) ou llama3.2:3b (fallback mais rapido)
# Prompt system: "Voce e um especialista em medicina baseada em evidencias.
#                 Sintetize as evidencias de forma clara e objetiva para
#                 um profissional de saude, indicando nivel de evidencia."
# Se Ollama offline: retornar fontes sem sintese (graceful degradation)
```

---

## 6. Modelos Pydantic

```python
class PubMedArticle(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str]
    authors: list[str]
    journal: str
    year: int
    doi: Optional[str]
    study_type: Optional[str]     # "meta-analysis", "review", etc.
    evidence_level: Optional[str] # "I", "II", "III", "IV"

class WebResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str                    # "pubmed", "bvs", "tavily", "duckduckgo"
    published_date: Optional[str]
    relevance_score: Optional[float]

class SynthesisResult(BaseModel):
    question: str
    synthesis: str                 # Texto sintetizado pelo LLM
    sources: list[WebResult | PubMedArticle]
    evidence_quality: str          # "high", "moderate", "low", "insufficient"
    model_used: str
    synthesis_time_ms: int
```

---

## 7. Configuracao (environment)

```env
# Opcional mas recomendado
NCBI_API_KEY=              # Eleva rate limit PubMed
TAVILY_API_KEY=            # Habilita Tavily (se vazio, usa DuckDuckGo)

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=30

# Cache
REDIS_URL=redis://redis:6379/0
CACHE_TTL_PUBMED=3600
CACHE_TTL_BVS=3600

# API
PORT=8000
LOG_LEVEL=INFO
```

---

## 8. Testes

```python
# Estrategia: respx para mockar todas as chamadas HTTP externas

# test_pubmed_service.py
test_search_retorna_artigos()
test_search_com_filtro_tipo_estudo()
test_search_retorna_cache_hit()
test_pubmed_offline_retorna_cache_ou_erro_gracioso()

# test_mcp_tools.py
test_list_tools_retorna_4_tools()
test_search_pubmed_tool_funciona()
test_synthesize_tool_funciona_sem_ollama()  # deve funcionar sem LLM

# test_routes.py
test_health_ok()
test_analyze_retorna_artigos()
test_mcp_sse_endpoint_acessivel()
```

---

*PIERRE v1.0 — Especificacoes Tecnicas — 2026-03-04*
