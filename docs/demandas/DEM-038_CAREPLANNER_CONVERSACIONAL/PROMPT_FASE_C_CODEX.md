# DEM-038 Fase C — Prompt para Codex

> **PLANEJADOR** | 2026-03-17
> Base path: `C:\Users\egara\INTELLICARE\`
> Fases A e B commitadas e aceitas (commits `b6a3966` e `a646bc2`).

---

## Objetivo da Fase C

Integrar o CarePlanner com a infraestrutura interna do IntelliCare:

1. **Notificações realtime** ao CLINICO quando o paciente responde (`REPLIED`)
2. **Gatilho para o módulo `cuidado`** — ao atingir `REPLIED`, criar sugestão de consulta
3. **Métricas Prometheus** — expor os 6 contadores/histogramas definidos na spec
4. **Dashboard operacional** em GestorUI — página `/careplanner` com KPIs das jornadas

---

## O que já existe (NÃO ALTERAR)

| Arquivo | O que tem |
|---------|-----------|
| `modules/careplanner/contracts.py` | `TaskStatus`, `EventType`, todos os models Pydantic |
| `modules/careplanner/config.py` | `CareplannerSettings`, `get_careplanner_settings()` |
| `modules/careplanner/repository.py` | CRUD completo + `find_conversation`, `list_tasks`, `get_template_by_code` |
| `modules/careplanner/migrations.py` | 5 tabelas: `care_tasks`, `care_conversations`, `care_events`, `care_templates`, `care_video_sessions` |
| `modules/careplanner/services.py` | `CareplannerService` com todos os fluxos + `build_careplanner_service()` |
| `modules/careplanner/api/routes.py` | 7 endpoints FastAPI |
| `modules/careplanner/adapters/` | `rocketchat.py`, `jitsi.py`, `kestra.py` |
| `modules/careplanner/main.py` | `Module(BaseModule)` com startup migrations |

---

## Interfaces que a Fase C deve usar

### Módulo `notifications` (DEM-026 — já ativo)

```python
# modules/notifications/redis_pubsub.py
async def publish_notification(tenant_id: str, user_id: str, payload: dict) -> int:
    """Publica notificação no canal Redis do usuário específico."""
    ...

async def publish_broadcast(tenant_id: str, payload: dict) -> int:
    """Publica notificação broadcast para todos do tenant."""
    ...
```

```python
# modules/notifications/service.py  →  NotificationService.send()
from modules.notifications.schemas import NotificationCreate
# NotificationType: "appointment" | "clinical" | "system" | "message" | "alert"
# NotificationPriority: "low" | "normal" | "high" | "urgent"

notif = NotificationCreate(
    user_id="keycloak-id-do-clinico",   # destinatário
    type="message",
    priority="high",
    title="Paciente respondeu",
    body="PAC-123 respondeu à jornada CONTATO_INICIAL",
    data={"correlation_id": "...", "task_type": "CONTATO_INICIAL"},
)
await NotificationService().send(ctx, notif)
```

O CLINICO recebe a notificação em tempo real via SSE (`GET /notifications/stream`)
ou WebSocket (`WS /notifications/ws?token=...`) — ambos já implementados no módulo.

### Módulo `cuidado` (DEM-032 — já ativo)

O módulo `cuidado` expõe `CuidadoService`. Para a integração de Fase C, a abordagem
correta é **não chamar o CuidadoService diretamente** do careplanner (evita acoplamento
de módulo → módulo). Em vez disso:

- Publicar um **evento Redis** no canal `careplanner:{tenant_id}:replied`
- O handler do cuidado pode assinar esse canal em Fase D/E (arquitetura de eventos)
- Para Fase C: adicionar um **endpoint interno** no módulo careplanner que pode ser
  chamado pelo Kestra para criar a consulta via `POST /cuidado/encounters`

Alternativa mais simples e aceita para Fase C: chamar o serviço `cuidado` via
**HTTP interno** usando `httpx` apontado para `http://intellicare-service:8000/cuidado/encounters`.

