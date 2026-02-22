# EF-W005 — Workflows Multi-Agente com LangGraph

> Fluxos de orquestracao complexos e multi-passo usando LangGraph para coordenacao de agentes.

## 1. Objetivo

Implementar workflows multi-agente usando LangGraph que permitem:
- Fluxos com multiplos passos dependentes (nao apenas consulta unica)
- Tomada de decisao condicionada a resultados intermediarios
- Loop de refinamento (LLM revisa e decide proximo passo)
- Execucao paralela de agentes independentes
- Fluxos com estado persistido (checkpoint)

## 2. Justificativa

- **Complexidade real**: "Analisar o paciente e criar plano de cuidado" requer Florence → Oswaldo → Geralda em sequencia
- **Condicional**: "Se TFG caiu abaixo de 30, agendar nefrologista urgente"
- **Iterativo**: LLM pode precisar de mais dados antes de concluir
- **Paralelo**: Florence e Oswaldo podem ser consultados simultaneamente
- **Estado**: Consultas longas nao podem perder progresso

## 3. Escopo

### 3.1 Workflows Definidos

#### WORKFLOW 1: Analise Clinica Completa
```
Trigger: Query clinica complexa com patient_id

[START]
    │
    ├─ (Paralelo)─────────────────────────────┐
    │   Florence: analise clinica              │
    │   Oswaldo: estagiamento cronico          │
    │   Geralda: estado da jornada             │
    └──────────────────────────────────────────┤
                                               │
    [Agregacao parcial]                        │
         │                                     │
         ▼
    LLM avalia: precisa de mais dados?
         │
         ├─ Sim → Florence: buscar labs especificos
         │                      │
         │                      ▼
         │                 [Agregar novamente]
         │
         └─ Nao → [Agregacao Final]
                       │
                       ▼
                  [END] Resposta completa
```

#### WORKFLOW 2: Pre-Internacao (Onboarding)
```
Trigger: clinical.admission (novo paciente)

[START]
    │
    ├─ Florence: carregar historico clinico
    ├─ Zilda: verificar UBS de referencia
    └─ Geralda: verificar jornada existente
         │
    [JOIN] ← aguarda os 3
         │
    LLM: este paciente tem jornada previa?
         │
         ├─ Sim → Geralda: recuperar e continuar jornada
         └─ Nao → Geralda: iniciar nova jornada (admissao)
                      │
                 [END] Jornada iniciada
```

#### WORKFLOW 3: Alerta Critico Multi-Agente
```
Trigger: clinical.condition_worsened (CRITICO)

[START] [alta prioridade]
    │
    ├─ Florence: analise do alerta
    ├─ Oswaldo: contexto da progressao
    └─ Geralda: estado atual da jornada
         │
    [Verificacao de gravidade]
         │
         ├─ MUITO GRAVE → Comunicacao: notificar equipe URGENTE
         │                Geralda: escalar jornada
         │                Donabedian: registrar para qualidade
         │
         └─ GRAVE → Comunicacao: notificar equipe
                    Geralda: ajustar plano automaticamente
         │
    [END] Alertas disparados
```

### 3.2 Definicao do Grafo LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class OrchestratorState(TypedDict):
    """Estado compartilhado durante execucao do workflow."""
    query: str
    patient_id: Optional[str]
    ips: Optional[dict]
    agent_responses: dict[str, AgentResponse]
    synthesis: Optional[str]
    next_step: str
    iterations: int
    max_iterations: int
    workflow_id: str
    error: Optional[str]


def build_clinical_analysis_graph() -> StateGraph:
    """
    Constroi o grafo LangGraph para analise clinica completa.
    """
    workflow = StateGraph(OrchestratorState)

    # Nos do grafo
    workflow.add_node("load_ips", load_patient_ips)
    workflow.add_node("query_florence", query_florence_agent)
    workflow.add_node("query_oswaldo", query_oswaldo_agent)
    workflow.add_node("query_geralda", query_geralda_agent)
    workflow.add_node("aggregate_partial", aggregate_partial_responses)
    workflow.add_node("check_completeness", llm_check_completeness)
    workflow.add_node("get_more_data", get_additional_data)
    workflow.add_node("final_aggregation", final_aggregation)

    # Arestas (fluxo)
    workflow.set_entry_point("load_ips")
    workflow.add_edge("load_ips", "query_florence")
    workflow.add_edge("load_ips", "query_oswaldo")   # Paralelo
    workflow.add_edge("load_ips", "query_geralda")   # Paralelo

    # JOIN (aguarda os 3)
    workflow.add_edge(["query_florence", "query_oswaldo", "query_geralda"],
                      "aggregate_partial")

    workflow.add_edge("aggregate_partial", "check_completeness")

    # Condicional: mais dados necessarios?
    workflow.add_conditional_edges(
        "check_completeness",
        lambda state: "more_data" if state["iterations"] < 2 else "finalize",
        {
            "more_data": "get_more_data",
            "finalize": "final_aggregation",
        }
    )

    workflow.add_edge("get_more_data", "aggregate_partial")
    workflow.add_edge("final_aggregation", END)

    return workflow.compile()
