# EF-Z002 — Subagente Zilda e Contrato Wanda

> Implementar o subagente LangChain da Zilda e o endpoint /api/v1/analyze para integracao com a orquestradora Wanda.

## 1. Objetivo

Transformar a Zilda de um conjunto de endpoints REST em um **agente conversacional** capaz de:
- Responder perguntas em linguagem natural sobre dados territoriais e de saude publica
- Ser descoberto e utilizado pela Wanda automaticamente
- Usar as ferramentas CNES + DATASUS como LangChain Tools
- Manter o comportamento REST existente (sem quebrar v1.0)

## 2. Justificativa

- **Bloqueio critico**: Wanda nao consegue usar a Zilda sem `/api/v1/analyze`
- **LangGraph requer agents**: EF-W005 (Wanda LangGraph) espera que todos os agentes respondam a `/analyze`
- **Consultas naturais**: "Tem hemodialise SUS perto de Campinas?" deve ser respondida sem SQL manual
- **Autonomia**: com LangChain Tools, o agente decide qual dado buscar para responder

## 3. Escopo

### 3.1 Capabilities Declaradas no `/api/v1/info`

```python
# GET /api/v1/info — resposta atualizada
{
    "agent_name": "Zilda",
    "version": "2.0.0",
    "description": "Agente de dados territoriais e saude publica brasileira",
    "homage": "Zilda Arns",
    "port": 8003,

    "capabilities": [
        {
            "id": "cnes_search",
            "name": "Busca de Unidades de Saude",
            "description": "Localizar estabelecimentos de saude por municipio, tipo e servico",
            "keywords": ["CNES", "hospital", "UBS", "posto", "unidade", "estabelecimento",
                         "clinica", "hemodiálise", "dialise", "UTI", "leito"],
            "input_types": ["city_code", "state_code", "service_type", "cnes_code"],
            "output_types": ["establishment", "establishment_list", "cnes_validation"],
        },
        {
            "id": "territorial_context",
            "name": "Contexto Territorial",
            "description": "Regiao de saude, populacao, cobertura e rede assistencial por municipio",
            "keywords": ["regiao de saude", "territorio", "municipio", "populacao",
                         "cobertura", "rede", "macrorregiao"],
            "input_types": ["city_code", "state_code"],
            "output_types": ["territorial_summary", "region_context"],
        },
        {
            "id": "datasus_indicators",
            "name": "Indicadores DATASUS",
            "description": "Dados de producao hospitalar, mortalidade e nascimentos por municipio",
            "keywords": ["internacao", "SIH", "mortalidade", "SIM", "nascimento", "SINASC",
                         "indicador", "producao", "epidemiologico"],
            "input_types": ["city_code", "state_code", "year", "cid_code"],
            "output_types": ["hospitalization_data", "mortality_data", "birth_data"],
        },
        {
            "id": "coverage_analysis",
            "name": "Analise de Cobertura",
            "description": "Cobertura ESF, vazios assistenciais e oferta vs demanda",
            "keywords": ["cobertura", "ESF", "saude da familia", "vazio", "oferta", "demanda"],
            "input_types": ["city_code", "state_code", "region_code"],
            "output_types": ["coverage_report", "void_analysis", "supply_demand"],
        },
    ],

    "requires_patient_context": False,
    "supports_ips_first": False,  # Zilda e territorial, nao clinica

    "endpoints": {
        "analyze": "/api/v1/analyze",
        "health": "/api/v1/health",
        "info": "/api/v1/info",
    },
}
```

### 3.2 ZildaAgent (LangChain)

```python
class ZildaAgent:
    """
    Subagente Zilda — responde perguntas territoriais via LangChain.
    """

    def __init__(
        self,
        cnes_client: CnesClient,
        territorial_engine: TerritorialEngine,
        llm_provider,               # OllamaProvider ou fallback
    ):
        self._tools = self._build_tools(cnes_client, territorial_engine)
        self._agent = self._create_agent(llm_provider)

    def _build_tools(
        self,
        cnes_client,
        territorial_engine,
    ) -> list[Tool]:
        """
        Define as LangChain Tools disponiveis para o agente.
        """
        return [
            Tool(
                name="search_establishments",
                description="Busca estabelecimentos de saude por municipio, estado ou tipo. "
                            "Use quando perguntar sobre hospitais, UBS, clinicas, postos.",
                func=self._tool_search_establishments,
            ),
            Tool(
                name="get_establishment_detail",
                description="Detalhes completos de um estabelecimento: leitos, servicos, profissionais. "
                            "Use com codigo CNES.",
                func=self._tool_get_detail,
            ),
            Tool(
                name="validate_cnes",
                description="Valida se um codigo CNES existe e retorna dados do estabelecimento.",
                func=self._tool_validate_cnes,
            ),
            Tool(
                name="get_territorial_context",
                description="Contexto territorial de um municipio: regiao de saude, populacao, "
                            "numero de estabelecimentos por tipo.",
                func=self._tool_territorial_context,
            ),
            Tool(
                name="find_establishments_with_service",
                description="Encontra estabelecimentos com servico especifico (dialise, UTI, quimio, etc). "
                            "Use quando perguntar 'onde tem X perto de Y'.",
                func=self._tool_find_with_service,
            ),
            Tool(
                name="get_health_regions",
                description="Lista regioes de saude de um estado com populacao.",
                func=self._tool_get_regions,
            ),
        ]

    async def analyze(
        self,
        query: str,
        context: dict,
    ) -> ZildaAnalysis:
        """
        Processa consulta via LangChain ReAct Agent.

        O agente:
        1. Entende a query em portugues
        2. Decide qual(is) tool(s) usar
        3. Executa as ferramentas
        4. Sintetiza resposta em portugues

        Ex:
        Query: "Qual hospital mais proximo de Campinas tem hemodialise SUS?"
        -> usa find_establishments_with_service(city="Campinas", service="dialise", sus=True)
        -> retorna lista de hospitais com dialise SUS ordenados por distancia
        """
```

