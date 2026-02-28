# EF-D009 — Alertas Inteligentes e Recomendacoes para Gestao

> Implementar motor de alertas e recomendacoes priorizadas para gestores de qualidade, detectando automaticamente deterioracao de indicadores, pilar abaixo do limiar e tendencias negativas — com notificacao via webhook e email.

## 1. Objetivo

Transformar o Donabedian de repositorio de indicadores em **sistema proativo de gestao de qualidade**, que:

- Detecta deterioracao de indicadores antes que se tornem criticos (tendencia negativa)
- Alerta gestores quando pilar cai abaixo de limiar configuravel
- Gera recomendacoes de melhoria contextualizadas e priorizadas por impacto
- Entrega alertas via webhook (Slack, Teams, N8N) ou email
- Cria ActionPlan com passos concretos para recuperacao do indicador

## 2. Justificativa

- Dashboard e passivo — gestor precisa abrir o sistema para ver problemas
- Pilar de Aceitabilidade inclui "resposta rapida a alertas" — o proprio Donabedian deve gerar alertas
- Sem recomendacoes, o gestor sabe que ha problema mas nao sabe o que fazer
- Integracao com N8N (em estudo) exige webhook de alertas com payload estruturado
- Ciclo PDCA: Planejar (indicadores) → Agir (alertas) → Verificar (recomendacoes) → Corrigir (action plan)

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AlertSeverity(str, Enum):
    CRITICAL = "critical"      # Indicador ultrapassou limite critico (> 150% da meta negativa)
    HIGH = "high"              # Indicador em vermelho (fora da meta)
    MEDIUM = "medium"          # Indicador em amarelo (proximo da meta)
    LOW = "low"                # Tendencia negativa (ainda verde, mas piorando)
    INFO = "info"              # Informativo (ex: nova medicao disponivel)


class AlertType(str, Enum):
    INDICATOR_RED = "indicator_red"          # Indicador entrou no vermelho
    INDICATOR_CRITICAL = "indicator_critical" # Indicador atingiu nivel critico
    PILLAR_BELOW_THRESHOLD = "pillar_below_threshold"  # Pilar abaixo de limiar
    TREND_NEGATIVE = "trend_negative"        # Tendencia negativa detectada
    TREND_IMPROVING = "trend_improving"      # Tendencia positiva (alerta positivo)
    NO_DATA = "no_data"                      # Indicador sem medicao ha N dias
    TARGET_ACHIEVED = "target_achieved"      # Indicador atingiu a meta


class AlertStatus(str, Enum):
    ACTIVE = "active"          # Alerta ativo — ainda valido
    ACKNOWLEDGED = "acknowledged"  # Reconhecido (gestor viu)
    RESOLVED = "resolved"      # Resolvido (indicador voltou ao verde)
    SUPPRESSED = "suppressed"  # Suprimido manualmente


@dataclass
class QualityAlert:
    """
    Alerta de qualidade gerado pelo AlertEngine.
    """
    alert_id: str               # UUID
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus

    # Contexto do alerta
    indicator_id: Optional[str]
    indicator_name: Optional[str]
    pillar_id: Optional[str]
    pillar_name: Optional[str]

    # Valores que geraram o alerta
    current_value: Optional[float]
    target_value: Optional[float]
    previous_value: Optional[float]         # Para detectar deterioracao
    trend_slope: Optional[float]            # Slope da tendencia (negativo = piorando)

    # Mensagem
    title: str                  # Titulo curto (para notificacao push)
    description: str            # Descricao completa do problema
    recommended_action: str     # Acao imediata recomendada

    # Metadados
    created_at: str
    resolved_at: Optional[str]
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[str]

    # Notificacao
    notification_sent: bool = False
    notification_channels: list[str] = field(default_factory=list)


