# EF-012 — Ciclo de Vida Completo do Paciente

> Gestao da jornada completa: admissao, engajamento, cuidados, alta, pos-alta e encerramento.

## 1. Objetivo

Implementar a gestao do ciclo de vida completo do paciente dentro da Geralda, cobrindo:
- Admissao e inicio da jornada (E0 → E1)
- Engajamento digital do paciente/familia (E1 → E2)
- Cuidados ativos com plano e monitoramento (E2 → E3)
- Programacao e preparacao para alta (E3 → E4)
- Alta clinica e orientacoes (E4 → E5)
- Acompanhamento pos-alta (E5 → E6)
- Encerramento da jornada (E6 → E7)
- Reinternacao (E6 → E1)

## 2. Justificativa

- **Continuidade**: O cuidado nao comeca e termina na consulta
- **Rastreabilidade**: Saber exatamente onde cada paciente esta na jornada
- **Automacao**: Cada transicao dispara protocolos automaticos
- **Indicadores**: Medir tempo em cada fase, taxa de reinternacao, etc.
- **Equipe informada**: Profissionais visualizam a jornada completa

## 3. Escopo

### 3.1 Fases da Jornada com Detalhamento

#### E0 → E1: Admissao (Inicio da Jornada)

**Trigger**: `clinical.admission` (FHIR Encounter com status=in-progress)

**Acoes automaticas**:
1. Criar registro de jornada (`patient_journey` com macrostate=E1)
2. Ativar contexto C1 (Paciente Internado)
3. Executar protocolo P-C1-INTERNACAO-V1:
   - Registrar dados basicos do paciente
   - Criar plano de cuidado inicial (esqueleto)
   - Notificar equipe sobre nova admissao
   - Agendar avaliacao inicial
4. Emitir evento `journey.started`

```python
class AdmissionHandler:
    async def handle_admission(
        self,
        patient_id: str,
        admission_data: dict,
    ) -> JourneyInitResult:
        """
        Processa admissao do paciente.

        admission_data:
            - encounter_id: ID do Encounter FHIR
            - unit_id: Unidade de internacao
            - admission_date: Data da admissao
            - primary_diagnosis: ICD-10 principal
            - attending_physician: Medico responsavel
            - estimated_stay: Dias estimados de internacao

        Returns:
            JourneyInitResult com IDs criados
        """
```

#### E1 → E2: Engajamento Digital

**Trigger**: `digital.patient_onboarded` (paciente/acompanhante aceitou engajamento)

**Acoes automaticas** (protocolo P-C21):
1. Enviar mensagem de boas-vindas personalizada
2. Solicitar consentimento LGPD
3. Coletar preferencias (canal, idioma, horario)
4. Criar sala Matrix para o paciente
5. Iniciar trilha educativa pela condicao principal
6. Notificar equipe sobre engajamento

```python
class EngagementHandler:
    async def handle_onboarding(
        self,
        patient_id: str,
        onboarding_data: dict,
    ) -> EngagementResult:
        """
        Processa engajamento digital.

        onboarding_data:
            - contact_type: "patient" ou "caregiver"
            - contact_name: Nome do contato
            - preferred_channel: Canal escolhido
            - phone: Telefone (opcional)
            - email: Email (opcional)
            - consent: True/False
        """
```

#### E2 → E3: Cuidados Ativos

**Trigger**: Plano de cuidado criado E paciente engajado

**Acoes permanentes durante E3**:
1. Monitorar adesao diariamente
2. Enviar lembretes conforme agenda
3. Processar respostas do paciente (medicamento tomado, etc.)
4. Receber alertas de Florence/Oswaldo e ajustar plano
5. Gerar materiais educativos conforme progresso
6. Acompanhar resultados de exames
7. Preparar resumos para consultas

