import type { DiseaseProgram } from '@/types/index';

/**
 * Disease program registry — 4 chronic disease programs for dashboards.
 * Each maps to ICD-10 codes and has color/icon/stage definitions.
 */
export const DISEASE_PROGRAMS: DiseaseProgram[] = [
  {
    code: 'drc',
    name: 'Doença Renal Crônica',
    icdCodes: ['N18', 'N18.1', 'N18.2', 'N18.3', 'N18.4', 'N18.5', 'N18.9'],
    color: '#8b5cf6',
    icon: 'Droplets',
    stages: [
      { id: 'G1', label: 'Estágio 1', description: 'TFG ≥ 90 ml/min', severity: 'low' },
      { id: 'G2', label: 'Estágio 2', description: 'TFG 60-89 ml/min', severity: 'low' },
      { id: 'G3a', label: 'Estágio 3a', description: 'TFG 45-59 ml/min', severity: 'moderate' },
      { id: 'G3b', label: 'Estágio 3b', description: 'TFG 30-44 ml/min', severity: 'moderate' },
      { id: 'G4', label: 'Estágio 4', description: 'TFG 15-29 ml/min', severity: 'high' },
      { id: 'G5', label: 'Estágio 5', description: 'TFG < 15 ml/min (diálise)', severity: 'critical' },
    ],
  },
  {
    code: 'diabetes',
    name: 'Diabetes Mellitus',
    icdCodes: ['E10', 'E11', 'E12', 'E13', 'E14'],
    color: '#f59e0b',
    icon: 'Activity',
    stages: [
      { id: 'pre', label: 'Pré-diabetes', description: 'HbA1c 5.7-6.4%', severity: 'low' },
      { id: 'controlled', label: 'Controlado', description: 'HbA1c < 7%', severity: 'low' },
      { id: 'moderate', label: 'Moderado', description: 'HbA1c 7-8.5%', severity: 'moderate' },
      { id: 'uncontrolled', label: 'Descompensado', description: 'HbA1c > 8.5%', severity: 'high' },
      { id: 'complications', label: 'Com Complicações', description: 'Nefropatia/Retinopatia/Neuropatia', severity: 'critical' },
    ],
  },
  {
    code: 'hipertensao',
    name: 'Hipertensão Arterial',
    icdCodes: ['I10', 'I11', 'I12', 'I13', 'I15'],
    color: '#ef4444',
    icon: 'HeartPulse',
    stages: [
      { id: 'elevated', label: 'PA Elevada', description: 'PAS 120-129 / PAD <80', severity: 'low' },
      { id: 'stage1', label: 'Estágio 1', description: 'PAS 130-139 / PAD 80-89', severity: 'moderate' },
      { id: 'stage2', label: 'Estágio 2', description: 'PAS ≥140 / PAD ≥90', severity: 'high' },
      { id: 'crisis', label: 'Crise Hipertensiva', description: 'PAS >180 / PAD >120', severity: 'critical' },
    ],
  },
  {
    code: 'cancer',
    name: 'Neoplasias',
    icdCodes: ['C00-C97', 'D00-D09'],
    color: '#ec4899',
    icon: 'Ribbon',
    stages: [
      { id: 'screening', label: 'Rastreamento', description: 'Pacientes em rastreamento ativo', severity: 'low' },
      { id: 'early', label: 'Estágio Inicial', description: 'TNM I-II', severity: 'moderate' },
      { id: 'advanced', label: 'Estágio Avançado', description: 'TNM III', severity: 'high' },
      { id: 'metastatic', label: 'Metastático', description: 'TNM IV', severity: 'critical' },
      { id: 'remission', label: 'Remissão', description: 'Sem evidência de doença', severity: 'low' },
    ],
  },
];

export const getDiseaseByCode = (code: string): DiseaseProgram | undefined =>
  DISEASE_PROGRAMS.find((d) => d.code === code);

export const SEVERITY_COLORS = {
  low: '#22c55e',
  moderate: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
} as const;

export const STATUS_LABELS = {
  controlled: 'Controlado',
  attention: 'Atenção',
  critical: 'Crítico',
  lost: 'Perda de Seguimento',
} as const;

export const STATUS_COLORS = {
  controlled: '#22c55e',
  attention: '#f59e0b',
  critical: '#ef4444',
  lost: '#94a3b8',
} as const;

export const PERIOD_OPTIONS = [
  { value: '30d', label: 'Últimos 30 dias' },
  { value: '90d', label: 'Últimos 90 dias' },
  { value: '6m', label: 'Últimos 6 meses' },
  { value: '1y', label: 'Último ano' },
  { value: 'all', label: 'Todo o período' },
] as const;