@dataclass
class ManagementRecommendation:
    """
    Recomendacao de melhoria para gestores — diferente das recomendacoes clinicas do Oswaldo.
    Foco em gestao, processos e estrutura.
    """
    rec_id: str
    priority: int               # 1 = mais urgente
    pillar_id: str
    indicator_id: Optional[str]

    title: str
    problem_description: str    # O que esta errado
    root_cause: str             # Causa raiz provavel
    recommended_action: str     # O que fazer
    expected_impact: str        # Impacto esperado na qualidade
    timeline_days: int          # Prazo sugerido para implementacao

    category: str               # "processo" | "estrutura" | "capacitacao" | "protocolo" | "recurso"
    complexity: str             # "simples" | "media" | "complexa"
    responsible_area: str       # "direcao" | "enfermagem" | "farmacia" | "ti" | "qualidade"

    evidence_source: str        # Fonte da recomendacao (guideline, benchmark, tendencia)
    related_alerts: list[str]   # IDs de alertas que geraram esta recomendacao


@dataclass
class ActionPlan:
    """
    Plano de acao estruturado para recuperar um indicador ou pilar.
    """
    plan_id: str
    indicator_id: Optional[str]
    pillar_id: Optional[str]
    title: str

    problem_statement: str
    goal_description: str       # O que se quer atingir
    target_value: float
    target_date: str            # Data-alvo para atingir a meta

    steps: list[ActionStep]     # Passos concretos
    estimated_effort: str       # "1-5 dias" | "1-4 semanas" | "1-3 meses"
    resources_needed: list[str]

    created_at: str
    created_by: Optional[str]
    status: str                 # "draft" | "in_progress" | "completed" | "cancelled"


@dataclass
class ActionStep:
    step_number: int
    action: str                 # O que fazer
    responsible: str            # Quem faz
    deadline: str               # Data limite
    success_indicator: str      # Como saber que este passo foi concluido
    status: str = "pending"     # "pending" | "done" | "blocked"
```

### 3.2 AlertEngine

```python
class AlertEngine:
    """
    Motor de geracao de alertas de qualidade.

    Executado:
    1. Via job schedulado (cron diario as 06:00 — apos sync Oswaldo/Zilda)
    2. Via trigger: sempre que nova Measurement e registrada (evento)
    3. Via endpoint manual: POST /api/v1/alerts/run

    Regras de alerta (em ordem de prioridade):
    - CRITICAL: indicador >= 150% acima da meta negativa (ex: infeccao 4.5%, meta 2%)
    - HIGH: indicador em vermelho (fora da meta)
    - MEDIUM: indicador em amarelo (> 80% da meta negativa)
    - LOW: tendencia negativa por >= 3 periodos consecutivos (ainda verde)
    - INFO: sem medicao ha > 60 dias (dado desatualizado)
    """

    # Limiares de pilar para alertas automaticos
    PILLAR_ALERT_THRESHOLDS = {
        "critical": 40,     # Score < 40 = alerta critico
        "high": 50,         # Score < 50 = alerta alto
        "medium": 60,       # Score < 60 = alerta medio
    }

    async def run_alert_cycle(self) -> AlertCycleResult:
        """
        Executa ciclo completo de deteccao de alertas.

        1. Carrega todos os indicadores ativos
        2. Para cada indicador: avalia status atual
        3. Para cada pilar: avalia score atual
        4. Detecta tendencias (ultimas 3-6 medicoes)
        5. Detecta indicadores sem dados recentes
        6. Compara com alertas ativos (evitar duplicatas)
        7. Cria novos alertas para condicoes novas
        8. Resolve alertas cujas condicoes ja nao existem
        9. Dispara notificacoes para novos alertas HIGH+CRITICAL
        """

    async def evaluate_indicator(
        self,
        indicator_id: str,
    ) -> list[QualityAlert]:
        """
        Avalia um indicador especifico e retorna alertas aplicaveis.
        """

    async def evaluate_pillar(
        self,
        pillar_id: str,
        period_start: str,
        period_end: str,
    ) -> list[QualityAlert]:
        """
        Avalia score de um pilar e gera alerta se abaixo do limiar.
        """

    def detect_trend(
        self,
        measurements: list[dict],
    ) -> Optional[TrendAlert]:
        """
        Detecta tendencia negativa ou positiva em serie de medicoes.

        Algoritmo:
        1. Requer >= 3 medicoes no periodo
        2. Calcula regressao linear simples (scipy.stats.linregress)
        3. Slope < -0.5 por periodo = tendencia negativa
        4. R² > 0.7 = tendencia confiavel
        5. Retorna TrendAlert apenas se slope < 0 e R² > 0.5
        """

    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        comment: Optional[str] = None,
    ) -> QualityAlert:
        """Reconhece um alerta — muda status para ACKNOWLEDGED."""

    async def suppress_alert(
        self,
        alert_id: str,
        reason: str,
        suppress_until: Optional[str] = None,
    ) -> QualityAlert:
        """Suprime um alerta com justificativa (ex: periodo de manutencao)."""
