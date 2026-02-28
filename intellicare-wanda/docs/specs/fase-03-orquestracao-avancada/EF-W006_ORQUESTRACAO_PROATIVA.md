# EF-W006 — Orquestracao Proativa

> Wanda age sem ser chamada, coordenando agentes em resposta a eventos do ecossistema.

## 1. Objetivo

Transformar a Wanda de uma **orquestradora reativa** (responde quando chamada) para uma **orquestradora proativa** (age automaticamente em resposta a eventos):
- Recebe eventos de todos os agentes do ecossistema
- Avalia quais agentes devem ser acionados em resposta
- Coordena respostas multi-agente a eventos clinicos
- Garante que eventos criticos sejam tratados mesmo sem usuario chamando

## 2. Justificativa

- **Tempo real**: Evento de piora clinica nao pode esperar usuario perguntar
- **Coordenacao**: Um evento pode requerer acao de 3-4 agentes simultaneamente
- **Duplicidade**: Sem coordenacao central, Geralda e Florence podem notificar o mesmo paciente duplamente
- **Prioridade**: Wanda decide qual agente trata primeiro
- **Registro**: Log centralizado de todos os eventos do ecossistema

## 3. Escopo

### 3.1 Consumidor de Eventos do Ecossistema

```python
class EcosystemEventConsumer:
    """
    Consome eventos de todos os agentes via Redis Streams.

    Wanda e o hub central de eventos do ecossistema.
    """

    STREAMS = [
        "intellicare:events:clinical",       # Florence, Oswaldo, FHIR
        "intellicare:events:care",            # Geralda (cuidado)
        "intellicare:events:digital",         # Comunicacao, Portal
        "intellicare:events:operational",     # Agenda, Comunicacao
    ]

    CONSUMER_GROUP = "wanda"
    CONSUMER_NAME = "wanda-orchestrator"

    async def start_consuming(self) -> None:
        """
        Inicia consumo continuo de eventos.

        Usa XREADGROUP para consumo distribuido:
        - Garante que cada evento e processado exatamente uma vez
        - Permite retry de eventos nao confirmados
        - Historico de eventos processados
        """

    async def handle_event(
        self,
        stream: str,
        event_data: dict,
    ) -> None:
        """
        Delega para EventCoordinator.coordinate().
        Confirma processamento no stream (XACK).
        """
```

### 3.2 Coordenador de Eventos

```python
class EventCoordinator:
    """
    Decide quais agentes devem ser acionados para cada evento.
    """

    # Mapa de evento → agentes que devem ser notificados
    EVENT_COORDINATION_MAP = {
        "clinical.condition_worsened": {
            "notify": ["geralda", "comunicacao"],
            "workflow": "critical_alert",
            "priority": "high",
        },
        "clinical.exam_result": {
            "notify": ["geralda", "florence"],
            "workflow": None,
            "priority": "medium",
        },
        "clinical.admission": {
            "notify": ["geralda"],
            "workflow": "patient_onboarding",
            "priority": "high",
        },
        "clinical.discharge": {
            "notify": ["geralda", "comunicacao"],
            "workflow": None,
            "priority": "high",
        },
        "care.adherence_low": {
            "notify": ["comunicacao"],
            "workflow": None,
            "priority": "medium",
        },
        "clinical.vital_sign_alert": {
            "notify": ["geralda", "florence"],
            "workflow": "critical_alert",
            "priority": "high",
        },
    }

    async def coordinate(
        self,
        event: IntelliCareEvent,
    ) -> CoordinationResult:
        """
        Coordena resposta ao evento.

        Fluxo:
        1. Verificar se evento esta no mapa
        2. Verificar deduplicacao (mesmo evento nao processado 2x)
        3. Carregar IPS se patient_id presente (EF-W002)
        4. Notificar agentes via HTTP (/api/v1/events)
        5. Se workflow definido → executar via WorkflowExecutor
        6. Registrar coordenacao no audit log
        7. Retornar resultado
        """

    async def broadcast_event(
        self,
        event: IntelliCareEvent,
        target_agents: list[str],
        priority: str = "medium",
    ) -> dict[str, bool]:
        """
        Envia evento para multiplos agentes simultaneamente.

        HTTP POST /{agent}/api/v1/events para cada target.
        Retorna dict {agent: success} para rastreabilidade.
        """
```

