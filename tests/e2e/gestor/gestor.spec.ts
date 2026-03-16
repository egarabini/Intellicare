import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('GestorUI', () => {
  test('login e dashboard visível', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, USERS.gestor)

    // Header do Gestor carregado
    await expect(page.locator('text=IntelliCare — Gestor')).toBeVisible({ timeout: 10_000 })

    // Sidebar com itens de navegação
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Pacientes')).toBeVisible()
  })

  test('navegação completa entre seções', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, USERS.gestor)

    await expect(page.locator('text=IntelliCare — Gestor')).toBeVisible({ timeout: 10_000 })

    // Pacientes
    await page.click('text=Pacientes')
    await page.waitForURL(/\/patients/)

    // Agenda
    await page.click('text=Agenda')
    await page.waitForURL(/\/appointments/)

    // Faturamento
    await page.click('text=Faturamento')
    await page.waitForURL(/\/financeiro/)

    // Base de Conhecimento
    await page.click('text=Base de Conhecimento')
    await page.waitForURL(/\/rag/)

    // Configurações
    await page.click('text=Configurações')
    await page.waitForURL(/\/settings/)
  })

  test('logout redireciona para portal', async ({ page }) => {
    await page.goto('/gestor-ui/')
    await keycloakLogin(page, USERS.gestor)

    await expect(page.locator('text=IntelliCare — Gestor')).toBeVisible({ timeout: 10_000 })

    // Clicar em "Sair"
    await page.click('text=Sair')

    await page.waitForURL(
      url => url.pathname === '/' || url.hostname === 'localhost',
      { timeout: 15_000 }
    )
  })

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
})
