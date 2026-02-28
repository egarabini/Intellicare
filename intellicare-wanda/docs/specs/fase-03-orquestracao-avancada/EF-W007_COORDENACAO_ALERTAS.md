# EF-W007 — Coordenacao de Alertas Clinicos

> Agregacao, deduplicacao e priorizacao de alertas de multiplos agentes para evitar sobrecarga da equipe.

## 1. Objetivo

Implementar um hub de alertas clinicos centralizado que:
- Recebe alertas de todos os agentes (Florence, Oswaldo, Geralda)
- Deduplica alertas relacionados ao mesmo paciente/evento
- Prioriza alertas por gravidade e urgencia
- Coordena a notificacao para a equipe evitando spam
- Fornece fila gerenciada de alertas pendentes

## 2. Justificativa

- **Fadiga de alertas**: Sem coordenacao, equipe recebe 10 alertas para o mesmo paciente
- **Priorizacao**: Alerta CRITICO nao pode ser perdido entre alertas BAIXOS
- **Deduplicacao**: Florence e Oswaldo podem emitir alertas sobre o mesmo evento
- **Janela**: Multiplos alertas em 5 minutos devem ser consolidados em 1
- **Escalonamento**: Alerta nao lido escala automaticamente

## 3. Escopo

### 3.1 Hub de Alertas

```python
class AlertHub:
    """
    Hub centralizado de alertas clinicos.

    Todos os alertas do ecossistema passam pela Wanda
    antes de chegar a equipe.
    """

    def __init__(
        self,
        alert_store: AlertStore,
        deduplicator: AlertDeduplicator,
        prioritizer: AlertPrioritizer,
        consolidator: AlertConsolidator,
        notification_dispatcher: NotificationDispatcher,
    ):
        ...

    async def receive_alert(
        self,
        alert: ClinicalAlert,
    ) -> AlertProcessingResult:
        """
        Recebe e processa alerta.

        Fluxo:
        1. Deduplicar: alerta duplicado?
        2. Enriquecer: carregar IPS (EF-W002)
        3. Priorizar: calcular prioridade final
        4. Consolidar: janela de consolidacao (5 min)?
        5. Despachar: enviar para equipe via Comunicacao
        6. Persistir: registrar no alert_store
        7. Agendar escalacao: se nao lido em X min
        """
```

### 3.2 Estrutura de Alerta

```python
@dataclass
class ClinicalAlert:
    """Alerta clinico unificado."""
    alert_id: UUID
    source_agent: str           # florence, oswaldo, geralda
    alert_type: str             # vital_sign, lab_result, adherence, condition
    patient_id: str
    severity: str               # low, medium, high, critical
    title: str
    description: str
    recommended_action: str
    clinical_data: dict         # Dados especificos (valor, referencia, etc.)
    timestamp: datetime
    idempotency_key: str
```

### 3.3 Deduplicacao de Alertas

```python
class AlertDeduplicator:
    """
    Previne alertas duplicados sobre o mesmo evento clinico.
    """

    # Janelas de deduplicacao por tipo
    DEDUP_WINDOWS = {
        "vital_sign": timedelta(minutes=10),
        "lab_result": timedelta(hours=1),
        "condition_worsened": timedelta(hours=4),
        "adherence_low": timedelta(hours=24),
        "medication_missed": timedelta(hours=12),
    }

    async def is_duplicate(
        self,
        alert: ClinicalAlert,
    ) -> bool:
        """
        Verifica duplicata dentro da janela de deduplicacao.

        Chave de deduplicacao:
        f"wanda:alert:dedup:{alert.patient_id}:{alert.alert_type}:{alert.severity}"

        TTL = janela de deduplicacao por tipo
        """
```

### 3.4 Priorizador de Alertas

```python
class AlertPrioritizer:
    """
    Calcula prioridade final do alerta considerando multiplos fatores.
    """

    async def calculate_priority(
        self,
        alert: ClinicalAlert,
        patient_context: Optional[dict],
    ) -> AlertPriority:
        """
        Prioridade = f(severidade_base, fatores_contextuais)

        Fatores que AUMENTAM prioridade:
        - Paciente internado (E1, E3) + alerta → +1 nivel
        - Primeiro alerta do tipo (nunca teve antes) → +1 nivel
        - Tendencia de piora (3+ alertas do tipo em 7 dias) → +1 nivel
        - Paciente em alto risco (score Geralda) → +1 nivel

        Fatores que REDUZEM:
        - Alerta recorrente e ja sendo tratado → -1 nivel
        - Profissional ja ciente (alerta anterior nao lido) → ignorar
        """
```

### 3.5 Consolidador de Alertas

