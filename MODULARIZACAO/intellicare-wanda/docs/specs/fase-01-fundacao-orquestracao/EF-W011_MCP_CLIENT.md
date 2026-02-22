# EF-W011 — MCP Client Integration (MINERVA + PIERRE)

**Modulo:** `intellicare-wanda`
**Fase:** 1 — Fundacao e Orquestracao
**Versao:** 1.0 (IntelliCare V5.1.0)
**Data:** 2026-02-16
**Prioridade:** ALTA
**Dependencias:** EF-W001 (Module Registry), V5.0.1 (MINERVA e PIERRE implementados)

---

## 1. Objetivo

Habilitar a WANDA como **MCP Client** para consumir ferramentas dos MCP Servers do IntelliCare V5:
- **MINERVA** (`intellicare-ocr`, :8008) — extrai dados de documentos medicos
- **PIERRE** (`intellicare-superz`, :8009) — busca web, literatura medica, analise de textos

Com esta EF, a WANDA passa a ter acesso a 12 ferramentas adicionais alem dos 6 modulos HTTP existentes.

---

## 2. Contexto

```
WANDA (MCP Client)
    │
    ├── MINERVA :8008 (MCP Server)
    │     ├── extract_document(file_base64, file_type, document_type)
    │     ├── ocr_image(image_base64, image_type, enhance_quality)
    │     ├── parse_lab_result(file_content_base64 | document_text)
    │     ├── parse_discharge_summary(file_content_base64, patient_id)
    │     ├── search_documents(query, patient_id, top_k, date_from)
    │     └── index_document(document_text, document_type, patient_id, metadata)
    │
    └── PIERRE :8009 (MCP Server)
          ├── web_search(query, max_results, search_depth, include_domains)
          ├── search_medical_literature(query, database, study_type, date_from)
          ├── check_regulatory(query, authority, document_type)
          ├── analyze_text(text, instruction, output_format, max_tokens)
          ├── summarize_document(text | url, summary_type, max_sentences)
          └── translate_to_portuguese(text, source_language, context)
```

---

## 3. Modelo de Dados

### 3.1 Registro de MCP Modules (extensao de EF-W001)

```python
class MCPModuleRecord(BaseModel):
    """Registro de um MCP Server no Module Registry."""

    id: UUID = Field(default_factory=uuid4)
    module_name: str              # "intellicare-ocr" | "intellicare-superz"
    agent_name: str               # "MINERVA" | "PIERRE"
    base_url: str                 # "http://minerva:8008"
    mcp_transport: str = "sse"   # "sse" | "stdio"
    mcp_endpoint: str             # "/mcp/sse"

    # Tools disponibilizadas por este servidor MCP
    available_tools: List[MCPToolInfo] = []

    # Estado
    status: str = "healthy"       # "healthy" | "degraded" | "unavailable"
    last_health_check: Optional[datetime]
    last_tools_discovery: Optional[datetime]

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MCPToolInfo(BaseModel):
    """Descricao de uma ferramenta MCP."""

    name: str                     # "parse_lab_result"
    description: str              # Descricao para LLM usar no routing
    input_schema: Dict            # JSON Schema dos parametros
    module_name: str              # "intellicare-ocr"
    last_validated: Optional[datetime]
```

### 3.2 Registro de Chamadas MCP (auditoria)

