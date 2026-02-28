# EF-008 — Motor de Protocolos Institucionais

> Execucao deterministica de protocolos clinicos versionados baseados no contexto da jornada.

## 1. Objetivo

Implementar a camada **Protocol** do MCP (Model-Context-Protocol), responsavel por:
- Transformar contextos de jornada em acoes concretas e auditaveis
- Executar protocolos institucionais de forma deterministica
- Versionar protocolos (BCCO — Base de Conhecimento Clinico-Operacional)
- Garantir rastreabilidade completa (entrada → decisao → acao → evidencia)
- Separar logica de protocolo da logica de aplicacao

## 2. Justificativa

- **Padronizacao**: Todos os pacientes recebem o mesmo cuidado no mesmo contexto
- **Auditoria**: Cada acao tem protocolo, versao e justificativa rastreavel
- **Governanca**: NGC (Nucleo de Gestao Clinica) valida protocolos antes da ativacao
- **Seguranca**: Protocolo impede acoes fora do escopo clinico
- **Evolucao**: Protocolos podem ser atualizados sem alterar codigo

## 3. Escopo

### 3.1 Arquitetura

```
geralda/mcp/
  protocols/
    __init__.py
    protocol_engine.py        # Motor de execucao
    protocol_registry.py      # Registro/catalogo de protocolos
    protocol_loader.py        # Carrega protocolos do DB/YAML
    protocol_versioning.py    # Versionamento e validacao
    action_executor.py        # Executa acoes do protocolo
    evidence_generator.py     # Gera evidencias FHIR
  protocols_data/
    bemcuidar_v1/
      C1_internacao.yaml
      C21_engajamento_digital.yaml
      C22_engajamento_aps.yaml
      C33_programacao_alta.yaml
      C41_alta_clinica.yaml
      C51_triagem_risco.yaml
      C52_acompanhamento_pos_alta.yaml
      C82_assistencia_paciente.yaml
      C83_sugestao_intervencao.yaml
```

### 3.2 Estrutura de um Protocolo

```python
@dataclass
class Protocol:
    """Protocolo institucional executavel."""
    protocol_id: str              # ex: "P-C21-ENGAJAMENTO-V1"
    name: str                     # ex: "Engajamento Digital Inicial"
    version: str                  # ex: "1.0.0" (semver)
    context_id: str               # Contexto que dispara (ex: "C21")
    description: str
    approved_by: str              # NGC, equipe tecnica
    approved_at: datetime
    effective_from: datetime      # Valido a partir de
    effective_until: Optional[datetime]  # Valido ate (None = sem expiracao)

    # Preconditions para execucao
    preconditions: list[str]

    # Passos do protocolo (sequencia ordenada)
    steps: list[ProtocolStep]

    # Metadata
    tags: list[str]
    severity: str                 # low, medium, high, critical
```

```python
@dataclass
class ProtocolStep:
    """Passo individual do protocolo."""
    step_id: str                  # ex: "step-1"
    order: int                    # Ordem de execucao
    action_type: str              # Tipo de acao (ver catalogo 3.4)
    description: str              # Descricao legivel
    parameters: dict              # Parametros da acao
    condition: Optional[str]      # Condicao para executar (opcional)
    on_failure: str               # "skip", "retry", "abort", "escalate"
    timeout_seconds: int          # Timeout do passo
    evidence_type: Optional[str]  # Tipo de evidencia FHIR a gerar
```

### 3.3 Exemplo Completo — Protocolo C21 (Engajamento Digital)