```python
class AlertConsolidator:
    """
    Consolida multiplos alertas do mesmo paciente em janela temporal.
    """

    CONSOLIDATION_WINDOW = timedelta(minutes=5)

    async def should_consolidate(
        self,
        alert: ClinicalAlert,
    ) -> Optional[list[ClinicalAlert]]:
        """
        Verifica se ha alertas recentes do mesmo paciente para consolidar.

        Se sim: retorna lista de alertas para consolidar
        Se nao: retorna None (enviar imediatamente)
        """

    async def consolidate(
        self,
        alerts: list[ClinicalAlert],
    ) -> ConsolidatedAlert:
        """
        Cria alerta consolidado de multiplos alertas.

        Ex:
        INPUT: [
            {vital_sign: PA 160/100, severity: high},
            {lab_result: creatinina 2.1, severity: medium},
            {adherence_low: 45%, severity: medium},
        ]

        OUTPUT: ConsolidatedAlert {
            severity: high (maior),
            title: "3 alertas para Joao da Silva",
            summary: "PA elevada + creatinina em alta + adesao baixa",
            recommended_action: "Avaliar urgente — PA critica",
            details: [...]
        }
        """
```

### 3.6 Escalacao de Alertas

```python
class AlertEscalator:
    """
    Escala alertas nao lidos ou nao tratados.
    """

    # Tempo ate escalacao por severidade
    ESCALATION_TIMEOUTS = {
        "critical": timedelta(minutes=5),
        "high": timedelta(minutes=15),
        "medium": timedelta(hours=2),
        "low": timedelta(hours=24),
    }

    async def schedule_escalation(
        self,
        alert: ClinicalAlert,
    ) -> None:
        """Agenda verificacao de leitura e escalacao."""

    async def check_and_escalate(
        self,
        alert_id: UUID,
    ) -> None:
        """
        Verifica se alerta foi lido/tratado.

        Se nao lido em tempo:
        - CRITICAL: Notificar medico de plantao + coordenador
        - HIGH: Notificar supervisor
        - MEDIUM: Reenviar
        - LOW: Marcar como expirado
        """
```

### 3.7 Fila de Alertas para Equipe

```python
class AlertQueue:
    """
    Fila gerenciada de alertas pendentes por unidade.
    """

    async def get_pending_alerts(
        self,
        unit_id: str,
        severity_filter: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[ClinicalAlert]:
        """
        Retorna alertas pendentes para a unidade.

        Ordena por: severity (critico primeiro) + timestamp
        """

    async def acknowledge_alert(
        self,
        alert_id: UUID,
        professional_id: str,
        comment: Optional[str] = None,
    ) -> None:
        """
        Profissional reconhece o alerta.

        Cancela escalacao pendente.
        Registra acknowledgment.
        """

    async def resolve_alert(
        self,
        alert_id: UUID,
        professional_id: str,
        resolution_notes: str,
    ) -> None:
        """
        Profissional resolve o alerta.

        Status: pending → acknowledged → resolved
        """
```

### 3.8 Tabelas

```sql
-- Alertas clinicos
CREATE TABLE clinical_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    source_agent VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    recommended_action TEXT,
    clinical_data JSONB DEFAULT '{}',
    priority_score INTEGER DEFAULT 50,     -- 0-100
    is_consolidated BOOLEAN DEFAULT FALSE,
    consolidated_from JSONB DEFAULT '[]',  -- alert_ids agrupados

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, acknowledged, resolved, expired, deduplicated
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,

    -- Escalacao
    escalation_scheduled_at TIMESTAMPTZ,
    escalated BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMPTZ,

    -- Rastreabilidade
    idempotency_key VARCHAR(128) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_patient ON clinical_alerts(patient_id);
CREATE INDEX idx_alerts_status ON clinical_alerts(status);
CREATE INDEX idx_alerts_severity ON clinical_alerts(severity, status);
CREATE INDEX idx_alerts_pending ON clinical_alerts(status, priority_score)
    WHERE status = 'pending';
```

### 3.9 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/alerts` | Receber alerta de agente |
| GET | `/api/v1/alerts/queue` | Fila de alertas pendentes |
| PUT | `/api/v1/alerts/{id}/acknowledge` | Reconhecer alerta |
| PUT | `/api/v1/alerts/{id}/resolve` | Resolver alerta |
| GET | `/api/v1/alerts/patient/{patient_id}` | Alertas do paciente |
| GET | `/api/v1/alerts/stats` | Metricas de alertas |

## 4. Testes

- AlertHub: receive, dedup, priority, consolidate, dispatch (8 testes)
- AlertDeduplicator: duplicado, nao duplicado, janelas (5 testes)
- AlertPrioritizer: fatores que aumentam, que reduzem (5 testes)
- AlertConsolidator: 1 alerta, 3 alertas, janela expirada (4 testes)
- AlertEscalator: sem escalacao, com escalacao, cada severidade (5 testes)
- AlertQueue: pending, acknowledge, resolve (4 testes)
- Endpoints (6 testes)
- **Total**: 37+ testes

## 5. Criterios de Aceitacao

- [ ] Hub centralizado recebe alertas de todos os agentes
- [ ] Deduplicacao com janelas por tipo de alerta
- [ ] Priorizacao com fatores contextuais (IPS, jornada)
- [ ] Consolidacao de alertas em janela de 5 minutos
- [ ] Escalacao automatica por severidade
- [ ] Fila de alertas gerenciada por unidade
- [ ] Acknowledge e resolve por profissional
- [ ] Metricas (alertas pendentes, tempo medio de resolucao)
- [ ] 6 endpoints funcionais
- [ ] 37+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~9
- **Arquivos modificados**: ~3 (api, config, event_coordinator)
- **Linhas estimadas**: ~1.600
- **Testes novos**: ~37
