import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

import App from '../../src/App';
import WhiteLabelLoginPage from '../../src/components/tenant/WhiteLabelLoginPage';

type JsonBody = Record<string, unknown> | Array<unknown>;

function jsonResponse(body: JsonBody, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function resolveUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}

function mockFetch(url: string): Response {
  const parsed = new URL(url, 'http://localhost');
  const path = parsed.pathname;

  if (path.endsWith('/api/v1/info')) {
    return jsonResponse({
      name: 'intellicare-module',
      version: '1.0.0',
      description: 'mock',
      capabilities: [],
    });
  }

  if (path.endsWith('/api/v1/health')) {
    return jsonResponse({ status: 'healthy', version: '1.0.0' });
  }

  if (path.includes('/api/v1/dashboard')) {
    return jsonResponse({
      period_start: '2026-02-01',
      period_end: '2026-02-24',
      overall_score: 84.4,
      total_pillars: 3,
      total_indicators: 9,
      total_measurements: 42,
      status_distribution: {
        green: 30,
        yellow: 8,
        red: 4,
        total: 42,
        green_percent: 71.4,
        yellow_percent: 19.0,
        red_percent: 9.6,
      },
      triad_summaries: [
        { dimension: 'estrutura', indicator_count: 3, measurement_count: 14, current_score: 86.0 },
        { dimension: 'processo', indicator_count: 3, measurement_count: 16, current_score: 82.0 },
        { dimension: 'resultado', indicator_count: 3, measurement_count: 12, current_score: 85.0 },
      ],
    });
  }

  if (path.includes('/api/v1/alerts/queue')) {
    return jsonResponse({
      total: 2,
      alerts: [{ id: 'a-1' }, { id: 'a-2' }],
    });
  }

  if (path.includes('/api/v1/Patient')) {
    const name = parsed.searchParams.get('name');
    if (name && name.toLowerCase().includes('maria')) {
      return jsonResponse({
        total: 1,
        entry: [
          {
            resource: {
              resourceType: 'Patient',
              id: 'p-1',
              name: [{ given: ['Maria'], family: 'Silva' }],
            },
          },
        ],
      });
    }
    return jsonResponse({
      total: 2,
      entry: [
        {
          resource: {
            resourceType: 'Patient',
            id: 'p-1',
            name: [{ given: ['Maria'], family: 'Silva' }],
          },
        },
        {
          resource: {
            resourceType: 'Patient',
            id: 'p-2',
            name: [{ given: ['Joao'], family: 'Souza' }],
          },
        },
      ],
    });
  }

  if (path.includes('/api/v1/Condition')) {
    return jsonResponse({
      total: 1,
      entry: [
        {
          resource: {
            resourceType: 'Condition',
            id: 'c-1',
            clinicalStatus: { text: 'active' },
          },
        },
      ],
    });
  }

  if (path.endsWith('/api/v1/plans') || path.includes('/api/v1/plans?')) {
    return jsonResponse({
      success: true,
      total: 1,
      data: [
        {
          id: 'plan-1',
          patient_id: 'demo-001',
          patient_name: 'Joao da Silva',
          goals: ['Controlar pressao'],
          conditions: ['Hipertensao'],
          status: 'active',
        },
      ],
    });
  }

  if (path.endsWith('/api/v1/plans/plan-1/tasks')) {
    return jsonResponse({
      success: true,
      total: 2,
      data: [
        {
          id: 'task-1',
          description: 'Tomar losartana 50mg',
          category: 'medication',
          status: 'pending',
          due_time: '08:00',
        },
        {
          id: 'task-2',
          description: 'Caminhar 30 minutos',
          category: 'exercise',
          status: 'pending',
          due_time: '18:00',
        },
      ],
    });
  }

  if (path.endsWith('/api/v1/adherence/plan-1')) {
    return jsonResponse({
      success: true,
      data: {
        completed_tasks: 7,
        pending_tasks: 3,
        adherence_rate: 70,
      },
    });
  }

  if (path.includes('/api/v1/establishments')) {
    return jsonResponse([
      {
        cnes_code: '1234567',
        legal_name: 'UBS Central de Curitiba',
        fantasy_name: 'UBS Central',
        unit_type_description: 'Unidade Basica',
        city_name: 'Curitiba',
        state_code: '41',
        city_code: '4106902',
        active: true,
      },
    ]);
  }

  if (path.includes('/api/v1/region-context/4106902')) {
    return jsonResponse({
      territorial_summary: {
        region_name: 'REGIAO METROPOLITANA',
        population: 1773718,
      },
      ibge: {
        idh: 0.823,
        pib_per_capita: 48500,
        densidade: 4325.1,
      },
      rnds: {
        vaccination_coverage: 91.2,
        last_update: '2026-02-20T10:00:00Z',
      },
    });
  }

  return jsonResponse({ error: `Unhandled URL in test: ${url}` }, 404);
}

function renderAppAt(route: string) {
  window.history.pushState({}, 'E2E Test', route);
  return render(<App />);
}

describe('Portal workflows (2.2.C)', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = resolveUrl(input);
        return mockFetch(url);
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('Login white-label dispara autenticacao', async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(
      <WhiteLabelLoginPage
        config={{
          tenantSlug: 'hospital-demo',
          displayName: 'Hospital Demo',
          primaryColor: '#1d4ed8',
          secondaryColor: '#0891b2',
          accentColor: '#22c55e',
          logoUrl: null,
          backgroundGradient: 'linear-gradient(135deg, #0f172a, #1e293b)',
          keycloakRealm: 'intellicare',
        }}
        onLogin={onLogin}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Entrar com SSO/i }));
    await waitFor(() => expect(onLogin).toHaveBeenCalledTimes(1));
  });

  it('Dashboard carrega com dados reais mockados', async () => {
    renderAppAt('/dashboards');

    expect(await screen.findByText(/Dashboards de Saude/i)).toBeInTheDocument();
    expect(await screen.findByText(/Pacientes Atendidos/i)).toBeInTheDocument();
    expect(await screen.findByText('2')).toBeInTheDocument();
    expect(await screen.findByText(/Taxa de Aderencia/i)).toBeInTheDocument();
  });

  it('Busca de paciente no Grahame abre recurso no visualizador', async () => {
    renderAppAt('/grahame');

    expect(await screen.findByText(/GRAHAME/i)).toBeInTheDocument();
    const searchInput = await screen.findByPlaceholderText(/Buscar por nome/i);
    fireEvent.change(searchInput, { target: { value: 'Maria' } });
    fireEvent.keyDown(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });

    const patientCard = await screen.findByText(/Maria Silva/i);
    fireEvent.click(patientCard);

    expect(await screen.findByText(/"resourceType": "Patient"/)).toBeInTheDocument();
  });

  it('Plano de cuidado da Geralda permite atualizar status visual da tarefa', async () => {
    renderAppAt('/geralda');

    const taskText = await screen.findByText(/Tomar losartana 50mg/i);
    expect(taskText).toBeInTheDocument();
    fireEvent.click(taskText);

    await waitFor(() => {
      expect(taskText.className).toContain('line-through');
    });
  });

  it('Busca CNES na Zilda retorna estabelecimento e contexto territorial', async () => {
    renderAppAt('/zilda');

    expect(await screen.findByText(/Consulta Unificada/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Pesquisar/i }));

    expect(await screen.findByText(/UBS Central/i)).toBeInTheDocument();
    expect(await screen.findByText(/Contexto Territorial/i)).toBeInTheDocument();
  });
});
