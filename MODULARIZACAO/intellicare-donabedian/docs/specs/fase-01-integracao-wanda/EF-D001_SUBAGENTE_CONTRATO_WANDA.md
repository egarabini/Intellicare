# EF-D001 — Subagente Donabedian + Contrato Wanda

> Implementar o subagente LangChain do Donabedian e o endpoint `/api/v1/analyze` no formato padrao Wanda, permitindo consultas conversacionais sobre qualidade assistencial.

## 1. Objetivo

Transformar o Donabedian de um repositorio de indicadores em um **agente conversacional de avaliacao de qualidade** capaz de:
- Responder perguntas sobre qualidade assistencial em linguagem natural
- Ser descoberto e usado pela Wanda automaticamente
- Usar os 30 endpoints existentes como LangChain Tools
- Fornecer avaliacao de qualidade no contexto de uma consulta clinica

## 2. Justificativa

- **Bloqueio critico**: Wanda nao consegue usar o Donabedian sem `/api/v1/analyze`
- Perguntas como "a qualidade assistencial do servico e adequada para este paciente?" devem ser respondidas automaticamente
- Donabedian avalia **estrutura** — o Oswaldo precisa saber se ha UTI disponivel e com qualidade certificada
- Compliance regulatorio: Donabedian e acionado em toda avaliacao clinica para contexto de estrutura

## 3. Escopo

### 3.1 Capabilities Declaradas no `/api/v1/info`

```python
# GET /api/v1/info — resposta atualizada
{
    "agent_name": "Donabedian",
    "version": "2.0.0",
    "description": "Motor de avaliacao de qualidade assistencial pelos 7 pilares de Donabedian",
    "homage": "Avedis Donabedian",
    "port": 8004,

    "capabilities": [
        {
            "id": "quality_assessment",
            "name": "Avaliacao de Qualidade",
            "description": "Score dos 7 pilares (Eficacia, Efetividade, Eficiencia, Otimidade, "
                           "Aceitabilidade, Legitimidade, Equidade) para o servico ou periodo",
            "keywords": ["qualidade", "pilar", "score", "avaliacao", "Donabedian",
                         "eficacia", "efetividade", "eficiencia", "equidade"],
            "input_types": ["period_start", "period_end", "pillar_id"],
            "output_types": ["quality_score", "pillar_scores", "overall_status"],
        },
        {
            "id": "triad_assessment",
            "name": "Avaliacao pela Triada Donabedian",
            "description": "Scores de Estrutura, Processo e Resultado",
            "keywords": ["estrutura", "processo", "resultado", "triada", "structure", "outcome"],
            "input_types": ["period_start", "period_end"],
            "output_types": ["triad_scores", "triad_status"],
        },
        {
            "id": "indicator_status",
            "name": "Status de Indicadores",
            "description": "Status atual dos indicadores de qualidade (verde/amarelo/vermelho)",
            "keywords": ["indicador", "meta", "status", "semaforo", "compliance"],
            "input_types": ["indicator_id", "period"],
            "output_types": ["indicator_status", "measurement_list"],
        },
        {
            "id": "quality_trends",
            "name": "Tendencias de Qualidade",
            "description": "Evolucao dos scores de qualidade ao longo do tempo",
            "keywords": ["tendencia", "evolucao", "historico", "piorou", "melhorou"],
            "input_types": ["pillar_id", "indicator_id", "period_months"],
            "output_types": ["trend_direction", "trend_slope", "timeline"],
        },
        {
            "id": "service_readiness",
            "name": "Prontidao do Servico",
            "description": "O servico tem estrutura e qualidade adequadas para atender determinado perfil de paciente?",
            "keywords": ["prontidao", "estrutura", "capacidade", "adequado", "pronto"],
            "input_types": ["service_type", "patient_profile"],
            "output_types": ["readiness_score", "gaps", "recommendations"],
        },
    ],

    "requires_patient_context": False,   # Donabedian avalia servico, nao paciente
    "supports_ips_first": False,

    "endpoints": {
        "analyze": "/api/v1/analyze",
        "health": "/api/v1/health",
        "info": "/api/v1/info",
    },
}
```

### 3.2 DonabedianAgent (LangChain)