```

### 3.3 RecommendationEngine (Gestao)

```python
class ManagementRecommendationEngine:
    """
    Gera recomendacoes de melhoria de gestao baseadas em alertas e scores.

    Diferenca do Oswaldo:
    - Oswaldo: recomendacoes CLINICAS por paciente (o que fazer no cuidado)
    - Donabedian: recomendacoes de GESTAO por servico (o que mudar na organizacao)

    Fonte das recomendacoes:
    1. Regras baseadas em pilar + tipo de indicador em vermelho
    2. Benchmarking com percentil nacional (se EF-D004 implementado)
    3. Praticas de melhoria de qualidade (IHI Institute for Healthcare Improvement)
    """

    # Base de recomendacoes por pilar + tipo de problema
    RECOMMENDATION_RULES = {
        ("eficiencia", "alto_tempo_permanencia"): ManagementRecommendation(
            title="Revisar protocolo de alta hospitalar",
            root_cause="Ausencia de criterios claros de alta ou gargalo na alta medica",
            recommended_action="Implementar checklist de alta preenchido 24h antes com responsavel definido",
            category="protocolo",
            complexity="media",
            responsible_area="enfermagem",
            timeline_days=30,
        ),
        ("aceitabilidade", "baixa_satisfacao"): ManagementRecommendation(
            title="Melhorar comunicacao com pacientes",
            root_cause="Falha na comunicacao sobre diagnostico, tratamento e alta",
            recommended_action="Implementar 'Hora da Visita Estruturada' com enfermeiro + residente",
            category="processo",
            complexity="simples",
            responsible_area="enfermagem",
            timeline_days=14,
        ),
        ("legitimidade", "baixa_adesao_checklist"): ManagementRecommendation(
            title="Fortalecer cultura de seguranca cirurgica",
            root_cause="Checklist cirurgico nao internalizado pela equipe",
            recommended_action="Realizar auditoria de checklists + feedback individual por cirurgiao",
            category="capacitacao",
            responsible_area="qualidade",
            timeline_days=21,
        ),
        ("efetividade", "alta_infeccao_hospitalar"): ManagementRecommendation(
            title="Intensificar protocolo de higiene de maos",
            root_cause="Adesao insuficiente ao protocolo OMS de higiene de maos",
            recommended_action="Campanha intensiva + auditoria com feedback semanal por setor",
            category="processo",
            complexity="simples",
            responsible_area="qualidade",
            timeline_days=30,
        ),
        ("equidade", "baixa_cobertura_esf"): ManagementRecommendation(
            title="Expandir equipes de Saude da Familia",
            root_cause="Deficit de equipes ESF para a populacao adscrita",
            recommended_action="Solicitar abertura de credenciamento de equipes ESF junto ao municipio",
            category="recurso",
            complexity="complexa",
            responsible_area="direcao",
            timeline_days=90,
        ),
    }

    async def generate_recommendations(
        self,
        alerts: list[QualityAlert],
        period_start: str,
        period_end: str,
    ) -> list[ManagementRecommendation]:
        """
        Gera recomendacoes priorizadas com base nos alertas ativos.

        Ordem de prioridade:
        1. CRITICAL alerts → recomendacao IMEDIATA
        2. Multiplos indicadores do mesmo pilar em vermelho → recomendacao SISTEMICA
        3. Tendencia negativa prolongada → recomendacao PREVENTIVA
        4. Comparacao com benchmark nacional → recomendacao ESTRATEGICA
        """

    async def create_action_plan(
        self,
        indicator_id: Optional[str],
        pillar_id: Optional[str],
        target_value: float,
        target_date: str,
    ) -> ActionPlan:
        """
        Cria plano de acao estruturado.

        Automaticamente gera passos baseados na recomendacao mais relevante
        para o indicador/pilar alvo.
        """
