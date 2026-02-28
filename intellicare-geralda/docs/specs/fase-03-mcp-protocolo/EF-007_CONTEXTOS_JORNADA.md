# EF-007 — Contextos de Jornada do Paciente

> Identificacao, ativacao e gestao dos contextos da jornada de cuidado do paciente.

## 1. Objetivo

Implementar a camada **Context** do MCP (Model-Context-Protocol), responsavel por:
- Identificar em qual momento da jornada o paciente se encontra
- Ativar contextos apropriados baseado em eventos recebidos
- Gerenciar transicoes entre estados da jornada
- Manter historico de contextos ativos/concluidos
- Fornecer ao LLM (Ollama) o contexto correto para gerar respostas

## 2. Justificativa

- **Inteligencia contextual**: Geralda responde diferente a um paciente recem-internado vs pos-alta
- **Protocolo correto**: Cada contexto aciona protocolos especificos (EF-008)
- **Rastreabilidade**: Saber exatamente onde o paciente esta na jornada
- **Continuidade**: Equipe visualiza o caminho percorrido pelo paciente
- **Automacao**: Transicoes podem disparar acoes automaticas

## 3. Escopo

### 3.1 Arquitetura

```
geralda/mcp/
  contexts/
    __init__.py
    context_types.py        # Enum + dataclass dos contextos
    context_manager.py      # Ativacao, transicao, encerramento
    context_rules.py        # Regras de ativacao por evento
    journey_state.py        # Maquina de estados da jornada
    context_store.py        # Persistencia de contextos
```

### 3.2 Macroestados da Jornada (E0 a E7)

A jornada do paciente no BemCuidar segue 8 macroestados:

```
E0 ──► E1 ──► E2 ──► E3 ──► E4 ──► E5 ──► E6 ──► E7
│      │      │      │      │      │      │      │
Sem    Inter-  Enga-  Cuida-  Prog.  Alta   Pos-   Encer-
Jorn.  nacao   jam.   dos     Alta   Clin.  Alta   ramento
```

```python
class JourneyMacroState(str, Enum):
    """Macroestados da jornada do paciente."""
    E0_SEM_JORNADA = "E0"            # Sem jornada ativa
    E1_INTERNACAO = "E1"             # Paciente internado
    E2_ENGAJAMENTO = "E2"           # Engajamento digital iniciado
    E3_CUIDADOS_ATIVOS = "E3"       # Cuidados e acompanhamento ativo
    E4_PROGRAMACAO_ALTA = "E4"      # Alta programada, preparacao
    E5_ALTA_CLINICA = "E5"          # Alta clinica efetivada
    E6_POS_ALTA = "E6"             # Acompanhamento pos-alta
    E7_ENCERRAMENTO = "E7"          # Jornada encerrada
```

### 3.3 Tipologia de Contextos (5 Categorias)

#### C — Contextos Clinicos
| ID | Nome | Trigger | Macroestado |
|----|------|---------|-------------|
| C1 | Paciente Internado | `clinical.admission` | E1 |
| C41 | Alta Clinica | `clinical.discharge` | E5 |
| C51 | Triagem de Sintomas/Risco | `clinical.vital_sign_alert` | E3/E6 |

#### D — Contextos Digitais/IA
| ID | Nome | Trigger | Macroestado |
|----|------|---------|-------------|
| C12 | Conversa Inbound | `digital.message_received` | Qualquer |
| C21 | Engajamento Digital Paciente | `digital.patient_onboarded` | E2 |
| C22 | Engajamento Digital APS | `digital.aps_contacted` | E2 |
| C23 | Educacao Familiar | `digital.education_completed` | E3 |

#### O — Contextos Operacionais
| ID | Nome | Trigger | Macroestado |
|----|------|---------|-------------|
| C33 | Programacao de Alta | `operational.discharge_planned` | E4 |
| C52 | Acompanhamento Pos-Alta | Transicao de E5 | E6 |
| C72 | Problema/Quebra Vinculo APS | `operational.referral_failed` | E6 |

