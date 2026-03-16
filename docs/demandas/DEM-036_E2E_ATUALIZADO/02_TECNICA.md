# DEM-036 — E2E Atualizado — Especificação Técnica

## 1. Estrutura de arquivos

```
tests/
└── e2e/
    ├── conftest.py                        # já existe — adicionar fixture clinico_headers
    ├── test_health.py                     # já existe — não modificar
    ├── test_auth.py                       # já existe — não modificar
    ├── test_isolation.py                  # já existe — não modificar
    ├── test_rag.py                        # já existe — não modificar
    ├── test_tenant_flow.py                # já existe — não modificar
    ├── test_notifications_e2e.py          # NOVO — cobertura DEM-026
    ├── test_reports_e2e.py                # NOVO — cobertura DEM-027
    ├── test_grafana_e2e.py                # NOVO — cobertura DEM-028
    ├── test_appointments_e2e.py           # NOVO — cobertura DEM-029
    ├── admin/
    │   └── admin.spec.ts                  # modificar — adicionar testes DEM-030 + DEM-035
    ├── clinico/
    │   └── clinico.spec.ts                # modificar — adicionar testes DEM-032 + DEM-035
    ├── gestor/
    │   └── gestor.spec.ts                 # modificar — adicionar testes DEM-027 + DEM-035
    └── paciente/
        └── paciente.spec.ts               # modificar — adicionar teste DEM-035
```

---

## 2. Alteração em `tests/e2e/conftest.py`

Adicionar fixture `clinico_headers` (necessária para os novos testes de relatórios):

```python
# Adicionar ao conftest.py existente — NÃO remover nada

@pytest.fixture(scope="session")
def clinico_headers() -> dict[str, str]:
    """Token do clinico-dev (tenant_dev)."""
    return auth_headers(get_token("clinico-dev", "Clinico@2025!"))
```

---

## 3. Novo arquivo: `tests/e2e/test_notifications_e2e.py`

```python
"""E2E — DEM-026: Módulo de Notificações."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e


def test_create_notification(api: httpx.Client, gestor_headers: dict):
    """POST /notifications/ cria notificação e retorna 201."""
    resp = api.post(
        "/notifications/",
        json={
            "title": "Teste E2E",
            "message": "Notificação criada pelo teste E2E",
            "category": "info",
        },
        headers=gestor_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["is_read"] is False
    return data["id"]


def test_list_notifications(api: httpx.Client, gestor_headers: dict):
    """GET /notifications/ retorna lista (200)."""
    resp = api.get("/notifications/?limit=10", headers=gestor_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_mark_notification_read(api: httpx.Client, gestor_headers: dict):
    """Ciclo completo: criar → marcar como lida → confirmar is_read=true."""
    # Criar
    create_resp = api.post(
        "/notifications/",
        json={"title": "Para marcar", "message": "Marcar como lida", "category": "info"},
        headers=gestor_headers,
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    # Marcar como lida
    read_resp = api.patch(f"/notifications/{notif_id}/read", headers=gestor_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True


def test_delete_notification(api: httpx.Client, gestor_headers: dict):
    """Criar e deletar notificação retorna 204."""
    create_resp = api.post(
        "/notifications/",
        json={"title": "Para deletar", "message": "Deletar", "category": "info"},
        headers=gestor_headers,
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    del_resp = api.delete(f"/notifications/{notif_id}", headers=gestor_headers)
    assert del_resp.status_code == 204


def test_notifications_stream_header(api: httpx.Client, gestor_headers: dict):
    """GET /notifications/stream retorna Content-Type: text/event-stream."""
    token = gestor_headers["Authorization"].split(" ")[1]
    # Abre conexão SSE mas fecha imediatamente — só verifica o header
    with api.stream("GET", f"/notifications/stream?token={token}") as resp:
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/event-stream" in content_type
```

---

## 4. Novo arquivo: `tests/e2e/test_reports_e2e.py`

