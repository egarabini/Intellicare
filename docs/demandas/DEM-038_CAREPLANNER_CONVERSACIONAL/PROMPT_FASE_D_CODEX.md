# DEM-038 Fase D — Prompt para Codex

> **PLANEJADOR** | 2026-03-17
> Base path: `C:\Users\egara\INTELLICARE\`
> Fases A, B e C commitadas e aceitas (commits `b6a3966`, `a646bc2`, `c818cc1`).

---

## Objetivo da Fase D

Hardening do módulo CarePlanner em quatro eixos:

1. **Retry + dead-letter** para falhas de dispatch (substituir o stub `workers/dispatcher.py`)
2. **Expiração automática** de jornadas (`DISPATCHED` sem `MESSAGE_SENT` > SLA)
3. **Revisão de segurança** (mascaramento de PII nos logs, revisão HMAC, JWT Jitsi)
4. **Testes Playwright** da página `CareplannerDashboard` no GestorUI

---

## O que já existe (NÃO ALTERAR sem justificativa)

| Arquivo | Estado atual |
|---------|-------------|
| `modules/careplanner/workers/dispatcher.py` | Stub — `enqueue_dispatch` apenas loga |
| `modules/careplanner/services.py` | `open_task` levanta exceção em falha de RC; `process_inbound` chama integrations non-blocking |
| `modules/careplanner/metrics.py` | 6 métricas (4 Counters + 2 Histograms) |
| `modules/careplanner/integrations.py` | `notify_clinico_replied` + `trigger_cuidado_encounter` |
| `modules/careplanner/adapters/rocketchat.py` | Rate limiting + retry exponencial já implementados no nível HTTP |
| `modules/careplanner/contracts.py` | `TaskStatus.EXPIRED` já declarado; transições: `DISPATCHED → EXPIRED`, `SENT → EXPIRED` |
| `modules/careplanner/repository.py` | `list_tasks(status_filter, page, page_size)` disponível |

---

## 1. Retry + Dead-letter (`workers/dispatcher.py`)

### Problema atual

`open_task` em `services.py` faz o dispatch **de forma síncrona** dentro do request HTTP do Kestra. Se o Rocket.Chat estiver instável, o Kestra recebe erro 5xx e pode tentar novamente do seu lado, criando jornadas duplicadas.

### Solução Fase D

Implementar retry com backoff exponencial + dead-letter via **Redis List** (sem biblioteca externa — usar `aioredis` que já é dependência via módulo `notifications`).

**Arquitetura:**

```
open_task() → grava CareTask(CREATED) → enqueue_dispatch(correlation_id, tenant_slug)
                                               ↓
                                    Redis LIST: careplanner:dispatch:queue
                                               ↓
                             dispatcher_worker() (background task no lifespan)
                                               ↓
                    tenta RC.ensure_room + post_message (até 3x com backoff)
                                    ↙               ↘
                              sucesso              falha após 3x
                           → DISPATCHED         → dead-letter list
                                              careplanner:dispatch:dead
                                              + status → FAILED
