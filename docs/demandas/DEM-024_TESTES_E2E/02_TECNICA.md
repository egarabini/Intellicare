# DEM-024 — Testes E2E: Especificação Técnica

## Stack

- **Playwright** `^1.44` — browser automation
- **TypeScript** — tipagem nos testes
- **@playwright/test** — runner nativo (sem Jest)
- Browsers: **Chromium** (obrigatório), Firefox (opcional)
- Localização: `tests/e2e/` (já existe o placeholder)

---

## Estrutura de arquivos

```
tests/e2e/
├── playwright.config.ts          # config global
├── fixtures/
│   └── auth.fixture.ts           # helper de login reutilizável
├── admin/
│   └── admin.spec.ts
├── gestor/
│   └── gestor.spec.ts
├── clinico/
│   └── clinico.spec.ts
└── paciente/
    └── paciente.spec.ts
```

---

## playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  retries: 1,
  reporter: [['html', { outputFolder: 'tests/e2e/report' }], ['list']],
  use: {
    baseURL: 'http://127.0.0.1:9000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
```

---

## fixtures/auth.fixture.ts

Encapsula o fluxo de login via Keycloak OIDC (redirect → formulário Keycloak → callback).

```typescript
import { Page } from '@playwright/test'

interface Credentials {
  username: string
  password: string
}

export async function keycloakLogin(page: Page, creds: Credentials) {
  // Aguarda redirect para Keycloak
  await page.waitForURL(/localhost:8080.*auth/, { timeout: 15_000 })
  await page.fill('#username', creds.username)
  await page.fill('#password', creds.password)
  await page.click('[type=submit]')
  // Aguarda retorno ao frontend
  await page.waitForURL(/127\.0\.0\.1:9000/, { timeout: 15_000 })
}
```

---

## admin/admin.spec.ts

```typescript
import { test, expect } from '@playwright/test'
import { keycloakLogin } from '../fixtures/auth.fixture'

const ADMIN = { username: 'platform-admin', password: 'Admin@2025!' }

test.describe('AdminUI', () => {
  test('login e dashboard com dados', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, ADMIN)
    // Dashboard carregado
    await expect(page.locator('text=Dashboard')).toBeVisible()
    // Verifica que há pelo menos uma métrica com valor numérico
    await expect(page.locator('[data-testid="metric-tenants"]')).not.toHaveText('0')
  })

  test('crud de tenants', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, ADMIN)
    await page.click('text=Tenants')
    await expect(page.locator('table')).toBeVisible()
    // Criar novo tenant
    await page.click('[data-testid="btn-new-tenant"]')
    await page.fill('[name=name]', 'Clínica Teste E2E')
    await page.fill('[name=slug]', 'clinica-e2e')
    await page.click('[type=submit]')
    await expect(page.locator('text=Clínica Teste E2E')).toBeVisible()
  })

  test('logout', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, ADMIN)
    await page.click('[data-testid="btn-logout"]')
    await expect(page).toHaveURL(/keycloak|login/)
  })
})
```

---

## gestor/gestor.spec.ts

```typescript
import { test, expect } from '@playwright/test'
import { keycloakLogin } from '../fixtures/auth.fixture'

const GESTOR = { username: 'gestor.alfa', password: 'Demo@1234' }

test.describe('GestorUI', () => {
  test('login e navegação completa', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, GESTOR)
    await expect(page.locator('text=Dashboard')).toBeVisible()

    // Pacientes
    await page.click('text=Pacientes')
    await expect(page.locator('table')).toBeVisible()

    // Documentos
    await page.click('text=Documentos')
    await expect(page.locator('text=Documentos')).toBeVisible()

    // Relatórios
    await page.click('text=Relatórios')
    await expect(page.locator('text=Uso')).toBeVisible()
  })
})
```

---

## clinico/clinico.spec.ts

```typescript
import { test, expect } from '@playwright/test'
import { keycloakLogin } from '../fixtures/auth.fixture'

const CLINICO = { username: 'dr.silva', password: 'Demo@1234' }

test.describe('ClinicoUI', () => {
  test('login e dashboard com agenda', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, CLINICO)
    await expect(page.locator('text=Dashboard')).toBeVisible()
    // Verifica seção de agenda
    await expect(page.locator('[data-testid="agenda-hoje"]')).toBeVisible()
  })

  test('prontuário de paciente', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, CLINICO)
    await page.click('text=Pacientes')
    // Clica no primeiro paciente da lista
    await page.locator('table tbody tr').first().click()
    await expect(page.locator('[data-testid="patient-name"]')).toBeVisible()
    // Aba de encontros
    await page.click('text=Encontros')
    await expect(page.locator('table')).toBeVisible()
  })

  test('AI Assistant acessível', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, CLINICO)
    await page.click('text=AI Assistant')
    await expect(page.locator('textarea, input[type=text]')).toBeVisible()
  })
})
```

---

## paciente/paciente.spec.ts

```typescript
import { test, expect } from '@playwright/test'
import { keycloakLogin } from '../fixtures/auth.fixture'

const PACIENTE = { username: 'paciente.alfa', password: 'Demo@1234' }

test.describe('PacienteUI', () => {
  test('login e todas as páginas acessíveis', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, PACIENTE)
    await expect(page.locator('text=Painel')).toBeVisible()

    const paginas = ['Agenda', 'Histórico', 'Programas', 'Cadastro', 'Contato']
    for (const p of paginas) {
      await page.click(`text=${p}`)
      await expect(page.locator(`text=${p}`).first()).toBeVisible()
    }
  })
})
```

---

## package.json (raiz do projeto)

Adicionar scripts:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:report": "playwright show-report tests/e2e/report"
  },
  "devDependencies": {
    "@playwright/test": "^1.44.0",
    "typescript": "^5.4.0"
  }
}
```

---

## Instalação e execução

```bash
# Instalar Playwright e browsers
npm install --save-dev @playwright/test
npx playwright install chromium

# Garantir que o ambiente está rodando
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d

# Rodar testes
npx playwright test

# Ver relatório HTML
npx playwright show-report tests/e2e/report
```

---

## data-testid necessários nos frontends

O dev de E2E deve coordenar com os devs de frontend para adicionar os seguintes atributos onde ainda não existem:

| Componente | data-testid |
|-----------|-------------|
| AdminUI — botão novo tenant | `btn-new-tenant` |
| AdminUI — métrica de tenants | `metric-tenants` |
| AdminUI/GestorUI/Clínico/Paciente — botão logout | `btn-logout` |
| ClinicoUI — seção agenda do dashboard | `agenda-hoje` |
| ClinicoUI — nome do paciente no perfil | `patient-name` |

---

## Observações

- **Keycloak deve estar healthy** antes dos testes (healthcheck do docker-compose garante isso)
- Os `data-testid` devem ser adicionados pelos devs de frontend como parte desta demanda
- Se o ambiente local não estiver disponível, usar `BASE_URL` env var: `BASE_URL=http://staging.intellicare.ia.br npx playwright test`
- Testes de criação de dados (ex: criar tenant) podem deixar resíduos — considerar cleanup em `afterEach` nas próximas iterações
