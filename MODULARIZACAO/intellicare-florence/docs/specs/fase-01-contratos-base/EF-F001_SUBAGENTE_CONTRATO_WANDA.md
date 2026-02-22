# EF-F001 — Subagente Florence + Contrato Wanda

> Implementar o subagente LangChain da Florence e o endpoint `/api/v1/analyze` no formato padrao Wanda, permitindo que a Wanda use Florence para interpretacao clinica de exames laboratoriais em contexto conversacional.

## 1. Objetivo

Transformar a Florence de motor de analise em **agente conversacional de inteligencia clinica** capaz de:
- Responder perguntas sobre exames em linguagem natural
- Ser descoberta e usada automaticamente pela Wanda
- Contextualizar resultados com o historico do paciente
- Usar os 10 endpoints existentes como LangChain Tools

## 2. Justificativa

- **Bloqueio critico**: Wanda nao consegue usar Florence sem `/api/v1/analyze` no formato Wanda
- O endpoint `/api/v1/analyze` existente recebe `{patient_id, lab_results}` — nao o contrato Wanda `{query, patient_id, capability, context}`
- Florence tem o melhor motor de interpretacao de exames — e desperdicado sem integracao Wanda
- Oswaldo precisa da Florence para enriquecer estadiamentos com contexto laboratorial

## 3. Escopo

### 3.1 Capabilities Declaradas no `/api/v1/info`

```python
# GET /api/v1/info — resposta atualizada
{
    "agent_name": "Florence",
    "version": "2.0.0",
    "description": "Motor de inteligencia clinica laboratorial — interpretacao, tendencias e protocolos",
    "homage": "Florence Nightingale",
    "port": 8002,

    "capabilities": [
        {
            "id": "lab_interpretation",
            "name": "Interpretacao de Exames",
            "description": "Interpretacao contextualizada de resultados laboratoriais com "
                           "significancia clinica e recomendacoes de conduta",
            "keywords": ["exame", "laboratorio", "resultado", "interpretacao", "valor",
                         "hemograma", "creatinina", "glicose", "hba1c", "tsb"],
            "input_types": ["patient_id", "lab_results"],
            "output_types": ["lab_interpretation", "clinical_significance", "recommendations"],
        },
        {
            "id": "clinical_analysis",
            "name": "Analise Clinica Completa",
            "description": "Analise completa com correlacoes entre exames, deteccao de padroes "
                           "clinicos (renal, hepatico, metabolico, hematologico) e significancia geral",
            "keywords": ["analise", "correlacao", "padrao", "completa", "laboratorial", "sindrome"],
            "input_types": ["patient_id", "lab_results", "historical_data"],
            "output_types": ["clinical_analysis", "correlations", "patterns", "summary"],
        },
        {
            "id": "lab_trends",
            "name": "Tendencias Laboratoriais",
            "description": "Analise temporal de exames: tendencia de piora/melhora, "
                           "velocidade de mudanca e projecao",
            "keywords": ["tendencia", "historico", "evolucao", "piorou", "melhorou",
                         "progressao", "serie"],
            "input_types": ["patient_id", "lab_id", "period_months"],
            "output_types": ["trend_direction", "slope", "change_percent", "timeline"],
        },
        {
            "id": "protocol_search",
            "name": "Busca em Protocolos Clinicos",
            "description": "Busca semantica em 10 protocolos clinicos: DM2, IRC, HAS, "
                           "anemia, dislipidemia, hipotireoidismo, hepatopatia e outros",
            "keywords": ["protocolo", "guideline", "conduta", "tratamento", "manejo"],
            "input_types": ["query", "specialty"],
            "output_types": ["protocol_chunks", "relevance_score", "source"],
        },
        {
            "id": "critical_alert",
            "name": "Alertas de Valores Criticos",
            "description": "Identificacao imediata de valores criticos (panic) que exigem "
                           "acao imediata: hipercalemia grave, INR > 4.0, Hb < 7.0",
            "keywords": ["critico", "urgente", "alarme", "panico", "valor_critico", "emergencia"],
            "input_types": ["patient_id", "lab_results"],
            "output_types": ["critical_values", "urgency", "immediate_action"],
        },
    ],

    "requires_patient_context": True,   # Florence analisa dados de paciente
    "supports_ips_first": True,         # Aceita FHIR IPS para contexto

    "endpoints": {
        "analyze": "/api/v1/analyze",   # Contrato Wanda
        "health": "/api/v1/health",
        "info": "/api/v1/info",
    },
}
```