```python
class MCPCallRecord(BaseModel):
    """Registro de chamada a ferramenta MCP."""

    id: UUID = Field(default_factory=uuid4)
    correlation_id: str           # Propagado da requisicao original

    module_name: str              # "intellicare-ocr"
    tool_name: str                # "parse_lab_result"

    input_params: Dict            # Parametros enviados (sem dados sensiveis)
    output_summary: Optional[str] # Resumo do resultado (nao o conteudo completo)

    status: str                   # "success" | "error" | "timeout"
    error_message: Optional[str]

    duration_ms: int
    tokens_used: Optional[int]    # Se MCP server reportar

    called_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 4. WandaMCPClient

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from typing import Any, Dict, List, Optional
import httpx

class WandaMCPClient:
    """
    Cliente MCP para WANDA consumir MINERVA e PIERRE.

    Usa o MCP Python SDK para conexao via HTTP SSE.
    Gerencia sessoes por servidor MCP (uma sessao por servidor).
    """

    def __init__(self, config: MCPClientConfig):
        self._config = config
        self._sessions: Dict[str, ClientSession] = {}
        self._tools_cache: Dict[str, List[Dict]] = {}  # module -> tools list
        self._lock = asyncio.Lock()

    async def connect_all(self) -> Dict[str, bool]:
        """
        Conecta a todos os MCP Servers configurados.

        Chamado na inicializacao da WANDA.
        Retorna: { "intellicare-ocr": True, "intellicare-superz": False (se indisponivel) }
        """
        results = {}
        for module_name, mcp_url in self._config.mcp_servers.items():
            try:
                session = await self._create_session(module_name, mcp_url)
                self._sessions[module_name] = session
                tools = await session.list_tools()
                self._tools_cache[module_name] = [t.model_dump() for t in tools.tools]
                results[module_name] = True
                logger.info(f"MCP connected: {module_name} — {len(tools.tools)} tools")
            except Exception as e:
                logger.warning(f"MCP connection failed: {module_name} — {e}")
                results[module_name] = False
        return results

    async def _create_session(self, module_name: str, mcp_url: str) -> ClientSession:
        """Cria sessao MCP via SSE."""
        sse_url = f"{mcp_url}/mcp/sse"

        # Context manager para SSE — WANDA mantem a sessao aberta
        read, write = await sse_client(sse_url).__aenter__()
        session = ClientSession(read, write)
        await session.initialize()
        return session

    async def call_tool(
        self,
        module_name: str,
        tool_name: str,
        params: Dict[str, Any],
        correlation_id: str,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Chama uma ferramenta MCP e retorna o resultado.

        Args:
            module_name: "intellicare-ocr" ou "intellicare-superz"
            tool_name: Nome da ferramenta (ex: "parse_lab_result")
            params: Parametros da ferramenta
            correlation_id: Para rastreabilidade
            timeout_seconds: Timeout da chamada

        Returns:
            Dict com o resultado da ferramenta

        Raises:
            MCPModuleUnavailableError: Se modulo nao conectado
            MCPToolNotFoundError: Se ferramenta nao existe
            MCPCallTimeoutError: Se timeout
            MCPCallError: Se erro retornado pela ferramenta
        """
        session = self._sessions.get(module_name)
        if not session:
            raise MCPModuleUnavailableError(
                f"MCP module {module_name} not connected. "
                f"Ensure {module_name} is running and /mcp/sse is accessible."
            )

        started_at = datetime.utcnow()

        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, params),
                timeout=timeout_seconds
            )

            # Registrar chamada bem-sucedida
            await self._log_call(
                correlation_id=correlation_id,
                module_name=module_name,
                tool_name=tool_name,
                params=params,
                status="success",
                duration_ms=int((datetime.utcnow() - started_at).total_seconds() * 1000)
            )

            # MCP retorna result.content (lista de TextContent ou ImageContent)
            # Extrair o conteudo de texto e parsear como JSON
            if result.content and len(result.content) > 0:
                text_content = result.content[0].text
                return json.loads(text_content)

            return {}

        except asyncio.TimeoutError:
            await self._log_call(
                correlation_id=correlation_id,
                module_name=module_name,
                tool_name=tool_name,
                params=params,
                status="timeout",
                duration_ms=timeout_seconds * 1000
            )
            raise MCPCallTimeoutError(
                f"MCP tool {module_name}/{tool_name} timed out after {timeout_seconds}s"
            )

        except Exception as e:
            await self._log_call(
                correlation_id=correlation_id,
                module_name=module_name,
                tool_name=tool_name,
                params=params,
                status="error",
                error_message=str(e),
                duration_ms=int((datetime.utcnow() - started_at).total_seconds() * 1000)
            )
            raise MCPCallError(f"MCP tool {module_name}/{tool_name} failed: {e}") from e

    async def list_tools(self, module_name: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Lista ferramentas disponibilizadas pelos MCP Servers.

        Args:
            module_name: None = todos os modulos

        Returns:
            { "intellicare-ocr": [tools...], "intellicare-superz": [tools...] }
        """
        if module_name:
            return {module_name: self._tools_cache.get(module_name, [])}
        return dict(self._tools_cache)

    async def refresh_tools(self, module_name: str) -> List[Dict]:
        """Re-descobre as ferramentas de um MCP Server."""
        session = self._sessions.get(module_name)
        if not session:
            raise MCPModuleUnavailableError(module_name)

        tools = await session.list_tools()
        self._tools_cache[module_name] = [t.model_dump() for t in tools.tools]
        return self._tools_cache[module_name]

    async def health_check(self, module_name: str) -> bool:
        """Verifica se MCP Server esta respondendo."""
        try:
            url = self._config.mcp_servers[module_name]
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/api/v1/health")
                return resp.status_code == 200
        except Exception:
            return False


class MCPClientConfig(BaseModel):
    """Configuracao do MCP Client."""

    mcp_servers: Dict[str, str] = {
        "intellicare-ocr": "http://intellicare-ocr:8008",
        "intellicare-superz": "http://intellicare-superz:8009"
    }

    # Timeouts por tipo de ferramenta
    ocr_timeout_seconds: int = 30      # OCR pode ser lento (PDFs)
    search_timeout_seconds: int = 15   # Busca web
    analysis_timeout_seconds: int = 60 # Qwen2.5-72B analise de texto

    # Retry
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
```

