# intellicare-pierre — Especificacao Tecnica

**Modulo:** `intellicare-pierre` (PIERRE)
**Versao:** 1.0 (IntelliCare V5)
**Porta:** 8009
**Data:** 2026-02-16
**DEV responsavel:** DEV-PIERRE (independente — nao interfere com outros modulos)

---

## 1. Stack Tecnologico

| Componente | Tecnologia | Versao | Proposito |
|-----------|-----------|--------|-----------|
| Runtime | Python | 3.11+ | Runtime padrao do ecossistema |
| Framework API | FastAPI | 0.115+ | REST endpoints + /health + /info |
| Servidor ASGI | Uvicorn | 0.30+ | ASGI server |
| MCP SDK | `mcp` (Anthropic) | 1.x | Expor tools como MCP Server |
| Web Search | **Tavily Python SDK** | 0.3+ | Busca web curada para agentes LLM |
| HTTP Client | **httpx** | 0.27+ | Chamadas HTTP async para APIs externas |
| LLM Analysis | **Qwen2.5-72B** via Ollama | latest | Analise, sintese, traducao |
| LLM fallback | **Qwen2.5-7B** via Ollama | latest | Modelo menor para ambientes limitados |
| Cache | **Redis** | 7.x | Cache de queries (Tavily e pago) |
| Rate Limiter | **slowapi** | 0.1+ | Rate limiting no FastAPI |
| Validacao | Pydantic | 2.x | Schemas de input/output |
| Testes | pytest + pytest-asyncio | latest | Testes com mocks de APIs externas |
| Lint/Format | ruff | latest | Qualidade de codigo |

### Sobre as escolhas tecnicas

**Tavily vs alternativas:**
- Tavily e a API de busca web mais adotada no ecossistema de agentes LLM (LangChain, LlamaIndex)
- Retorna conteudo limpo (sem ads, sem boilerplate), com relevance scoring e answer sintetico
- Alternativa gratuita: DuckDuckGo (via `duckduckgo-search`) — sem API key, mas qualidade inferior

**Qwen2.5-72B vs alternativas:**
- Melhor modelo open-source para PT-BR em analise de textos medicos (supera LLaMA3 em PT-BR)
- Roda via Ollama — sem custo de API, privacidade total
- Fallback para Qwen2.5-7B se hardware limitado

**PubMed NCBI E-utilities:**
- API gratuita, sem autenticacao para uso educacional/pesquisa
- Com API key (gratuita no NCBI): 10 req/s vs 3 req/s sem key
- Retorna XML ou JSON — usar formato JSON

---

## 2. Estrutura de Diretorios

```
intellicare-pierre/
├── pierre/                                 # Modulo principal
│   ├── __init__.py
│   ├── config.py                           # PierreConfig (dataclass)
│   │
│   ├── api/                                # REST API
│   │   ├── __init__.py
│   │   └── app.py                         # FastAPI app
│   │
│   ├── mcp/                               # MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                      # MCPServer
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── web_search.py              # Tool 1
│   │   │   ├── search_medical_literature.py # Tool 2
│   │   │   ├── check_regulatory.py        # Tool 3
│   │   │   ├── analyze_text.py            # Tool 4
│   │   │   ├── summarize_document.py      # Tool 5
│   │   │   └── translate_to_portuguese.py # Tool 6
│   │   └── schemas.py
│   │
│   ├── search/                            # Adaptadores de busca
│   │   ├── __init__.py
│   │   ├── tavily_client.py               # TavilySearchClient
│   │   ├── pubmed_client.py               # PubMedClient (NCBI E-utilities)
│   │   ├── bireme_client.py               # BIREMEClient (BVS/BIREME API)
│   │   ├── scielo_client.py               # SciELOClient (API SciELO)
│   │   └── regulatory_client.py           # RegulatoryClient (ANVISA via Tavily)
│   │
│   ├── llm/                               # LLM Integration
│   │   ├── __init__.py
│   │   ├── qwen_client.py                 # QwenClient (Ollama)
│   │   ├── prompts.py                     # System prompts em PT-BR
│   │   └── url_fetcher.py                 # Busca conteudo de URL para summarize
│   │
│   ├── cache/                             # Cache Redis
│   │   ├── __init__.py
│   │   └── search_cache.py                # SearchCache
│   │
│   ├── rate_limiter/                      # Rate limiting
│   │   ├── __init__.py
│   │   └── limiter.py                     # TavilyRateLimiter
│   │
│   └── models.py                          # Dataclasses de output
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tavily_client.py              # Com mocks
│   ├── test_pubmed_client.py              # Com mocks
│   ├── test_bireme_client.py              # Com mocks
│   ├── test_qwen_client.py                # Com mocks
│   ├── test_mcp_tools.py                  # 6 tools com mocks
│   ├── test_api.py
│   ├── test_cache.py
│   └── test_rate_limiter.py
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── docs/
    ├── ESPECIFICACAO_FUNCIONAL.md
    └── ESPECIFICACAO_TECNICA.md
```

