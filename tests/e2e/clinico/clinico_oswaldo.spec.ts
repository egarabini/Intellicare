/**
 * DEM-063 — Oswaldo: aba Prescrição visível com campos e busca CID-10.
 */
import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('Oswaldo – aba Prescrição', () => {
  test('campos de prescrição e busca CID-10 visíveis', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    // Navega para Agenda → encounter
    await page.click('text=Agenda')
    await page.waitForURL(/\/agenda/)

    const atendeBtn = page.locator('[data-testid="btn-open-encounter"]').first()
      .or(page.locator('button:has-text("Atender")').first())
      .or(page.locator('button:has-text("Retomar")').first())
    await atendeBtn.click()

    // Troca para aba Oswaldo (Prescrição)
    await expect(page.locator('[data-testid="tab-oswaldo"]')).toBeVisible({ timeout: 10_000 })
    await page.locator('[data-testid="tab-oswaldo"]').click()

    // Busca CID-10
    await expect(page.locator('[data-testid="oswaldo-cid10-search"]')).toBeVisible({ timeout: 5_000 })

    // Campos de prescrição
    await expect(page.locator('[data-testid="oswaldo-drug"]')).toBeVisible()
    await expect(page.locator('[data-testid="oswaldo-posology"]')).toBeVisible()
    await expect(page.locator('[data-testid="oswaldo-duration"]')).toBeVisible()

    // Chief complaint
    await expect(page.locator('[data-testid="oswaldo-chief-complaint"]')).toBeVisible()
  })
})