### 3.3 Deduplicacao de Eventos

```python
class EventDeduplicator:
    """
    Garante que Wanda nao processe o mesmo evento duas vezes.

    Separado da deduplicacao dos agentes individuais.
    """

    def __init__(self, redis_client, ttl: int = 3600):
        self._redis = redis_client
        self._ttl = ttl

    async def is_duplicate(
        self,
        event: IntelliCareEvent,
    ) -> bool:
        """
        Verifica se evento ja foi coordenado.

        Chave: f"wanda:dedup:{event.idempotency_key}"
        """

    async def mark_processed(
        self,
        event: IntelliCareEvent,
    ) -> None:
        """Marca como processado no Redis."""
```

### 3.4 Orquestracao Proativa — Cenarios

#### Cenario 1: Piora Clinica
```
Oswaldo detecta: TFG caiu de 45 para 32 (piora DRC G3 → G3b)
    │
    ▼
Oswaldo publica: clinical.condition_worsened
    │
    ▼
Wanda consome evento
    │
    ├─ Carrega IPS do paciente
    ├─ Ativa WORKFLOW critical_alert:
    │     ├─ Florence: analisa impacto clnico
    │     ├─ Geralda: ajusta jornada (ativa C51)
    │     └─ Comunicacao: notifica equipe URGENTE
    └─ Registra no audit log
```

#### Cenario 2: Alta Clinica
```
FHIR Encounter muda para finished
    │
    ▼
Geralda publica: clinical.discharge
    │
    ▼
Wanda consome
    │
    ├─ Notifica Comunicacao: ativar canal pos-alta
    ├─ Notifica Geralda: iniciar fluxo E5 → E6
    └─ Verifica se Zilda precisa ser notificada (APS de referencia)
```

#### Cenario 3: Sem Interacao
```
Geralda publica: care.adherence_low (adesao caiu para 35%)
    │
    ▼
Wanda avalia severidade
    │
    ├─ Adesao < 40% → HIGH
    │     └─ Comunicacao: notificar equipe + mensagem urgente paciente
    │
    └─ Adesao 40-60% → MEDIUM
          └─ Comunicacao: mensagem motivacional ao paciente
```

### 3.5 Registro de Coordenacoes

```python
# Tabela wanda.event_coordinations
# (complementa orchestration_executions — EF-W001)
```

```sql
CREATE TABLE event_coordinations (
    id BIGSERIAL PRIMARY KEY,
    coordination_id UUID UNIQUE NOT NULL,
    event_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    patient_id VARCHAR(64),
    agents_notified JSONB DEFAULT '[]',
    agents_failed JSONB DEFAULT '[]',
    workflow_triggered VARCHAR(50),
    priority VARCHAR(20),
    coordination_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    coordinated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coordinations_event ON event_coordinations(event_id);
CREATE INDEX idx_coordinations_patient ON event_coordinations(patient_id);
CREATE INDEX idx_coordinations_date ON event_coordinations(coordinated_at);
```

### 3.6 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/events/stream` | Status dos streams Redis |
| GET | `/api/v1/events/coordinations` | Historico de coordenacoes |
| POST | `/api/v1/events/simulate` | Simular evento (dev/debug) |

## 4. Testes

- EcosystemEventConsumer: consumo, retry, grupo (5 testes)
- EventCoordinator: cada tipo de evento, multi-agent (8 testes)
- EventDeduplicator: duplicado, nao duplicado, TTL (4 testes)
- Broadcast: success, partial failure, todos falham (4 testes)
- Cenarios end-to-end: piora clinica, alta, adesao (3 testes)
- Endpoints (3 testes)
- **Total**: 27+ testes

## 5. Criterios de Aceitacao

- [ ] Consumo de 4 streams Redis com consumer group
- [ ] Mapa de coordenacao para eventos principais
- [ ] Broadcast para multiplos agentes em paralelo
- [ ] Deduplicacao de eventos (Redis TTL 1h)
- [ ] Ativacao de workflows para eventos criticos
- [ ] IPS carregado antes de notificar agentes
- [ ] Registro de coordenacoes (audit trail)
- [ ] Simulacao de eventos (debug)
- [ ] 27+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~7
- **Arquivos modificados**: ~3 (api, config, docker)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~27