```python
class DonabedianAgent:
    """
    Subagente Donabedian — avaliacao de qualidade via LangChain.

    Usa os endpoints REST existentes como ferramentas.
    Nao acessa banco diretamente — passa pela API.
    """

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="get_quality_scores",
                description="Score geral e por pilar de Donabedian para um periodo. "
                            "Use para perguntas sobre qualidade geral do servico, "
                            "score dos 7 pilares, ou status de qualidade.",
                func=self._tool_get_quality_scores,
            ),
            Tool(
                name="get_triad_scores",
                description="Scores da triada Donabedian: Estrutura, Processo, Resultado. "
                            "Use para perguntas sobre estrutura do servico, processos ou "
                            "resultados assistenciais.",
                func=self._tool_get_triad_scores,
            ),
            Tool(
                name="get_indicators_status",
                description="Lista de indicadores com status atual (verde/amarelo/vermelho). "
                            "Use para 'quais indicadores estao abaixo da meta', "
                            "'ha indicadores criticos', 'status dos indicadores'.",
                func=self._tool_get_indicators_status,
            ),
            Tool(
                name="get_pillar_trend",
                description="Tendencia de um pilar especifico ao longo do tempo. "
                            "Use para 'o pilar de efetividade melhorou?', "
                            "'qual a tendencia de qualidade dos ultimos 6 meses'.",
                func=self._tool_get_pillar_trend,
            ),
            Tool(
                name="get_indicator_detail",
                description="Detalhes de um indicador especifico: historico, meta, formula. "
                            "Use quando perguntar sobre um indicador por nome.",
                func=self._tool_get_indicator_detail,
            ),
            Tool(
                name="assess_service_readiness",
                description="Avalia se o servico tem estrutura de qualidade adequada "
                            "para atender um perfil de paciente (ex: paciente CKD G4 "
                            "precisa de dialise com qualidade certificada). "
                            "Combina score de estrutura + indicadores relevantes.",
                func=self._tool_assess_service_readiness,
            ),
        ]

    async def analyze(
        self,
        query: str,
        context: dict,
    ) -> DonabedianAnalysis:
        """
        Processa consulta de qualidade via LangChain ReAct Agent.

        Exemplos:
        Query: "O servico tem qualidade adequada?"
        -> get_quality_scores() + get_triad_scores()
        -> "Score geral: 73/100 (bom). Estrutura: 82, Processo: 69, Resultado: 68.
            Pilar de Eficiencia (58) e Equidade (51) abaixo de 60 — atencao necessaria."

        Query: "Ha indicadores criticos?"
        -> get_indicators_status(status_filter="red")
        -> "3 indicadores em vermelho: Taxa de infeccao hospitalar (3.2%, meta <2%),
            Tempo porta-balao (95min, meta <90min), Adesao ao checklist (78%, meta >90%)."
        """
```

### 3.3 Endpoint `/api/v1/analyze` (Contrato Wanda)

```python
# POST /api/v1/analyze
# Request (padrao Wanda — sem patient_id pois Donabedian avalia servico)
{
    "query": "Qual a qualidade assistencial do servico no ultimo trimestre?",
    "patient_id": null,
    "capability": "quality_assessment",
    "context": {
        "requesting_agent": "wanda",
        "session_id": "abc-123",
        "period_months": 3,
    },
}

# Response
{
    "success": True,
    "agent": "donabedian",
    "capability_used": "quality_assessment",
    "result": {
        "period": "2025-11-01 a 2026-01-31",
        "overall_score": 71.4,
        "overall_status": "yellow",
        "pillar_scores": {
            "eficacia": {"score": 82.0, "status": "green"},
            "efetividade": {"score": 74.0, "status": "yellow"},
            "eficiencia": {"score": 58.0, "status": "red"},
            "otimidade": {"score": 68.0, "status": "yellow"},
            "aceitabilidade": {"score": 77.0, "status": "yellow"},
            "legitimidade": {"score": 75.0, "status": "yellow"},
            "equidade": {"score": 51.0, "status": "red"},
        },
        "triad_scores": {
            "structure": {"score": 79.0, "status": "yellow"},
            "process": {"score": 70.0, "status": "yellow"},
            "outcome": {"score": 65.0, "status": "yellow"},
        },
        "critical_indicators": [
            {"name": "Taxa de infeccao hospitalar", "value": 3.2, "target": 2.0, "status": "red"},
        ],
        "improving_pillars": ["eficacia", "legitimidade"],
        "declining_pillars": ["eficiencia"],
    },
    "summary": "Qualidade assistencial em nivel intermediario (71.4/100). "
               "Eficiencia (58) e Equidade (51) requerem atencao prioritaria. "
               "Taxa de infeccao hospitalar acima da meta (3.2% vs meta <2%). "
               "Eficacia melhorando nos ultimos 3 meses.",
    "confidence": 0.88,
    "metadata": {
        "processing_time_ms": 420,
        "tools_used": ["get_quality_scores", "get_triad_scores", "get_indicators_status"],
        "indicators_evaluated": 15,
        "data_period": "90 dias",
    },
}
```

