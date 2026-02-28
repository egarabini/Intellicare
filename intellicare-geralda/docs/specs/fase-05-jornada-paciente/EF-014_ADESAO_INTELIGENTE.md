# EF-014 — Adesao Inteligente

> Monitoramento preditivo de adesao ao tratamento com deteccao precoce de risco e intervencoes automatizadas.

## 1. Objetivo

Implementar um motor de adesao inteligente que:
- Calcula score de adesao em tempo real por paciente
- Detecta padroes de queda de adesao precocemente
- Prediz risco de descontinuidade do tratamento
- Gera intervencoes automatizadas personalizadas
- Fornece ao profissional visibilidade da adesao do grupo
- Mede impacto das intervencoes na adesao

## 2. Justificativa

- **70% dos pacientes cronicos** abandonam tratamento em 1 ano
- **Deteccao precoce** de queda de adesao permite intervencao a tempo
- **Personalizacao** das intervencoes aumenta eficacia
- **Indicador de qualidade** (Donabedian) — adesao e resultado mensuravel
- **LGPD**: Monitoramento por consentimento explicito

## 3. Escopo

### 3.1 Modelo de Calculo de Adesao

```python
class AdherenceCalculator:
    """Calcula score de adesao multi-dimensional."""

    def calculate_adherence_score(
        self,
        patient_id: str,
        care_plan_id: str,
        period_days: int = 30,
    ) -> AdherenceReport:
        """
        Calcula adesao em 4 dimensoes:

        SCORE COMPOSTO = (
            medication * 0.40 +
            appointments * 0.30 +
            activities * 0.20 +
            monitoring * 0.10
        )

        Dimensoes:
        1. Medicamentos (40%):
           - Tarefas de medicamento completadas / total esperado
           - Peso maior para medicamentos essenciais (RAAS, antidiabeticos)

        2. Consultas e Exames (30%):
           - Consultas comparecidas / agendadas
           - Exames realizados / solicitados
           - Peso por urgencia (exame de controle DRC > rotina)

        3. Atividades (20%):
           - Atividade fisica, dieta, autocuidado
           - Peso pela prescricao do profissional

        4. Monitoramento (10%):
           - Registros de pressao/glicemia (se aplicavel)
           - Respostas a questionarios de sintomas

        Returns:
            AdherenceReport:
              - overall_score: 0.0-1.0
              - dimension_scores: {medication: 0.85, appointments: 0.90, ...}
              - trend: "stable" | "improving" | "declining" | "critical"
              - trend_delta: variacao 7 dias
              - missed_tasks: lista de tarefas perdidas
              - period_start/end: periodo analisado
        """
```

### 3.2 Classificacao de Adesao

| Score | Nivel | Cor | Intervencao |
|-------|-------|-----|-------------|
| >= 0.80 | Boa | 🟢 Verde | Reforco positivo semanal |
| 0.60-0.79 | Regular | 🟡 Amarelo | Lembrete personalizado + motivacao |
| 0.40-0.59 | Baixa | 🟠 Laranja | Contato proativo + revisao de barreiras |
| < 0.40 | Critica | 🔴 Vermelho | Alerta equipe + intervencao urgente |

### 3.3 Modelo Preditivo

```python
class AdherencePredictiveModel:
    """
    Modelo preditivo de risco de descontinuidade.

    Baseado em evidencias clinicas e comportamentais,
    NAO usa ML externo — usa regras deterministicas
    com pesos configurados pelo NGC.
    """

    # Fatores de risco com pesos
    RISK_FACTORS = {
        # Comportamentais
        "declining_trend_7d": 0.25,           # Queda nos ultimos 7 dias
        "missed_3_consecutive": 0.20,          # 3+ dias consecutivos sem tarefas
        "no_digital_interaction_5d": 0.15,     # Sem interacao ha 5+ dias
        "first_week_of_treatment": 0.10,       # Primeiros 7 dias (risco inicial)
        "recent_side_effect": 0.15,            # Relato de efeito colateral

        # Clinicos
        "condition_worsened": 0.20,            # Piora clinica recente
        "new_medication": 0.10,                # Novo medicamento introduzido
        "complex_regimen": 0.05,               # > 5 medicamentos

        # Sociais
        "lives_alone": 0.05,                   # Sem suporte social
        "missed_appointment": 0.15,            # Faltou consulta recente
        "readmission": 0.10,                   # Reinternacao recente
    }

    def calculate_dropout_risk(
        self,
        patient_id: str,
        current_adherence: AdherenceReport,
        patient_context: PatientFullContext,
    ) -> RiskAssessment:
        """
        Calcula risco de abandono do tratamento.

        Returns:
            RiskAssessment:
              - risk_score: 0.0-1.0
              - risk_level: low, medium, high, critical
              - active_factors: lista de fatores de risco ativos
              - protective_factors: fatores protetores
              - recommendation: acao recomendada
        """
```

### 3.4 Motor de Intervencoes

