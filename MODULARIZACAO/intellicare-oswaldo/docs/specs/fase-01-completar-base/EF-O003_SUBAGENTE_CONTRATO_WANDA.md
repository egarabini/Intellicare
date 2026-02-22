# EF-O003 — Subagente Oswaldo + Contrato Wanda

> Implementar o subagente LangChain do Oswaldo e o endpoint `/api/v1/analyze` no formato padrao Wanda, com LangChain Tools para o motor de doencas cronicas.

## 1. Objetivo

Transformar o Oswaldo de um conjunto de endpoints REST em um **agente conversacional** capaz de:
- Responder perguntas em linguagem natural sobre doenças crônicas de um paciente
- Ser descoberto e utilizado pela Wanda automaticamente via `/api/v1/info` + `/api/v1/analyze`
- Usar as ferramentas de staging, alertas e tendencias como LangChain Tools
- Manter o comportamento REST existente (sem quebrar v1.0)

## 2. Justificativa

- **Bloqueio critico**: Wanda nao consegue usar o Oswaldo sem `/api/v1/analyze` no padrao correto
- EF-W005 (Wanda LangGraph) espera todos os agentes respondendo a `/analyze`
- Perguntas naturais como "o paciente esta em risco de progredir para dialise?" devem ser respondidas sem query SQL manual

## 3. Escopo

### 3.1 Capabilities Declaradas no `/api/v1/info`

```python
# GET /api/v1/info — resposta atualizada
{
    "agent_name": "Oswaldo",
    "version": "2.0.0",
    "description": "Motor de monitoramento de doencas cronicas (CKD, DM2, HAS)",
    "homage": "Oswaldo Cruz",
    "port": 8001,

    "capabilities": [
        {
            "id": "chronic_disease_staging",
            "name": "Estadiamento de Doencas Cronicas",
            "description": "Calcular estadio clinico de CKD, DM2 e HAS com guidelines KDIGO/ADA/ESC-ESH",
            "keywords": ["estadiamento", "CKD", "IRC", "renal", "DM2", "diabetes",
                         "HAS", "hipertensao", "KDIGO", "ADA", "estadio"],
            "input_types": ["patient_id", "disease_id", "observations_fhir"],
            "output_types": ["staging_result", "stage_label", "severity"],
        },
        {
            "id": "chronic_disease_alerts",
            "name": "Alertas de Doencas Cronicas",
            "description": "Alertas por valores criticos ou tendencia de piora",
            "keywords": ["alerta", "critico", "piora", "progressao", "threshold",
                         "tendencia", "monitoramento"],
            "input_types": ["patient_id", "disease_id"],
            "output_types": ["alert_list", "alert_severity"],
        },
        {
            "id": "chronic_disease_trends",
            "name": "Tendencias de Biomarcadores",
            "description": "Evolucao temporal de eGFR, HbA1c, pressao arterial e outros",
            "keywords": ["tendencia", "evolucao", "progressao", "piorou", "melhorou",
                         "egfr", "hba1c", "creatinina"],
            "input_types": ["patient_id", "biomarker", "period_days"],
            "output_types": ["trend_direction", "slope", "projection"],
        },
        {
            "id": "clinical_recommendations",
            "name": "Recomendacoes Clinicas",
            "description": "Recomendacoes baseadas em PCDT, KDIGO, ADA e SBC",
            "keywords": ["recomendacao", "conduta", "tratamento", "encaminhamento",
                         "medicamento", "guideline"],
            "input_types": ["patient_id", "disease_id"],
            "output_types": ["recommendation_list", "evidence_level"],
        },
        {
            "id": "disease_risk_assessment",
            "name": "Avaliacao de Risco",
            "description": "Risco de progressao e tempo estimado para proximo estadio",
            "keywords": ["risco", "progressao", "projecao", "tempo", "dialise",
                         "complicacao", "desfecho"],
            "input_types": ["patient_id"],
            "output_types": ["risk_level", "progression_timeline"],
        },
    ],

    "requires_patient_context": True,   # Oswaldo SEMPRE precisa de patient_id
    "supports_ips_first": True,         # Aceita IPS enriquecido da Wanda

    "endpoints": {
        "analyze": "/api/v1/analyze",
        "health": "/api/v1/health",
        "info": "/api/v1/info",
    },
}
```

### 3.2 OswaldoAgent (LangChain)