#### G — Contextos de Governanca
| ID | Nome | Trigger | Macroestado |
|----|------|---------|-------------|
| C90 | Verificacao de Consistencia | Timer (diario) | Qualquer |
| C91 | Conflito de Estado | Evento inconsistente | Qualquer |
| C92 | Retentativa de Acao Falha | Acao com erro | Qualquer |

#### H — Contextos Humano-IA-Humano
| ID | Nome | Trigger | Macroestado |
|----|------|---------|-------------|
| C81 | Assistencia IA ao Profissional | Chat profissional | E3 |
| C82 | Assistencia IA ao Paciente | Chat paciente | E3/E6 |
| C83 | Sugestao de Intervencao | `care.adherence_low` | E3/E6 |

### 3.4 Regras de Ativacao

```python
class ContextActivationRules:
    """Define quais eventos ativam quais contextos."""

    RULES: dict[str, ContextActivationRule] = {
        # Contextos Clinicos
        "clinical.admission": ContextActivationRule(
            context_id="C1",
            preconditions=["macrostate == E0"],
            transitions_to=JourneyMacroState.E1_INTERNACAO,
            priority=1,  # Alta prioridade
        ),
        "clinical.discharge": ContextActivationRule(
            context_id="C41",
            preconditions=["macrostate in (E3, E4)"],
            transitions_to=JourneyMacroState.E5_ALTA_CLINICA,
            priority=1,
        ),
        "clinical.vital_sign_alert": ContextActivationRule(
            context_id="C51",
            preconditions=["macrostate in (E3, E6)"],
            transitions_to=None,  # Nao muda macroestado
            priority=1,
        ),

        # Contextos Digitais
        "digital.patient_onboarded": ContextActivationRule(
            context_id="C21",
            preconditions=["macrostate == E1", "C1 ativo"],
            transitions_to=JourneyMacroState.E2_ENGAJAMENTO,
            priority=2,
        ),
        "digital.message_received": ContextActivationRule(
            context_id="C12",
            preconditions=[],  # Sempre pode receber mensagem
            transitions_to=None,
            priority=3,
        ),

        # Contextos Operacionais
        "operational.discharge_planned": ContextActivationRule(
            context_id="C33",
            preconditions=["macrostate == E3"],
            transitions_to=JourneyMacroState.E4_PROGRAMACAO_ALTA,
            priority=2,
        ),

        # Contextos Humano-IA
        "care.adherence_low": ContextActivationRule(
            context_id="C83",
            preconditions=["macrostate in (E3, E6)", "adesao < 0.6"],
            transitions_to=None,
            priority=2,
        ),
    }

    def get_context_for_event(
        self,
        event_type: str,
        current_state: JourneyState,
    ) -> Optional[ContextActivationRule]:
        """
        Retorna regra de ativacao se o evento dispara um contexto.

        Verifica:
        1. Evento esta no catalogo?
        2. Preconditions satisfeitas?
        3. Contexto ja nao esta ativo?
        4. Prioridade vs contextos concorrentes

        Returns:
            ContextActivationRule ou None se nao ativar
        """
```

### 3.5 Gerenciador de Contextos

```python
class ContextManager:
    """Gerencia ciclo de vida dos contextos da jornada."""

    def __init__(
        self,
        rules: ContextActivationRules,
        journey_state: JourneyStateMachine,
        context_store: ContextStore,
    ):
        ...

    async def evaluate_event(
        self,
        enriched_event: EnrichedEvent,
    ) -> ContextEvaluation:
        """
        Avalia se evento deve ativar/atualizar/encerrar contexto.

        Returns:
            ContextEvaluation:
              - context_activated: Optional[str] (ID do contexto)
              - context_updated: Optional[str]
              - context_closed: Optional[str]
              - macrostate_transition: Optional[tuple[str, str]]  # (de, para)
              - protocol_to_execute: Optional[str]  # ID do protocolo
        """

    async def activate_context(
        self,
        context_id: str,
        patient_id: str,
        trigger_event: IntelliCareEvent,
    ) -> ActiveContext:
        """
        Ativa um contexto para o paciente.

        Passos:
        1. Verifica preconditions
        2. Cria registro do contexto ativo
        3. Atualiza macroestado se necessario
        4. Determina protocolo a executar
        5. Registra na timeline
        """

    async def close_context(
        self,
        context_id: str,
        patient_id: str,
        reason: str,
    ) -> None:
        """Encerra contexto (completado, cancelado, expirado)."""

    async def get_active_contexts(
        self,
        patient_id: str,
    ) -> list[ActiveContext]:
        """Retorna contextos ativos do paciente."""

    async def get_journey_state(
        self,
        patient_id: str,
    ) -> JourneyState:
        """
        Retorna estado completo da jornada:
        - Macroestado atual (E0-E7)
        - Contextos ativos
        - Contextos historicos
        - Tempo no macroestado atual
        - Proximas transicoes possiveis
        """
```

