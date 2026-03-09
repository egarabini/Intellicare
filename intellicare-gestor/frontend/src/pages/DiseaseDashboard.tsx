import { useParams, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { getDiseaseByCode } from '@config/diseases';
import { useDashboardStore } from '@store/dashboardStore';
import { useDiseaseData } from '@hooks/useDiseaseData';
import type { DiseaseCode } from '@/types/index';

import Header from '@components/layout/Header';
import Loading from '@components/common/Loading';
import {
  KPICard,
  TrendChart,
  StageDistribution,
  GeoMap,
  PatientTable,
  DiseaseSelector,
  PeriodSelector,
} from '@components/dashboard';

export default function DiseaseDashboard() {
  const { diseaseCode } = useParams<{ diseaseCode: string }>();
  const navigate = useNavigate();
  const { filters, setDisease, setPeriod, setPage, setSearch } = useDashboardStore();
  const { data, loading, refetch } = useDiseaseData();

  const disease = getDiseaseByCode(diseaseCode ?? '');

  // Sync URL param → store
  useEffect(() => {
    if (diseaseCode && diseaseCode !== filters.disease) {
      setDisease(diseaseCode as DiseaseCode);
    }
  }, [diseaseCode, filters.disease, setDisease]);

  // Redirect if invalid disease code
  useEffect(() => {
    if (diseaseCode && !disease) {
      navigate('/', { replace: true });
    }
  }, [diseaseCode, disease, navigate]);

  if (!disease) return null;

  return (
    <div>
      <Header
        title={disease.name}
        subtitle={`CID-10: ${disease.icdCodes.join(', ')} — Dashboard de indicadores e pacientes`}
        onRefresh={refetch}
      />

      {/* Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <DiseaseSelector
          selected={filters.disease}
          onChange={(code) => navigate(`/doenca/${code}`)}
        />
        <PeriodSelector selected={filters.period} onChange={setPeriod} />
      </div>

      {loading ? (
        <Loading message="Carregando indicadores..." />
      ) : data ? (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {data.kpis.map((kpi, idx) => (
              <KPICard key={idx} data={kpi} />
            ))}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TrendChart
              series={data.trends}
              title="Evolução Temporal"
            />
            <StageDistribution
              data={data.stageDistribution}
              title="Distribuição por Estágio"
            />
          </div>

          {/* Map */}
          <GeoMap
            data={data.geoData}
            title="Distribuição Geográfica"
          />

          {/* Patient Table */}
          <PatientTable
            patients={data.patients}
            totalPatients={data.totalPatients}
            totalPages={data.totalPages}
            currentPage={filters.page}
            onPageChange={setPage}
            onSearch={setSearch}
          />
        </div>
      ) : (
        <div className="text-center py-20 text-slate-400">
          <p className="text-lg">Nenhum dado disponível</p>
          <p className="text-sm mt-1">Verifique a conexão com o serviço Donabedian</p>
        </div>
      )}
    </div>
  );
}