---

## 5. Integracao com o LangGraph (EF-W005)

As ferramentas MCP sao expostas ao LangGraph como `Tool` objects:

```python
from langchain.tools import Tool

class WandaToolRegistry:
    """Registro unificado de todas as ferramentas da WANDA (HTTP + MCP)."""

    def __init__(
        self,
        http_clients: Dict[str, ModuleHTTPClient],
        mcp_client: WandaMCPClient
    ):
        self._http = http_clients
        self._mcp = mcp_client

    def get_all_tools(self) -> List[Tool]:
        """Retorna todas as ferramentas para o LangGraph."""
        return [
            # HTTP Tools (modulos existentes)
            *self._build_http_tools(),
            # MCP Tools (MINERVA + PIERRE)
            *self._build_mcp_tools()
        ]

    def _build_mcp_tools(self) -> List[Tool]:
        tools = []

        # MINERVA Tools
        tools.append(Tool(
            name="parse_lab_result",
            description=(
                "Extrai resultados de exames laboratoriais de PDFs ou imagens. "
                "Use quando o usuario enviar um laudo em PDF ou quando precisar "
                "interpretar exames de outro sistema. "
                "Retorna dict compativel com Florence para interpretacao."
            ),
            func=self._make_mcp_tool("intellicare-ocr", "parse_lab_result"),
            coroutine=self._make_async_mcp_tool("intellicare-ocr", "parse_lab_result")
        ))

        tools.append(Tool(
            name="search_documents",
            description=(
                "Busca semantica no historico de documentos do paciente. "
                "Use para encontrar laudos, prescricoes e sumarios de alta anteriores. "
                "Requer patient_id."
            ),
            func=self._make_mcp_tool("intellicare-ocr", "search_documents"),
            coroutine=self._make_async_mcp_tool("intellicare-ocr", "search_documents")
        ))

        # PIERRE Tools
        tools.append(Tool(
            name="web_search",
            description=(
                "Busca web em tempo real via Tavily. "
                "Use para: guidelines atualizados, aprovacoes ANVISA recentes, "
                "noticias medicas, documentos regulatorios. "
                "NAO use para conhecimento clinico geral (Oswaldo/Florence ja sabem)."
            ),
            func=self._make_mcp_tool("intellicare-superz", "web_search"),
            coroutine=self._make_async_mcp_tool("intellicare-superz", "web_search")
        ))

        tools.append(Tool(
            name="search_medical_literature",
            description=(
                "Busca na literatura medica indexada (PubMed, BVS/BIREME, SciELO). "
                "Use para: ensaios clinicos, revisoes sistematicas, evidencias para "
                "uma decisao clinica especifica. Prefira esta sobre web_search "
                "para perguntas sobre evidencias cientificas."
            ),
            func=self._make_mcp_tool("intellicare-superz", "search_medical_literature"),
            coroutine=self._make_async_mcp_tool("intellicare-superz", "search_medical_literature")
        ))

        tools.append(Tool(
            name="check_regulatory",
            description=(
                "Verifica status regulatorio de medicamentos, dispositivos e procedimentos. "
                "Use para: aprovacoes ANVISA, cobertura ANS, resolucoes CFM. "
                "Ex: 'empagliflozina aprovada para DRC no Brasil?'"
            ),
            func=self._make_mcp_tool("intellicare-superz", "check_regulatory"),
            coroutine=self._make_async_mcp_tool("intellicare-superz", "check_regulatory")
        ))

        tools.append(Tool(
            name="analyze_text",
            description=(
                "Analise profunda de texto longo via Qwen2.5-72B. "
                "Use para: extrair pontos de um guideline extenso, comparar protocolos, "
                "sintetizar multiplos resultados de busca. Custo: alto (LLM local)."
            ),
            func=self._make_mcp_tool("intellicare-superz", "analyze_text"),
            coroutine=self._make_async_mcp_tool("intellicare-superz", "analyze_text")
        ))

        return tools

    def _make_async_mcp_tool(self, module_name: str, tool_name: str):
        """Factory de funcao async para ferramenta MCP."""
        async def tool_func(params: Dict, correlation_id: str = "wanda-default") -> Dict:
            return await self._mcp.call_tool(
                module_name=module_name,
                tool_name=tool_name,
                params=params,
                correlation_id=correlation_id
            )
        return tool_func
```