```yaml
# bemcuidar_v1/C21_engajamento_digital.yaml
protocol_id: "P-C21-ENGAJAMENTO-V1"
name: "Engajamento Digital Inicial do Paciente"
version: "1.0.0"
context_id: "C21"
description: >
  Protocolo executado quando paciente/acompanhante e engajado
  digitalmente no BemCuidar. Envia boas-vindas, coleta consentimento,
  registra preferencias e inicia trilha educativa.
approved_by: "NGC"
approved_at: "2026-02-15"
effective_from: "2026-02-15"
severity: "medium"
tags: ["engajamento", "onboarding", "digital"]

preconditions:
  - "macrostate == E1 or macrostate == E2"
  - "patient.consent_status != 'active'"

steps:
  - step_id: "step-1"
    order: 1
    action_type: "send_message"
    description: "Enviar mensagem de boas-vindas personalizada"
    parameters:
      template: "welcome_patient"
      channel: "preferred"
      personalize: true
      reading_level: "from_patient_profile"
    on_failure: "retry"
    timeout_seconds: 30
    evidence_type: "Communication"

  - step_id: "step-2"
    order: 2
    action_type: "request_consent"
    description: "Solicitar consentimento digital LGPD"
    parameters:
      consent_type: "digital_engagement"
      channels: ["whatsapp", "sms", "email"]
      mandatory: true
    condition: "patient.consent_status != 'active'"
    on_failure: "escalate"
    timeout_seconds: 0  # Async — aguarda resposta
    evidence_type: "Consent"

  - step_id: "step-3"
    order: 3
    action_type: "collect_preferences"
    description: "Coletar preferencias de comunicacao"
    parameters:
      fields: ["preferred_channel", "quiet_hours", "reading_level", "language"]
    condition: "consent.status == 'active'"
    on_failure: "skip"
    timeout_seconds: 0
    evidence_type: null

  - step_id: "step-4"
    order: 4
    action_type: "create_learning_path"
    description: "Iniciar trilha educativa por condicao"
    parameters:
      conditions: "from_patient_conditions"
      auto_start: true
    condition: "consent.status == 'active'"
    on_failure: "skip"
    timeout_seconds: 30
    evidence_type: "CarePlan"

  - step_id: "step-5"
    order: 5
    action_type: "notify_team"
    description: "Notificar equipe sobre engajamento"
    parameters:
      channel: "rocketchat"
      room: "#equipe-{unit_id}"
      message_template: "patient_engaged"
      severity: "low"
    on_failure: "skip"
    timeout_seconds: 15
    evidence_type: null

  - step_id: "step-6"
    order: 6
    action_type: "update_journey_state"
    description: "Atualizar estado da jornada para E2"
    parameters:
      new_macrostate: "E2"
    on_failure: "abort"
    timeout_seconds: 5
    evidence_type: "AuditEvent"
```

### 3.4 Catalogo de Tipos de Acao

| action_type | Descricao | Executor |
|-------------|-----------|----------|
| `send_message` | Envia mensagem ao paciente/equipe | ComunicacaoClient |
| `request_consent` | Solicita consentimento digital | ConsentManager |
| `collect_preferences` | Coleta preferencias | PreferenceService |
| `create_care_plan` | Cria plano de cuidado | CareManager |
| `update_care_plan` | Atualiza plano existente | CareManager |
| `create_task` | Adiciona tarefa ao plano | CareManager |
| `create_reminder` | Cria lembrete | ReminderEngine |
| `create_learning_path` | Inicia trilha educativa | EducationEngine |
| `generate_education` | Gera material educativo via IA | ContentGenerator |
| `send_education` | Envia material educativo | ComunicacaoClient |
| `schedule_teleconsult` | Agenda teleconsulta | TeleconsultService |
| `generate_summary` | Gera resumo clinico via IA | LLMProvider |
| `notify_team` | Notifica equipe | ComunicacaoClient |
| `escalate` | Escala para profissional | AlertService |
| `update_journey_state` | Atualiza macroestado | JourneyStateMachine |
| `sync_fhir` | Sincroniza com FHIR Server | FHIRSync |
| `log_audit` | Registra evento de auditoria | AuditLogger |
| `wait_for_response` | Aguarda resposta (async) | EventConsumer |

### 3.5 Motor de Execucao

```python
class ProtocolEngine:
    """Executa protocolos de forma deterministica e auditavel."""

    def __init__(
        self,
        registry: ProtocolRegistry,
        action_executor: ActionExecutor,
        evidence_generator: EvidenceGenerator,
    ):
        ...

    async def execute(
        self,
        protocol_id: str,
        patient_id: str,
        trigger_event: IntelliCareEvent,
        enriched_context: EnrichedEvent,
    ) -> ProtocolExecutionResult:
        """
        Executa protocolo passo a passo.

        Fluxo:
        1. Carrega protocolo do registry
        2. Verifica versao vigente
        3. Valida preconditions
        4. Para cada step:
           a. Avalia condition (se houver)
           b. Executa acao via ActionExecutor
           c. Registra resultado
           d. Gera evidencia FHIR (se configurado)
           e. Se falhou: aplica on_failure (skip/retry/abort/escalate)
        5. Registra resultado final na tabela protocol_executions
        6. Retorna ProtocolExecutionResult

        Propriedades:
        - DETERMINISTICO: mesmos inputs = mesmas acoes
        - IDEMPOTENTE: re-execucao nao duplica efeitos
        - AUDITAVEL: cada passo registrado com timestamp
        - RESILIENTE: falhas isoladas nao derrubam pipeline
        """

    async def execute_step(
        self,
        step: ProtocolStep,
        patient_id: str,
        context: dict,
    ) -> StepResult:
        """Executa um passo individual do protocolo."""

    async def handle_failure(
        self,
        step: ProtocolStep,
        error: Exception,
        patient_id: str,
    ) -> FailureAction:
        """
        Trata falha conforme configuracao do passo:
        - skip: Pula e continua
        - retry: Tenta novamente (max 3x com backoff)
        - abort: Para execucao do protocolo
        - escalate: Notifica equipe e continua
        """
```

