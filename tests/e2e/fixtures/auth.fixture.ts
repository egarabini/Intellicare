import { Page } from '@playwright/test'

export interface Credentials {
  username: string
  password: string
}

/**
 * Realiza login via formulário Keycloak OIDC.
 *
 * Fluxo: SPA redireciona para Keycloak → preenche credenciais → submit
 * → Keycloak redireciona de volta para o frontend.
 */
export async function keycloakLogin(page: Page, creds: Credentials) {
  // Aguarda redirect para o formulário de login do Keycloak
  await page.waitForURL(
    url => url.hostname === 'localhost' && url.port === '8080',
    { timeout: 15_000 }
  )

  // Preenche formulário do Keycloak
  await page.fill('#username', creds.username)
  await page.fill('#password', creds.password)
  await page.click('#kc-login')

  // Aguarda retorno ao frontend (127.0.0.1:9000)
  await page.waitForURL(
    url => url.hostname === '127.0.0.1' && url.port === '9000',
    { timeout: 15_000 }
  )
}

/** Credenciais dos usuários de desenvolvimento */
export const USERS = {
  admin:    { username: 'platform-admin', password: 'Admin@2025!' },
  gestor:   { username: 'gestor-dev',     password: 'Gestor@2025!' },
  clinico:  { username: 'clinico-dev',    password: 'Clinico@2025!' },
  paciente: { username: 'paciente.alfa',  password: 'Demo@1234' },
} as const