### 3.3 Endpoint `/api/v1/analyze` (Contrato Wanda)

```python
# POST /api/v1/analyze
# Request (padrao Wanda)
{
    "query": "Qual a cobertura de unidades basicas de saude no municipio de Campinas?",
    "patient_id": null,             # Zilda e territorial — geralmente sem patient_id
    "capability": "territorial_context",
    "context": {
        "requesting_agent": "wanda",
        "session_id": "abc-123",
        "priority": "normal",
    },
}

# Response
{
    "success": True,
    "agent": "zilda",
    "capability_used": "territorial_context",
    "result": {
        "city": "Campinas",
        "state": "SP",
        "total_establishments": 87,
        "type_distribution": {
            "UNIDADE BASICA DE SAUDE": 52,
            "HOSPITAL GERAL": 18,
            "PRONTO ATENDIMENTO": 8,
            "OUTROS": 9
        },
        "region": "Regiao de Saude de Campinas",
        "population": 1213792,
        "ubs_coverage_ratio": 4.29,   # UBS por 100k habitantes
    },
    "summary": "Campinas tem 52 UBS para 1,2 milhao de habitantes (4,3 por 100k). "
               "A cobertura esta dentro da media estadual.",
    "confidence": 0.92,
    "metadata": {
        "processing_time_ms": 890,
        "tools_used": ["get_territorial_context", "search_establishments"],
        "data_source": "CNES",
        "data_freshness": "1h_cache",
    },
}
```

### 3.4 Fallback sem LLM

Se Ollama indisponivel, ZildaAgent usa logica deterministica:

```python
class ZildaFallbackHandler:
    """
    Handler deterministico quando LLM indisponivel.

    Mapeia keywords para tools diretamente (sem LLM).
    Similar ao comportamento da Wanda v1.0 com keywords.
    """

    KEYWORD_TO_TOOL = {
        "dialise|hemodialise": "find_with_service:117",
        "hospital|internacao": "search_establishments:05",
        "ubs|posto|basica": "search_establishments:01",
        "uti|intensiva": "find_with_service:100",
        "regiao|territorio|municipio": "get_territorial_context",
        "cnes": "validate_cnes",
    }

    def handle(self, query: str, context: dict) -> ZildaAnalysis:
        """Resposta deterministica por keywords."""
```

### 3.5 System Prompt da Zilda

```python
ZILDA_SYSTEM_PROMPT = """
Voce e a ZILDA, especialista em dados de saude publica brasileira do IntelliCare.
Homenagem a Zilda Arns, fundadora da Pastoral da Crianca.

Sua funcao: responder perguntas sobre a rede assistencial de saude brasileira
usando dados oficiais do CNES (Cadastro Nacional de Estabelecimentos de Saude).

CAPACIDADES:
- Localizar unidades de saude por municipio, tipo e servico especializado
- Informar sobre leitos, servicos (dialise, UTI, quimio) e profissionais
- Calcular cobertura assistencial por territorio
- Identificar onde o paciente pode ser encaminhado dado sua localizacao

REGRAS ABSOLUTAS:
1. Use SOMENTE dados oficiais do CNES — nunca invente ou estime
2. Sempre mencione a fonte (CNES, IBGE) e a data de referencia
3. Se dado nao disponivel: diga claramente
4. NAO faca analises clinicas — isso e funcao de Florence/Oswaldo
5. Se perguntarem sobre diagnostico/tratamento: redirecione para agentes clinicos
6. Sempre informe se servico e SUS ou apenas particular
"""
```

### 3.6 Arquitetura de Arquivos

```
zilda/
  subagent/
    __init__.py
    zilda_agent.py          # ZildaAgent com LangChain tools
    tools.py                # Definicao das tools LangChain
    fallback.py             # ZildaFallbackHandler
    prompts.py              # ZILDA_SYSTEM_PROMPT
```

### 3.7 Configuracao

```env
# LLM
INTELLICARE_OLLAMA_URL=http://ollama:11434
INTELLICARE_OLLAMA_MODEL=llama3.1:8b
INTELLICARE_OLLAMA_TIMEOUT=30
INTELLICARE_OLLAMA_ENABLED=true
```

## 4. Testes

- ZildaAgent: init, tools registradas (2 testes)
- analyze com LLM: busca simples, busca com servico, territorial (6 testes)
- Tools individuais: cada uma das 6 tools (6 testes)
- ZildaFallbackHandler: sem LLM, cada keyword (5 testes)
- /api/v1/analyze endpoint: sucesso, sem LLM, capability invalida (4 testes)
- /api/v1/info capabilities (2 testes)
- **Total**: 25+ testes novos

## 5. Criterios de Aceitacao

- [ ] `/api/v1/analyze` aceita request padrao Wanda e retorna resposta no formato padrao
- [ ] `/api/v1/info` declara 4 capabilities com keywords
- [ ] 6 LangChain Tools funcionais
- [ ] Fallback deterministico quando Ollama indisponivel
- [ ] System prompt em portugues com regras de escopo
- [ ] Wanda consegue descobrir e usar a Zilda (integracao testada)
- [ ] 68 testes v1.0 continuam passando
- [ ] 25+ testes novos
- [ ] Cobertura >= 90%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `subagent/zilda_agent.py`, `subagent/tools.py`, `subagent/fallback.py`, `subagent/prompts.py`
- **Arquivos modificados**: `api/app.py` (novo endpoint + info), `config.py`
- **Linhas estimadas**: ~350
- **Testes novos**: ~25
