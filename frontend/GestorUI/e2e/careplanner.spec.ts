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

async function openCareplanner(page: Parameters<typeof test.beforeEach>[0]['page']) {
  await page.goto('/gestor-ui/');
  await page.getByRole('link', { name: 'CarePlanner' }).click();
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
          recent_tasks: [],
        }),
      }),
    );

    await openCareplanner(page);
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
          recent_tasks: [],
        }),
      }),
    );

    await page.route('**/careplanner/tasks*', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'uuid-activity',
              correlation_id: 'aaa-bbb',
              kestra_execution_id: 'exec-activity',
              patient_ref: 'PAC-PLAYWRIGHT',
              task_type: 'FOLLOW_UP',
              status: 'REPLIED',
              channel: 'rocketchat',
              metadata: {},
              created_at: '2026-03-17T11:00:00Z',
              updated_at: '2026-03-17T12:00:00Z',
            },
          ],
          page: 1,
        }),
      }),
    );

    await openCareplanner(page);
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

    await page.route('**/careplanner/tasks*', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          page: 1,
        }),
      }),
    );

    await openCareplanner(page);
    await expect(page.getByText('Nenhuma jornada encontrada.')).toBeVisible();
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

    await page.route('**/careplanner/tasks*', async route => {
      await page.waitForTimeout(200);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          page: 1,
        }),
      });
    });

    await openCareplanner(page);
    await expect(page.getByText('CarePlanner — Jornadas')).toBeVisible({ timeout: 3000 });
  });

  test('DEM040-01: lista de jornadas com filtro de status', async ({ page }) => {
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
          recent_tasks: [],
        }),
      }),
    );

    await page.route('**/careplanner/tasks*', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'uuid-1',
              correlation_id: 'corr-uuid-1',
              kestra_execution_id: 'exec-1',
              patient_ref: 'paciente.teste',
              task_type: 'CHECK_IN',
              status: 'REPLIED',
              channel: 'rocketchat',
              metadata: {},
              created_at: '2026-03-18T00:00:00Z',
              updated_at: '2026-03-18T01:00:00Z',
            },
          ],
          page: 1,
        }),
      }),
    );

    await openCareplanner(page);
    await page.getByTestId('select-status').click();
    await page.getByRole('option', { name: 'Respondidas' }).click();
    await expect(page.getByText('paciente.teste')).toBeVisible();
    await expect(page.getByText('CHECK_IN')).toBeVisible();
  });

  test('DEM040-02: detalhe da jornada com timeline de eventos', async ({ page }) => {
    const correlationId = 'corr-uuid-detalhe';

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
          recent_tasks: [],
        }),
      }),
    );

    await page.route('**/careplanner/tasks*', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'uuid-t',
              correlation_id: correlationId,
              kestra_execution_id: 'exec-k',
              patient_ref: 'paciente.detalhe',
              task_type: 'MONITORAMENTO',
              status: 'REPLIED',
              channel: 'rocketchat',
              metadata: {},
              created_at: '2026-03-18T00:00:00Z',
              updated_at: '2026-03-18T01:30:00Z',
            },
          ],
          page: 1,
        }),
      }),
    );

    await page.route(`**/careplanner/tasks/${correlationId}`, route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task: {
            id: 'uuid-t',
            correlation_id: correlationId,
            kestra_execution_id: 'exec-k',
            patient_ref: 'paciente.detalhe',
            task_type: 'MONITORAMENTO',
            status: 'REPLIED',
            channel: 'rocketchat',
            metadata: {},
            created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T01:30:00Z',
          },
          conversation: null,
          events: [
            {
              id: 'ev-1',
              event_id: 'evt-001',
              correlation_id: correlationId,
              event_type: 'MESSAGE_SENT',
              status: 'SENT',
              payload: {},
              recorded_at: '2026-03-18T00:05:00Z',
            },
            {
              id: 'ev-2',
              event_id: 'evt-002',
              correlation_id: correlationId,
              event_type: 'INBOUND_RECEIVED',
              status: 'REPLIED',
              payload: { content: 'Sim, estou tomando o remédio.' },
              recorded_at: '2026-03-18T01:30:00Z',
            },
          ],
        }),
      }),
    );

    await page.route(`**/careplanner/consultations/video/${correlationId}`, route =>
      route.fulfill({ status: 404 }),
    );

    await openCareplanner(page);
    await page.getByTestId(`row-${correlationId}`).click();
    await expect(page.getByTestId('badge-status')).toHaveText('REPLIED');
    await expect(page.getByTestId('event-timeline')).toBeVisible();
    await expect(page.getByTestId('event-content')).toContainText('Sim, estou tomando');
    await expect(page.getByTestId('btn-encerrar')).toBeVisible();
  });

  test('DEM040-03: modal Nova Jornada - submit com sucesso', async ({ page }) => {
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
        body: JSON.stringify({
          items: [],
          page: 1,
        }),
      }),
    );

    await page.route('**/careplanner/journeys/trigger', route =>
      route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          ok: true,
          execution_id: 'exec-novo-123',
          flow_id: 'careplanner_jornada_basica',
          status: 'CREATED',
        }),
      }),
    );

    await openCareplanner(page);
    await page.getByTestId('btn-nova-jornada').click();
    await page.getByTestId('input-patient-ref').fill('paciente-novo-ref');
    await page.getByTestId('select-task-type').selectOption('CHECK_IN');
    await page.getByTestId('btn-submit-trigger').click();
    await expect(page.getByText('Execution: exec-novo-123')).toBeVisible();
  });
});