```python
class AdherenceInterventionEngine:
    """Gera e executa intervencoes personalizadas."""

    # Arvore de intervencoes por nivel de risco
    INTERVENTIONS = {
        "boa": [
            {
                "type": "positive_reinforcement",
                "trigger": "weekly",
                "message_template": "adherence_praise",
                "gamification": True,
            }
        ],
        "regular": [
            {
                "type": "personalized_reminder",
                "trigger": "daily",
                "message_template": "medication_reminder",
                "personalize": True,
            },
            {
                "type": "motivational_message",
                "trigger": "twice_weekly",
                "message_template": "motivation",
                "llm_generated": True,
            },
        ],
        "baixa": [
            {
                "type": "proactive_contact",
                "trigger": "immediate",
                "message_template": "check_in",
                "llm_generated": True,
            },
            {
                "type": "barrier_assessment",
                "trigger": "chat",
                "message_template": "barrier_questions",
            },
            {
                "type": "care_plan_review",
                "trigger": "scheduled",
                "action": "schedule_review",
            },
        ],
        "critica": [
            {
                "type": "team_alert",
                "trigger": "immediate",
                "channel": "rocketchat",
                "severity": "high",
            },
            {
                "type": "urgent_contact",
                "trigger": "immediate",
                "message_template": "urgent_checkin",
                "channel": "preferred",
            },
            {
                "type": "teleconsult_suggestion",
                "trigger": "immediate",
                "action": "suggest_teleconsult",
            },
        ],
    }

    async def generate_personalized_intervention(
        self,
        patient_id: str,
        adherence_report: AdherenceReport,
        risk_assessment: RiskAssessment,
    ) -> Intervention:
        """
        Gera intervencao personalizada via LLM.

        Usa contexto do paciente para personalizar:
        - Nome, idade, tempo de tratamento
        - Historico de comunicacoes
        - Barreiras relatadas anteriormente
        - Motivacoes conhecidas (familia, trabalho, etc.)
        - Canal de preferencia
        - Horario de preferencia

        Ex para baixa adesao com DRC:
        "Joao, percebi que esta semana voce nao tomou a Losartana
         alguns dias. Sei que pode ser dificil manter a rotina.
         Que tal conversar um pouco? Posso te ajudar a entender
         por que isso esta sendo dificil e encontrar uma solucao
         juntos. O que voce acha?"
        """

    async def assess_barriers(
        self,
        patient_id: str,
        chat_session: str,
    ) -> BarrierAssessment:
        """
        Realiza avaliacao de barreiras via chat com LLM.

        Perguntas exploradas:
        1. Esqueceu de tomar o medicamento?
        2. Teve efeitos colaterais?
        3. Nao conseguiu comprar o medicamento?
        4. Nao entendeu como tomar?
        5. Nao acredita que o medicamento funciona?

        Returns:
            BarrierAssessment com tipo de barreira identificada
            e sugestao de intervencao especifica
        """
```

### 3.5 Gamificacao (Opcional — v2.0)

```python
class AdherenceGamification:
    """
    Elementos de gamificacao para manter engajamento.

    NOTA: Recursos de gamificacao precisam de aprovacao NGC.
    Implementar de forma discreta, adequada para saude.
    """

    BADGES = {
        "first_week": {"name": "Primeira Semana", "threshold": 7},
        "consistent_30d": {"name": "30 Dias Forte", "threshold": 30},
        "perfect_week": {"name": "Semana Perfeita", "score": 1.0, "days": 7},
        "comeback": {"name": "Voltei!", "after_low_period": True},
    }

    async def get_patient_achievements(
        self,
        patient_id: str,
    ) -> list[Badge]:
        """Retorna conquistas do paciente."""

    async def get_streak(
        self,
        patient_id: str,
    ) -> int:
        """Retorna sequencia atual de dias com boa adesao."""

    async def should_send_achievement(
        self,
        patient_id: str,
        new_achievement: Badge,
    ) -> bool:
        """
        Verifica se deve enviar notificacao de conquista.

        LGPD: Paciente deve ter optado por notificacoes motivacionais.
        """
```

### 3.6 Relatorio de Adesao para Equipe

```python
class AdherenceTeamReport:
    """Relatorios de adesao para a equipe de saude."""

    async def get_cohort_adherence(
        self,
        unit_id: Optional[str] = None,
        period_days: int = 30,
    ) -> CohortAdherenceReport:
        """
        Relatorio de adesao do grupo.

        Sections:
        - Distribuicao por nivel (boa/regular/baixa/critica)
        - Top 10 pacientes em queda de adesao
        - Dimensao com pior desempenho (medicamento? consultas?)
        - Tendencia geral
        - Correlacao com reinternacoes
        """

    async def get_patient_adherence_history(
        self,
        patient_id: str,
        months: int = 6,
    ) -> AdherenceHistory:
        """
        Historico de adesao do paciente com graficos.

        - Score mensal (6 meses)
        - Score por dimensao
        - Intervencoes realizadas e impacto
        - Correlacao com eventos clinicos
        """
```

### 3.7 Tabelas