### 3.2 FlorenceAgent (LangChain)

```python
class FlorenceAgent:
    """
    Subagente Florence — analise clinica via LangChain ReAct.

    Usa os endpoints REST existentes como ferramentas.
    Nao acessa banco ou ChromaDB diretamente — passa pela API.
    """

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="interpret_labs",
                description="Interpreta um ou mais resultados laboratoriais individuais. "
                            "Use para perguntas como 'o que significa creatinina 2.1?', "
                            "'o potassio esta normal?', 'como esta a funcao renal?'.",
                func=self._tool_interpret_labs,
            ),
            Tool(
                name="analyze_clinical",
                description="Analise clinica completa — correlacoes entre exames e padroes. "
                            "Use quando ha multiplos exames e perguntas como 'como estao os "
                            "exames do paciente?', 'ha padroes clinicos preocupantes?'.",
                func=self._tool_analyze_clinical,
            ),
            Tool(
                name="get_lab_trends",
                description="Tendencia de um exame especifico ao longo do tempo. "
                            "Use para 'a creatinina esta piorando?', 'qual a evolucao "
                            "da hemoglobina nos ultimos meses?'.",
                func=self._tool_get_lab_trends,
            ),
            Tool(
                name="search_protocols",
                description="Busca em protocolos clinicos por tema. "
                            "Use para 'qual o protocolo de manejo de anemia?', "
                            "'o que diz o guideline sobre hipotireoidismo?'.",
                func=self._tool_search_protocols,
            ),
            Tool(
                name="check_critical_values",
                description="Verifica se ha valores criticos (panic) nos exames. "
                            "Use SEMPRE quando houver exames novos para garantir que "
                            "nenhum valor de emergencia seja ignorado.",
                func=self._tool_check_critical_values,
            ),
            Tool(
                name="get_patient_history",
                description="Recupera historico de exames do paciente do banco de dados. "
                            "Use para contextualizar resultados atuais com historico. "
                            "Requer EF-F002 (Persistencia) implementado.",
                func=self._tool_get_patient_history,
            ),
        ]

    async def analyze(
        self,
        query: str,
        patient_id: Optional[str],
        context: dict,
    ) -> FlorenceAnalysis:
        """
        Processa consulta clinica via LangChain ReAct Agent.

        Exemplos:
        Query: "Como estao os exames do paciente?"
        Context: {"lab_results": {"creatinine": 2.1, "potassium": 5.8, "egfr": 38}}
        -> check_critical_values() → alerta hipercalemia + IR
        -> analyze_clinical() → padrão renal_impairment + hyperkalemia_risk
        -> search_protocols("insuficiencia renal hipercalemia manejo")
        -> "Creatinina elevada (2.1) e potassio 5.8 com TFG 38 configuram DRC G3b com "
           "hipercalemia moderada — URGENTE. Recomenda-se ECG, restricao de potassio "
           "e contato com nefrologia."

        Query: "A funcao tireoidiana esta normal?"
        Context: {"lab_results": {"tsh": 12.4, "free_t4": 0.7}}
        -> interpret_labs(["tsh", "free_t4"])
        -> search_protocols("hipotireoidismo TSH elevado")
        -> "TSH 12.4 e T4L 0.7 indicam hipotireoidismo primario confirmado.
            Inicio de levotiroxina recomendado — dose inicial 1.6 mcg/kg/dia."
        """
```

### 3.3 Endpoint `/api/v1/analyze` (Contrato Wanda) — SUBSTITUI O ATUAL