### 3.6 Maquina de Estados da Jornada

```python
class JourneyStateMachine:
    """Maquina de estados semantica (nao puramente matematica)."""

    # Transicoes validas entre macroestados
    VALID_TRANSITIONS = {
        "E0": ["E1"],                    # Sem jornada → Internacao
        "E1": ["E2", "E7"],             # Internacao → Engajamento ou Encerramento
        "E2": ["E3", "E7"],             # Engajamento → Cuidados ou Encerramento
        "E3": ["E4", "E5", "E7"],       # Cuidados → Prog. Alta, Alta, ou Encerramento
        "E4": ["E5", "E3", "E7"],       # Prog. Alta → Alta, Volta Cuidados, ou Encerramento
        "E5": ["E6", "E7"],             # Alta → Pos-alta ou Encerramento
        "E6": ["E3", "E7"],             # Pos-alta → Reinternacao ou Encerramento
        "E7": ["E0"],                    # Encerramento → Sem jornada (nova jornada)
    }

    async def transition(
        self,
        patient_id: str,
        from_state: str,
        to_state: str,
        trigger: IntelliCareEvent,
    ) -> TransitionResult:
        """
        Executa transicao de macroestado.

        Validacoes:
        1. Transicao e valida? (VALID_TRANSITIONS)
        2. Paciente esta no from_state?
        3. Preconditions do to_state satisfeitas?

        Acoes:
        1. Fecha contextos do macroestado anterior
        2. Atualiza macroestado
        3. Registra transicao na timeline
        4. Notifica Wanda sobre mudanca de estado
        """

    async def get_possible_transitions(
        self,
        patient_id: str,
    ) -> list[str]:
        """Retorna proximos macroestados possiveis."""
```

### 3.7 Estado da Jornada (Model)

```python
@dataclass
class JourneyState:
    """Estado completo da jornada do paciente (camada Model do MCP)."""
    patient_id: str
    macrostate: JourneyMacroState
    macrostate_since: datetime
    active_contexts: list[ActiveContext]
    conditions: list[str]            # ICD-10 ativas
    active_care_plans: list[str]     # IDs dos planos ativos
    risk_level: str                  # baixo, medio, alto, critico
    adherence_score: float           # 0.0-1.0
    last_contact: Optional[datetime] # Ultima interacao
    preferences: dict                # Canal, idioma, horarios
    journey_history: list[dict]      # Historico de transicoes
```

### 3.8 Tabelas de Persistencia

```sql
-- Estado da jornada do paciente
CREATE TABLE patient_journey (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) UNIQUE NOT NULL,
    macrostate VARCHAR(5) NOT NULL DEFAULT 'E0',
    macrostate_since TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    risk_level VARCHAR(20) DEFAULT 'medio',
    adherence_score FLOAT DEFAULT 1.0,
    last_contact TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_journey_patient ON patient_journey(patient_id);
CREATE INDEX idx_journey_macrostate ON patient_journey(macrostate);

-- Contextos ativos e historicos
CREATE TABLE journey_contexts (
    id BIGSERIAL PRIMARY KEY,
    context_id VARCHAR(10) NOT NULL,       -- C1, C21, C22, etc.
    patient_id VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',   -- active, completed, cancelled, expired
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    trigger_event_id UUID,                 -- Evento que ativou
    close_reason VARCHAR(100),
    protocol_executed VARCHAR(50),
    actions_taken JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contexts_patient ON journey_contexts(patient_id);
CREATE INDEX idx_contexts_status ON journey_contexts(status);
CREATE INDEX idx_contexts_active ON journey_contexts(patient_id, status) WHERE status = 'active';

-- Transicoes de macroestado (historico imutavel)
CREATE TABLE journey_transitions (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    from_state VARCHAR(5) NOT NULL,
    to_state VARCHAR(5) NOT NULL,
    trigger_event_id UUID,
    trigger_event_type VARCHAR(100),
    context_activated VARCHAR(10),
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_transitions_patient ON journey_transitions(patient_id);
CREATE INDEX idx_transitions_date ON journey_transitions(transitioned_at);
```

