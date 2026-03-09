import type {
  DiseaseCode,
  DiseaseDashboardData,
  KPIData,
  TrendSeries,
  StageDistribution,
  GeoRegion,
  PatientRecord,
} from '@/types/index';
import { getDiseaseByCode } from '@config/diseases';

// ─── Helpers ────────────────────────────────────────────────

function rand(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randFloat(min: number, max: number, decimals = 1): number {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

function randomDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - rand(0, daysAgo));
  return d.toISOString().split('T')[0];
}

const FIRST_NAMES = [
  'Maria', 'José', 'Ana', 'João', 'Francisca', 'Antonio', 'Adriana', 'Carlos',
  'Lúcia', 'Paulo', 'Juliana', 'Pedro', 'Fernanda', 'Lucas', 'Patrícia', 'Marcos',
  'Cláudia', 'Rafael', 'Sandra', 'Gabriel', 'Rosângela', 'Matheus', 'Vera', 'Renato',
];
const LAST_NAMES = [
  'Silva', 'Santos', 'Oliveira', 'Souza', 'Lima', 'Pereira', 'Costa', 'Ferreira',
  'Rodrigues', 'Almeida', 'Nascimento', 'Araújo', 'Ribeiro', 'Carvalho', 'Melo', 'Gomes',
];
const ESTABLISHMENTS = [
  'UBS Central', 'UBS Norte', 'UBS Sul', 'UPA Leste', 'Hospital Municipal',
  'CAPS II', 'Policlínica', 'UBS Vila Nova', 'UBS Jardim', 'CEO Regional',
];
const REGIONS: GeoRegion[] = [
  { id: 'centro', name: 'Centro', lat: -15.79, lng: -47.88, patientCount: 0, controlRate: 0, alertCount: 0 },
  { id: 'norte', name: 'Zona Norte', lat: -15.75, lng: -47.90, patientCount: 0, controlRate: 0, alertCount: 0 },
  { id: 'sul', name: 'Zona Sul', lat: -15.83, lng: -47.86, patientCount: 0, controlRate: 0, alertCount: 0 },
  { id: 'leste', name: 'Zona Leste', lat: -15.78, lng: -47.82, patientCount: 0, controlRate: 0, alertCount: 0 },
  { id: 'oeste', name: 'Zona Oeste', lat: -15.80, lng: -47.94, patientCount: 0, controlRate: 0, alertCount: 0 },
  { id: 'rural', name: 'Zona Rural', lat: -15.70, lng: -48.00, patientCount: 0, controlRate: 0, alertCount: 0 },
];

// ─── Disease-specific KPI generators ────────────────────────

function generateKPIs(disease: DiseaseCode): KPIData[] {
  const base: Record<DiseaseCode, KPIData[]> = {
    drc: [
      { label: 'Total de Pacientes', value: rand(1200, 3500), previousValue: rand(1100, 3400), format: 'number', trend: 'up', trendIsGood: false },
      { label: 'Taxa de Controle', value: randFloat(45, 72), previousValue: randFloat(42, 68), unit: '%', format: 'percent', trend: 'up', trendIsGood: true },
      { label: 'Em Diálise', value: rand(80, 250), previousValue: rand(85, 260), format: 'number', trend: 'down', trendIsGood: true },
      { label: 'TFG Média', value: randFloat(35, 65), unit: 'ml/min', format: 'number', trend: 'stable', trendIsGood: true },
      { label: 'Perda de Seguimento', value: rand(30, 120), previousValue: rand(35, 130), format: 'number', trend: 'down', trendIsGood: true, color: '#f59e0b' },
      { label: 'Alertas Ativos', value: rand(5, 45), format: 'number', trend: 'down', trendIsGood: true, color: '#ef4444' },
    ],
    diabetes: [
      { label: 'Total de Pacientes', value: rand(3000, 8000), previousValue: rand(2800, 7500), format: 'number', trend: 'up', trendIsGood: false },
      { label: 'HbA1c < 7%', value: randFloat(50, 68), previousValue: randFloat(48, 65), unit: '%', format: 'percent', trend: 'up', trendIsGood: true },
      { label: 'Com Complicações', value: rand(200, 800), previousValue: rand(210, 820), format: 'number', trend: 'down', trendIsGood: true },
      { label: 'HbA1c Média', value: randFloat(6.5, 8.5), unit: '%', format: 'number', trend: 'down', trendIsGood: true },
      { label: 'Perda de Seguimento', value: rand(50, 200), previousValue: rand(55, 220), format: 'number', trend: 'down', trendIsGood: true, color: '#f59e0b' },
      { label: 'Alertas Ativos', value: rand(10, 60), format: 'number', trend: 'down', trendIsGood: true, color: '#ef4444' },
    ],
    hipertensao: [
      { label: 'Total de Pacientes', value: rand(5000, 15000), previousValue: rand(4800, 14000), format: 'number', trend: 'up', trendIsGood: false },
      { label: 'PA Controlada', value: randFloat(40, 65), previousValue: randFloat(38, 62), unit: '%', format: 'percent', trend: 'up', trendIsGood: true },
      { label: 'Crise Hipertensiva', value: rand(20, 100), previousValue: rand(25, 110), format: 'number', trend: 'down', trendIsGood: true },
      { label: 'PAS Média', value: randFloat(128, 155), unit: 'mmHg', format: 'number', trend: 'down', trendIsGood: true },
      { label: 'Perda de Seguimento', value: rand(100, 500), previousValue: rand(120, 520), format: 'number', trend: 'down', trendIsGood: true, color: '#f59e0b' },
      { label: 'Alertas Ativos', value: rand(15, 80), format: 'number', trend: 'down', trendIsGood: true, color: '#ef4444' },
    ],
    cancer: [
      { label: 'Pacientes em Acompanhamento', value: rand(400, 1500), previousValue: rand(380, 1400), format: 'number', trend: 'up', trendIsGood: false },
      { label: 'Diagnóstico Precoce', value: randFloat(30, 55), previousValue: randFloat(28, 50), unit: '%', format: 'percent', trend: 'up', trendIsGood: true },
      { label: 'Em Remissão', value: rand(100, 400), previousValue: rand(90, 380), format: 'number', trend: 'up', trendIsGood: true },
      { label: 'Rastreamentos/mês', value: rand(200, 800), format: 'number', trend: 'up', trendIsGood: true },
      { label: 'Perda de Seguimento', value: rand(20, 80), previousValue: rand(25, 90), format: 'number', trend: 'down', trendIsGood: true, color: '#f59e0b' },
      { label: 'Alertas Ativos', value: rand(5, 30), format: 'number', trend: 'down', trendIsGood: true, color: '#ef4444' },
    ],
  };
  return base[disease];
}