```python
class ActiveCareHandler:
    async def daily_monitoring(
        self,
        patient_id: str,
    ) -> DailyReport:
        """
        Monitoramento diario do paciente em cuidados ativos.

        Executado por scheduler (cron-like):
        - Calcular adesao do dia anterior
        - Verificar tarefas perdidas
        - Enviar agenda do dia
        - Verificar exames pendentes
        - Detectar anomalias (sem interacao ha X dias)
        """

    async def handle_patient_interaction(
        self,
        patient_id: str,
        interaction_type: str,
        data: dict,
    ) -> None:
        """
        Processa interacao do paciente:
        - "task_completed": Marca tarefa como feita
        - "question": Processa duvida
        - "symptom_report": Registra sintoma
        - "side_effect": Registra efeito colateral
        """
```

#### E3 → E4: Programacao de Alta

**Trigger**: `operational.discharge_planned` (equipe define data de alta)

**Acoes automaticas** (protocolo P-C33):
1. Gerar checklist de alta (personalizado por condicao)
2. Iniciar materiais educativos pos-alta
3. Verificar se APS de referencia esta articulada (via Zilda)
4. Agendar teleconsulta pos-alta
5. Preparar resumo de alta para o paciente
6. Notificar equipe de APS sobre alta programada

```python
class DischargePlanningHandler:
    async def handle_discharge_planning(
        self,
        patient_id: str,
        planning_data: dict,
    ) -> DischargePlanResult:
        """
        Processa programacao de alta.

        planning_data:
            - planned_date: Data prevista da alta
            - conditions_at_discharge: Condicoes na alta
            - medications_at_discharge: Medicamentos para casa
            - follow_up_needed: Acompanhamento necessario
            - aps_unit_id: Unidade APS de referencia
        """

    async def generate_discharge_checklist(
        self,
        patient_id: str,
    ) -> list[dict]:
        """
        Gera checklist de alta personalizado.

        Itens tipicos:
        - [ ] Orientacoes sobre medicamentos explicadas
        - [ ] Material educativo sobre condicao entregue
        - [ ] Consulta de retorno agendada
        - [ ] Teleconsulta pos-alta agendada
        - [ ] APS notificada
        - [ ] Exames de controle agendados
        - [ ] Paciente sabe sinais de alerta
        - [ ] Contato de emergencia registrado
        """
```

#### E4 → E5: Alta Clinica

**Trigger**: `clinical.discharge` (FHIR Encounter com status=finished)

**Acoes automaticas** (protocolo P-C41):
1. Gerar documento de alta simplificado
2. Enviar orientacoes de alta ao paciente via canal preferido
3. Ativar lembretes pos-alta (medicamentos, retornos)
4. Confirmar teleconsulta pos-alta
5. Registrar CarePlan FHIR com status=active (ambulatorial)
6. Transicionar para E5

```python
class DischargeHandler:
    async def handle_discharge(
        self,
        patient_id: str,
        discharge_data: dict,
    ) -> DischargeResult:
        """
        Processa alta clinica.

        discharge_data:
            - discharge_date: Data efetiva da alta
            - discharge_summary: Resumo da internacao
            - medications: Medicamentos para casa
            - follow_up_instructions: Orientacoes de acompanhamento
            - return_date: Data de retorno
            - restrictions: Restricoes (atividade fisica, dieta, etc.)
        """

    async def generate_patient_discharge_summary(
        self,
        patient_id: str,
        reading_level: str = "basico",
    ) -> str:
        """
        Gera resumo de alta em linguagem acessivel via LLM.

        Inclui:
        - O que aconteceu durante a internacao (resumo simples)
        - Medicamentos para tomar em casa (horarios, dosagens)
        - O que voce pode e nao pode fazer (restricoes)
        - Quando voltar ao medico (data, local)
        - Sinais de alerta (quando ir ao pronto-socorro)
        - Telefones uteis
        """
```

#### E5 → E6: Acompanhamento Pos-Alta

**Trigger**: Transicao automatica apos alta clinica

**Acoes permanentes durante E6**:
1. Acompanhamento telefonico/digital nos primeiros 7 dias
2. Teleconsulta pos-alta (7-14 dias)
3. Monitorar adesao ao tratamento ambulatorial
4. Verificar se retornou a APS
5. Enviar materiais educativos progressivos
6. Detectar sinais de reinternacao