---

## 3. Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SearchStatus(str, Enum):
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    RATE_LIMITED = "rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str                    # Conteudo limpo da pagina
    published_date: Optional[str]
    relevance_score: float          # 0.0 a 1.0
    source_type: str                # "guideline" | "article" | "news" | "regulatory" | "other"


@dataclass
class WebSearchResponse:
    status: SearchStatus
    results: list[WebSearchResult]
    answer: Optional[str]           # Resposta sintetica do Tavily
    total_results: int
    query_time_ms: int
    cached: bool = False            # True se servido do cache Redis


@dataclass
class MedicalArticle:
    pmid: Optional[str]             # PubMed ID
    title: str
    authors: list[str]
    journal: str
    year: int
    abstract: str
    conclusion: Optional[str]       # Extraido do abstract
    study_type: str                 # "rct" | "meta_analysis" | "systematic_review" | "guideline" | "other"
    url: str
    evidence_level: Optional[str]   # "A" | "B" | "C" | "D"
    doi: Optional[str]


@dataclass
class LiteratureSearchResponse:
    status: SearchStatus
    articles: list[MedicalArticle]
    total_found: int
    returned: int
    database_used: str
    query_time_ms: int
    cached: bool = False


@dataclass
class RegulatoryResult:
    title: str
    authority: str                  # "ANVISA" | "ANS" | "CFM" | "COFEN"
    document_type: str
    status: Optional[str]           # "aprovado" | "suspenso" | "cancelado" | "em_analise"
    publication_date: Optional[str]
    url: str
    key_information: Optional[str]
    contraindications: Optional[str]


@dataclass
class TextAnalysisResult:
    analysis: str                   # Texto da analise
    key_points: list[str]           # Bullet points principais
    confidence: float
    model_used: str
    processing_time_ms: int


@dataclass
class SummaryResult:
    summary: str
    key_actions: list[str]
    source_url: Optional[str]
    document_title: Optional[str]
    summary_type: str
    processing_time_ms: int


@dataclass
class TranslationResult:
    translated_text: str
    source_language_detected: str
    medical_terms_preserved: list[str]
    confidence: float
    processing_time_ms: int
```

---

## 4. Implementacao dos Componentes

### 4.1 TavilySearchClient

```python
class TavilySearchClient:
    """
    Cliente para Tavily API — busca web curada para agentes LLM.
    Documentacao: https://docs.tavily.com

    Rate limit padrao: 100 queries/hora (configuravel)
    Cache: 6h por query identica (Redis)
    Fallback: DuckDuckGo (sem API key, qualidade menor)
    """

    def __init__(self, api_key: str, cache: SearchCache, rate_limiter: TavilyRateLimiter):
        from tavily import TavilyClient
        self._client = TavilyClient(api_key=api_key)
        self._cache = cache
        self._rate_limiter = rate_limiter

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",   # "basic" | "advanced"
        include_domains: list[str] = None,
        exclude_domains: list[str] = None,
        time_range: str = None,           # "1d" | "1w" | "1m" | "1y"
    ) -> WebSearchResponse:
        """
        1. Verificar cache Redis
        2. Verificar rate limit
        3. Chamar Tavily API (async via executor)
        4. Parsear response
        5. Salvar no cache
        """

    async def is_available(self) -> bool:
        """Tavily health check."""
