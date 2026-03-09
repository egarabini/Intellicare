// ─── Disease / Condition Types ──────────────────────────────

export type DiseaseCode = 'drc' | 'diabetes' | 'hipertensao' | 'cancer';

export interface DiseaseProgram {
  code: DiseaseCode;
  name: string;
  icdCodes: string[];
  color: string;
  icon: string;
  stages?: DiseaseStage[];
}

export interface DiseaseStage {
  id: string;
  label: string;
  description: string;
  severity: 'low' | 'moderate' | 'high' | 'critical';
}

// ─── KPI Types ──────────────────────────────────────────────

export interface KPIData {
  label: string;
  value: number;
  previousValue?: number;
  unit?: string;
  format?: 'number' | 'percent' | 'currency';
  trend?: 'up' | 'down' | 'stable';
  trendIsGood?: boolean;
  color?: string;
}

// ─── Trend / Time Series ────────────────────────────────────

export interface TrendPoint {
  date: string;
  value: number;
  target?: number;
}

export interface TrendSeries {
  id: string;
  label: string;
  color: string;
  data: TrendPoint[];
}

// ─── Stage Distribution ─────────────────────────────────────

export interface StageDistribution {
  stage: string;
  label: string;
  count: number;
  percentage: number;
  color: string;
}

// ─── Geographic Data ────────────────────────────────────────

export interface GeoRegion {
  id: string;
  name: string;
  lat: number;
  lng: number;
  patientCount: number;
  controlRate: number;
  alertCount: number;
}

// ─── Patient Table ──────────────────────────────────────────

export interface PatientRecord {
  id: string;
  name: string;
  cpf: string;
  age: number;
  gender: 'M' | 'F';
  disease: DiseaseCode;
  stage: string;
  lastVisit: string;
  nextVisit?: string;
  status: 'controlled' | 'attention' | 'critical' | 'lost';
  establishment: string;
  indicators: PatientIndicator[];
}

export interface PatientIndicator {
  name: string;
  value: number;
  unit: string;
  reference: string;
  status: 'normal' | 'elevated' | 'critical';
}

// ─── Dashboard Aggregate ────────────────────────────────────

export interface DiseaseDashboardData {
  disease: DiseaseCode;
  period: string;
  kpis: KPIData[];
  trends: TrendSeries[];
  stageDistribution: StageDistribution[];
  geoData: GeoRegion[];
  patients: PatientRecord[];
  totalPatients: number;
  totalPages: number;
}

// ─── Filters ────────────────────────────────────────────────

export interface DashboardFilters {
  disease: DiseaseCode;
  period: '30d' | '90d' | '6m' | '1y' | 'all';
  establishment?: string;
  region?: string;
  stage?: string;
  status?: string;
  search?: string;
  page: number;
  pageSize: number;
}

// ─── Auth ───────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  roles: string[];
  tenantId: string;
  tenantName: string;
}