```
POST /cuidado/encounters
Authorization: Bearer <JWT service account>
{
  "patient_id": "<UUID do paciente se mapeado>",   # pode ser None se mapeamento ainda não existe
  "chief_complaint": "Jornada CarePlanner: {task_type}",
  "priority": "normal"
}
```

Se `patient_id` não estiver disponível (patient_ref é string opaca, não UUID),
registrar o evento e **não bloquear** o fluxo — log warning e seguir.

### Prometheus (`prometheus-fastapi-instrumentator` — já ativo)

O `intellicare-core/main.py` já configura o Instrumentator que expõe `/metrics`.
Para adicionar métricas customizadas do CarePlanner usar `prometheus_client` diretamente:

```python
from prometheus_client import Counter, Histogram

# Instanciar UMA VEZ como variáveis de módulo (não dentro de funções)
careplanner_dispatch_total = Counter(
    "careplanner_dispatch_total",
    "Total de dispatches por tenant e status",
    ["tenant_slug", "status"],
)
careplanner_event_total = Counter(
    "careplanner_event_total",
    "Total de eventos por tenant e tipo",
    ["tenant_slug", "event_type"],
)
# ... etc
```

`prometheus_client` já está disponível como dependência transitiva de
`prometheus-fastapi-instrumentator`. Não adicionar ao `pyproject.toml`.

### GestorUI (Mantine UI 7 + React Query + Axios)

Padrão existente (ver `frontend/GestorUI/src/`):

- **Página**: `src/pages/NomeDaPagina.tsx` — componente React com Mantine UI
- **Hook**: `src/hooks/useGestor.ts` — `useQuery` / `useMutation` via `@tanstack/react-query`
- **API client**: `src/api/client.ts` — `axios` com interceptor de Bearer token
- **Rota**: `src/App.tsx` — `<Route path="/careplanner" element={<CareplannerDashboard />} />`
- **Nav link**: `src/App.tsx` — `<MantineNavLink component={NavLink} to="/careplanner" label="CarePlanner" />`

Para reconstruir o frontend após mudanças:
```
cd C:\Users\egara\INTELLICARE\frontend\GestorUI && npm run build
```
O artefato fica em `frontend/GestorUI/dist/` (servido pelo FastAPI como estático).

---

## Arquivos a criar / modificar

### CRIAR

```
modules/careplanner/metrics.py          ← contadores/histogramas Prometheus
modules/careplanner/integrations.py     ← lógica de notificação + gatilho cuidado
frontend/GestorUI/src/pages/CareplannerDashboard.tsx   ← nova página
```

### MODIFICAR

```
modules/careplanner/services.py         ← chamar integrations em process_inbound e open_task
modules/careplanner/api/routes.py       ← + endpoint GET /careplanner/dashboard/stats
frontend/GestorUI/src/hooks/useGestor.ts  ← + useCareplannerStats hook
frontend/GestorUI/src/App.tsx           ← + rota /careplanner + nav link
packages/intellicare-core/tests/test_careplanner_phase_c.py  ← CRIAR (7 testes)
```

---

## 1. `modules/careplanner/metrics.py`

```python
"""Métricas Prometheus do módulo CarePlanner."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

# ── Contadores ───────────────────────────────────────────────────────────────

careplanner_dispatch_total = Counter(
    "careplanner_dispatch_total",
    "Disparos de mensagem por tenant e status final",
    ["tenant_slug", "status"],           # status: dispatched | failed
)

careplanner_event_total = Counter(
    "careplanner_event_total",
    "Eventos CarePlanner por tenant e tipo",
    ["tenant_slug", "event_type"],       # MESSAGE_SENT, INBOUND_RECEIVED, etc.
)

careplanner_orphan_inbound_total = Counter(
    "careplanner_orphan_inbound_total",
    "Inbounds sem correlação por tenant",
    ["tenant_slug"],
)

careplanner_video_session_total = Counter(
    "careplanner_video_session_total",
    "Videoconsultas abertas por tenant",
    ["tenant_slug"],
)

# ── Histogramas ──────────────────────────────────────────────────────────────

careplanner_dispatch_to_sent_seconds = Histogram(
    "careplanner_dispatch_to_sent_seconds",
    "Tempo entre DISPATCHED e SENT (confirmação de entrega)",
    ["tenant_slug"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

careplanner_inbound_to_close_seconds = Histogram(
    "careplanner_inbound_to_close_seconds",
    "Tempo entre REPLIED e CLOSED (resolução da jornada)",
    ["tenant_slug"],
    buckets=[60, 300, 900, 1800, 3600, 7200, 86400],
)
```