---

## 6. Fluxos de Uso

### Fluxo 1 — Laudo PDF + Interpretacao Clinica

```
Medico: "Interpretam o laudo PDF anexado da Maria Santos"
  │
  ▼
WANDA (LangGraph):
  │
  ├── 1. [MCP] MINERVA.parse_lab_result(file_base64=pdf_bytes)
  │         → { lab_results: { creatinine: 2.1, egfr: 28.5, potassium: 5.8 } }
  │
  ├── 2. [HTTP] Florence.analyze({ patient_id, lab_results })
  │         → { interpretation, critical_values, recommendations }
  │
  ├── 3. [HTTP] Oswaldo.get_patient_context(patient_id)
  │         → { staging: "DRC G3b", conditions: ["DM2", "HAS"] }
  │
  ├── 4. [MCP] PIERRE.check_regulatory("metformina DRC eGFR 28")
  │         → { status: "contraindicado eGFR < 30", source: "ANVISA/bula" }
  │
  └── 5. WANDA sintetiza e responde:
        "Exames da Maria Santos (laudo 10/02/2026):
         - eGFR: 28.5 ml/min (critico, DRC G3b confirmada)
         - Creatinina: 2.1 mg/dL (elevada)
         - Potassio: 5.8 mEq/L (hipercalemia leve)

         Alerta ANVISA: Metformina CONTRAINDICADA com eGFR < 30.
         Recomendacao: suspender metformina, revisar dosagem de insulina."
```

### Fluxo 2 — Pergunta sobre Guideline Atual

