import { test, expect } from '@playwright/test'
import { keycloakLogin, USERS } from '../fixtures/auth.fixture'

test.describe('AdminUI', () => {
  test('login e dashboard visível', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)

    // Header do Admin carregado
    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    // Sidebar com itens de navegação
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Tenants')).toBeVisible()
    await expect(page.locator('text=Auditoria')).toBeVisible()
  })

  test('navegação para Tenants', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)

    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    // Navegar para Tenants
    await page.click('text=Tenants')
    await page.waitForURL(/\/tenants/)

    // Deve exibir lista ou conteúdo da página de tenants
    await expect(page.locator('text=Tenants').first()).toBeVisible()
  })

  test('navegação para Auditoria', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)

    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    await page.click('text=Auditoria')
    await page.waitForURL(/\/audit/)
  })

  test('logout redireciona para portal', async ({ page }) => {
    await page.goto('/admin-ui/')
    await keycloakLogin(page, USERS.admin)

    await expect(page.locator('text=IntelliCare Admin')).toBeVisible({ timeout: 10_000 })

    // Clicar em "Sair" na sidebar
    await page.click('text=Sair')

    // Deve redirecionar para Keycloak logout e depois para o portal
    await page.waitForURL(
      url => url.pathname === '/' || url.hostname === 'localhost',
      { timeout: 15_000 }
    )
  })
})