---

## 2. `modules/careplanner/integrations.py`

```python
"""
Integrações internas do CarePlanner com outros módulos IntelliCare.

Responsabilidades:
  - notify_clinico_replied: publicar notificação realtime ao CLINICO via módulo notifications
  - trigger_cuidado_encounter: sugerir criação de consulta via HTTP interno
"""
from __future__ import annotations

import logging
from uuid import UUID

from intellicare_core.contracts.base import TenantContext

logger = logging.getLogger(__name__)


async def notify_clinico_replied(
    ctx: TenantContext,
    correlation_id: UUID,
    task_type: str,
    patient_ref: str,
    clinico_ref: str | None,
    content: str,
) -> None:
    """
    Publica notificação realtime ao CLINICO quando paciente responde.

    Usa publish_notification do módulo notifications (DEM-026):
      from modules.notifications.redis_pubsub import publish_notification

    Se clinico_ref for None ou Redis estiver indisponível:
      → logar warning e retornar silenciosamente (nunca bloquear o fluxo principal)

    Payload da notificação:
    {
      "type": "message",
      "priority": "high",
      "title": "Paciente respondeu",
      "body": f"{patient_ref} respondeu à jornada {task_type}: \"{content[:80]}\"",
      "data": {
        "correlation_id": str(correlation_id),
        "task_type": task_type,
        "patient_ref": patient_ref,
        "module": "careplanner",
        "event": "REPLIED"
      }
    }

    user_id para notify_notification = clinico_ref (ID Keycloak do clínico)
    Se clinico_ref for None → publish_broadcast(tenant_id, payload) para todo o tenant
    """
    try:
        from modules.notifications.redis_pubsub import publish_broadcast, publish_notification

        payload = {
            "type": "message",
            "priority": "high",
            "title": "Paciente respondeu",
            "body": f"{patient_ref} respondeu à jornada {task_type}: \"{content[:80]}\"",
            "data": {
                "correlation_id": str(correlation_id),
                "task_type": task_type,
                "patient_ref": patient_ref,
                "module": "careplanner",
                "event": "REPLIED",
            },
        }
        if clinico_ref:
            await publish_notification(ctx.tenant_id, clinico_ref, payload)
        else:
            await publish_broadcast(ctx.tenant_id, payload)
        logger.info(
            "Notificação REPLIED enviada: tenant=%s correlation=%s clinico=%s",
            ctx.tenant_id, correlation_id, clinico_ref,
        )
    except Exception:
        logger.warning(
            "Falha ao notificar CLINICO (non-fatal): correlation=%s", correlation_id,
            exc_info=True,
        )


async def trigger_cuidado_encounter(
    ctx: TenantContext,
    correlation_id: UUID,
    task_type: str,
    patient_ref: str,
) -> None:
    """
    Sugere criação de consulta no módulo cuidado após REPLIED.

    Estratégia Fase C: publicar evento Redis no canal
      careplanner:{tenant_id}:replied
    para desacoplamento (Kestra/cuidado pode assinar em Fase D).

    Também tenta resolução do patient_ref para UUID:
    - Se patient_ref for UUID válido → criar encounter via HTTP interno
    - Se não for UUID → logar info e publicar apenas o evento Redis

    HTTP interno (se patient_ref for UUID):
      POST http://intellicare-service:8000/cuidado/encounters
      Authorization: Bearer <service_account_token>   # não disponível em Fase C → pular
    → Para Fase C: APENAS publicar o evento Redis. HTTP internal fica para Fase D
      quando service account Keycloak estiver configurado.

    Formato do evento Redis (canal: careplanner:{tenant_id}:replied):
    {
      "event": "REPLIED",
      "correlation_id": str(correlation_id),
      "task_type": task_type,
      "patient_ref": patient_ref,
      "tenant_id": ctx.tenant_id
    }
    """
    try:
        import json
        from modules.notifications.redis_pubsub import get_redis

        r = await get_redis()
        channel = f"careplanner:{ctx.tenant_id}:replied"
        payload = json.dumps({
            "event": "REPLIED",
            "correlation_id": str(correlation_id),
            "task_type": task_type,
            "patient_ref": patient_ref,
            "tenant_id": ctx.tenant_id,
        })
        await r.publish(channel, payload)
        logger.info(
            "Evento REPLIED publicado no Redis: tenant=%s correlation=%s",
            ctx.tenant_id, correlation_id,
        )
    except Exception:
        logger.warning(
            "Falha ao publicar evento cuidado (non-fatal): correlation=%s", correlation_id,
            exc_info=True,
        )
```