```
Medico: "Qual a recomendacao atual do KDIGO 2024 para SGLT2 em DRC?"
  │
  ▼
WANDA (LangGraph — LLM classifica):
  │
  ├── Classifica: pergunta sobre guideline → acionar PIERRE
  │
  ├── [MCP] PIERRE.web_search("KDIGO 2024 SGLT2 inhibitors CKD guidelines")
  │         → 5 resultados com URL + relevance_score
  │
  ├── [MCP] PIERRE.search_medical_literature("SGLT2 CKD EMPA-KIDNEY DAPA-CKD 2024")
  │         → 3 artigos com abstract e evidence_level
  │
  ├── [MCP] PIERRE.check_regulatory("dapagliflozina empagliflozina DRC ANVISA 2024")
  │         → status aprovacao no Brasil
  │
  └── WANDA sintetiza com citacoes:
        "Conforme KDIGO 2024 (kdigo.org):
         - Dapagliflozina indicada para DRC com TFG >= 25 e ACR >= 200
         - Aprovada pela ANVISA para esta indicacao (Out/2024)
         - Evidencia: DAPA-CKD (NEJM 2020, Level A) — reducao de 44% na progressao

         Fontes: [KDIGO 2024](https://kdigo.org/...) | [DAPA-CKD](https://pubmed...)"
```

---

## 7. Graceful Degradation

Se MINERVA ou PIERRE estiverem indisponiveis:

```python
DEGRADATION_POLICY = {
    "intellicare-ocr": {
        "fallback_message": (
            "Servico de OCR (MINERVA) indisponivel. "
            "Nao e possivel processar documentos no momento. "
            "Tente novamente em alguns minutos."
        ),
        "can_continue_without": True,  # WANDA continua sem MCP OCR
        "tools_affected": ["parse_lab_result", "extract_document", "search_documents"]
    },
    "intellicare-superz": {
        "fallback_message": (
            "Servico de pesquisa externa (PIERRE) indisponivel. "
            "Usando apenas conhecimento dos agentes clinicos locais. "
            "Informacoes podem nao refletir guidelines mais recentes."
        ),
        "can_continue_without": True,  # WANDA continua com modulos HTTP
        "tools_affected": ["web_search", "search_medical_literature", "check_regulatory"]
    }
}
```

---

## 8. API Endpoints (WANDA — expostos por esta EF)

```yaml
# ── Gerenciamento MCP ──
GET /api/v1/mcp/modules
  Description: Lista MCP Servers registrados e seu status
  Auth: Keycloak (admin)
  Response 200: {
    modules: [
      {
        module_name: "intellicare-ocr",
        agent_name: "MINERVA",
        status: "healthy",
        tools_count: 6,
        tools: [{ name, description }]
      }
    ]
  }

GET /api/v1/mcp/modules/{module_name}/tools
  Description: Lista ferramentas de um MCP Server especifico
  Auth: Keycloak
  Response 200: { tools: List[MCPToolInfo] }

POST /api/v1/mcp/modules/{module_name}/refresh
  Description: Re-descobre ferramentas (quando modulo atualizar)
  Auth: Keycloak (admin)
  Response 200: { tools: List[MCPToolInfo], refreshed_at: datetime }

POST /api/v1/mcp/tools/{module_name}/{tool_name}
  Description: Executa ferramenta MCP diretamente (debug/admin)
  Auth: Keycloak (admin)
  Body: { params: Dict, correlation_id: Optional[str] }
  Response 200: { result: Dict, duration_ms: int }
```

---

## 9. Schema SQL

