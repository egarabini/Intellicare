# EF-009 — Integracao com Wanda (Orquestradora)

> Registrar Geralda como agente no ecossistema Wanda e definir contrato de comunicacao bidirecional.

## 1. Objetivo

Integrar a Geralda ao ecossistema de orquestracao da Wanda, permitindo:
- Wanda descobrir Geralda automaticamente via `/api/v1/info`
- Wanda rotear solicitacoes de cuidado para Geralda
- Geralda notificar Wanda sobre eventos importantes da jornada
- Geralda solicitar dados de outros agentes via Wanda
- Resposta agregada em consultas multi-agente

## 2. Justificativa

- **Desacoplamento**: Geralda nao importa outros agentes diretamente
- **Orquestracao**: Wanda decide quando e como acionar Geralda
- **Visibilidade**: Wanda monitora saude e disponibilidade da Geralda
- **Escalabilidade**: Novas capacidades da Geralda sao descobertas automaticamente
- **Seguranca**: Wanda aplica regras IPS-First antes de rotear

## 3. Escopo

### 3.1 Contrato `/api/v1/info` (Autodescricao)

Geralda deve responder ao endpoint de autodescricao com suas capacidades:

```python
# Resposta de GET /api/v1/info
{
    "agent_name": "Geralda",
    "version": "2.0.0",
    "description": "Agente de acompanhamento do paciente — gestao de cuidado, lembretes, educacao, jornada",
    "homage": "Geralda Lopes da Silva",
    "port": 8006,
    "status": "healthy",

    "capabilities": [
        {
            "id": "care_management",
            "name": "Gestao de Cuidado",
            "description": "Criar, gerenciar e monitorar planos de cuidado do paciente",
            "keywords": ["plano de cuidado", "care plan", "cuidado", "tarefa", "atividade", "acompanhamento"],
            "input_types": ["patient_id", "condition_code", "care_plan_request"],
            "output_types": ["care_plan", "task_list", "adherence_report"],
        },
        {
            "id": "reminders",
            "name": "Sistema de Lembretes",
            "description": "Gerenciar lembretes de medicamentos, consultas e atividades",
            "keywords": ["lembrete", "reminder", "medicamento", "consulta", "agenda"],
            "input_types": ["patient_id", "reminder_request"],
            "output_types": ["reminder", "daily_schedule"],
        },
        {
            "id": "education",
            "name": "Educacao em Saude",
            "description": "Materiais educativos personalizados por condicao e nivel de leitura",
            "keywords": ["educacao", "material", "orientacao", "aprender", "entender", "doenca"],
            "input_types": ["patient_id", "condition_code", "topic"],
            "output_types": ["education_content", "learning_path", "quiz"],
        },
        {
            "id": "patient_journey",
            "name": "Jornada do Paciente",
            "description": "Gestao do ciclo de vida do paciente (internacao, cuidados, alta, pos-alta)",
            "keywords": ["jornada", "internacao", "alta", "pos-alta", "acompanhamento", "estado"],
            "input_types": ["patient_id", "event"],
            "output_types": ["journey_state", "timeline", "context"],
        },
        {
            "id": "adherence",
            "name": "Monitoramento de Adesao",
            "description": "Calcular e monitorar adesao ao tratamento com predicao de risco",
            "keywords": ["adesao", "aderencia", "compliance", "tratamento", "medicamento"],
            "input_types": ["patient_id", "care_plan_id"],
            "output_types": ["adherence_score", "risk_prediction", "intervention_suggestion"],
        },
        {
            "id": "chat",
            "name": "Chat Inteligente",
            "description": "Conversa com paciente/profissional mediada por IA local",
            "keywords": ["chat", "conversa", "duvida", "pergunta", "orientacao"],
            "input_types": ["message", "patient_id", "role"],
            "output_types": ["response", "actions_taken"],
        },
    ],

    "requires_patient_context": True,  # Sempre precisa de patient_id
    "supports_ips_first": True,        # Aceita IPS no request

    "endpoints": {
        "analyze": "/api/v1/analyze",   # Endpoint padrao Wanda
        "chat": "/api/v1/chat",
        "health": "/api/v1/health",
        "events": "/api/v1/events",
    },
}
```