### 3.6 Executor de Acoes

```python
class ActionExecutor:
    """Resolve e executa acoes dos protocolos."""

    def __init__(
        self,
        care_manager,           # Para acoes de cuidado
        reminder_engine,        # Para lembretes
        education_engine,       # Para educacao
        comunicacao_client,     # Para mensagens
        fhir_sync,             # Para FHIR
        llm_provider,          # Para IA
        teleconsult_service,   # Para agendamento
    ):
        ...

    # Mapeamento action_type → metodo executor
    ACTION_MAP = {
        "send_message": "_execute_send_message",
        "create_care_plan": "_execute_create_care_plan",
        "create_reminder": "_execute_create_reminder",
        "create_learning_path": "_execute_create_learning_path",
        "generate_education": "_execute_generate_education",
        "schedule_teleconsult": "_execute_schedule_teleconsult",
        "generate_summary": "_execute_generate_summary",
        "notify_team": "_execute_notify_team",
        "escalate": "_execute_escalate",
        "update_journey_state": "_execute_update_journey_state",
        "sync_fhir": "_execute_sync_fhir",
        "log_audit": "_execute_log_audit",
        # ...
    }

    async def execute(
        self,
        action_type: str,
        parameters: dict,
        patient_id: str,
        context: dict,
    ) -> ActionResult:
        """
        Resolve e executa acao pelo tipo.

        Interpola parametros com contexto do paciente.
        Ex: "channel": "preferred" → resolve para "whatsapp" do paciente
        Ex: "conditions": "from_patient_conditions" → resolve para ["N18.3", "E11"]
        """
```

### 3.7 Gerador de Evidencias

```python
class EvidenceGenerator:
    """Gera evidencias FHIR para cada acao executada."""

    async def generate(
        self,
        evidence_type: str,
        step: ProtocolStep,
        result: ActionResult,
        patient_id: str,
    ) -> dict:
        """
        Gera recurso FHIR como evidencia:

        - "Communication": Mensagem enviada
        - "CarePlan": Plano criado/atualizado
        - "Task": Tarefa criada
        - "Consent": Consentimento registrado
        - "AuditEvent": Acao de auditoria
        - "Provenance": Rastreabilidade de quem fez o que
        """
```

### 3.8 Registro de Protocolos

```python
class ProtocolRegistry:
    """Catalogo de protocolos disponveis com versionamento."""

    async def register(self, protocol: Protocol) -> None:
        """Registra novo protocolo ou nova versao."""

    async def get_active(self, context_id: str) -> Optional[Protocol]:
        """
        Retorna protocolo vigente para o contexto.

        Busca por:
        1. context_id correspondente
        2. effective_from <= now <= effective_until
        3. Maior versao dentro do periodo vigente
        """

    async def list_all(
        self,
        include_expired: bool = False,
    ) -> list[Protocol]:
        """Lista todos os protocolos."""

    async def get_version_history(
        self,
        protocol_id: str,
    ) -> list[Protocol]:
        """Historico de versoes de um protocolo."""

    async def deprecate(
        self,
        protocol_id: str,
        version: str,
        reason: str,
    ) -> None:
        """Depreca uma versao de protocolo."""
```

### 3.9 Tabelas de Persistencia