```

### 3.4 NotificationService

```python
class AlertNotificationService:
    """
    Envia notificacoes de alerta para canais configurados.

    Canais suportados:
    1. Webhook (Slack, Teams, N8N, Discord) — payload JSON padrao
    2. Email (SMTP) — template HTML
    3. Synapse/Matrix (via intellicare-comunicacao) — mensagem formatada

    Regras de notificacao:
    - CRITICAL: imediato, todos os canais
    - HIGH: imediato, canais primarios
    - MEDIUM: consolidado (1x/dia as 08:00)
    - LOW: consolidado (1x/semana as 09:00 segunda)
    - INFO: nenhuma notificacao automatica (apenas no dashboard)
    """

    async def send_alert(
        self,
        alert: QualityAlert,
        channels: list[str],
    ) -> NotificationResult:
        """Envia alerta para canais especificados."""

    async def send_webhook(
        self,
        alert: QualityAlert,
        webhook_url: str,
    ) -> bool:
        """
        Payload webhook padrao (compativel com N8N, Slack, Teams):
        {
            "event": "donabedian.alert",
            "severity": "high",
            "title": "Indicador em Vermelho: Taxa de Infeccao",
            "description": "...",
            "indicator_id": "...",
            "pillar": "efetividade",
            "current_value": 3.2,
            "target_value": 2.0,
            "timestamp": "2026-02-16T10:30:00Z",
            "dashboard_url": "http://donabedian:8004/dashboard"
        }
        """

    async def send_daily_digest(self) -> int:
        """
        Envia digest diario com alertas MEDIUM acumulados.
        Retorna: numero de alertas incluidos no digest.
        """
```

### 3.5 Endpoints REST Novos

```python
# GET /api/v1/alerts
# Query params: severity, status, pillar_id, indicator_id, limit (default 50)
# Retorna: list[QualityAlert]

# GET /api/v1/alerts/{alert_id}
# Retorna: QualityAlert completo

# POST /api/v1/alerts/run
# Dispara ciclo manual de deteccao de alertas
# Retorna: AlertCycleResult {alerts_created, alerts_resolved, duration_ms}

# POST /api/v1/alerts/{alert_id}/acknowledge
# Body: {user_id, comment?}
# Retorna: QualityAlert atualizado

# POST /api/v1/alerts/{alert_id}/suppress
# Body: {reason, suppress_until?}
# Retorna: QualityAlert atualizado

# GET /api/v1/recommendations
# Query params: pillar_id, priority, period_start, period_end
# Retorna: list[ManagementRecommendation] ordenada por prioridade

# POST /api/v1/recommendations/generate
# Body: {period_start, period_end}
# Dispara geracao de recomendacoes baseada nos alertas ativos
# Retorna: list[ManagementRecommendation]

# POST /api/v1/action-plans
# Body: {indicator_id?, pillar_id?, target_value, target_date}
# Retorna: ActionPlan criado

# GET /api/v1/action-plans
# Retorna: list[ActionPlan] ativos

# PATCH /api/v1/action-plans/{plan_id}/steps/{step_number}
# Body: {status: "done" | "blocked", comment?}
# Atualiza status de um passo do plano de acao
```

### 3.6 Tabelas SQL

```sql
CREATE TABLE donabedian_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    indicator_id UUID REFERENCES donabedian_indicators(id),
    pillar_id UUID REFERENCES donabedian_pillars(id),
    current_value NUMERIC(12,4),
    target_value NUMERIC(12,4),
    previous_value NUMERIC(12,4),
    trend_slope NUMERIC(10,6),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    recommended_action TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    suppressed_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE donabedian_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pillar_id UUID REFERENCES donabedian_pillars(id),
    indicator_id UUID REFERENCES donabedian_indicators(id),
    priority INTEGER NOT NULL,
    title VARCHAR(300) NOT NULL,
    problem_description TEXT,
    root_cause TEXT,
    recommended_action TEXT,
    expected_impact TEXT,
    timeline_days INTEGER,
    category VARCHAR(50),
    complexity VARCHAR(20),
    responsible_area VARCHAR(50),
    evidence_source TEXT,
    status VARCHAR(20) DEFAULT 'active',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE donabedian_action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator_id UUID REFERENCES donabedian_indicators(id),
    pillar_id UUID REFERENCES donabedian_pillars(id),
    title VARCHAR(300) NOT NULL,
    problem_statement TEXT,
    goal_description TEXT,
    target_value NUMERIC(12,4),
    target_date DATE,
    estimated_effort VARCHAR(50),
    status VARCHAR(20) DEFAULT 'draft',
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE donabedian_action_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES donabedian_action_plans(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    action TEXT NOT NULL,
    responsible VARCHAR(100),
    deadline DATE,
    success_indicator TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    UNIQUE (plan_id, step_number)
);