### 3.9 Contexto para o LLM

O ContextManager fornece contexto formatado para o LLM (Ollama) via EF-003:

```python
async def get_llm_context(self, patient_id: str) -> str:
    """
    Gera texto de contexto para injecao no system prompt do LLM.

    Exemplo de saida:
    ---
    JORNADA DO PACIENTE:
    - Estado atual: E3 (Cuidados Ativos) desde 05/02/2026
    - Contextos ativos: C82 (Assistencia IA ao Paciente), C23 (Educacao Familiar)
    - Condicoes: DRC Estagio 3a (N18.3), Diabetes Tipo 2 (E11)
    - Nivel de risco: MEDIO
    - Adesao: 72% (boa, mas em queda nos ultimos 7 dias)
    - Ultimo contato: Ontem, 14:30

    HISTORICO RECENTE:
    - 10/02: Completou material educativo "Alimentacao para DRC"
    - 08/02: Faltou lembrete de medicamento (Losartana 50mg)
    - 05/02: Consulta com nefrologista — ajuste de dieta
    ---
    """
```

### 3.10 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/journey/{patient_id}` | Estado completo da jornada |
| GET | `/api/v1/journey/{patient_id}/contexts` | Contextos ativos |
| GET | `/api/v1/journey/{patient_id}/timeline` | Timeline de transicoes |
| GET | `/api/v1/journey/{patient_id}/transitions` | Transicoes possiveis |
| POST | `/api/v1/journey/{patient_id}/transition` | Forcar transicao manual |

## 4. Diagrama de Fluxo Completo

```
Evento recebido (EF-006)
    │
    ▼
ContextManager.evaluate_event()
    │
    ├─ Evento nao dispara contexto → Registra e retorna
    │
    ├─ Preconditions nao satisfeitas → Registra rejeicao
    │
    └─ Contexto deve ser ativado:
         │
         ▼
    activate_context()
         │
         ├─ Macroestado muda? ──► JourneyStateMachine.transition()
         │                              │
         │                              ├─ Fecha contextos antigos
         │                              ├─ Atualiza macroestado
         │                              └─ Notifica Wanda
         │
         ├─ Determina protocolo (EF-008)
         │
         └─ Retorna ContextEvaluation com:
              - context_activated
              - protocol_to_execute
              - macrostate_transition (se houver)
```

## 5. Testes

- JourneyMacroState: enum e transicoes validas (5 testes)
- ContextActivationRules: cada regra, preconditions (10 testes)
- ContextManager: ativacao, encerramento, multiplos ativos (10 testes)
- JourneyStateMachine: transicoes validas, invalidas, reinternacao (8 testes)
- JourneyState: construcao, atualizacao, serializacao (4 testes)
- LLM context generation (3 testes)
- Endpoints: journey, contexts, timeline, transition (5 testes)
- **Total**: 45+ testes

## 6. Criterios de Aceitacao

- [ ] 8 macroestados (E0-E7) com transicoes validas
- [ ] 16+ contextos catalogados (C, D, O, G, H)
- [ ] Regras de ativacao por tipo de evento
- [ ] Preconditions verificadas antes de ativacao
- [ ] Maquina de estados com transicoes validas/invalidas
- [ ] Historico imutavel de transicoes
- [ ] Contexto formatado para LLM (Ollama)
- [ ] Tabelas patient_journey, journey_contexts, journey_transitions
- [ ] 5 endpoints funcionais
- [ ] 45+ testes
- [ ] Cobertura >= 85%

## 7. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~4 (config, api, event_pipeline, docker)
- **Linhas estimadas**: ~1.800
- **Testes novos**: ~45