```sql
-- Scores de adesao (calculados periodicamente)
CREATE TABLE adherence_scores (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    care_plan_id UUID NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Scores
    overall_score FLOAT NOT NULL,
    medication_score FLOAT,
    appointments_score FLOAT,
    activities_score FLOAT,
    monitoring_score FLOAT,

    -- Tendencia
    trend VARCHAR(20),           -- stable, improving, declining, critical
    trend_delta FLOAT,           -- variacao vs periodo anterior

    -- Risco
    dropout_risk_score FLOAT,
    risk_level VARCHAR(20),      -- low, medium, high, critical
    risk_factors JSONB DEFAULT '[]',

    -- Detalhes
    total_tasks INTEGER,
    completed_tasks INTEGER,
    missed_tasks JSONB DEFAULT '[]',

    -- Intervencao
    intervention_triggered BOOLEAN DEFAULT FALSE,
    intervention_type VARCHAR(50),
    intervention_at TIMESTAMPTZ,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adherence_patient ON adherence_scores(patient_id);
CREATE INDEX idx_adherence_period ON adherence_scores(patient_id, period_start);
CREATE INDEX idx_adherence_risk ON adherence_scores(risk_level);

-- Intervencoes de adesao
CREATE TABLE adherence_interventions (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    adherence_score_id BIGINT REFERENCES adherence_scores(id),
    intervention_type VARCHAR(50) NOT NULL,
    trigger_event VARCHAR(100),
    message_sent TEXT,
    channel VARCHAR(50),
    sent_at TIMESTAMPTZ,
    response_received BOOLEAN DEFAULT FALSE,
    response_text TEXT,
    response_at TIMESTAMPTZ,
    barrier_identified VARCHAR(100),
    outcome VARCHAR(50),         -- improved, unchanged, worsened, unknown
    outcome_measured_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interventions_patient ON adherence_interventions(patient_id);
CREATE INDEX idx_interventions_type ON adherence_interventions(intervention_type);

-- Conquistas (gamificacao)
CREATE TABLE patient_achievements (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    badge_id VARCHAR(50) NOT NULL,
    badge_name VARCHAR(100) NOT NULL,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified BOOLEAN DEFAULT FALSE,
    UNIQUE(patient_id, badge_id, earned_at::date)
);
```

### 3.8 Scheduler de Adesao

```python
# Calcular adesao diariamente para todos os pacientes em E3/E6
# Executar as 06:00 (antes do envio de agendas do dia)
async def daily_adherence_calculation() -> None:
    """
    Para cada paciente ativo:
    1. Calcular score do dia
    2. Verificar se mudou de nivel
    3. Calcular risco de abandono
    4. Disparar intervencao se necessario
    5. Notificar equipe se nivel critico
    """

# Relatorio semanal (segunda-feira, 08:00)
async def weekly_cohort_adherence_report() -> None:
    """Enviar relatorio semanal para equipe via Rocket.Chat."""
```

### 3.9 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/adherence/{patient_id}` | Score atual do paciente |
| GET | `/api/v1/adherence/{patient_id}/history` | Historico de scores |
| GET | `/api/v1/adherence/{patient_id}/risk` | Avaliacao de risco |
| GET | `/api/v1/adherence/{patient_id}/interventions` | Intervencoes realizadas |
| POST | `/api/v1/adherence/{patient_id}/assess-barriers` | Iniciar avaliacao de barreiras |
| GET | `/api/v1/adherence/cohort` | Relatorio do grupo |
| GET | `/api/v1/adherence/{patient_id}/achievements` | Conquistas |
| POST | `/api/v1/adherence/{patient_id}/calculate` | Calcular manualmente (admin) |

## 4. Testes

- AdherenceCalculator: 4 dimensoes, score composto, sem tarefas (8 testes)
- AdherencePredictiveModel: cada fator de risco, score composto (8 testes)
- AdherenceInterventionEngine: cada nivel, personalizacao via LLM (8 testes)
- BarrierAssessment: cada tipo de barreira (4 testes)
- AdherenceGamification: badges, streak, notificacao (4 testes)
- AdherenceTeamReport: cohort, historico (4 testes)
- Scheduler: calculo diario, relatorio semanal (3 testes)
- Endpoints: todos 8 (6 testes)
- **Total**: 45+ testes

## 5. Criterios de Aceitacao

- [ ] Score de adesao em 4 dimensoes (medicamento 40%, consultas 30%, atividades 20%, monitoramento 10%)
- [ ] 4 niveis de adesao com cores e acoes
- [ ] Modelo preditivo com 11 fatores de risco
- [ ] Motor de intervencoes por nivel
- [ ] Mensagem personalizada via LLM
- [ ] Avaliacao de barreiras via chat
- [ ] Gamificacao basica (badges, streak)
- [ ] Relatorio para equipe (cohort + historico)
- [ ] Scheduler diario (06:00) e semanal
- [ ] 8 endpoints funcionais
- [ ] 45+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~10
- **Arquivos modificados**: ~4 (scheduler, api, event_pipeline, docker)
- **Linhas estimadas**: ~2.200
- **Testes novos**: ~45
