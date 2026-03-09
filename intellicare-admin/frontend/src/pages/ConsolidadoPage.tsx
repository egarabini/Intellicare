import { Globe, TrendingUp, AlertTriangle, Users } from 'lucide-react';
import Header from '@components/layout/Header';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const CONSOLIDATED_DATA = [
  { tenant: 'Brasília', drc: 1240, diabetes: 3200, hipertensao: 5800, cancer: 420 },
  { tenant: 'Montes Claros', drc: 620, diabetes: 1500, hipertensao: 2900, cancer: 180 },
  { tenant: 'São Paulo', drc: 4580, diabetes: 12000, hipertensao: 22000, cancer: 1800 },
  { tenant: 'Rio de Janeiro', drc: 3820, diabetes: 9500, hipertensao: 18000, cancer: 1400 },
  { tenant: 'Belo Horizonte', drc: 2210, diabetes: 5500, hipertensao: 10000, cancer: 750 },
];

const DISEASE_COLORS = {
  drc: '#8b5cf6',
  diabetes: '#f59e0b',
  hipertensao: '#ef4444',
  cancer: '#ec4899',
};

export default function ConsolidadoPage() {
  const totals = CONSOLIDATED_DATA.reduce(
    (acc, row) => ({
      drc: acc.drc + row.drc,
      diabetes: acc.diabetes + row.diabetes,
      hipertensao: acc.hipertensao + row.hipertensao,
      cancer: acc.cancer + row.cancer,
    }),
    { drc: 0, diabetes: 0, hipertensao: 0, cancer: 0 },
  );

  const grandTotal = totals.drc + totals.diabetes + totals.hipertensao + totals.cancer;

  return (
    <div>
      <Header
        title="Consolidado Nacional"
        subtitle="Dados agregados de todos os tenants — visão estratégica"
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Users className="h-4 w-4 text-primary-500" />
            <span className="text-xs text-slate-500">Total Geral</span>
          </div>
          <p className="text-2xl font-bold text-slate-800">{grandTotal.toLocaleString('pt-BR')}</p>
        </div>
        {[
          { label: 'DRC', value: totals.drc, color: DISEASE_COLORS.drc },
          { label: 'Diabetes', value: totals.diabetes, color: DISEASE_COLORS.diabetes },
          { label: 'Hipertensão', value: totals.hipertensao, color: DISEASE_COLORS.hipertensao },
        ].map((item) => (
          <div key={item.label} className="p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-xs text-slate-500">{item.label}</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: item.color }}>
              {item.value.toLocaleString('pt-BR')}
            </p>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 mb-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">
          Distribuição por Secretaria e Programa
        </h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={CONSOLIDATED_DATA} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="tenant" tick={{ fontSize: 12, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
              formatter={(value: unknown) => Number(value).toLocaleString('pt-BR')}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="drc" name="DRC" fill={DISEASE_COLORS.drc} radius={[4, 4, 0, 0]} />
            <Bar dataKey="diabetes" name="Diabetes" fill={DISEASE_COLORS.diabetes} radius={[4, 4, 0, 0]} />
            <Bar dataKey="hipertensao" name="Hipertensão" fill={DISEASE_COLORS.hipertensao} radius={[4, 4, 0, 0]} />
            <Bar dataKey="cancer" name="Câncer" fill={DISEASE_COLORS.cancer} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Alerts */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Alertas Cross-Tenant
        </h3>
        <div className="space-y-3">
          {[
            { severity: 'high', msg: 'Taxa de controle de DRC em Belo Horizonte caiu 8% nos últimos 30 dias', tenant: 'SMS BH' },
            { severity: 'medium', msg: 'Aumento de 15% em casos de diabetes descompensado em Montes Claros', tenant: 'SMS MC' },
            { severity: 'low', msg: 'São Paulo atingiu meta de 60% de controle de hipertensão', tenant: 'SMS SP' },
          ].map((alert, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 p-3 rounded-lg ${
                alert.severity === 'high'
                  ? 'bg-red-50 border border-red-100'
                  : alert.severity === 'medium'
                    ? 'bg-amber-50 border border-amber-100'
                    : 'bg-emerald-50 border border-emerald-100'
              }`}
            >
              <TrendingUp
                className={`h-4 w-4 mt-0.5 ${
                  alert.severity === 'high'
                    ? 'text-red-500'
                    : alert.severity === 'medium'
                      ? 'text-amber-500'
                      : 'text-emerald-500'
                }`}
              />
              <div>
                <p className="text-sm text-slate-700">{alert.msg}</p>
                <p className="text-xs text-slate-400 mt-0.5">{alert.tenant}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