---

## 3. Modificar `modules/careplanner/services.py`

### 3a. Instrumentar métricas em pontos-chave

Adicionar imports no topo:
```python
from .metrics import (
    careplanner_dispatch_total,
    careplanner_dispatch_to_sent_seconds,
    careplanner_event_total,
    careplanner_inbound_to_close_seconds,
    careplanner_orphan_inbound_total,
    careplanner_video_session_total,
)
```

Pontos de instrumentação:

```python
# Em open_task() — após transition_task_status(DISPATCHED):
careplanner_dispatch_total.labels(tenant_slug=ctx.tenant_id, status="dispatched").inc()

# Em open_task() — no bloco except (httpx error / RC >= 500):
careplanner_dispatch_total.labels(tenant_slug=ctx.tenant_id, status="failed").inc()

# Em process_message_sent() — após transition_task_status(SENT):
careplanner_event_total.labels(
    tenant_slug=ctx.tenant_id, event_type="MESSAGE_SENT"
).inc()
# Histograma DISPATCHED→SENT: calcular delta created_at da task vs now
# (approximação: usar task.updated_at antes da transição como t0)

# Em process_inbound() — após transition REPLIED:
careplanner_event_total.labels(
    tenant_slug=ctx.tenant_id, event_type="INBOUND_RECEIVED"
).inc()

# Em process_inbound() — orphan:
careplanner_orphan_inbound_total.labels(tenant_slug=ctx.tenant_id).inc()

# Em open_video_session() — após create_video_session:
careplanner_video_session_total.labels(tenant_slug=ctx.tenant_id).inc()
careplanner_event_total.labels(
    tenant_slug=ctx.tenant_id, event_type="VIDEO_SESSION_OPENED"
).inc()

# Em close_task() — após transition CLOSED:
careplanner_event_total.labels(
    tenant_slug=ctx.tenant_id, event_type="TASK_CLOSED"
).inc()
# Histograma REPLIED→CLOSED: task.updated_at (antes da transição) = t0
```

### 3b. Chamar integrations em process_inbound()

Após confirmar transição para `REPLIED` e antes do `return`:

```python
# Notificar CLINICO realtime (non-blocking)
clinico_ref = task.metadata.get("clinico_ref") if task.metadata else None
await notify_clinico_replied(
    ctx,
    correlation_id=conversation.correlation_id,
    task_type=task.task_type,
    patient_ref=task.patient_ref,
    clinico_ref=clinico_ref,
    content=content,
)

# Publicar evento para módulo cuidado (non-blocking)
await trigger_cuidado_encounter(
    ctx,
    correlation_id=conversation.correlation_id,
    task_type=task.task_type,
    patient_ref=task.patient_ref,
)
```