```python
"""E2E — DEM-027: Endpoints de Relatórios PDF."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e


def test_admin_report_tenants_returns_pdf(api: httpx.Client, admin_headers: dict):
    """GET /reports/admin/tenants retorna application/pdf."""
    resp = api.get("/reports/admin/tenants", headers=admin_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    # PDF começa com o magic bytes %PDF
    assert resp.content[:4] == b"%PDF"


def test_gestor_report_appointments_returns_pdf(api: httpx.Client, gestor_headers: dict):
    """GET /reports/gestor/appointments retorna application/pdf."""
    resp = api.get("/reports/gestor/appointments", headers=gestor_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content[:4] == b"%PDF"


def test_clinico_report_patients_returns_pdf(api: httpx.Client, clinico_headers: dict):
    """GET /reports/clinico/patients retorna application/pdf."""
    resp = api.get("/reports/clinico/patients", headers=clinico_headers)
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content[:4] == b"%PDF"


def test_report_unauthenticated_returns_401(api: httpx.Client):
    """GET /reports/admin/tenants sem token retorna 401."""
    resp = api.get("/reports/admin/tenants")
    assert resp.status_code == 401


def test_report_wrong_role_returns_403(api: httpx.Client, gestor_headers: dict):
    """GET /reports/admin/tenants com token de gestor retorna 403."""
    resp = api.get("/reports/admin/tenants", headers=gestor_headers)
    assert resp.status_code == 403
```

---

## 5. Novo arquivo: `tests/e2e/test_grafana_e2e.py`

```python
"""E2E — DEM-028: Grafana Alert Rules."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"  # GF_SECURITY_ADMIN_PASSWORD padrão local


def test_grafana_alert_rules_count():
    """Grafana deve ter pelo menos 9 regras de alerta provisionadas."""
    resp = httpx.get(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        timeout=10,
    )
    assert resp.status_code == 200
    rules = resp.json()
    assert isinstance(rules, list)
    assert len(rules) >= 9, f"Esperado ≥ 9 regras, encontrado {len(rules)}"


def test_grafana_alert_rules_uids():
    """Verificar que os UIDs esperados estão presentes."""
    resp = httpx.get(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        timeout=10,
    )
    assert resp.status_code == 200
    rules = resp.json()
    uids = {r["uid"] for r in rules}
    expected_uids = {
        "alt-i01", "alt-i02", "alt-i03", "alt-i04",
        "alt-i05", "alt-i06", "alt-a01", "alt-a02", "alt-a03",
    }
    missing = expected_uids - uids
    assert not missing, f"UIDs ausentes: {missing}"
```

---

## 6. Novo arquivo: `tests/e2e/test_appointments_e2e.py`

```python
"""E2E — DEM-029: Robustez do módulo de agendamento."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e

FAKE_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture(scope="module")
def paciente_headers() -> dict[str, str]:
    """Token do paciente.alfa (tenant_alfa)."""
    from .conftest import get_token, auth_headers
    return auth_headers(get_token("paciente.alfa", "Demo@1234"))


def test_confirm_nonexistent_appointment_returns_404(
    api: httpx.Client, paciente_headers: dict
):
    """PATCH confirm em appointment inexistente deve retornar 404."""
    resp = api.patch(
        f"/cuidado/appointments/{FAKE_UUID}/confirm",
        headers=paciente_headers,
    )
    assert resp.status_code == 404


def test_cancel_nonexistent_appointment_returns_404(
    api: httpx.Client, paciente_headers: dict
):
    """PATCH cancel em appointment inexistente deve retornar 404."""
    resp = api.patch(
        f"/cuidado/appointments/{FAKE_UUID}/cancel",
        headers=paciente_headers,
    )
    assert resp.status_code == 404
```

---

## 7. Modificação em `tests/e2e/admin/admin.spec.ts`

Adicionar ao final do `test.describe('AdminUI', ...)` existente (não substituir — apenas acrescentar):

```typescript
  // DEM-030 — Páginas novas de administração
  test('navegação para Servidores (DEM-030)', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)
    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Servidores')
    await page.waitForURL(/\/servers/)
    await expect(page.locator('text=Servidores').first()).toBeVisible()
  })

  test('navegação para Módulos (DEM-030)', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)
    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Modulos')
    await page.waitForURL(/\/modules/)
    await expect(page.locator('text=Modulos').first()).toBeVisible()
  })

  test('navegação para Financeiro (DEM-030)', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)
    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Financeiro')
    await page.waitForURL(/\/financeiro/)
    await expect(page.locator('text=Financeiro').first()).toBeVisible()
  })

  // DEM-035 — Sino de notificações
  test('sino de notificações visível no header (DEM-035)', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)
    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    // NotificationBell renderiza ActionIcon com aria-label="Notificações"
    await expect(page.locator('[aria-label="Notificações"]')).toBeVisible()
  })
```

---

## 8. Modificação em `tests/e2e/clinico/clinico.spec.ts`

Adicionar ao final do `test.describe('ClinicoUI', ...)` existente:

```typescript
  // DEM-032 — Gestão clínica (grupos, profissionais, equipe)
  test('navegação para Grupos (DEM-032)', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Grupos')
    await page.waitForURL(/\/groups/)
    await expect(page.locator('text=Grupos').first()).toBeVisible()
  })

  test('navegação para Profissionais (DEM-032)', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Profissionais')
    await page.waitForURL(/\/professionals/)
    await expect(page.locator('text=Profissionais').first()).toBeVisible()
  })

  test('navegação para Equipe (DEM-032)', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Equipe')
    await page.waitForURL(/\/clinical-users/)
    await expect(page.locator('text=Equipe').first()).toBeVisible()
  })

  // DEM-035 — Sino de notificações
  test('sino de notificações visível no header (DEM-035)', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    await expect(page.locator('[aria-label="Notificações"]')).toBeVisible()
  })
```

---

## 9. Modificação em `tests/e2e/gestor/gestor.spec.ts`

Adicionar ao final do `test.describe('GestorUI', ...)` existente:

```typescript
  // DEM-027 — Página de Relatórios
  test('navegação para Relatórios (DEM-027)', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, USERS.gestor)
    await expect(page.locator('text=IntelliCare — Gestor')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Relatórios')
    await page.waitForURL(/\/relatorios/)
    await expect(page.locator('text=Relatórios').first()).toBeVisible()
  })

  // DEM-035 — Sino de notificações
  test('sino de notificações visível no header (DEM-035)', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, USERS.gestor)
    await expect(page.locator('text=IntelliCare — Gestor')).toBeVisible({ timeout: 10_000 })

    await expect(page.locator('[aria-label="Notificações"]')).toBeVisible()
  })
```

---

## 10. Modificação em `tests/e2e/paciente/paciente.spec.ts`

Adicionar ao final do `test.describe('PacienteUI', ...)` existente:

```typescript
  // DEM-035 — Sino de notificações
  test('sino de notificações visível no header (DEM-035)', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)
    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })

    await expect(page.locator('[aria-label="Notificações"]')).toBeVisible()
  })
```

---

## 11. Contagem final de testes

### Pytest E2E

| Arquivo | Testes |
|---------|--------|
| `test_health.py` | 3 (existente) |
| `test_auth.py` | ~2 (existente) |
| `test_isolation.py` | ~1 (existente) |
| `test_rag.py` | ~1 (existente) |
| `test_tenant_flow.py` | ~1 (existente) |
| `test_notifications_e2e.py` | 5 (novo) |
| `test_reports_e2e.py` | 5 (novo) |
| `test_grafana_e2e.py` | 2 (novo) |
| `test_appointments_e2e.py` | 2 (novo) |
| **Total** | **≥ 22** |

### Playwright E2E

| Arquivo | Antes | Novos | Total |
|---------|-------|-------|-------|
| `admin.spec.ts` | 4 | 4 | 8 |
| `clinico.spec.ts` | 3 | 4 | 7 |
| `gestor.spec.ts` | 3 | 2 | 5 |
| `paciente.spec.ts` | 3 | 1 | 4 |
| **Total** | **13** | **11** | **24** |

---

## 12. Execução

```bash
# Pytest E2E (requer ambiente rodando)
cd packages/intellicare-core
pytest tests/e2e/ -m e2e -q --tb=short

# Playwright (requer ambiente rodando)
npx playwright test --workers=4
```

---

## 13. Checklist de entrega

- [ ] `tests/e2e/conftest.py`: fixture `clinico_headers` adicionada
- [ ] `tests/e2e/test_notifications_e2e.py`: 5 testes criados
- [ ] `tests/e2e/test_reports_e2e.py`: 5 testes criados
- [ ] `tests/e2e/test_grafana_e2e.py`: 2 testes criados
- [ ] `tests/e2e/test_appointments_e2e.py`: 2 testes criados
- [ ] `tests/e2e/admin/admin.spec.ts`: 4 testes adicionados (Servidores, Módulos, Financeiro, Sino)
- [ ] `tests/e2e/clinico/clinico.spec.ts`: 4 testes adicionados (Grupos, Profissionais, Equipe, Sino)
- [ ] `tests/e2e/gestor/gestor.spec.ts`: 2 testes adicionados (Relatórios, Sino)
- [ ] `tests/e2e/paciente/paciente.spec.ts`: 1 teste adicionado (Sino)
- [ ] `pytest tests/e2e/ -m e2e -q` → todos passam (dependência: DEM-035 já implementada)
- [ ] `npx playwright test --workers=4` → 24/24 passando em < 3 min
- [ ] Nenhum teste existente regrediu