```python
class PostDischargeHandler:
    async def start_post_discharge(
        self,
        patient_id: str,
    ) -> None:
        """
        Inicia acompanhamento pos-alta.

        Cronograma padrao:
        - D+1: Mensagem de acompanhamento ("Como voce esta?")
        - D+3: Verificar adesao medicamentosa
        - D+7: Teleconsulta pos-alta (se agendada)
        - D+14: Verificar retorno a APS
        - D+30: Avaliacao final do periodo pos-alta
        """

    async def check_readmission_risk(
        self,
        patient_id: str,
    ) -> dict:
        """
        Avalia risco de reinternacao.

        Fatores:
        - Adesao medicamentosa < 70%
        - Nao retornou a APS
        - Piora de condicao (via Oswaldo)
        - Sem interacao digital ha > 5 dias
        - Condicao cronica descompensada
        - Multiplas internacoes no ultimo ano

        Returns:
            {"risk": "alto", "score": 0.78, "factors": [...], "suggestion": "..."}
        """
```

#### E6 → E7: Encerramento

**Trigger**: `operational.journey_closed` (manual ou automatico)

**Condicoes para encerramento automatico**:
- Pos-alta concluido (D+30 sem intercorrencias)
- Paciente estavel e vinculado a APS
- Plano de cuidado completado

**Acoes**:
1. Gerar relatorio final da jornada
2. Arquivar planos de cuidado
3. Desativar lembretes
4. Manter sala Matrix (historico)
5. Registrar metricas finais (tempo de jornada, adesao media, etc.)

#### E6 → E1: Reinternacao

**Trigger**: `clinical.admission` quando paciente tem jornada em E6

**Acoes**:
1. Registrar reinternacao (flag `is_readmission = True`)
2. Manter historico da jornada anterior
3. Criar nova jornada vinculada
4. Alertar equipe sobre reinternacao
5. Carregar contexto da jornada anterior para continuidade

### 3.2 Servico de Ciclo de Vida

```python
class PatientLifecycleService:
    """Gerencia o ciclo de vida completo do paciente."""

    def __init__(
        self,
        admission_handler: AdmissionHandler,
        engagement_handler: EngagementHandler,
        active_care_handler: ActiveCareHandler,
        discharge_planning_handler: DischargePlanningHandler,
        discharge_handler: DischargeHandler,
        post_discharge_handler: PostDischargeHandler,
        journey_state_machine: JourneyStateMachine,
    ):
        ...

    async def get_patient_dashboard(
        self,
        patient_id: str,
    ) -> PatientDashboard:
        """
        Retorna dashboard completo do paciente:
        - Estado da jornada (macroestado + tempo)
        - Plano de cuidado ativo + progresso
        - Adesao atual + tendencia
        - Proximas acoes (lembretes, consultas)
        - Materiais educativos recomendados
        - Alertas pendentes
        """

    async def get_cohort_overview(
        self,
        unit_id: Optional[str] = None,
        macrostate: Optional[str] = None,
    ) -> CohortOverview:
        """
        Retorna visao geral de um grupo de pacientes:
        - Total por macroestado
        - Adesao media
        - Pacientes em risco
        - Reinternacoes nos ultimos 30 dias
        - Tempo medio em cada fase
        """
```

### 3.3 Tabelas Adicionais

```sql
-- Historico de jornadas (uma por internacao)
CREATE TABLE patient_journeys (
    id BIGSERIAL PRIMARY KEY,
    journey_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    is_readmission BOOLEAN DEFAULT FALSE,
    previous_journey_id UUID,
    admission_date TIMESTAMPTZ NOT NULL,
    discharge_date TIMESTAMPTZ,
    closure_date TIMESTAMPTZ,
    total_days INTEGER,
    final_macrostate VARCHAR(5),
    adherence_avg FLOAT,
    readmission_within_30d BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_journeys_patient ON patient_journeys(patient_id);
CREATE INDEX idx_journeys_admission ON patient_journeys(admission_date);
CREATE INDEX idx_journeys_readmission ON patient_journeys(is_readmission);

-- Checklist de alta
CREATE TABLE discharge_checklists (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    journey_id UUID NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_by VARCHAR(100),
    completed_at TIMESTAMPTZ,
    mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_checklist_patient ON discharge_checklists(patient_id);
CREATE INDEX idx_checklist_journey ON discharge_checklists(journey_id);
```