```

### 3.3 Nos do Grafo (Node Functions)

```python
async def load_patient_ips(state: OrchestratorState) -> OrchestratorState:
    """
    Carrega IPS do paciente (EF-W002).
    Aplica regra IPS-First.
    """

async def query_florence_agent(state: OrchestratorState) -> OrchestratorState:
    """
    Consulta Florence com query e IPS.
    Timeout configuravel (padrao 30s).
    """

async def llm_check_completeness(state: OrchestratorState) -> OrchestratorState:
    """
    LLM avalia se respostas sao suficientes.

    Prompt:
    "Dado a query '{query}' e as respostas dos agentes,
     as informacoes sao suficientes para responder?
     Responda: complete | need_more_data:florence:topico"
    """

async def final_aggregation(state: OrchestratorState) -> OrchestratorState:
    """
    Agrega todas as respostas em sintese final (EF-W004).
    """
```

### 3.4 Executor de Workflows

```python
class WorkflowExecutor:
    """Executa workflows LangGraph com controle e monitoramento."""

    WORKFLOW_REGISTRY = {
        "clinical_analysis": build_clinical_analysis_graph,
        "patient_onboarding": build_onboarding_graph,
        "critical_alert": build_critical_alert_graph,
    }

    async def execute(
        self,
        workflow_id: str,
        initial_state: dict,
        timeout: int = 60,
    ) -> WorkflowResult:
        """
        Executa workflow com timeout e tratamento de erros.

        Registra execution_id para rastreabilidade.
        """

    def select_workflow(
        self,
        intent: RoutingDecision,
        context: dict,
    ) -> Optional[str]:
        """
        Seleciona qual workflow usar.

        Logica:
        - Multi-agente complexo + condicional → workflow especifico
        - Simples (1-2 agentes, sem condicional) → fluxo direto
        """
```

### 3.5 Checkpoint de Estado

```python
class WorkflowCheckpointer:
    """
    Persistencia de estado de workflows longas.

    Para workflows que podem ser interrompidas e retomadas.
    Ex: workflow que aguarda resposta do paciente.
    """

    async def save_checkpoint(
        self,
        execution_id: str,
        state: OrchestratorState,
    ) -> None:
        """Salva estado atual no Redis (TTL 1 hora)."""

    async def restore_checkpoint(
        self,
        execution_id: str,
    ) -> Optional[OrchestratorState]:
        """Restaura estado de execucao pausada."""
```

### 3.6 Configuracao

```env
# LangGraph
INTELLICARE_WANDA_LANGGRAPH_ENABLED=true
INTELLICARE_WANDA_WORKFLOW_MAX_ITERATIONS=3
INTELLICARE_WANDA_WORKFLOW_TIMEOUT=60
INTELLICARE_WANDA_WORKFLOW_PARALLEL_TIMEOUT=30
```

## 4. Testes

- Build graphs: clinical_analysis, onboarding, critical_alert (3 testes)
- WorkflowExecutor: executa, timeout, erro em no (6 testes)
- Nos individuais: load_ips, query_agent, aggregate (5 testes)
- Condicional: need_more_data, finalize, max_iterations (4 testes)
- Paralelo: Florence e Oswaldo simultaneos (3 testes)
- Checkpointer: save, restore (3 testes)
- Selecao de workflow automatica (3 testes)
- **Total**: 27+ testes

## 5. Criterios de Aceitacao

- [ ] 3 workflows LangGraph definidos e funcionais
- [ ] Execucao paralela de agentes independentes
- [ ] Condicional LLM (need_more_data vs finalize)
- [ ] Limite de iteracoes configuravel (max 3)
- [ ] Timeout total e por no
- [ ] Checkpoint de estado no Redis
- [ ] Selecao automatica de workflow vs fluxo direto
- [ ] Rastreabilidade de cada no executado
- [ ] 27+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~4 (orchestrator, api, config, docker)
- **Linhas estimadas**: ~1.500
- **Testes novos**: ~27