Imports no topo de `services.py`:
```python
from .integrations import notify_clinico_replied, trigger_cuidado_encounter
```

---

## 4. Endpoint de stats para o dashboard

### Adicionar em `modules/careplanner/api/routes.py`

```python
@router.get("/dashboard/stats")
async def dashboard_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    """
    KPIs das jornadas para o GestorUI.
    Retorna contagens por status + últimas 5 jornadas com atividade recente.

    Resposta esperada:
    {
      "total": 120,
      "by_status": {
        "CREATED": 5,
        "DISPATCHED": 12,
        "SENT": 30,
        "REPLIED": 20,
        "CLOSED": 50,
        "FAILED": 2,
        "EXPIRED": 1
      },
      "recent_tasks": [
        {
          "correlation_id": "...",
          "patient_ref": "PAC-001",
          "task_type": "CONTATO_INICIAL",
          "status": "REPLIED",
          "updated_at": "2026-03-17T10:00:00Z"
        }
      ]
    }
    """
    return await service.get_dashboard_stats(ctx)
```

### Adicionar `get_dashboard_stats` em `services.py`

```python
async def get_dashboard_stats(self, ctx: TenantContext) -> dict:
    """
    Agrega contagens por status e últimas 5 jornadas com atividade recente.
    Usa repository.list_tasks para cada status ou uma query direta com COUNT.
    """
    from .contracts import TaskStatus
    from intellicare_core.db.session import tenant_session
    from sqlalchemy import text

    # Contar por status com uma query só (eficiente)
    async with tenant_session(ctx) as db:
        rows = (
            await db.execute(
                text("""
                    SELECT status, COUNT(*) as cnt
                    FROM care_tasks
                    GROUP BY status
                """)
            )
        ).mappings().all()

        recent = (
            await db.execute(
                text("""
                    SELECT correlation_id, patient_ref, task_type, status, updated_at
                    FROM care_tasks
                    ORDER BY updated_at DESC
                    LIMIT 5
                """)
            )
        ).mappings().all()

    by_status = {s.value: 0 for s in TaskStatus}
    total = 0
    for row in rows:
        by_status[row["status"]] = row["cnt"]
        total += row["cnt"]

    return {
        "total": total,
        "by_status": by_status,
        "recent_tasks": [
            {
                "correlation_id": str(r["correlation_id"]),
                "patient_ref": r["patient_ref"],
                "task_type": r["task_type"],
                "status": r["status"],
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            }
            for r in recent
        ],
    }
```

---

## 5. `frontend/GestorUI/src/pages/CareplannerDashboard.tsx`

Nova página seguindo exatamente o padrão de `src/pages/Dashboard.tsx`.