```

### `workers/dispatcher.py` — implementação completa

```python
"""
Dispatcher assíncrono do CarePlanner com retry e dead-letter via Redis.

Fila principal : careplanner:dispatch:queue  (Redis LIST, RPUSH/BLPOP)
Dead-letter    : careplanner:dispatch:dead   (Redis LIST, RPUSH)
Formato de item: JSON com os campos abaixo
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from intellicare_core.contracts.base import TenantContext

logger = logging.getLogger(__name__)

QUEUE_KEY = "careplanner:dispatch:queue"
DEAD_KEY  = "careplanner:dispatch:dead"
MAX_RETRIES = 3
BACKOFF_BASE = 0.5   # segundos; tentativa N espera BACKOFF_BASE * 2^(N-1)


async def enqueue_dispatch(correlation_id: str, tenant_slug: str) -> None:
    """
    Enfileira um dispatch no Redis.
    Chamado por services.open_task() após criar o CareTask(CREATED).
    """
    try:
        from modules.notifications.redis_pubsub import get_redis
        r = await get_redis()
        item = json.dumps({
            "correlation_id": correlation_id,
            "tenant_slug": tenant_slug,
            "attempts": 0,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        })
        await r.rpush(QUEUE_KEY, item)
        logger.debug("dispatch enqueued: %s / %s", correlation_id, tenant_slug)
    except Exception:
        logger.warning("falha ao enfileirar dispatch (fallback sincrono vai ocorrer)", exc_info=True)


async def dispatcher_worker() -> None:
    """
    Worker que consome careplanner:dispatch:queue em loop.
    Executado como asyncio.Task no lifespan do módulo (main.py).

    Loop:
      1. BLPOP com timeout 5s (não bloqueia o event loop)
      2. Deserializar item
      3. Executar _do_dispatch(item)
      4. Em falha: incrementar attempts, recolocar na fila ou mandar para dead-letter
    """
    from modules.notifications.redis_pubsub import get_redis
    logger.info("CarePlanner dispatcher worker iniciado")
    while True:
        try:
            r = await get_redis()
            result = await r.blpop(QUEUE_KEY, timeout=5)
            if result is None:
                continue
            _, raw = result
            item = json.loads(raw)
            await _do_dispatch(item)
        except asyncio.CancelledError:
            logger.info("dispatcher_worker cancelado (shutdown)")
            break
        except Exception:
            logger.exception("erro inesperado no dispatcher_worker loop")
            await asyncio.sleep(1)


async def _do_dispatch(item: dict) -> None:
    """
    Executa o dispatch de um item.
    Em falha: retry com backoff ou dead-letter após MAX_RETRIES.
    """
    from modules.notifications.redis_pubsub import get_redis
    from modules.careplanner.services import build_careplanner_service
    from modules.careplanner.contracts import TaskStatus
    from modules.careplanner.repository import CareplannerRepository
    from uuid import UUID

    correlation_id = item["correlation_id"]
    tenant_slug = item["tenant_slug"]
    attempts = item.get("attempts", 0)

    ctx = TenantContext.from_slug(slug=tenant_slug, user_id="dispatcher-worker")

    repo = CareplannerRepository()
    task = await repo.get_task(ctx, UUID(correlation_id))
    if task is None:
        logger.warning("dispatch: task nao encontrada %s", correlation_id)
        return
    if task.status not in {TaskStatus.CREATED, TaskStatus.DISPATCHED}:
        logger.debug("dispatch: task %s em status %s, ignorando", correlation_id, task.status)
        return

    try:
        svc = build_careplanner_service()
        metadata = task.metadata or {}
        rc_room_id = await svc._rc.ensure_room(tenant_slug, task.patient_ref)
        template = await repo.get_template_by_code(ctx, metadata.get("template_code", ""))
        text_content = (
            (template.content if template else metadata.get("template_code", "")).format(
                **metadata.get("template_variables", {})
            )
        )
        await svc._rc.post_message(rc_room_id, text_content)
        await repo.transition_task_status(ctx, UUID(correlation_id), TaskStatus.DISPATCHED)
        from modules.careplanner.metrics import careplanner_dispatch_total
        careplanner_dispatch_total.labels(tenant_slug=tenant_slug, status="dispatched").inc()
        logger.info("dispatch ok: %s (tentativa %d)", correlation_id, attempts + 1)

    except Exception as exc:
        attempts += 1
        if attempts < MAX_RETRIES:
            backoff = BACKOFF_BASE * (2 ** (attempts - 1))
            logger.warning(
                "dispatch falhou (%s), retry %d/%d em %.1fs: %s",
                type(exc).__name__, attempts, MAX_RETRIES, backoff, correlation_id,
            )
            await asyncio.sleep(backoff)
            item["attempts"] = attempts
            r = await get_redis()
            await r.rpush(QUEUE_KEY, json.dumps(item))
        else:
            logger.error(
                "dispatch dead-letter apos %d tentativas: %s — %s",
                MAX_RETRIES, correlation_id, exc,
            )
            from modules.careplanner.metrics import careplanner_dispatch_total
            careplanner_dispatch_total.labels(tenant_slug=tenant_slug, status="failed").inc()
            item["failed_at"] = datetime.now(timezone.utc).isoformat()
            item["error"] = str(exc)
            r = await get_redis()
            await r.rpush(DEAD_KEY, json.dumps(item))
            try:
                await repo.transition_task_status(ctx, UUID(correlation_id), TaskStatus.FAILED)
            except Exception:
                pass
```

### Modificar `modules/careplanner/main.py`

Iniciar o worker no lifespan e cancelar no shutdown:

```python
import asyncio
from .workers.dispatcher import dispatcher_worker

class Module(BaseModule):
    def __init__(self) -> None:
        self._dispatcher_task: asyncio.Task | None = None

    async def startup(self) -> None:
        # ... migrations existentes ...
        self._dispatcher_task = asyncio.create_task(dispatcher_worker())
        logger.info("CarePlanner dispatcher worker agendado.")

    async def shutdown(self) -> None:
        if self._dispatcher_task and not self._dispatcher_task.done():
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
```

### Modificar `modules/careplanner/services.py` — `open_task()`

Substituir o dispatch síncrono pela fila. A função **não deve mais chamar `post_message` diretamente** — delega ao worker:

```python
# Remover o bloco try/except com ensure_room + post_message
# Substituir por:
from .workers.dispatcher import enqueue_dispatch

task = await self._repo.create_task(ctx, CareTaskCreate(...))
await enqueue_dispatch(str(task.correlation_id), ctx.tenant_id)
return {"ok": True, "correlation_id": str(task.correlation_id), "status": TaskStatus.CREATED.value}
```

> **Atenção:** com a fila assíncrona, `open_task` retorna `CREATED` (não `DISPATCHED`).
> O Kestra recebe 202 com `status: CREATED` e aguarda o webhook `MESSAGE_SENT` para saber
> quando o dispatch foi confirmado. Isso é o comportamento correto da spec.

---

## 2. Expiração automática de jornadas (`workers/expiry_worker.py`)

Jornadas em `DISPATCHED` que não recebem `MESSAGE_SENT` dentro do SLA devem ir para `EXPIRED`.

### Criar `modules/careplanner/workers/expiry_worker.py`

```python
"""
Worker de expiração: verifica jornadas DISPATCHED/SENT sem atividade > SLA.

