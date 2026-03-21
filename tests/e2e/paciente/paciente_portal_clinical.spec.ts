/**
 * DEM-063 — Portal Paciente: Jornadas + Histórico clínico (sem soap_a).
 */
import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('PacienteUI — Portal Clínico', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/paciente-ui/')
    await keycloakLogin(page, USERS.paciente)
    await expect(page.locator('text=IntelliCare — Paciente')).toBeVisible({ timeout: 10_000 })
  })

  test('página Minhas Jornadas carrega com data-testid', async ({ page }) => {
    await page.click('text=Minhas Jornadas')
    await page.waitForURL(/\/jornadas/)

    // Container principal renderizado
    await expect(page.locator('[data-testid="jornadas-page"]')).toBeVisible({ timeout: 5_000 })
    await expect(page.locator('text=Minhas Jornadas').first()).toBeVisible()
  })

  test('página Histórico carrega timeline sem dados SOAP', async ({ page }) => {
    await page.click('text=Histórico')
    await page.waitForURL(/\/historico/)

    // Container e timeline renderizados
    await expect(page.locator('[data-testid="historico-page"]')).toBeVisible({ timeout: 5_000 })
    await expect(page.locator('[data-testid="historico-timeline"]')).toBeVisible()

    // Garantir que nenhum campo SOAP é exposto na página do paciente
    const pageContent = await page.locator('[data-testid="historico-page"]').textContent()
    expect(pageContent).not.toContain('soap_a')
    expect(pageContent).not.toContain('soap_s')
  })
})