### 3.4 DonabedianFallbackHandler

```python
class DonabedianFallbackHandler:
    """
    Handler deterministico quando Ollama indisponivel.
    Chama diretamente os endpoints de assessment existentes.
    """

    CAPABILITY_TO_ENDPOINT = {
        "quality_assessment": "/api/v1/assess",
        "triad_assessment": "/api/v1/assessment/triad",
        "indicator_status": "/api/v1/dashboard/indicators",
        "quality_trends": "/api/v1/trends/pillar/{pillar_id}",
        "service_readiness": "/api/v1/assess",   # Combinacao de assess + filtros
    }
```

### 3.5 System Prompt do Donabedian

```python
DONABEDIAN_SYSTEM_PROMPT = """
Voce e o DONABEDIAN, especialista em avaliacao de qualidade assistencial do IntelliCare.
Homenagem a Avedis Donabedian, pai da avaliacao de qualidade em saude.

Sua funcao: avaliar a qualidade dos servicos de saude usando os 7 pilares de Donabedian
e a triada Estrutura-Processo-Resultado.

OS 7 PILARES:
1. Eficacia: o tratamento funciona em condicoes ideais?
2. Efetividade: funciona na pratica real (nao apenas em ensaios)?
3. Eficiencia: funciona com uso otimo de recursos (custo-beneficio)?
4. Otimidade: o melhor balanco entre beneficio e custo?
5. Aceitabilidade: o paciente/familia aceita e adere?
6. Legitimidade: conforme normas, etica e sociedade?
7. Equidade: distribuicao justa independente de raca, renda, genero?

TRIADA:
- Estrutura: recursos fisicos, humanos e organizacionais
- Processo: o que e feito e como
- Resultado: o que foi alcanado

REGRAS ABSOLUTAS:
1. Sempre contextualizar o score (71% e bom ou ruim? Comparado a que?)
2. Priorizar indicadores em VERMELHO — sao os urgentes
3. Nao fazer julgamentos de valor sem dados — basear-se apenas nos indicadores registrados
4. Linguagem tecnica de gestao em saude (para gestores e profissionais)
5. Sempre citar o pilar ou dimensao da triada ao fazer uma afirmacao
"""
```

### 3.6 Arquitetura de Arquivos

```
src/donabedian/
  subagent/
    __init__.py
    donabedian_agent.py    # DonabedianAgent com LangChain
    tools.py               # Tool definitions
    fallback.py            # DonabedianFallbackHandler
    prompts.py             # DONABEDIAN_SYSTEM_PROMPT
```

## 4. Testes

- DonabedianAgent: init, tools registradas (2 testes)
- analyze: quality_assessment, triad, indicators, trends, service_readiness (5 testes)
- Tools: cada uma das 6 tools (6 testes)
- DonabedianFallbackHandler: 5 capabilities (5 testes)
- /api/v1/analyze: sucesso, sem LLM, capability invalida (4 testes)
- /api/v1/info capabilities (2 testes)
- **Total**: 24+ testes novos

## 5. Criterios de Aceitacao

- [ ] `/api/v1/analyze` aceita request padrao Wanda (sem patient_id obrigatorio)
- [ ] `/api/v1/info` declara 5 capabilities com keywords
- [ ] 6 LangChain Tools cobrindo todos os endpoints principais
- [ ] Response inclui pillar_scores, triad_scores e critical_indicators
- [ ] Fallback deterministico quando Ollama indisponivel
- [ ] 363 testes v1.0 continuam passando
- [ ] 24+ testes novos
- [ ] Cobertura >= 80%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `subagent/donabedian_agent.py`, `subagent/tools.py`, `subagent/fallback.py`, `subagent/prompts.py`
- **Arquivos modificados**: `api/routes/health.py` (update /info), `api/main.py` (novo endpoint)
- **Linhas estimadas**: ~380
- **Testes novos**: ~24