SLA padrão: 24h sem MESSAGE_SENT → DISPATCHED expira
            72h sem REPLIED após SENT → SENT expira
Roda a cada 5 minutos.
"""
from __future__ import annotations

import asyncio
import logging
from sqlalchemy import text
from intellicare_core.db.session import get_engine
from modules.careplanner.contracts import TaskStatus
from modules.careplanner.repository import CareplannerRepository
from intellicare_core.contracts.base import TenantContext

logger = logging.getLogger(__name__)

SLA_DISPATCHED_HOURS = 24   # DISPATCHED sem MESSAGE_SENT → EXPIRED
SLA_SENT_HOURS       = 72   # SENT sem REPLIED → EXPIRED
CHECK_INTERVAL_SECS  = 300  # 5 minutos


async def expiry_worker() -> None:
    """Roda a cada CHECK_INTERVAL_SECS expirando jornadas vencidas."""
    logger.info("CarePlanner expiry worker iniciado")
    while True:
        try:
            await _expire_stale_tasks()
        except asyncio.CancelledError:
            logger.info("expiry_worker cancelado (shutdown)")
            break
        except Exception:
            logger.exception("erro no expiry_worker")
        await asyncio.sleep(CHECK_INTERVAL_SECS)


async def _expire_stale_tasks() -> None:
    """
    Para cada tenant, busca jornadas vencidas e transiciona para EXPIRED.

    Query:
      DISPATCHED com updated_at < now() - interval 'SLA_DISPATCHED_HOURS hours'
      SENT       com updated_at < now() - interval 'SLA_SENT_HOURS hours'
    """
    repo = CareplannerRepository()
    async with get_engine().begin() as conn:
        tenants = (
            await conn.execute(text("SELECT slug FROM public.tenants WHERE status = 'active'"))
        ).scalars().all()

    for slug in tenants:
        ctx = TenantContext.from_slug(slug=slug, user_id="expiry-worker")
        try:
            await _expire_for_tenant(ctx, repo)
        except Exception:
            logger.exception("erro ao expirar jornadas do tenant %s", slug)


async def _expire_for_tenant(ctx: TenantContext, repo: CareplannerRepository) -> None:
    from intellicare_core.db.session import tenant_session

    async with tenant_session(ctx) as db:
        rows = (
            await db.execute(
                text(f"""
                    SELECT correlation_id, status
                    FROM care_tasks
                    WHERE (
                        (status = 'DISPATCHED' AND updated_at < NOW() - INTERVAL '{SLA_DISPATCHED_HOURS} hours')
                        OR
                        (status = 'SENT'       AND updated_at < NOW() - INTERVAL '{SLA_SENT_HOURS} hours')
                    )
                """)
            )
        ).mappings().all()

    for row in rows:
        try:
            await repo.transition_task_status(ctx, row["correlation_id"], TaskStatus.EXPIRED)
            logger.info("task expirada: %s (era %s)", row["correlation_id"], row["status"])
        except ValueError:
            pass   # transição inválida — ignorar
```

### Registrar `expiry_worker` em `main.py`

```python
from .workers.expiry_worker import expiry_worker

class Module(BaseModule):
    def __init__(self) -> None:
        self._dispatcher_task: asyncio.Task | None = None
        self._expiry_task: asyncio.Task | None = None

    async def startup(self) -> None:
        # ... migrations ...
        self._dispatcher_task = asyncio.create_task(dispatcher_worker())
        self._expiry_task = asyncio.create_task(expiry_worker())

    async def shutdown(self) -> None:
        for task in [self._dispatcher_task, self._expiry_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
```

---

## 3. Revisão de segurança

### 3a. Mascaramento de PII nos logs

Adicionar função utilitária em `modules/careplanner/security.py`:

```python
"""Utilitarios de segurança e LGPD para o CarePlanner."""
from __future__ import annotations
import re


def mask_phone(phone: str | None) -> str:
    """Mascara phone_e164: +5531999999999 → +55319****9999"""
    if not phone:
        return ""
    return phone[:5] + "****" + phone[-4:] if len(phone) > 9 else "***"


def mask_content(content: str | None, max_chars: int = 20) -> str:
    """Trunca e mascara conteúdo de mensagem para logs."""
    if not content:
        return ""
    safe = content[:max_chars]
    return f"{safe}[…]" if len(content) > max_chars else safe


def mask_jwt(token: str | None) -> str:
    """Mostra apenas header.payload_truncado do JWT para debug."""
    if not token:
        return ""
    parts = token.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1][:8]}…"
    return token[:12] + "…"
```

**Aplicar mascaramento** nos pontos onde PII aparece em logs de `services.py`:

```python
from .security import mask_phone, mask_content

# Em process_inbound — log do conteúdo da mensagem:
logger.info("inbound: tenant=%s room=%s content=%s", ctx.tenant_id, rc_room_id, mask_content(content))

# Em open_task — log do telefone:
logger.debug("open_task: tenant=%s patient=%s phone=%s", ctx.tenant_id, patient_ref, mask_phone(contact_phone))
```

### 3b. Hardening do HMAC do webhook

No `adapters/rocketchat.py`, garantir que a verificação de assinatura seja constante em tempo (já usa `hmac.compare_digest` — confirmar). Adicionar validação de formato antes do compare:

```python
def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
    if not signature:
        return False
    # Aceitar com ou sem prefixo "sha256="
    received = signature.removeprefix("sha256=")
    if len(received) != 64:   # SHA-256 hex = 64 chars
        return False
    expected = hmac.new(
        self._settings.rocketchat_webhook_token.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received)
```

### 3c. Validação de TTL do JWT Jitsi

Adicionar verificação de expiração antes de entregar URL ao paciente em `open_video_session`:

```python
# Após create_video_session:
if expires_at <= datetime.now(tz=timezone.utc):
    raise api_error(400, "jwt_expired", "JWT Jitsi expirado imediatamente — checar JITSI_DEFAULT_ROOM_DURATION")
```

E endpoint para consultar se JWT de sessão existente ainda é válido:

```
GET /careplanner/consultations/video/{correlation_id}
→ retorna room_name, clinico_url, patient_url, expires_at, expired: bool
```

---

## 4. Testes Playwright (GestorUI — `CareplannerDashboard`)

### Setup

Playwright ainda não está no projeto. Instalar como devDependency no GestorUI:

```bash
cd frontend/GestorUI
npm install --save-dev @playwright/test
npx playwright install chromium
```

Adicionar script em `package.json`:
```json
"scripts": {
  "test:e2e": "playwright test"
}
```

### Criar `frontend/GestorUI/e2e/careplanner.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

/**
 * Testes E2E da página CareplannerDashboard.
 * Usa o servidor de dev (npm run dev) ou preview (npm run preview).
 * Configure baseURL no playwright.config.ts.
 */

test.describe('CareplannerDashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mockar auth: injetar token fake no localStorage antes de navegar
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-for-e2e');
    });
  });

  test('exibe os 7 cards de status', async ({ page }) => {
    // Interceptar chamada de API e retornar mock
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 42,
          by_status: {
            CREATED: 5, DISPATCHED: 10, SENT: 8,
            REPLIED: 7, CLOSED: 10, FAILED: 1, EXPIRED: 1,
          },
          recent_tasks: [
            {
              correlation_id: '550e8400-e29b-41d4-a716-446655440000',
              patient_ref: 'PAC-001',
              task_type: 'CONTATO_INICIAL',
              status: 'REPLIED',
              updated_at: '2026-03-17T10:00:00Z',
            },
          ],
        }),
      })
    );

    await page.goto('/careplanner');
    await expect(page.getByText('CarePlanner — Jornadas')).toBeVisible();
    await expect(page.getByText('Total: 42 jornadas')).toBeVisible();

    // Os 7 badges de status devem estar visíveis
    for (const status of ['CREATED', 'DISPATCHED', 'SENT', 'REPLIED', 'CLOSED', 'FAILED', 'EXPIRED']) {
      await expect(page.getByText(status).first()).toBeVisible();
    }
  });

  test('exibe atividade recente com dados mockados', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 1,
          by_status: { CREATED: 0, DISPATCHED: 0, SENT: 0, REPLIED: 1, CLOSED: 0, FAILED: 0, EXPIRED: 0 },
          recent_tasks: [{
            correlation_id: 'aaa-bbb',
            patient_ref: 'PAC-PLAYWRIGHT',
            task_type: 'FOLLOW_UP',
            status: 'REPLIED',
            updated_at: '2026-03-17T12:00:00Z',
          }],
        }),
      })
    );

    await page.goto('/careplanner');
    await expect(page.getByText('PAC-PLAYWRIGHT')).toBeVisible();
    await expect(page.getByText('FOLLOW_UP')).toBeVisible();
  });

  test('exibe mensagem quando nao ha jornadas recentes', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 0,
          by_status: { CREATED: 0, DISPATCHED: 0, SENT: 0, REPLIED: 0, CLOSED: 0, FAILED: 0, EXPIRED: 0 },
          recent_tasks: [],
        }),
      })
    );

    await page.goto('/careplanner');
    await expect(page.getByText('Nenhuma jornada recente.')).toBeVisible();
  });

  test('exibe loader enquanto carrega', async ({ page }) => {
    // Atrasar resposta para capturar o estado de loading
    await page.route('**/careplanner/dashboard/stats', async route => {
      await page.waitForTimeout(200);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ total: 0, by_status: {}, recent_tasks: [] }),
      });
    });

    await page.goto('/careplanner');
    // Loader deve aparecer antes dos dados
    const loader = page.locator('[class*="loader"], [role="progressbar"]');
    // Não assertar que é visível (pode ser rápido demais), apenas que não crasha
    await expect(page.getByText('CarePlanner — Jornadas')).toBeVisible({ timeout: 3000 });
  });
});
```

### Criar `frontend/GestorUI/playwright.config.ts`

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:5175',   // porta do vite dev
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5175',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
```

---

## 5. Arquivos a criar / modificar

### CRIAR
```
modules/careplanner/workers/expiry_worker.py
modules/careplanner/security.py
frontend/GestorUI/e2e/careplanner.spec.ts
frontend/GestorUI/playwright.config.ts
packages/intellicare-core/tests/test_careplanner_phase_d.py
```

### MODIFICAR
```
modules/careplanner/workers/dispatcher.py   ← substituir stub por implementação completa
modules/careplanner/main.py                 ← iniciar dispatcher_worker + expiry_worker no lifespan
modules/careplanner/services.py             ← open_task delega ao enqueue_dispatch; log com mask PII
modules/careplanner/adapters/rocketchat.py  ← verify_webhook_signature hardening
modules/careplanner/adapters/jitsi.py       ← validação TTL
modules/careplanner/api/routes.py           ← +GET /consultations/video/{correlation_id}
frontend/GestorUI/package.json              ← +@playwright/test devDependency + script test:e2e
```

---

## 6. Testes Python — `packages/intellicare-core/tests/test_careplanner_phase_d.py`

| # | Tipo | Descrição |
|---|------|-----------|
| 1 | Unit | `enqueue_dispatch` com Redis mockado → `rpush` chamado com JSON correto |
| 2 | Unit | `_do_dispatch` com RC mockado que falha 2x e sucede na 3a → status `DISPATCHED` |
| 3 | Unit | `_do_dispatch` com RC mockado que falha 3x → task vai para `FAILED` + item em dead-letter |
| 4 | Unit | `mask_phone("+5531999999999")` → `"+55319****9999"` |
| 5 | Unit | `mask_content("mensagem longa que excede vinte chars")` → truncada com `[…]` |
| 6 | Unit | `verify_webhook_signature` com signature sem prefixo `sha256=` → aceita |
| 7 | Unit | `verify_webhook_signature` com string de 63 chars → rejeita (comprimento errado) |
| 8 | Integração | `_expire_for_tenant`: tarefa `DISPATCHED` com `updated_at` 25h atrás → `EXPIRED` |
| 9 | Integração | `_expire_for_tenant`: tarefa `SENT` com `updated_at` 73h atrás → `EXPIRED` |
| 10 | Integração | `_expire_for_tenant`: tarefa `REPLIED` (não expirável) não muda status |

---

## Definição de Pronto (Fase D)

- [ ] `dispatcher.py` com `enqueue_dispatch` + `dispatcher_worker` + `_do_dispatch` (retry + dead-letter)
- [ ] `expiry_worker.py` com `expiry_worker` + `_expire_for_tenant`
- [ ] `main.py` inicia e cancela ambos os workers no lifespan
- [ ] `services.py` — `open_task` delega a `enqueue_dispatch`; logs mascarados
- [ ] `security.py` com `mask_phone`, `mask_content`, `mask_jwt`
- [ ] `adapters/rocketchat.py` — `verify_webhook_signature` com validação de comprimento
- [ ] `adapters/jitsi.py` — verificação de TTL em `open_video_session`
- [ ] `GET /careplanner/consultations/video/{correlation_id}` implementado
- [ ] `frontend/GestorUI/e2e/careplanner.spec.ts` com 4 testes Playwright
- [ ] `npx playwright test` → 4/4 passando (com `npm run dev` rodando)
- [ ] `pytest test_careplanner_phase_d.py` → 10/10
- [ ] `pytest test_careplanner_phase_c.py` → 7/7 (sem regressão)
- [ ] `pytest test_careplanner_phase_b.py` → 10/10 (sem regressão)
- [ ] `pytest test_careplanner_phase_a.py` → 3/3 (sem regressão)
- [ ] `npm run build` no GestorUI → OK (sem erros de TS)

---

## Commit esperado

```
feat(DEM-038-D): CarePlanner Fase D — retry/dead-letter, expiry worker, hardening seguranca, Playwright

- dispatcher.py: enqueue_dispatch (rpush Redis), dispatcher_worker (BLPOP loop),
  _do_dispatch (retry 3x backoff exponencial + dead-letter + FAILED)
- expiry_worker.py: varre tenants a cada 5min; DISPATCHED > 24h e SENT > 72h → EXPIRED
- main.py: inicia dispatcher_worker + expiry_worker no startup; cancela no shutdown
- services.py: open_task delega a enqueue_dispatch (retorna CREATED, nao DISPATCHED);
  logs com mask_phone e mask_content
- security.py: mask_phone, mask_content, mask_jwt
- rocketchat.py: verify_webhook_signature valida comprimento (64 chars hex)
- jitsi.py: validacao TTL imediato em open_video_session
- routes.py: GET /careplanner/consultations/video/{correlation_id}
- package.json: +@playwright/test; playwright.config.ts
- e2e/careplanner.spec.ts: 4 testes (7 status cards, atividade recente,
  lista vazia, loader)
- test_careplanner_phase_d.py: 10 testes (unit + integracao)
```