```

### 4.2 PubMedClient

```python
class PubMedClient:
    """
    Cliente para PubMed via NCBI E-utilities API.
    Documentacao: https://www.ncbi.nlm.nih.gov/books/NBK25500/

    Endpoints usados:
    - esearch.fcgi — busca de IDs
    - efetch.fcgi — busca de abstracts por ID
    - esummary.fcgi — metadados dos artigos

    API Key: gratuita em https://www.ncbi.nlm.nih.gov/account/
    Sem API key: 3 req/s | Com API key: 10 req/s
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        study_type: str = "any",
        date_from: Optional[str] = None,  # YYYY
        language: str = "any",
    ) -> LiteratureSearchResponse:
        """
        Pipeline:
        1. esearch: query → list[pmid]
        2. efetch: list[pmid] → abstracts XML
        3. Parsear XML → list[MedicalArticle]
        4. Extrair conclusao do abstract (ultima sentenca ou secao Conclusion)
        5. Classificar study_type via titulo/abstract keywords
        """

    def _build_pubmed_query(
        self,
        query: str,
        study_type: str,
        date_from: Optional[str],
        language: str,
    ) -> str:
        """
        Constroi query PubMed com filtros:
        - study_type: "Randomized Controlled Trial[pt]", "Meta-Analysis[pt]", etc.
        - language: "English[la]", "Portuguese[la]", etc.
        - date: "2020/01/01:2026/12/31[dp]"
        """

    def _classify_evidence_level(self, study_type: str) -> str:
        """
        A: meta_analysis, systematic_review, guideline
        B: rct
        C: cohort, case_control
        D: case_report, expert_opinion
        """
```

### 4.3 BIREMEClient

```python
class BIREMEClient:
    """
    Cliente para BVS/BIREME API (Biblioteca Virtual em Saude).
    Foco em literatura em portugues e espanhol — essencial para guidelines brasileiros.

    Documentacao: https://bvsalud.org/developers/
    API: iAH (Interface de busca DeCS)
    Base URL: https://pesquisa.bvsalud.org/portal/api/v2/
    """

    BASE_URL = "https://pesquisa.bvsalud.org/portal/api/v2/"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "pt",
        database: str = "MEDLINE,LILACS,IBECS",
    ) -> LiteratureSearchResponse:
        """
        Busca na BVS com filtros de idioma e base.
        Retorna artigos em PT-BR que o PubMed pode nao ter.
        """
```

### 4.4 QwenClient

```python
class QwenClient:
    """
    Cliente para Qwen2.5 via Ollama.
    Modelo primario: qwen2.5:72b (melhor qualidade)
    Modelo fallback: qwen2.5:7b (mais rapido, menor qualidade)

    Timeout: 120s para 72b, 30s para 7b
    """

    SYSTEM_PROMPTS = {
        "analyze": """
Voce e PIERRE, assistente de pesquisa medica do IntelliCare.
Sua funcao e analisar textos medicos e extrair informacoes precisas e acionaveis.

REGRAS:
- Baseie-se APENAS no texto fornecido — nunca adicione informacoes externas
- Se o texto nao contem a informacao pedida: diga claramente
- Use terminologia medica em portugues brasileiro
- Seja conciso: medicos precisam de informacao direta, nao dissertacoes
- Cite trechos do texto para embasar suas afirmacoes
""",
        "summarize": """
Voce e PIERRE, especialista em sintese de documentos medicos.
Gere resumos concisos priorizando pontos de acao pratica para clinicos.

