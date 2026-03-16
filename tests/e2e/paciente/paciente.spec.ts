import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('PacienteUI', () => {
  test('login e painel visível', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)

    // Header do Paciente carregado
    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })

    // Sidebar com itens de navegação
    await expect(page.locator('text=Painel')).toBeVisible()
    await expect(page.locator('text=Agenda')).toBeVisible()
    await expect(page.locator('text=Histórico')).toBeVisible()
    await expect(page.locator('text=Programas')).toBeVisible()
    await expect(page.locator('text=Meus Dados')).toBeVisible()
    await expect(page.locator('text=Contato')).toBeVisible()
  })

  test('navegação por todas as páginas', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)

    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })

    // Navegar por cada seção
    const sections = [
      { label: 'Agenda',    url: /\/agenda/ },
      { label: 'Histórico', url: /\/historico/ },
      { label: 'Programas', url: /\/programas/ },
      { label: 'Meus Dados', url: /\/cadastro/ },
      { label: 'Contato',   url: /\/contato/ },
    ]

    for (const section of sections) {
      await page.click(`text=${section.label}`)
      await page.waitForURL(section.url)
      // A seção carregou (label visível no sidebar)
      await expect(page.locator(`text=${section.label}`).first()).toBeVisible()
    }
  })

  test('logout redireciona para portal', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)

    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Sair')

    await page.waitForURL(
      url => url.pathname === '/' || url.hostname === 'localhost',
      { timeout: 15_000 }
    )
  })

  // DEM-035 — Sino de notificações
  test('sino de notificações visível no header (DEM-035)', async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)
    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })

    await expect(page.locator('[aria-label="Notificações"]')).toBeVisible()
  })
})
