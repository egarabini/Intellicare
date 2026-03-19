import { expect, test } from '@playwright/test';

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

async function openJourneyModal(page: Parameters<typeof test.beforeEach>[0]['page']) {
  await page.goto('/gestor-ui/');
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
  await page.route('**/careplanner/tasks*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], page: 1 }),
    }),
  );
  await page.route('**/careplanner/templates*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'tpl-rc',
            template_code: 'check_in',
            channel: 'rocketchat',
            content: 'Template RC',
            variables: [],
            active: true,
            tenant_slug: 'alfa',
            created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T00:00:00Z',
          },
          {
            id: 'tpl-wa',
            template_code: 'check_in_wa',
            channel: 'whatsapp',
            content: 'Template WA',
            variables: [],
            active: true,
            tenant_slug: 'alfa',
            created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T00:00:00Z',
          },
          {
            id: 'tpl-sms',
            template_code: 'check_in_sms',
            channel: 'sms',
            content: 'Template SMS',
            variables: [],
            active: true,
            tenant_slug: 'alfa',
            created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T00:00:00Z',
          },
        ],
      }),
    }),
  );

  await page.getByRole('link', { name: 'CarePlanner' }).click();
  await page.getByTestId('btn-nova-jornada').click();
}

test.describe('CarePlanner - seletor de canal', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page);
  });

  test('exibe Rocket.Chat, WhatsApp e SMS no seletor de canal', async ({ page }) => {
    await openJourneyModal(page);

    const options = await page.getByTestId('select-channel').locator('option').allTextContents();
    expect(options).toContain('Rocket.Chat Público');
    expect(options).toContain('WhatsApp via Evolution');
    expect(options).toContain('SMS via Jasmin');
  });

  test('ao selecionar WhatsApp, campo de telefone aparece', async ({ page }) => {
    await openJourneyModal(page);

    await page.getByTestId('select-channel').selectOption('whatsapp');
    await expect(page.getByLabel('Telefone (E.164)')).toBeVisible();
    await expect(page.getByTestId('select-template-code')).toBeVisible();
  });

  test('ao selecionar RocketChat, campo de telefone fica oculto', async ({ page }) => {
    await openJourneyModal(page);

    await page.getByTestId('select-channel').selectOption('rocketchat');
    await expect(page.getByLabel('Telefone (E.164)')).toHaveCount(0);
  });
});