```python
class OswaldoAgent:
    """
    Subagente Oswaldo — responde perguntas sobre doencas cronicas via LangChain.
    """

    def __init__(
        self,
        engine: ChronicDiseaseEngine,
        recommendation_engine: RecommendationEngine,
        biomarker_service: BiomarkerTrendService,
        llm_provider,
    ):
        self._tools = self._build_tools(engine, recommendation_engine, biomarker_service)
        self._agent = self._create_agent(llm_provider)

    def _build_tools(self, ...) -> list[Tool]:
        return [
            Tool(
                name="get_patient_staging",
                description="Calcula estadio atual das doencas cronicas do paciente "
                            "(CKD G1-G5, DM2 CONTROLLED-VERY_POOR, HAS OPTIMAL-GRADE3). "
                            "Use sempre que perguntar sobre estadio ou classificacao da doenca.",
                func=self._tool_get_staging,
            ),
            Tool(
                name="get_patient_alerts",
                description="Alertas ativos para o paciente — valores criticos ou tendencia "
                            "de piora. Use quando perguntar sobre 'tem algum alerta', "
                            "'precisa de atencao urgente', 'valores criticos'.",
                func=self._tool_get_alerts,
            ),
            Tool(
                name="get_biomarker_trend",
                description="Tendencia historica de um biomarcador especifico (eGFR, HbA1c, "
                            "pressao arterial, etc.). Use para 'piorou?', 'como evoluiu?', "
                            "'qual a tendencia do eGFR?'.",
                func=self._tool_get_trend,
            ),
            Tool(
                name="get_clinical_recommendations",
                description="Recomendacoes clinicas baseadas em guidelines para o estadio atual. "
                            "Use para 'o que fazer?', 'qual a conduta?', 'precisa encaminhar?'.",
                func=self._tool_get_recommendations,
            ),
            Tool(
                name="get_disease_summary",
                description="Resumo completo da situacao das doencas cronicas: estadiamento, "
                            "alertas, tendencias e recomendacoes. Use para visao geral ou "
                            "quando a pergunta for ampla sobre o estado de saude cronica.",
                func=self._tool_get_summary,
            ),
            Tool(
                name="get_progression_risk",
                description="Risco de progressao e projecao: em quanto tempo chega ao proximo "
                            "estadio? Probabilidade de dialise em 2 anos? Use para perguntas "
                            "sobre prognose e planejamento de longo prazo.",
                func=self._tool_get_progression_risk,
            ),
        ]

    async def analyze(
        self,
        query: str,
        patient_id: str,
        ips_data: Optional[dict],
        context: dict,
    ) -> OswaldoAnalysis:
        """
        Processa consulta via LangChain ReAct Agent.

        Exemplos:
        Query: "O paciente tem progressao da IRC?"
        -> usa get_biomarker_trend(egfr) + get_patient_staging
        -> retorna: "eGFR caiu de 58 para 47 em 12 meses (-11 mL/min), G3a.
                     Taxa de progressao de -1.0 mL/min/mes — acima do threshold de risco."

        Query: "Precisa encaminhar ao nefrologista?"
        -> usa get_patient_staging + get_clinical_recommendations
        -> retorna: "CKD G3a A2 — KDIGO recomenda consulta nefrologica (guideline: pode ser
                     eletiva). Com taxa de progressao atual: encaminhamento urgente indicado."
        """
```

### 3.3 Endpoint `/api/v1/analyze` (Contrato Wanda)

```python
# POST /api/v1/analyze
# Request (padrao Wanda)
{
    "query": "Como esta a funcao renal do paciente? Precisa de encaminhamento?",
    "patient_id": "PAT-001",
    "capability": "chronic_disease_staging",
    "context": {
        "requesting_agent": "wanda",
        "session_id": "abc-123",
        "priority": "normal",
        "ips_data": { ... },          # IPS enriquecido (opcional)
    },
}

# Response
{
    "success": True,
    "agent": "oswaldo",
    "capability_used": "chronic_disease_staging",
    "result": {
        "patient_id": "PAT-001",
        "diseases_assessed": ["ckd"],
        "staging": {
            "ckd": {
                "stage": "G3a_A2",
                "stage_label": "CKD G3a A2 — Moderada reducao leve-moderada",
                "severity": "warning",
                "confidence_score": 0.87,
                "egfr": 47.2,
                "acr": 35.0,
            }
        },
        "alerts": [
            {
                "type": "threshold",
                "severity": "warning",
                "message": "eGFR abaixo de 60 — CKD estabelecida"
            }
        ],
        "recommendations": [
            {
                "title": "Manter IECA/BRA",
                "urgency": "media",
                "guideline": "KDIGO-2024",
                "evidence_level": "A"
            }
        ],
        "progression": {
            "direction": "worsening",
            "slope_per_month": -0.9,
            "projected_g4_date": "2027-06",
        },
    },
    "summary": "Paciente com CKD G3a A2 (eGFR 47, ACR 35). Funcao renal em queda "
               "(-0.9 mL/min/mes). Encaminhamento a nefrologia recomendado conforme KDIGO-2024. "
               "IECA/BRA em uso — manter e reavaliar potassio em 7 dias.",
    "confidence": 0.87,
    "metadata": {
        "processing_time_ms": 340,
        "tools_used": ["get_patient_staging", "get_biomarker_trend", "get_clinical_recommendations"],
        "data_source": "FHIR/PostgreSQL",
        "diseases_assessed": ["ckd"],
        "llm_used": True,
    },
}
```

