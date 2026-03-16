import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('ClinicoUI', () => {
  test('login e dashboard visível', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)

    // Shell do Clínico carregado — sidebar com navegação
    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Agenda')).toBeVisible()
    await expect(page.locator('text=Pacientes')).toBeVisible()
    await expect(page.locator('text=Assistente IA')).toBeVisible()
  })

  test('navegação entre seções', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)

    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    // Agenda
    await page.click('text=Agenda')
    await page.waitForURL(/\/agenda/)

    // Pacientes
    await page.click('text=Pacientes')
    await page.waitForURL(/\/patients/)

    // Assistente IA
    await page.click('text=Assistente IA')
    await page.waitForURL(/\/assistant/)

    // Meu Perfil
    await page.click('text=Meu Perfil')
    await page.waitForURL(/\/profile/)
  })

  test('logout redireciona para portal', async ({ page }) => {
    await page.goto('/clinico-ui/')
    await keycloakLogin(page, USERS.clinico)

    await expect(page.locator('text=Início')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Sair')

    await page.waitForURL(
      url => url.pathname === '/' || url.hostname === 'localhost',
      { timeout: 15_000 }
    )
  })

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
})