-- Indice para consulta rapida de alertas ativos
CREATE INDEX idx_alerts_active ON donabedian_alerts (status, severity, created_at DESC)
    WHERE status = 'active';
```

### 3.7 Configuracao

```env
# Alertas
INTELLICARE_DONABEDIAN_ALERTS_ENABLED=true
INTELLICARE_DONABEDIAN_ALERTS_CRON="0 6 * * *"    # Diario as 06:00
INTELLICARE_DONABEDIAN_PILLAR_ALERT_THRESHOLD=60   # Score < 60 gera alerta MEDIUM

# Notificacoes
INTELLICARE_DONABEDIAN_WEBHOOK_URL=                 # URL do webhook (N8N, Slack, etc.)
INTELLICARE_DONABEDIAN_SMTP_HOST=
INTELLICARE_DONABEDIAN_SMTP_PORT=587
INTELLICARE_DONABEDIAN_SMTP_USER=
INTELLICARE_DONABEDIAN_SMTP_PASSWORD=
INTELLICARE_DONABEDIAN_NOTIFY_EMAILS=               # Lista separada por virgula
INTELLICARE_DONABEDIAN_NOTIFY_ON_SEVERITY=high,critical  # Severidades que disparam notificacao

# Digest diario
INTELLICARE_DONABEDIAN_DIGEST_ENABLED=true
INTELLICARE_DONABEDIAN_DIGEST_CRON="0 8 * * 1-5"   # Seg-Sex 08:00
```

## 4. Testes

- AlertEngine.evaluate_indicator: vermelho, amarelo, verde com tendencia negativa (4 testes)
- AlertEngine.evaluate_pillar: abaixo do limiar, acima do limiar (2 testes)
- AlertEngine.detect_trend: tendencia negativa confiavel, positiva, sem dados suficientes (3 testes)
- AlertEngine.run_alert_cycle: ciclo completo com mocks (2 testes)
- ManagementRecommendationEngine.generate_recommendations: critico, multiplos pilares (3 testes)
- ActionPlan: criacao com passos, atualizacao de passo (2 testes)
- NotificationService: webhook, suppress (2 testes)
- Endpoints: GET alerts, POST run, acknowledge, recommendations, action-plan (6 testes)
- **Total**: 24+ testes novos

## 5. Criterios de Aceitacao

- [ ] `AlertEngine` com 5 tipos de alerta (indicator_red, critical, pillar, trend, no_data)
- [ ] Deduplicacao: nao cria alerta duplicado para condicao ja existente
- [ ] Auto-resolucao: alerta e marcado como resolved quando indicador volta ao verde
- [ ] `ManagementRecommendationEngine` com regras por pilar + tipo de problema
- [ ] `ActionPlan` com passos concretos e rastreamento por passo
- [ ] `AlertNotificationService` com suporte a webhook e email
- [ ] 4 tabelas SQL com migrations
- [ ] 10 endpoints REST funcionais
- [ ] Digest diario configuravel
- [ ] 363 testes v1.0 continuam passando
- [ ] 24+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `alerts/engine.py`, `alerts/models.py`, `alerts/notification.py`, `recommendations/engine.py`, `recommendations/rules.py`, `api/routes/alerts.py`, 4 migrations SQL
- **Arquivos modificados**: `api/main.py`, `config.py`, `docker-compose.yml` (cron alerts), `dashboard/pages/1_🏠_Home.py` (widget de alertas ativos)
- **Linhas estimadas**: ~700
- **Testes novos**: ~24
- **Dependencias novas**: `scipy` (para regressao linear de tendencias), `aiosmtplib` (SMTP async)