### 3.2 Endpoint `/api/v1/analyze` (Contrato Wanda)

Endpoint padrao que Wanda usa para consultar qualquer agente:

```python
# POST /api/v1/analyze
# Request (vindo da Wanda)
{
    "query": "Qual o estado de adesao do paciente Joao?",
    "patient_id": "patient-123",
    "capability": "adherence",         # Wanda ja selecionou a capability
    "ips": { ... },                    # IPS do paciente (regra IPS-First)
    "context": {
        "requesting_agent": "wanda",
        "original_query": "Como esta o paciente Joao?",
        "session_id": "session-abc",
        "priority": "normal",
    },
}

# Response
{
    "success": True,
    "agent": "geralda",
    "capability_used": "adherence",
    "result": {
        "adherence_score": 0.72,
        "trend": "declining",
        "days_analyzed": 30,
        "missed_tasks": [
            {"task": "Losartana 50mg", "missed_count": 4, "last_missed": "2026-02-13"},
            {"task": "Caminhada 30min", "missed_count": 8, "last_missed": "2026-02-14"},
        ],
        "recommendation": "Adesao em queda. Sugerir conversa motivacional e ajuste de horarios.",
    },
    "summary": "Paciente Joao tem adesao de 72% nos ultimos 30 dias, em tendencia de queda. Principal dificuldade: exercicios fisicos e Losartana.",
    "confidence": 0.95,
    "metadata": {
        "processing_time_ms": 230,
        "llm_used": False,  # Calculo deterministico
    },
}
```

### 3.3 Roteamento na Wanda

Wanda utiliza keywords das capabilities para rotear. Exemplo de mapeamento:

| Consulta do Usuario | Keywords Matched | Capability | Agente |
|---------------------|-----------------|------------|--------|
| "Como esta a adesao do paciente?" | adesao, tratamento | adherence | Geralda |
| "Criar plano de cuidado para DRC" | plano de cuidado, cuidado | care_management | Geralda |
| "O que o paciente deve fazer hoje?" | agenda, atividade | reminders | Geralda |
| "Material sobre diabetes" | educacao, doenca | education | Geralda |
| "Qual o estagio da DRC?" | DRC, estagio | chronic_disease | Oswaldo |
| "Resultados de laboratorio" | laboratorio, exame | lab_analysis | Florence |

### 3.4 Geralda → Wanda (Notificacoes)

Geralda notifica Wanda sobre eventos que podem requerer acao de outros agentes:

```python
class WandaNotifier:
    """Notifica Wanda sobre eventos da jornada."""

    def __init__(self, wanda_url: str, http_client):
        self._wanda_url = wanda_url  # ex: "http://wanda:8007"
        self._client = http_client

    async def notify_event(
        self,
        event: IntelliCareEvent,
        requires_action: bool = False,
    ) -> None:
        """
        Envia evento para Wanda.

        POST {wanda_url}/api/v1/events
        {
            "source": "geralda",
            "event": { ... IntelliCareEvent serializado ... },
            "requires_action": true/false,
            "suggested_agents": ["florence", "oswaldo"],
        }
        """

    async def request_patient_data(
        self,
        patient_id: str,
        data_needed: list[str],
    ) -> dict:
        """
        Solicita dados de outros agentes via Wanda.

        Ex: Geralda precisa de dados de Oswaldo (estagio DRC)
            e Florence (ultimo laboratorio) para gerar resumo.

        POST {wanda_url}/api/v1/query
        {
            "source": "geralda",
            "patient_id": "patient-123",
            "queries": [
                {"agent": "oswaldo", "capability": "chronic_disease", "query": "estagio atual DRC"},
                {"agent": "florence", "capability": "lab_analysis", "query": "ultimo creatinina"},
            ],
        }

        Response: dados agregados de todos os agentes consultados
        """

    async def escalate_to_wanda(
        self,
        patient_id: str,
        reason: str,
        severity: str,
        context: dict,
    ) -> None:
        """
        Escalona situacao critica para Wanda decidir acao.

        Ex: Paciente com adesao critica + piora clinica
            → Wanda pode acionar Florence + Comunicacao + Donabedian
        """
```