```python
# POST /api/v1/analyze
# ATENÇÃO: Este endpoint SUBSTITUI o /api/v1/analyze atual (que recebe lab_results diretamente)
# O endpoint atual passa a ser /api/v1/analyze-labs (compatibilidade retroativa)

# Request (padrao Wanda)
{
    "query": "Como estao os exames renais do paciente? Ha algum valor critico?",
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "capability": "clinical_analysis",
    "context": {
        "requesting_agent": "wanda",
        "session_id": "abc-123",
        "lab_results": {
            "creatinine": 2.1,
            "egfr": 38.0,
            "potassium": 5.8,
            "urea": 82.0,
        },
        "patient_context": {
            "age": 65,
            "sex": "male",
            "known_conditions": ["ckd_g3b", "dm2"],
        },
        "include_protocols": True,
    },
}

# Response
{
    "success": True,
    "agent": "florence",
    "capability_used": "clinical_analysis",
    "result": {
        "critical_values": [
            {
                "lab_id": "potassium",
                "value": 5.8,
                "level": "critical_high",
                "message": "Hipercalemia grave — risco de arritmia",
                "immediate_action": "ECG urgente, restricao de potassio, avaliar suspensao de IECA",
            }
        ],
        "interpretations": {
            "creatinine": {"value": 2.1, "level": "high", "significance": "urgent"},
            "egfr": {"value": 38.0, "level": "low", "significance": "urgent"},
            "potassium": {"value": 5.8, "level": "critical_high", "significance": "critical"},
            "urea": {"value": 82.0, "level": "high", "significance": "urgent"},
        },
        "patterns_detected": [
            {
                "pattern_id": "renal_impairment",
                "name": "Comprometimento Renal",
                "significance": "urgent",
                "recommendation": "Avaliar TFG, hidratacao, medicamentos nefrotoxicos",
            },
            {
                "pattern_id": "hyperkalemia_risk",
                "name": "Risco de Hipercalemia",
                "significance": "critical",
                "recommendation": "ECG imediato, avaliar IECA/BRA, restricao dietetica",
            },
        ],
        "protocols_retrieved": [
            {
                "title": "Insuficiencia Renal Cronica — Manejo",
                "chunk": "Em pacientes com DRC G3b e hipercalemia, suspender IECA/BRA se K > 5.5...",
                "relevance_score": 0.92,
            }
        ],
    },
    "summary": "Paciente com DRC G3b (TFG 38) e hipercalemia CRITICA (K 5.8 mEq/L). "
               "Risco de arritmia por hipercalemia — ECG urgente indicado. "
               "Avaliar suspensao de IECA/BRA e restricao de potassio na dieta. "
               "Encaminhamento para nefrologista recomendado.",
    "confidence": 0.91,
    "metadata": {
        "processing_time_ms": 380,
        "tools_used": ["check_critical_values", "analyze_clinical", "search_protocols"],
        "labs_analyzed": 4,
        "critical_alerts": 1,
        "protocols_consulted": 1,
    },
}
```

### 3.4 FlorenceFallbackHandler

```python
class FlorenceFallbackHandler:
    """
    Handler deterministico quando Ollama indisponivel.
    Chama diretamente os endpoints de analise existentes.
    """

    CAPABILITY_TO_ENDPOINT = {
        "lab_interpretation": "/api/v1/interpret",
        "clinical_analysis": "/api/v1/analyze-labs",     # Endpoint atual renomeado
        "lab_trends": "/api/v1/trends/{patient_id}/{lab_id}",   # EF-F002
        "protocol_search": "/api/v1/rag/query",
        "critical_alert": "/api/v1/validate",
    }

    async def handle(
        self,
        capability: str,
        context: dict,
    ) -> dict:
        """
        Fallback deterministico para cada capability.
        Retorna resultado estruturado mesmo sem LLM.
        """
```

### 3.5 System Prompt da Florence