```tsx
import {
  Box, Card, Center, Group, Loader, SimpleGrid,
  Stack, Text, ThemeIcon, Title, Badge,
} from '@mantine/core';
import {
  IconMessage, IconCheck, IconClock, IconAlertCircle,
  IconMessageCheck, IconRefresh,
} from '@tabler/icons-react';
import { useCareplannerStats } from '../hooks/useGestor';

const STATUS_META: Record<string, { color: string; label: string }> = {
  CREATED:    { color: 'gray',   label: 'Criadas' },
  DISPATCHED: { color: 'blue',   label: 'Disparadas' },
  SENT:       { color: 'cyan',   label: 'Entregues' },
  REPLIED:    { color: 'teal',   label: 'Respondidas' },
  CLOSED:     { color: 'green',  label: 'Fechadas' },
  FAILED:     { color: 'red',    label: 'Falhas' },
  EXPIRED:    { color: 'orange', label: 'Expiradas' },
};

export function CareplannerDashboard() {
  const { data, isLoading, error, refetch } = useCareplannerStats();

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (error) return <Text c="red">Erro ao carregar CarePlanner.</Text>;
  if (!data) return null;

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>CarePlanner — Jornadas</Title>
        <Text c="dimmed" size="sm">Total: {data.total} jornadas</Text>
      </Group>

      {/* KPIs por status */}
      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md" mb="xl">
        {Object.entries(STATUS_META).map(([status, meta]) => (
          <Card key={status} withBorder padding="md" radius="md">
            <Group justify="space-between">
              <div>
                <Text c="dimmed" tt="uppercase" fw={700} fz="xs">{meta.label}</Text>
                <Text fw={700} fz="xl">{data.by_status[status] ?? 0}</Text>
              </div>
              <Badge color={meta.color} variant="light" size="lg">
                {status}
              </Badge>
            </Group>
          </Card>
        ))}
      </SimpleGrid>

      {/* Jornadas recentes */}
      <Title order={3} mb="md">Atividade Recente</Title>
      <Card withBorder>
        {data.recent_tasks.length === 0 ? (
          <Text c="dimmed">Nenhuma jornada recente.</Text>
        ) : (
          <Stack gap="sm">
            {data.recent_tasks.map((task: any) => (
              <Group key={task.correlation_id} wrap="nowrap" justify="space-between">
                <Group wrap="nowrap">
                  <ThemeIcon
                    variant="light"
                    radius="xl"
                    color={STATUS_META[task.status]?.color ?? 'gray'}
                  >
                    <IconMessage size={16} />
                  </ThemeIcon>
                  <div>
                    <Text size="sm" fw={500}>{task.patient_ref}</Text>
                    <Text size="xs" c="dimmed">{task.task_type}</Text>
                  </div>
                </Group>
                <Group>
                  <Badge color={STATUS_META[task.status]?.color ?? 'gray'} variant="light">
                    {task.status}
                  </Badge>
                  <Text size="xs" c="dimmed">
                    {task.updated_at ? new Date(task.updated_at).toLocaleString('pt-BR') : '—'}
                  </Text>
                </Group>
              </Group>
            ))}
          </Stack>
        )}
      </Card>
    </Box>
  );
}
```

---

## 6. Modificar `frontend/GestorUI/src/hooks/useGestor.ts`

Adicionar após o hook `useDashboardStats` existente:

```typescript
// ── CarePlanner ──────────────────────────────────────────────────────────────

export interface CareplannerStats {
  total: number;
  by_status: Record<string, number>;
  recent_tasks: {
    correlation_id: string;
    patient_ref: string;
    task_type: string;
    status: string;
    updated_at: string | null;
  }[];
}

export function useCareplannerStats() {
  return useQuery<CareplannerStats>({
    queryKey: ['careplanner_stats'],
    queryFn: async () => {
      const { data } = await api.get('/careplanner/dashboard/stats');
      return data;
    },
    refetchInterval: 30_000,   // atualiza a cada 30s
  });
}
```

---

## 7. Modificar `frontend/GestorUI/src/App.tsx`

### Import da nova página (junto dos outros imports de páginas):
```typescript
import { CareplannerDashboard } from './pages/CareplannerDashboard';
```

### Nav link (junto dos outros MantineNavLink, em ordem lógica após Dashboard):
```tsx
<MantineNavLink
  component={NavLink}
  to="/careplanner"
  label="CarePlanner"
  leftSection={<IconMessage size="1rem"/>}
/>
```
Adicionar `IconMessage` ao import do `@tabler/icons-react` se ainda não estiver.

### Rota (dentro do `<Routes>`, após `/dashboard`):
```tsx
<Route path="/careplanner" element={<CareplannerDashboard />} />
```

---

## 8. Testes — `packages/intellicare-core/tests/test_careplanner_phase_c.py`

| # | Tipo | Descrição |
|---|------|-----------|
| 1 | Unit | `notify_clinico_replied` com Redis mockado → `publish_notification` chamado com payload correto |
| 2 | Unit | `notify_clinico_replied` com Redis lançando exceção → retorna silenciosamente (sem raise) |
| 3 | Unit | `notify_clinico_replied` com `clinico_ref=None` → `publish_broadcast` chamado |
| 4 | Unit | `trigger_cuidado_encounter` → publica no canal `careplanner:{tenant_id}:replied` |
| 5 | Unit | Métricas: `careplanner_dispatch_total` incrementa ao chamar `open_task` com mock RC |
| 6 | Integração | `process_inbound` → `notify_clinico_replied` é invocado (mock da função) |
| 7 | Integração | `GET /careplanner/dashboard/stats` retorna `by_status` com todos os status e `recent_tasks` como lista |

