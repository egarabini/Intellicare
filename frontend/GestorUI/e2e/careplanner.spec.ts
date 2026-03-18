import { test, expect } from '@playwright/test';

const AUTH_KEY = 'oidc.user:http://localhost:8080/realms/intellicare:gestor-ui';

async function mockAuth(page: Parameters<typeof test.beforeEach>[0]['page']) {
  await page.addInitScript(([key]) => {
    sessionStorage.setItem(
      key,
      JSON.stringify({
        access_token: 'fake-jwt-for-e2e',
        token_type: 'Bearer',
        profile: {
          email: 'gestor@teste.local',
          realm_access: { roles: ['TENANT_GESTOR'] },
        },
      }),
    );
  }, [AUTH_KEY]);
}

test.describe('CareplannerDashboard', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page);
  });

  test('exibe os 7 cards de status', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 42,
          by_status: {
            CREATED: 5,
            DISPATCHED: 10,
            SENT: 8,
            REPLIED: 7,
            CLOSED: 10,
            FAILED: 1,
            EXPIRED: 1,
          },
          recent_tasks: [
            {
              correlation_id: '550e8400-e29b-41d4-a716-446655440000',
              patient_ref: 'PAC-001',
              task_type: 'CONTATO_INICIAL',
              status: 'REPLIED',
              updated_at: '2026-03-17T10:00:00Z',
            },
          ],
        }),
      }),
    );

    await page.goto('/careplanner');
    await expect(page.getByText('CarePlanner — Jornadas')).toBeVisible();
    await expect(page.getByText('Total: 42 jornadas')).toBeVisible();
    for (const status of ['CREATED', 'DISPATCHED', 'SENT', 'REPLIED', 'CLOSED', 'FAILED', 'EXPIRED']) {
      await expect(page.getByText(status).first()).toBeVisible();
    }
  });

  test('exibe atividade recente com dados mockados', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 1,
          by_status: {
            CREATED: 0,
            DISPATCHED: 0,
            SENT: 0,
            REPLIED: 1,
            CLOSED: 0,
            FAILED: 0,
            EXPIRED: 0,
          },
          recent_tasks: [
            {
              correlation_id: 'aaa-bbb',
              patient_ref: 'PAC-PLAYWRIGHT',
              task_type: 'FOLLOW_UP',
              status: 'REPLIED',
              updated_at: '2026-03-17T12:00:00Z',
            },
          ],
        }),
      }),
    );

    await page.goto('/careplanner');
    await expect(page.getByText('PAC-PLAYWRIGHT')).toBeVisible();
    await expect(page.getByText('FOLLOW_UP')).toBeVisible();
  });

  test('exibe mensagem quando nao ha jornadas recentes', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 0,
          by_status: {
            CREATED: 0,
            DISPATCHED: 0,
            SENT: 0,
            REPLIED: 0,
            CLOSED: 0,
            FAILED: 0,
            EXPIRED: 0,
          },
          recent_tasks: [],
        }),
      }),
    );

    await page.goto('/careplanner');
    await expect(page.getByText('Nenhuma jornada recente.')).toBeVisible();
  });

  test('exibe loader enquanto carrega', async ({ page }) => {
    await page.route('**/careplanner/dashboard/stats', async route => {
      await page.waitForTimeout(200);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 0,
          by_status: {
            CREATED: 0,
            DISPATCHED: 0,
            SENT: 0,
            REPLIED: 0,
            CLOSED: 0,
            FAILED: 0,
            EXPIRED: 0,
          },
          recent_tasks: [],
        }),
      });
    });

    await page.goto('/careplanner');
    const loader = page.locator('[class*="loader"], [role="progressbar"]');
    await expect(loader.first()).toBeVisible();
    await expect(page.getByText('CarePlanner — Jornadas')).toBeVisible({ timeout: 3000 });
  });
});