```sql
-- MCP Servers registrados
CREATE TABLE wanda_operacional.mcp_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_name VARCHAR(100) NOT NULL UNIQUE,
    agent_name VARCHAR(100) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    mcp_endpoint VARCHAR(200) NOT NULL DEFAULT '/mcp/sse',
    status VARCHAR(20) NOT NULL DEFAULT 'healthy',
    tools_count INT DEFAULT 0,
    last_health_check TIMESTAMPTZ,
    last_tools_discovery TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tools disponibilizadas pelos MCP Servers
CREATE TABLE wanda_operacional.mcp_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES wanda_operacional.mcp_modules(id),
    tool_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}',
    last_validated TIMESTAMPTZ,

    UNIQUE(module_id, tool_name)
);

-- Log de chamadas MCP
CREATE TABLE wanda_operacional.mcp_call_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id VARCHAR(200) NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(200) NOT NULL,
    input_summary TEXT,            -- Resumo dos params (sem dados sensiveis)
    status VARCHAR(20) NOT NULL,   -- success | error | timeout
    error_message TEXT,
    duration_ms INT NOT NULL,
    called_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mcp_log_correlation ON wanda_operacional.mcp_call_log(correlation_id);
CREATE INDEX idx_mcp_log_module ON wanda_operacional.mcp_call_log(module_name, tool_name);
CREATE INDEX idx_mcp_log_called ON wanda_operacional.mcp_call_log(called_at);
```

---

## 10. Estrutura de Codigo

```
wanda/
├── mcp/
│   ├── __init__.py
│   ├── client.py              # WandaMCPClient
│   ├── config.py              # MCPClientConfig
│   ├── models.py              # MCPModuleRecord, MCPToolInfo, MCPCallRecord
│   ├── exceptions.py          # MCPModuleUnavailableError, MCPCallTimeoutError
│   └── tool_registry.py       # WandaToolRegistry (HTTP + MCP unificado)
├── api/
│   └── mcp_routes.py          # GET /mcp/modules, GET /mcp/tools, POST /mcp/tools/{name}
└── tests/
    └── test_mcp/
        ├── test_mcp_client.py
        ├── test_tool_registry.py
        └── test_mcp_routes.py
```

---

## 11. Configuracao

```bash
# MCP Servers
MCP_OCR_URL=http://intellicare-ocr:8008
MCP_SUPERZ_URL=http://intellicare-superz:8009
MCP_CONNECTION_TIMEOUT=10
MCP_OCR_TOOL_TIMEOUT=30
MCP_SEARCH_TOOL_TIMEOUT=15
MCP_ANALYSIS_TOOL_TIMEOUT=60
MCP_MAX_RETRIES=2
```

---

## 12. Testes Esperados

```
test_mcp/
├── test_mcp_client.py
│   ├── test_connect_all_success
│   ├── test_connect_partial_failure_graceful
│   ├── test_call_tool_success
│   ├── test_call_tool_module_unavailable_raises
│   ├── test_call_tool_timeout_raises
│   ├── test_call_tool_logs_to_db
│   ├── test_list_tools_returns_all
│   └── test_refresh_tools_updates_cache
├── test_tool_registry.py
│   ├── test_get_all_tools_includes_http_and_mcp
│   ├── test_mcp_tool_descriptions_for_llm
│   └── test_tool_call_routes_to_correct_module
└── test_mcp_routes.py
    ├── test_list_modules_endpoint
    ├── test_list_tools_endpoint
    ├── test_refresh_endpoint
    └── test_call_tool_admin_endpoint
```

**Minimo:** 15 testes para esta EF.

---

## 13. Criterios de Aceitacao

- [ ] `WandaMCPClient.connect_all()` conecta a MINERVA e PIERRE sem erro
- [ ] `WandaMCPClient.call_tool("intellicare-ocr", "parse_lab_result", ...)` retorna dict valido
- [ ] `WandaMCPClient.call_tool("intellicare-superz", "web_search", ...)` retorna resultados
- [ ] Se MINERVA indisponivel → WANDA continua funcionando, retorna mensagem de degradacao
- [ ] Se PIERRE indisponivel → WANDA continua funcionando, retorna mensagem de degradacao
- [ ] `GET /api/v1/mcp/modules` lista MINERVA e PIERRE com status correto
- [ ] Chamadas MCP registradas na tabela `mcp_call_log` com correlation_id
- [ ] MCPToolInfo disponivel para o LangGraph como `Tool` objects (EF-W005)
- [ ] 15+ testes com cobertura >= 80%