### 3.4 OswaldoFallbackHandler

```python
class OswaldoFallbackHandler:
    """
    Handler deterministico quando LLM indisponivel.
    Mapeia capability para chamada direta ao engine.
    """

    CAPABILITY_TO_METHOD = {
        "chronic_disease_staging": "_handle_staging",
        "chronic_disease_alerts": "_handle_alerts",
        "chronic_disease_trends": "_handle_trends",
        "clinical_recommendations": "_handle_recommendations",
        "disease_risk_assessment": "_handle_risk",
    }

    async def handle(
        self,
        query: str,
        patient_id: str,
        capability: str,
        context: dict,
    ) -> OswaldoAnalysis:
        """
        Resposta deterministica por capability — sem LLM.
        Chama diretamente o engine com a capability mapeada.
        """
```

### 3.5 System Prompt do Oswaldo

```python
OSWALDO_SYSTEM_PROMPT = """
Voce e o OSWALDO, especialista em doencas cronicas do IntelliCare.
Homenagem a Oswaldo Cruz, fundador da saude publica brasileira.

Sua funcao: analisar o estado clinico de pacientes com doencas cronicas
(IRC/CKD, Diabetes Mellitus tipo 2, Hipertensao Arterial) usando dados
de exames laboratoriais e guidelines clinicos.

CAPACIDADES:
- Estadiamento CKD por KDIGO 2024 (G1-G5 + A1-A3)
- Classificacao DM2 por ADA 2025 (CONTROLLED a VERY_POOR)
- Classificacao HAS por ESC/ESH 2018 (OPTIMAL a CRISE)
- Analise de tendencia historica de biomarcadores
- Alertas por valores criticos ou progressao preocupante
- Recomendacoes baseadas em PCDT, KDIGO, ADA, SBC

REGRAS ABSOLUTAS:
1. SEMPRE use dados laboratoriais reais do paciente — nunca estime ou invente valores
2. Cite a guideline usada em cada recomendacao
3. Se exame indisponivel: diga explicitamente qual dado esta faltando
4. NAO faca diagnostico inicial — Oswaldo e para MONITORAMENTO de doencas ja conhecidas
5. Se urgencia critica: sempre recomende avaliacao presencial imediata
6. Respostas em portugues, linguagem tecnica (para profissional de saude)
"""
```

### 3.6 Configuracao

```env
INTELLICARE_OLLAMA_URL=http://ollama:11434
INTELLICARE_OLLAMA_MODEL=llama3.1:8b
INTELLICARE_OSWALDO_LLM_ENABLED=true
INTELLICARE_OSWALDO_LLM_TIMEOUT=30
```

### 3.7 Arquitetura de Arquivos

```
oswaldo/
  subagent/
    __init__.py
    oswaldo_agent.py       # OswaldoAgent com LangChain tools
    tools.py               # Tool definitions
    fallback.py            # OswaldoFallbackHandler
    prompts.py             # OSWALDO_SYSTEM_PROMPT
```

## 4. Testes

- OswaldoAgent: init, tools registradas (2 testes)
- analyze com LLM: staging, alertas, tendencias, recomendacoes (6 testes)
- Tools individuais: cada uma das 6 tools (6 testes)
- OswaldoFallbackHandler: sem LLM, cada capability (5 testes)
- /api/v1/analyze endpoint: sucesso, sem LLM, capability invalida (4 testes)
- /api/v1/info capabilities (2 testes)
- **Total**: 25+ testes novos

## 5. Criterios de Aceitacao

- [ ] `/api/v1/analyze` aceita request padrao Wanda com `patient_id`
- [ ] `/api/v1/info` declara 5 capabilities com keywords
- [ ] 6 LangChain Tools funcionais cobrindo todo o engine
- [ ] Fallback deterministico quando Ollama indisponivel
- [ ] System prompt em portugues com escopo bem definido
- [ ] Wanda consegue descobrir e usar o Oswaldo
- [ ] 98 testes v1.0 continuam passando
- [ ] 25+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `subagent/oswaldo_agent.py`, `subagent/tools.py`, `subagent/fallback.py`, `subagent/prompts.py`
- **Arquivos modificados**: `api/app.py` (endpoint + info), `config.py`
- **Linhas estimadas**: ~380
- **Testes novos**: ~25