FORMATO DO RESUMO:
1. Ponto principal (1 sentenca)
2. Pontos de acao (lista bulleted, maximo 5)
3. Contexto/limitacoes (1 sentenca, se relevante)
""",
        "translate": """
Voce e um especialista em traducao medica PT-BR.
Traduza textos medicos mantendo a terminologia tecnica correta em portugues brasileiro.

REGRAS:
- Preserve termos tecnicos sem traducao quando nao ha equivalente consolidado (ex: SGLT2, eGFR)
- Use nomenclatura ANVISA/CFM quando aplicavel (ex: "bupropiona" nao "bupropion")
- Clareza e precisao acima de literalidade
"""
    }

    async def analyze(
        self,
        text: str,
        instruction: str,
        output_format: str = "paragraph",
        max_tokens: int = 500,
    ) -> TextAnalysisResult:
        """
        Analise com prompt de sistema "analyze".
        """

    async def summarize(
        self,
        text: str,
        summary_type: str,
        max_sentences: int,
        target_audience: str,
    ) -> SummaryResult:
        """Resumo com prompt de sistema "summarize"."""

    async def translate(
        self,
        text: str,
        source_language: str,
        preserve_medical_terms: bool = True,
    ) -> TranslationResult:
        """Traducao com prompt de sistema "translate"."""

    async def is_available(self, model: str = "qwen2.5:72b") -> bool:
        """Verifica se Ollama tem o modelo disponivel."""
```

### 4.5 SearchCache (Redis)

```python
class SearchCache:
    """
    Cache Redis para queries de busca.
    Evita cobrar Tavily para queries identicas dentro do TTL.

    Prefixos:
    - "pierre:tavily:{hash}" → WebSearchResponse (TTL 6h)
    - "pierre:pubmed:{hash}" → LiteratureSearchResponse (TTL 24h)
    - "pierre:bireme:{hash}" → LiteratureSearchResponse (TTL 24h)
    - "pierre:regulatory:{hash}" → list[RegulatoryResult] (TTL 12h)

    Hash: SHA256(query + params relevantes)
    """

    TTLS = {
        "tavily": 6 * 3600,       # 6h — web muda mais rapido
        "pubmed": 24 * 3600,      # 24h — artigos nao mudam
        "bireme": 24 * 3600,
        "regulatory": 12 * 3600,  # 12h — regulatorio muda menos
    }

    async def get(self, source: str, query: str, params: dict) -> Optional[dict]: ...
    async def set(self, source: str, query: str, params: dict, data: dict) -> None: ...
    async def is_available(self) -> bool: ...
```

### 4.6 TavilyRateLimiter

```python
class TavilyRateLimiter:
    """
    Rate limiter em memoria para Tavily API.
    Usa algoritmo token bucket.

    Padrao: 100 tokens/hora, 1 token por query.
    Configuravel via env: PIERRE_TAVILY_RATE_LIMIT_PER_HOUR
    """

    async def acquire(self) -> bool:
        """
        Tenta adquirir 1 token.
        Retorna True se pode fazer a query, False se limite atingido.
        """

    async def get_status(self) -> dict:
        """{"tokens_remaining": 87, "reset_at": "...", "limit_per_hour": 100}"""
```

---

## 5. MCP Server

```python
# pierre/mcp/server.py

class PierreMCPServer:
    """
    MCP Server para intellicare-pierre.
    Expoe 6 tools via protocolo MCP sobre HTTP SSE.
    """

    def __init__(self, config: PierreConfig):
        self._server = Server("intellicare-pierre")
        # Inicializar clientes
        self._tavily = TavilySearchClient(config.tavily_api_key, ...)
        self._pubmed = PubMedClient(config.pubmed_api_key)
        self._bireme = BIREMEClient()
        self._qwen = QwenClient(config.ollama_url, config.llm_model)
        self._cache = SearchCache(config.redis_url)
        self._rate_limiter = TavilyRateLimiter(config.tavily_rate_limit)
        self._url_fetcher = URLFetcher()
        self._register_handlers()

    def _register_handlers(self):
        @self._server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="web_search",
                    description="Busca web em tempo real via Tavily. Use para encontrar guidelines "
                                "atualizados, informacoes recentes de medicamentos, noticias regulatorias "
                                "ou qualquer informacao medica nao coberta pelos outros agentes.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Termos de busca"},
                            "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                            "search_depth": {
                                "type": "string",
                                "enum": ["basic", "advanced"],
                                "default": "advanced"
                            },
                            "include_domains": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Dominios prioritarios (ex: pubmed.ncbi.nlm.nih.gov)"
                            },
                            "time_range": {
                                "type": "string",
                                "enum": ["1d", "1w", "1m", "1y"],
                                "description": "Filtro de data dos resultados"
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="search_medical_literature",
                    description="Busca em PubMed e BVS/BIREME (literatura medica indexada). "
                                "Use para encontrar evidencias cientificas, ensaios clinicos, "
                                "revisoes sistematicas e meta-analises.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "database": {
                                "type": "string",
                                "enum": ["pubmed", "bireme", "scielo", "all"],
                                "default": "pubmed"
                            },
                            "max_results": {"type": "integer", "default": 5},
                            "study_type": {
                                "type": "string",
                                "enum": ["rct", "systematic_review", "meta_analysis",
                                         "guideline", "any"],
                                "default": "any"
                            },
                            "date_from": {"type": "string", "description": "Ex: 2020"},
                            "language": {
                                "type": "string",
                                "enum": ["any", "pt", "en", "es"],
                                "default": "any"
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="check_regulatory",
                    description="Verifica status regulatorio de medicamentos e dispositivos no Brasil. "
                                "Use para confirmar aprovacao ANVISA, cobertura ANS ou regulamentacao CFM.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Nome do medicamento ou procedimento"},
                            "authority": {
                                "type": "string",
                                "enum": ["anvisa", "ans", "cfm", "cofen", "all"],
                                "default": "all"
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["bula", "resolucao", "nota_tecnica", "lista_cobertura", "any"],
                                "default": "any"
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="analyze_text",
                    description="Analise profunda de texto medico via LLM local (Qwen2.5). "
                                "Use para extrair informacoes especificas, responder perguntas sobre "
                                "um texto, comparar documentos ou sintetizar conteudo complexo.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Texto a analisar"},
                            "instruction": {"type": "string", "description": "O que extrair ou analisar"},
                            "output_format": {
                                "type": "string",
                                "enum": ["bullet_points", "paragraph", "structured_json", "table"],
                                "default": "bullet_points"
                            },
                            "max_tokens": {"type": "integer", "default": 500},
                        },
                        "required": ["text", "instruction"],
                    },
                ),
                Tool(
                    name="summarize_document",
                    description="Resume documento longo (guideline, artigo, relatorio) em formato "
                                "clinicamente acionavel. Aceita texto direto ou URL publica.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Texto do documento"},
                            "url": {"type": "string", "description": "URL alternativa ao texto"},
                            "summary_type": {
                                "type": "string",
                                "enum": ["executive", "clinical_action", "methodology", "full_abstract"],
                                "default": "clinical_action"
                            },
                            "max_sentences": {"type": "integer", "default": 5},
                            "target_audience": {
                                "type": "string",
                                "enum": ["medico", "gestor", "paciente", "tecnico"],
                                "default": "medico"
                            },
                        },
                        "required": [],   # Aceita text OU url
                    },
                ),
                Tool(
                    name="translate_to_portuguese",
                    description="Traduz textos medicos para PT-BR com terminologia medica correta. "
                                "Preserva termos tecnicos sem traducao consolidada.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "source_language": {
                                "type": "string",
                                "enum": ["en", "es", "fr", "auto"],
                                "default": "auto"
                            },
                            "context": {
                                "type": "string",
                                "enum": ["medical_guideline", "research_article",
                                         "patient_information", "regulatory"],
                                "default": "medical_guideline"
                            },
                            "preserve_medical_terms": {"type": "boolean", "default": True},
                        },
                        "required": ["text"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            import json
            from mcp.types import TextContent
            router = {
                "web_search": self._web_search,
                "search_medical_literature": self._search_medical_literature,
                "check_regulatory": self._check_regulatory,
                "analyze_text": self._analyze_text,
                "summarize_document": self._summarize_document,
                "translate_to_portuguese": self._translate_to_portuguese,
            }
            if name not in router:
                raise ValueError(f"Tool desconhecida: {name}")
            result = await router[name](arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
```

---

## 6. Configuracao

### 6.1 PierreConfig

```python
@dataclass
class PierreConfig:
    # Tavily Web Search
    tavily_api_key: str = ""                     # OBRIGATORIO para web_search
    tavily_rate_limit_per_hour: int = 100
    tavily_search_depth: str = "advanced"

    # PubMed
    pubmed_api_key: str = ""                     # Opcional — aumenta rate limit
    pubmed_max_results: int = 10

    # Qwen / Ollama
    ollama_url: str = "http://ollama:11434"
    llm_model: str = "qwen2.5:72b"
    llm_model_fallback: str = "qwen2.5:7b"
    llm_timeout_seconds: int = 120               # 72b pode ser lento
    llm_max_tokens: int = 500

    # Redis Cache
    redis_url: str = "redis://redis:6379/1"      # DB 1 para nao conflitar com outros modulos
    cache_enabled: bool = True

    # Limites
    max_text_length_chars: int = 100_000         # Para analyze_text — evitar tokens excessivos

    @classmethod
    def from_env(cls) -> "PierreConfig":
        import os
        return cls(
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            pubmed_api_key=os.getenv("NCBI_API_KEY", ""),
            ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
            llm_model=os.getenv("PIERRE_LLM_MODEL", "qwen2.5:72b"),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379/1"),
        )
```

### 6.2 Variaveis de Ambiente (.env.example)

```env
# Tavily Web Search (OBRIGATORIO para web_search tool)
# Plano gratuito: 1000 queries/mes — https://app.tavily.com
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# NCBI PubMed (opcional — melhora rate limit de 3 para 10 req/s)
# Registro gratuito: https://www.ncbi.nlm.nih.gov/account/
NCBI_API_KEY=

# Ollama (LLM local)
OLLAMA_URL=http://ollama:11434
PIERRE_LLM_MODEL=qwen2.5:72b

# Redis (cache de queries — compartilhado se ja existir no stack)
REDIS_URL=redis://redis:6379/1

# Rate limiting Tavily
PIERRE_TAVILY_RATE_LIMIT_PER_HOUR=100

# API
PIERRE_PORT=8009
PIERRE_WORKERS=2
```

---

## 7. Docker

### 7.1 Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY . .

EXPOSE 8009

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
    CMD curl -f http://localhost:8009/api/v1/health || exit 1

CMD ["uvicorn", "pierre.api.app:app", "--host", "0.0.0.0", "--port", "8009", "--workers", "2"]
```

### 7.2 docker-compose.yml

```yaml
version: "3.9"

services:
  intellicare-superz:
    build: .
    container_name: intellicare-superz
    ports:
      - "8009:8009"
    environment:
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - NCBI_API_KEY=${NCBI_API_KEY:-}
      - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
      - PIERRE_LLM_MODEL=${PIERRE_LLM_MODEL:-qwen2.5:72b}
      - REDIS_URL=redis://redis:6379/1
      - PIERRE_PORT=8009
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    restart: unless-stopped
    networks:
      - intellicare-network

  redis:
    image: redis:7-alpine
    container_name: superz-redis
    ports:
      - "6380:6379"      # Porta diferente para nao conflitar com redis de outros modulos
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - intellicare-network

networks:
  intellicare-network:
    name: intellicare-network
```

---

## 8. Tratamento de Erros e Graceful Degradation

```python
# Hierarquia de erros

class SuperZError(Exception):
    """Base"""

class TavilyUnavailableError(SuperZError):
    """Tavily API nao configurada ou fora do ar"""

class TavilyRateLimitError(SuperZError):
    """Rate limit atingido"""

class LLMUnavailableError(SuperZError):
    """Ollama indisponivel"""

class NoResultsFoundError(SuperZError):
    """Query valida mas sem resultados"""


# Politica de degradacao:
#
# Tavily indisponivel:
#   web_search → retorna status="source_unavailable", results=[], mensagem clara
#
# Ollama indisponivel:
#   analyze_text → retorna error estruturado (nao crash)
#   summarize_document → retorna apenas os primeiros 500 chars do texto (sem LLM)
#   translate_to_portuguese → retorna texto original com aviso
#
# Redis indisponivel:
#   Cache ignorado — todas as queries vao para as APIs diretamente
#
# PubMed/BIREME temporariamente fora:
#   Retorna o que conseguiu + aviso de qual base falhou
```

---

## 9. Plano de Testes (meta: >= 25 testes)

| Arquivo | Testes | O que cobre |
|---------|--------|------------|
| `test_tavily_client.py` | 4 | Search success, no results, rate limited, cache hit |
| `test_pubmed_client.py` | 4 | Search success, date filter, study_type filter, unavailable |
| `test_bireme_client.py` | 2 | Search PT, unavailable fallback |
| `test_qwen_client.py` | 5 | analyze, summarize, translate, unavailable, fallback model |
| `test_mcp_tools.py` | 6 | Uma tool por teste com mocks completos |
| `test_api.py` | 3 | /health (Tavily ok), /health (Tavily indisponivel), /info |
| `test_cache.py` | 3 | Cache hit, cache miss, Redis indisponivel |
| `test_rate_limiter.py` | 2 | Limite atingido, limite restaurado |
| **TOTAL** | **29** | Cobertura > 80% |

### Convencao de Mocks
```python
# conftest.py
@pytest.fixture
def mock_tavily(mocker):
    """Mock TavilyClient para nao fazer chamadas reais."""
    return mocker.patch("superz.search.tavily_client.TavilyClient")

@pytest.fixture
def mock_ollama(mocker):
    """Mock Ollama para nao depender de instancia local."""
    return mocker.patch("superz.llm.qwen_client.httpx.AsyncClient")
```

---

## 10. Ordem de Implementacao para o DEV

```
1. Estrutura base (pyproject.toml, config, Dockerfile, docker-compose)   [Dia 1]
2. SearchCache (Redis) + TavilyRateLimiter (+ tests)                      [Dia 2]
3. TavilySearchClient (+ tests)                                           [Dia 3]
4. PubMedClient (+ tests)                                                 [Dia 4]
5. BIREMEClient + SciELOClient (+ tests)                                  [Dia 5]
6. QwenClient + prompts + URLFetcher (+ tests)                            [Dia 6]
7. MCP Server — 6 tools (+ tests)                                         [Dia 7-8]
8. FastAPI endpoints + /health + /info + /mcp/* (+ tests)                 [Dia 9]
9. RegulatoryClient (Tavily focado em ANVISA/ANS) (+ tests)               [Dia 10]
10. Integracao final + README                                             [Dia 11]
```

---

## 11. pyproject.toml (dependencias principais)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
mcp = "^1.0.0"               # MCP SDK Anthropic
tavily-python = "^0.3.0"     # Tavily SDK
httpx = "^0.27.0"            # HTTP async (PubMed, BIREME)
pydantic = "^2.0.0"
redis = "^5.0.0"
slowapi = "^0.1.9"           # Rate limiting FastAPI
beautifulsoup4 = "^4.12.0"   # Parse HTML de URLs (summarize)
lxml = "^5.0.0"              # Parse XML PubMed
tenacity = "^8.2.0"          # Retry com backoff

[tool.poetry.dev-dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
ruff = "^0.4.0"
```