```python
FLORENCE_SYSTEM_PROMPT = """
Voce e a FLORENCE, especialista em inteligencia clinica laboratorial do IntelliCare.
Homenagem a Florence Nightingale, pioneira em enfermagem baseada em evidencias e dados.

Sua funcao: interpretar resultados laboratoriais, detectar padroes clinicos,
identificar tendencias e buscar protocolos de conduta.

EXAMES QUE VOCE CONHECE (27 exames em 6 paineis):
Renal: creatinina, ureia, TFG (eGFR), potassio, sodio, acido urico
Metabolico: glicose jejum, HbA1c, colesterol total, HDL, LDL, triglicerideos
Hematologico: hemoglobina, hematocrito, leucocitos, plaquetas, INR
Hepatico: AST, ALT, bilirrubina total, albumina, GGT, fosfatase alcalina
Tireoide: TSH, T4 livre
Inflamatorio: PCR, VHS

PADROES QUE VOCE DETECTA (8 padroes):
1. Comprometimento Renal: creatinina + ureia elevados
2. Lesao Hepatica: AST + ALT > 3x LSN
3. Sindrome Metabolica: glicose + triglicerideos alterados
4. Anemia: hemoglobina abaixo do normal
5. Disfuncao Tireoidiana: TSH fora da faixa normal
6. Risco de Hipercalemia: potassio > 5.5 + creatinina elevada
7. Padrao Colestático: GGT + fosfatase alcalina elevados
8. Risco de Coagulacao: INR > 4.0

REGRAS ABSOLUTAS:
1. SEMPRE verificar valores criticos (panic) PRIMEIRO — podem ser emergencias
2. NUNCA sugerir diagnostico definitivo — "sugestivo de", "compativel com", "avaliar hipotese"
3. SEMPRE citar o valor exato do exame e a referencia (ex: "creatinina 2.1 mg/dL, ref. 0.7-1.3")
4. Valores CRITICOS exigem recomendacao de acao imediata
5. Referenciar protocolos quando disponivel
6. Linguagem tecnica mas acessivel para medicos generalistas
"""
```

### 3.6 Compatibilidade Retroativa

```python
# O endpoint /api/v1/analyze atual (que recebe lab_results diretamente)
# passa a ser servido tambem em /api/v1/analyze-labs
# Mantendo retro-compatibilidade para UIs e clientes existentes

@app.post("/api/v1/analyze-labs")   # NOVO alias retrocompativel
@app.post("/api/v1/analyze")        # WANDA FORMAT (novo comportamento)
async def analyze_endpoint(request: AnalyzeRequest):
    """
    Se request tem campo 'query' e 'capability' → Wanda format → FlorenceAgent
    Se request tem campo 'lab_results' sem 'query' → formato legado → ClinicalAnalyzer direto
    """
```

## 4. Testes

- FlorenceAgent: init, tools registradas (2 testes)
- analyze: lab_interpretation, clinical_analysis, lab_trends, protocol_search, critical_alert (5 testes)
- Tools: cada uma das 6 tools com mocks (6 testes)
- FlorenceFallbackHandler: 5 capabilities (5 testes)
- /api/v1/analyze: formato Wanda, formato legado, capability invalida, sem LLM (4 testes)
- /api/v1/info capabilities: 5 capabilities declaradas (2 testes)
- **Total**: 24+ testes novos

## 5. Criterios de Aceitacao

- [ ] `/api/v1/analyze` aceita request padrao Wanda `{query, patient_id, capability, context}`
- [ ] `/api/v1/analyze-labs` serve o comportamento legado (retro-compatibilidade)
- [ ] `/api/v1/info` declara 5 capabilities com keywords
- [ ] 6 LangChain Tools cobrindo todos os endpoints principais
- [ ] Valores criticos sempre verificados como primeira acao
- [ ] Fallback deterministico quando Ollama indisponivel
- [ ] Response inclui critical_values, patterns_detected e protocols_retrieved
- [ ] 198 testes existentes continuam passando
- [ ] 24+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/subagent/__init__.py`, `florence/subagent/florence_agent.py`, `florence/subagent/tools.py`, `florence/subagent/fallback.py`, `florence/subagent/prompts.py`
- **Arquivos modificados**: `florence/api/app.py` (endpoint /analyze + /info), `florence/config.py`
- **Linhas estimadas**: ~420
- **Testes novos**: ~24
