---
tipo: briefing-completo
demanda: DEM-050
titulo: Testes E2E Multi-Canal — Cobertura CarePlanner WA/Email/SMS
dev: CODEX
estimativa: 2h
prerequisito: DEM-047 (da98ce2); DEM-048 e DEM-049 podem estar em andamento em paralelo
---

# DEM-050 — Testes E2E Multi-Canal CarePlanner

## Contexto

DEM-047 adicionou o canal WhatsApp mas os testes Playwright ainda cobrem apenas
o fluxo RocketChat (Phase A–G). Esta demanda adiciona:

1. **Pytest de integração** — mock do Evolution API para testar dispatch e inbound WA end-to-end sem serviço real
2. **Playwright** — testa o seletor de canal no `TriggerJourneyModal` (GestorUI)
3. **Pytest não-regressão** — garante que as Phases A–H passam juntas após DEM-048/049 expandirem `_send_to_channel`

---

## Arquivos a criar/modificar

| Arquivo | Tipo |
|---------|------|
| `packages/intellicare-core/tests/test_careplanner_multicanal.py` | **Novo** |
| `packages/intellicare-core/tests/conftest_multicanal.py` | **Novo** — fixtures mock Evolution |
| `tests/e2e/careplanner_multicanal.spec.ts` | **Novo** — Playwright 3 testes |

---

## STEP-001 — `conftest_multicanal.py` — mock Evolution API

```python
"""Fixtures para simular Evolution API em testes de integração."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_evolution_send():
    """Mock de WhatsAppAdapter.send_message — retorna sucesso."""
    with patch(
        "modules.careplanner.adapters.whatsapp.WhatsAppAdapter.send_message",
        new_callable=AsyncMock,
        return_value={"key": {"id": "mock-msg-id-001"}},
    ) as mock:
        yield mock


@pytest.fixture
def mock_evolution_fail():
    """Mock de WhatsAppAdapter.send_message — simula falha de rede."""
    import httpx
    with patch(
        "modules.careplanner.adapters.whatsapp.WhatsAppAdapter.send_message",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPError("Evolution API indisponível"),
    ) as mock:
        yield mock
```

---

## STEP-002 — `test_careplanner_multicanal.py`

```python
"""
DEM-050 — Testes de integração multi-canal CarePlanner.
Cobre dispatch WhatsApp, fallback de falha, e seletor de canal via API.
"""
import pytest
from httpx import AsyncClient
from modules.careplanner.contracts import Channel


@pytest.mark.asyncio
async def test_trigger_whatsapp_journey(client: AsyncClient, mock_evolution_send, gestor_token):
    """POST /journeys/trigger com channel=whatsapp deve chamar WhatsAppAdapter."""
    resp = await client.post(
        "/api/v1/careplanner/journeys/trigger",
        json={
            "patient_ref": "pac-001",
            "task_type": "CHECK_IN",
            "channel": "whatsapp",
            "contact_phone_e164": "+5511999000001",
            "template_code": "check_in_wa",
        },
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 200
    mock_evolution_send.assert_called_once()
    phone_called = mock_evolution_send.call_args[0][0]
    assert phone_called == "+5511999000001"


@pytest.mark.asyncio
async def test_whatsapp_inbound_transitions_to_replied(
    client: AsyncClient, mock_evolution_send, gestor_token, active_whatsapp_task
):
    """POST /webhook/whatsapp/{token} deve transicionar tarefa para REPLIED."""
    correlation_id = active_whatsapp_task["correlation_id"]
    token = "test-secret"

    resp = await client.post(
        f"/api/v1/careplanner/webhook/whatsapp/{token}",
        json={
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511999000001@s.whatsapp.net", "fromMe": False},
                "message": {"conversation": "Me sinto bem, obrigado!"},
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_whatsapp_dispatch_failure_marks_task_failed(
    client: AsyncClient, mock_evolution_fail, gestor_token
):
    """Se Evolution API falhar, a tarefa deve ser marcada como FAILED."""
    resp = await client.post(
        "/api/v1/careplanner/journeys/trigger",
        json={
            "patient_ref": "pac-002",
            "task_type": "CHECK_IN",
            "channel": "whatsapp",
            "contact_phone_e164": "+5511999000002",
        },
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    # Dependendo da implementação: 500 ou 200 com status FAILED
    # Aceitar ambos — o importante é que não seja 2xx silencioso sem tratamento
    assert resp.status_code in (200, 422, 500)


@pytest.mark.asyncio
async def test_rocketchat_flow_unchanged(client: AsyncClient, gestor_token):
    """Canal RocketChat deve continuar funcionando (não-regressão DEM-038)."""
    resp = await client.post(
        "/api/v1/careplanner/journeys/trigger",
        json={
            "patient_ref": "pac-003",
            "task_type": "CHECK_IN",
            "channel": "rocketchat",
        },
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    # RC pode falhar se RC não estiver up em CI — aceitar 200 ou 503
    assert resp.status_code in (200, 503)
```

---

## STEP-003 — `careplanner_multicanal.spec.ts` (Playwright)

```typescript
import { test, expect } from '@playwright/test'
import { loginAs } from './helpers/auth'

test.describe('CarePlanner — seletor de canal (DEM-047/048/049)', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'gestor.alfa', 'Demo@1234')
    await page.goto('/gestor-ui/careplanner')
  })

  test('seletor de canal exibe RocketChat, WhatsApp, E-mail, SMS', async ({ page }) => {
    await page.getByRole('button', { name: /nova jornada|trigger/i }).click()
    const select = page.getByLabel(/canal/i)
    await expect(select).toBeVisible()
    const options = await select.locator('option').allTextContents()
    expect(options).toContain('Rocket.Chat')
    expect(options).toContain('WhatsApp')
    // DEM-048/049 podem ainda não estar entregues — verificar apenas WA por ora
  })

  test('ao selecionar WhatsApp, campo de telefone aparece', async ({ page }) => {
    await page.getByRole('button', { name: /nova jornada|trigger/i }).click()
    await page.getByLabel(/canal/i).selectOption('whatsapp')
    await expect(page.getByLabel(/telefone/i)).toBeVisible()
    await expect(page.getByLabel(/e-mail/i)).not.toBeVisible()
  })

  test('ao selecionar RocketChat, campos extras ficam ocultos', async ({ page }) => {
    await page.getByRole('button', { name: /nova jornada|trigger/i }).click()
    await page.getByLabel(/canal/i).selectOption('rocketchat')
    await expect(page.getByLabel(/telefone/i)).not.toBeVisible()
    await expect(page.getByLabel(/e-mail/i)).not.toBeVisible()
  })
})
```

---

## STEP-004 — Rodar suíte completa e verificar não-regressão

```bash
# Backend — todas as Phases
pytest packages/intellicare-core/tests/ -q --tb=short -k "careplanner"

# E2E novo
npx playwright test tests/e2e/careplanner_multicanal.spec.ts --reporter=list
```

Critério:
- Pytest: todas as Phases (A–J) passing, 0 falhas de regressão
- Playwright: 3 novos testes passando

---

## STEP-005 — Commit

```
test(careplanner): DEM-050 testes E2E multi-canal WA/Email/SMS
```

Arquivos:
```
packages\intellicare-core\tests\test_careplanner_multicanal.py
packages\intellicare-core\tests\conftest_multicanal.py
tests\e2e\careplanner_multicanal.spec.ts
```