// ─── Trend generator ────────────────────────────────────────

function generateTrends(disease: DiseaseCode, period: string): TrendSeries[] {
  const months = period === '30d' ? 4 : period === '90d' ? 6 : period === '6m' ? 6 : 12;
  const diseaseConfig = getDiseaseByCode(disease);
  const color = diseaseConfig?.color ?? '#3b82f6';

  const labels: Record<DiseaseCode, string[]> = {
    drc: ['Taxa de Controle (%)', 'TFG Média (ml/min)', 'Pacientes em Diálise'],
    diabetes: ['HbA1c < 7% (%)', 'HbA1c Média (%)', 'Com Complicações'],
    hipertensao: ['PA Controlada (%)', 'PAS Média (mmHg)', 'Crises Hipertensivas'],
    cancer: ['Diagnóstico Precoce (%)', 'Em Remissão', 'Rastreamentos/mês'],
  };

  return labels[disease].map((label, idx) => {
    const data = Array.from({ length: months }, (_, i) => {
      const d = new Date();
      d.setMonth(d.getMonth() - (months - 1 - i));
      return {
        date: d.toISOString().split('T')[0],
        value: randFloat(30, 80),
        target: idx === 0 ? 70 : undefined,
      };
    });
    const colors = [color, '#06b6d4', '#f97316'];
    return { id: `trend-${idx}`, label, color: colors[idx] ?? color, data };
  });
}

// ─── Stage distribution generator ───────────────────────────

function generateStageDistribution(disease: DiseaseCode): StageDistribution[] {
  const diseaseConfig = getDiseaseByCode(disease);
  if (!diseaseConfig?.stages) return [];

  const stageColors = ['#22c55e', '#84cc16', '#f59e0b', '#f97316', '#ef4444'];
  const total = rand(1000, 5000);
  let remaining = total;

  return diseaseConfig.stages.map((stage, idx) => {
    const isLast = idx === diseaseConfig.stages!.length - 1;
    const count = isLast ? remaining : rand(Math.floor(remaining * 0.1), Math.floor(remaining * 0.4));
    remaining -= count;
    return {
      stage: stage.id,
      label: stage.label,
      count,
      percentage: parseFloat(((count / total) * 100).toFixed(1)),
      color: stageColors[idx % stageColors.length],
    };
  });
}

// ─── Geo generator ──────────────────────────────────────────

function generateGeoData(): GeoRegion[] {
  return REGIONS.map((r) => ({
    ...r,
    patientCount: rand(50, 800),
    controlRate: randFloat(35, 75),
    alertCount: rand(0, 20),
  }));
}

// ─── Patient generator ──────────────────────────────────────

function generatePatients(disease: DiseaseCode, count: number): PatientRecord[] {
  const diseaseConfig = getDiseaseByCode(disease);
  const stages = diseaseConfig?.stages?.map((s) => s.id) ?? ['unknown'];
  const statuses: PatientRecord['status'][] = ['controlled', 'attention', 'critical', 'lost'];

  return Array.from({ length: count }, (_, i) => ({
    id: `PAT-${String(i + 1).padStart(5, '0')}`,
    name: `${FIRST_NAMES[rand(0, FIRST_NAMES.length - 1)]} ${LAST_NAMES[rand(0, LAST_NAMES.length - 1)]}`,
    cpf: String(rand(10000000000, 99999999999)),
    age: rand(35, 85),
    gender: Math.random() > 0.5 ? 'M' : 'F',
    disease,
    stage: stages[rand(0, stages.length - 1)],
    lastVisit: randomDate(90),
    nextVisit: Math.random() > 0.3 ? randomDate(-30) : undefined,
    status: statuses[rand(0, statuses.length - 1)],
    establishment: ESTABLISHMENTS[rand(0, ESTABLISHMENTS.length - 1)],
    indicators: [
      { name: 'Creatinina', value: randFloat(0.6, 8.0), unit: 'mg/dL', reference: '0.6-1.2', status: randFloat(0, 1) > 0.5 ? 'normal' : 'elevated' },
    ],
  }));
}

// ─── Main mock generator ────────────────────────────────────

export function generateMockDashboardData(
  disease: DiseaseCode,
  period: string,
): DiseaseDashboardData {
  const patients = generatePatients(disease, 20);
  return {
    disease,
    period,
    kpis: generateKPIs(disease),
    trends: generateTrends(disease, period),
    stageDistribution: generateStageDistribution(disease),
    geoData: generateGeoData(),
    patients,
    totalPatients: rand(500, 5000),
    totalPages: rand(25, 250),
  };
}
