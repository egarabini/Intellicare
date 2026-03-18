import { test, expect } from '@playwright/test';

const AUTH_KEY = 'oidc.user:http://localhost:8080/realms/intellicare:clinico-ui';

async function mockAuth(page: Parameters<typeof test.beforeEach>[0]['page']) {
  await page.addInitScript(([key]) => {
    sessionStorage.setItem(
      key,
      JSON.stringify({
        access_token: 'fake-token-clincio-123',
        profile: {
          sub: 'clinico-id-456',
          name: 'Dr. Teste',
          email: 'clinico@teste.local',
          tenant_slug: 'alfa',
          realm_access: { roles: ['CLINICO'] }
        },
      })
    );
  }, [AUTH_KEY]);
}

test.describe('CarePlanner no Clinico', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuth(page);
    await page.route('**/careplanner/tasks*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              correlation_id: 'corr-id-789',
              task_type: 'CHECK_IN',
              status: 'REPLIED',
              patient_ref: 'Paciente A',
              clinico_ref: 'clinico-id-456',
              created_at: '2026-03-18T10:00:00Z',
              updated_at: '2026-03-18T10:05:00Z',
            },
            {
              correlation_id: 'corr-id-000',
              task_type: 'FOLLOW_UP',
              status: 'CREATED',
              patient_ref: 'Paciente B',
              clinico_ref: 'outro-clinico-id',
              created_at: '2026-03-18T09:00:00Z',
              updated_at: null,
            }
          ],
          total: 2,
          page: 1
        })
      });
    });

    await page.route('**/careplanner/tasks/corr-id-789', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task: {
             correlation_id: 'corr-id-789', task_type: 'CHECK_IN', status: 'REPLIED',
             patient_ref: 'Paciente A', clinico_ref: 'clinico-id-456',
             created_at: '2026-03-18T10:00:00Z', updated_at: '2026-03-18T10:05:00Z'
          },
          conversation: { phone_e164: '+5511999999999' },
          events: [
            { id: 1, event_type: 'INBOUND_RECEIVED', recorded_at: '2026-03-18T10:05:00Z', payload: { content: 'Estou bem.' } }
          ]
        })
      });
    });

    await page.route('**/careplanner/consultations/video/corr-id-789', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ clinico_url: 'http://video.local', patient_url: 'http://video.local/p', expired: false })
      });
    });
  });

  test('Acessa a listagem de jornadas, exibe ambas e filtra por MINHAS JORNADAS', async ({ page }) => {
    await page.goto('/clinico-ui/');
    await page.getByText('Jornadas').click();
    
    await expect(page.getByText('Paciente A')).toBeVisible();
    await expect(page.getByText('Paciente B')).toBeVisible();

    await page.locator('label').filter({ hasText: 'Minhas Jornadas' }).click();

    await expect(page.getByText('Paciente A')).toBeVisible();
    await expect(page.getByText('Paciente B')).not.toBeVisible();
  });

  test('Detalhamento não possui botões de edição, exibe timeline e entra na videoconsulta', async ({ page }) => {
    await page.goto('/clinico-ui/');
    await page.getByText('Jornadas').click();
    await page.getByText('Paciente A').click();

    // Valida UI read-only e informações renderizadas
    await expect(page.getByText('Detalhe da Jornada')).toBeVisible();
    await expect(page.getByText('Paciente A')).toBeVisible();
    await expect(page.getByText('Estou bem.')).toBeVisible();

    await expect(page.getByTestId('btn-encerrar')).not.toBeVisible();
    await expect(page.getByTestId('btn-criar-video')).not.toBeVisible();

    const btnVideo = page.getByRole('link', { name: 'Entrar na Videoconsulta' });
    await expect(btnVideo).toBeVisible();
    expect(await btnVideo.getAttribute('href')).toBe('http://video.local');
  });
});