```sql
-- Protocolos registrados
CREATE TABLE protocols (
    id BIGSERIAL PRIMARY KEY,
    protocol_id VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,
    context_id VARCHAR(10) NOT NULL,
    description TEXT,
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_until TIMESTAMPTZ,
    severity VARCHAR(20) DEFAULT 'medium',
    tags TEXT[] DEFAULT '{}',
    preconditions JSONB DEFAULT '[]',
    steps JSONB NOT NULL,            -- Lista de ProtocolStep serializada
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, draft
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(protocol_id, version)
);

CREATE INDEX idx_protocols_context ON protocols(context_id);
CREATE INDEX idx_protocols_active ON protocols(context_id, status, effective_from);

-- Execucoes de protocolos (historico auditavel)
CREATE TABLE protocol_executions (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID UNIQUE NOT NULL,
    protocol_id VARCHAR(100) NOT NULL,
    protocol_version VARCHAR(20) NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    trigger_event_id UUID,
    context_id VARCHAR(10),
    status VARCHAR(20) DEFAULT 'running',  -- running, completed, failed, aborted
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    steps_total INTEGER,
    steps_completed INTEGER DEFAULT 0,
    steps_skipped INTEGER DEFAULT 0,
    steps_failed INTEGER DEFAULT 0,
    results JSONB DEFAULT '[]',       -- Resultado de cada step
    evidences JSONB DEFAULT '[]',     -- Evidencias FHIR geradas
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_executions_patient ON protocol_executions(patient_id);
CREATE INDEX idx_executions_protocol ON protocol_executions(protocol_id);
CREATE INDEX idx_executions_status ON protocol_executions(status);
CREATE INDEX idx_executions_date ON protocol_executions(started_at);
```

### 3.10 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/protocols` | Lista protocolos registrados |
| GET | `/api/v1/protocols/{protocol_id}` | Detalhes de um protocolo |
| GET | `/api/v1/protocols/{protocol_id}/versions` | Historico de versoes |
| POST | `/api/v1/protocols` | Registra novo protocolo (admin) |
| GET | `/api/v1/protocols/executions/{patient_id}` | Execucoes do paciente |
| GET | `/api/v1/protocols/executions/{execution_id}/trace` | Trace completo |

### 3.11 Principios de Governanca

1. **Todo protocolo deve ser aprovado pelo NGC** antes de entrar em producao
2. **Protocolos nunca sao deletados** — sao deprecados com motivo
3. **Versionamento semantico** (MAJOR.MINOR.PATCH)
4. **Apenas uma versao ativa** por context_id em qualquer momento
5. **Mudancas em protocolos requerem analise de impacto** nos pacientes ativos
6. **IA nunca modifica protocolos** — IA apenas sugere, humanos aprovam
7. **Execucao deterministica** — dado o mesmo input, sempre as mesmas acoes

## 4. Fluxo Completo MCP (EF-006 + EF-007 + EF-008)

```
Evento recebido
    │
    ▼
[EF-006] EventPipeline
    │  Normaliza → Deduplica → Enriquece
    │
    ▼
[EF-007] ContextManager.evaluate_event()
    │  Identifica contexto → Ativa → Transiciona macroestado
    │
    ▼
[EF-008] ProtocolEngine.execute()
    │  Carrega protocolo vigente → Executa passos → Gera evidencias
    │
    ▼
Resultado:
    ├─ Acoes executadas (mensagens, lembretes, planos)
    ├─ Evidencias FHIR geradas
    ├─ Journey state atualizado
    └─ Timeline registrada
```

## 5. Testes

- Protocol parsing: YAML → Protocol (5 testes)
- ProtocolRegistry: registro, versoes, deprecacao (6 testes)
- ProtocolEngine: execucao completa, falha em step, abort (10 testes)
- ActionExecutor: cada action_type (12 testes)
- EvidenceGenerator: cada evidence_type (6 testes)
- Failure handling: skip, retry, abort, escalate (5 testes)
- Endpoints: list, get, executions, trace (5 testes)
- Integracao MCP completo: evento → contexto → protocolo → evidencia (3 testes)
- **Total**: 52+ testes

## 6. Criterios de Aceitacao

- [ ] Motor de execucao deterministica funcional
- [ ] 9+ protocolos YAML para BemCuidar v1
- [ ] 18 tipos de acao no catalogo
- [ ] Versionamento semantico funcional
- [ ] Failure handling: skip, retry, abort, escalate
- [ ] Evidencias FHIR geradas automaticamente
- [ ] Trace completo de execucao auditavel
- [ ] Tabelas protocols e protocol_executions
- [ ] 6 endpoints funcionais
- [ ] Governanca: aprovacao, deprecacao, impacto
- [ ] Pipeline MCP completo (EF-006 + EF-007 + EF-008) integrado
- [ ] 52+ testes
- [ ] Cobertura >= 85%

## 7. Estimativa de Complexidade

- **Arquivos novos**: ~12 (codigo) + ~9 (YAML de protocolos)
- **Arquivos modificados**: ~4 (config, api, context_manager, docker)
- **Linhas estimadas**: ~2.500
- **Testes novos**: ~52
