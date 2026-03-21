/**
 * DEM-063 — Florence: aba SOAP visível + botão sugerir.
 */
import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('Florence – aba Notas SOAP', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })
  })

  test('campos SOAP visíveis ao abrir aba Florence', async ({ page }) => {
    // Navega para Agenda → primeiro paciente → encounter
    await page.click('text=Agenda')
    await page.waitForURL(/\/agenda/)

    // Abre/retoma encounter do primeiro paciente da lista
    const atendeBtn = page.locator('[data-testid="btn-open-encounter"]').first()
      .or(page.locator('button:has-text("Atender")').first())
      .or(page.locator('button:has-text("Retomar")').first())
    await atendeBtn.click()

    // Aba Florence deve estar aberta por default
    await expect(page.locator('[data-testid="tab-florence"]')).toBeVisible({ timeout: 10_000 })
    await page.locator('[data-testid="tab-florence"]').click()

    // Campos SOAP devem existir
    await expect(page.locator('[data-testid="florence-soap-s"]')).toBeVisible({ timeout: 5_000 })
    await expect(page.locator('[data-testid="florence-soap-o"]')).toBeVisible()
    await expect(page.locator('[data-testid="florence-soap-a"]')).toBeVisible()
    await expect(page.locator('[data-testid="florence-soap-p"]')).toBeVisible()
  })

  test('botão Sugerir SOAP presente na aba Florence', async ({ page }) => {
    await page.click('text=Agenda')
    await page.waitForURL(/\/agenda/)

    const atendeBtn = page.locator('[data-testid="btn-open-encounter"]').first()
      .or(page.locator('button:has-text("Atender")').first())
      .or(page.locator('button:has-text("Retomar")').first())
    await atendeBtn.click()

    await page.locator('[data-testid="tab-florence"]').click()

    // Chief complaint + botão de sugestão
    await expect(page.locator('[data-testid="florence-chief-complaint"]')).toBeVisible({ timeout: 5_000 })
    await expect(page.locator('[data-testid="btn-suggest-soap"]')).toBeVisible()
  })
})