### 3.5 Consulta Multi-Agente via Wanda

Quando Wanda identifica que uma consulta requer multiplos agentes:

```
Usuario: "Como esta o paciente Joao no geral?"
    │
    ▼
Wanda analisa → Multi-agente necessario
    │
    ├─ Geralda.analyze(capability="adherence")  → Adesao 72%
    ├─ Oswaldo.analyze(capability="chronic_disease") → DRC estagio 3a estavel
    ├─ Florence.analyze(capability="lab_analysis")   → Creatinina 1.8 mg/dL
    │
    ▼
Wanda agrega respostas → Resposta consolidada:
"Paciente Joao: DRC estagio 3a estavel (Oswaldo).
 Creatinina 1.8 mg/dL no ultimo exame (Florence).
 Adesao ao tratamento 72%, em leve queda — principal dificuldade
 com exercicios e Losartana (Geralda).
 Recomendacao: conversa motivacional sobre importancia dos exercicios."
```

### 3.6 Arquitetura de Integracao

```
geralda/integrations/
  __init__.py
  wanda_client.py           # Cliente HTTP para Wanda
  wanda_notifier.py         # Notificacao de eventos
  agent_info.py             # Autodescricao (/api/v1/info)
  analyze_handler.py        # Handler do endpoint /api/v1/analyze
```

### 3.7 Configuracao

```env
# Wanda
INTELLICARE_WANDA_URL=http://wanda:8007
INTELLICARE_WANDA_ENABLED=true
INTELLICARE_WANDA_TIMEOUT=30
INTELLICARE_WANDA_RETRY_MAX=3
INTELLICARE_WANDA_RETRY_DELAY=2

# Auto-registro
INTELLICARE_AGENT_NAME=geralda
INTELLICARE_AGENT_PORT=8006
INTELLICARE_AGENT_VERSION=2.0.0
```

### 3.8 Health Check Enriquecido

```python
# GET /api/v1/health (enriquecido para Wanda)
{
    "status": "healthy",
    "agent": "geralda",
    "version": "2.0.0",
    "uptime_seconds": 3600,
    "dependencies": {
        "postgresql": "healthy",
        "redis": "healthy",
        "ollama": "healthy",        # ou "degraded" se indisponivel
        "fhir_server": "healthy",   # ou "unreachable"
    },
    "metrics": {
        "active_care_plans": 42,
        "active_reminders": 128,
        "events_processed_24h": 1520,
        "avg_response_time_ms": 180,
    },
}
```

### 3.9 Graceful Degradation

Se Wanda estiver indisponivel:
- Geralda continua funcionando standalone (v1.0 behavior)
- Eventos sao enfileirados no Redis para envio posterior
- Consultas multi-agente retornam apenas dados da Geralda
- Log de aviso "Wanda unreachable — operating standalone"

Se Geralda estiver indisponivel:
- Wanda marca Geralda como "unhealthy" no discovery
- Consultas de cuidado/adesao retornam "Agente Geralda indisponivel"
- Outros agentes continuam funcionando normalmente

## 4. Testes

- AgentInfo: resposta /api/v1/info completa (3 testes)
- AnalyzeHandler: cada capability (6 testes)
- WandaNotifier: envio de evento, request de dados, escalation (6 testes)
- WandaClient: conexao, timeout, retry (5 testes)
- HealthCheck: com/sem dependencias (4 testes)
- Graceful degradation: Wanda indisponivel (3 testes)
- Integracao: fluxo completo Wanda → Geralda → resposta (3 testes)
- **Total**: 30+ testes

## 5. Criterios de Aceitacao

- [ ] `/api/v1/info` com 6 capabilities declaradas
- [ ] `/api/v1/analyze` funcional para todas as capabilities
- [ ] Notificacao de eventos para Wanda via HTTP
- [ ] Solicitacao de dados de outros agentes via Wanda
- [ ] Escalation para Wanda em situacoes criticas
- [ ] Health check enriquecido com dependencias
- [ ] Graceful degradation quando Wanda indisponivel
- [ ] Configuracao via environment variables
- [ ] 30+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~6
- **Arquivos modificados**: ~4 (api/app, config, health, docker)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~30