**Estrutura dos mocks para testes de notificação:**

```python
# Mockar o redis_pubsub com monkeypatch ou mock direto
from unittest.mock import AsyncMock, patch

async def test_notify_clinico_replied_calls_publish():
    with patch("modules.notifications.redis_pubsub.publish_notification", new_callable=AsyncMock) as mock_pub:
        from modules.careplanner.integrations import notify_clinico_replied
        from intellicare_core.contracts.base import TenantContext
        import uuid

        ctx = TenantContext.from_slug("test_c", "user-1", roles=["CLINICO"])
        await notify_clinico_replied(
            ctx,
            correlation_id=uuid.uuid4(),
            task_type="CONTATO_INICIAL",
            patient_ref="PAC-001",
            clinico_ref="dr.silva",
            content="SIM",
        )

        mock_pub.assert_called_once()
        call_kwargs = mock_pub.call_args
        assert call_kwargs.args[0] == "test_c"          # tenant_id
        assert call_kwargs.args[1] == "dr.silva"        # user_id
        payload = call_kwargs.args[2]
        assert payload["type"] == "message"
        assert payload["priority"] == "high"
        assert "REPLIED" in payload["data"]["event"]
```

---

## Build do frontend

Após modificar os arquivos do GestorUI, executar:

```
cd C:\Users\egara\INTELLICARE\frontend\GestorUI && npm run build
```

O build copia os artefatos para `frontend/GestorUI/dist/` que é servido pelo FastAPI.
Incluir `frontend/GestorUI/dist/` no commit (ou confirmar se está no `.gitignore`).

---

## Definição de Pronto (Fase C)

- [ ] `modules/careplanner/metrics.py` com 6 métricas definidas
- [ ] `modules/careplanner/integrations.py` com `notify_clinico_replied` e `trigger_cuidado_encounter`
- [ ] `services.py` instrumentado com métricas nos pontos corretos
- [ ] `services.py` chama integrations em `process_inbound` (non-blocking)
- [ ] `GET /careplanner/dashboard/stats` retorna `{total, by_status, recent_tasks}`
- [ ] `services.py` tem `get_dashboard_stats`
- [ ] `CareplannerDashboard.tsx` criado e rota `/careplanner` registrada no App.tsx
- [ ] `useCareplannerStats` adicionado em `useGestor.ts`
- [ ] GestorUI buildado sem erros
- [ ] `pytest test_careplanner_phase_c.py` → 7/7 passando
- [ ] `pytest test_careplanner_phase_b.py` → 10/10 (sem regressão)
- [ ] `pytest test_careplanner_phase_a.py` → 3/3 (sem regressão)

---

## Commit esperado

```
feat(DEM-038-C): CarePlanner Fase C — notificações realtime, métricas Prometheus, dashboard GestorUI

- metrics.py: 6 métricas (4 Counters + 2 Histograms) conforme spec
- integrations.py: notify_clinico_replied (Redis pub/sub via DEM-026) +
  trigger_cuidado_encounter (evento Redis canal careplanner:{tenant}:replied)
- services.py: instrumentação de métricas + chamada de integrations em
  process_inbound (non-blocking, nunca bloqueia fluxo principal)
- services.py: get_dashboard_stats (COUNT por status + 5 recentes)
- api/routes.py: GET /careplanner/dashboard/stats
- CareplannerDashboard.tsx: KPIs por status + atividade recente (Mantine UI 7)
- useGestor.ts: useCareplannerStats com refetchInterval 30s
- App.tsx: rota /careplanner + nav link
- test_careplanner_phase_c.py: 7 testes (unit + integração)
```