### 3.4 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/lifecycle/admit` | Registrar admissao |
| POST | `/api/v1/lifecycle/engage` | Registrar engajamento |
| POST | `/api/v1/lifecycle/plan-discharge` | Programar alta |
| POST | `/api/v1/lifecycle/discharge` | Registrar alta |
| POST | `/api/v1/lifecycle/close` | Encerrar jornada |
| GET | `/api/v1/lifecycle/{patient_id}/dashboard` | Dashboard do paciente |
| GET | `/api/v1/lifecycle/{patient_id}/history` | Historico de jornadas |
| GET | `/api/v1/lifecycle/cohort` | Visao geral do grupo |
| GET | `/api/v1/lifecycle/{patient_id}/checklist` | Checklist de alta |
| PUT | `/api/v1/lifecycle/{patient_id}/checklist/{item_id}` | Marcar item do checklist |

### 3.5 Scheduler (Tarefas Periodicas)

```python
class LifecycleScheduler:
    """Tarefas periodicas do ciclo de vida."""

    # Executar a cada 6 horas
    async def check_stale_journeys(self) -> None:
        """
        Detecta pacientes parados em um macroestado ha muito tempo.

        Ex: E1 ha > 48h sem engajamento → Alerta para equipe
        Ex: E6 ha > 45 dias → Candidato a encerramento
        Ex: E3 sem interacao ha > 7 dias → Alerta de perda de vinculo
        """

    # Executar diariamente as 07:00
    async def daily_patient_check(self) -> None:
        """
        Verificacao diaria de todos os pacientes ativos.

        Para cada paciente em E3/E6:
        - Enviar agenda do dia
        - Verificar adesao do dia anterior
        - Detectar tarefas perdidas
        - Gerar alertas se necessario
        """

    # Executar semanalmente
    async def weekly_cohort_report(self) -> None:
        """
        Relatorio semanal do grupo de pacientes.

        Envia para equipe via Rocket.Chat:
        - Pacientes por macroestado
        - Adesao media
        - Reinternacoes da semana
        - Pacientes em risco
        """
```

## 4. Testes

- AdmissionHandler: admissao normal, readmissao (5 testes)
- EngagementHandler: onboarding, consent, sem consent (5 testes)
- ActiveCareHandler: daily monitoring, interactions (6 testes)
- DischargePlanningHandler: planning, checklist (5 testes)
- DischargeHandler: alta, resumo, orientacoes (5 testes)
- PostDischargeHandler: cronograma, risco reinternacao (6 testes)
- PatientLifecycleService: dashboard, cohort (4 testes)
- JourneyStateMachine: todas transicoes, reinternacao (6 testes)
- LifecycleScheduler: stale, daily, weekly (4 testes)
- Endpoints: todos 10 (6 testes)
- **Total**: 52+ testes

## 5. Criterios de Aceitacao

- [ ] 8 macroestados (E0-E7) com transicoes implementadas
- [ ] Handler especifico para cada fase da jornada
- [ ] Checklist de alta personalizado por condicao
- [ ] Resumo de alta em linguagem acessivel via LLM
- [ ] Acompanhamento pos-alta com cronograma D+1 a D+30
- [ ] Deteccao de risco de reinternacao
- [ ] Reinternacao tratada (nova jornada vinculada)
- [ ] Dashboard do paciente e visao de grupo
- [ ] Scheduler para tarefas periodicas
- [ ] 10 endpoints funcionais
- [ ] 52+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~12
- **Arquivos modificados**: ~5 (config, api, scheduler, context_manager, docker)
- **Linhas estimadas**: ~2.500
- **Testes novos**: ~52
