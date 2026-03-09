import { useNavigate } from 'react-router-dom';
import { DISEASE_PROGRAMS } from '@config/diseases';
import { Droplets, Activity, HeartPulse, Ribbon, ArrowRight, Users, AlertTriangle, TrendingUp } from 'lucide-react';
import Header from '@components/layout/Header';

const ICON_MAP: Record<string, React.ElementType> = {
  Droplets,
  Activity,
  HeartPulse,
  Ribbon,
};

/** Quick stats for the home overview — will come from API later */
const OVERVIEW_STATS = [
  { label: 'Total de Pacientes Crônicos', value: '18.432', icon: Users, color: '#3b82f6' },
  { label: 'Taxa de Controle Geral', value: '58,3%', icon: TrendingUp, color: '#22c55e' },
  { label: 'Alertas Ativos', value: '127', icon: AlertTriangle, color: '#ef4444' },
];

export default function DashboardHome() {
  const navigate = useNavigate();

  return (
    <div>
      <Header
        title="Dashboard de Saúde"
        subtitle="Visão geral dos programas de doenças crônicas"
      />

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {OVERVIEW_STATS.map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-4 p-5 bg-white rounded-xl border border-slate-100 shadow-sm"
          >
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: `${stat.color}15` }}
            >
              <stat.icon className="h-6 w-6" style={{ color: stat.color }} />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800">{stat.value}</p>
              <p className="text-xs text-slate-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Disease Program Cards */}
      <h2 className="text-lg font-semibold text-slate-700 mb-4">Programas de Doenças</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {DISEASE_PROGRAMS.map((disease) => {
          const Icon = ICON_MAP[disease.icon] ?? Activity;
          return (
            <button
              key={disease.code}
              onClick={() => navigate(`/doenca/${disease.code}`)}
              className="group flex items-start gap-4 p-6 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md hover:border-slate-200 transition-all text-left"
            >
              <div
                className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: `${disease.color}15` }}
              >
                <Icon className="h-7 w-7" style={{ color: disease.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-semibold text-slate-800 group-hover:text-primary-600 transition-colors">
                  {disease.name}
                </h3>
                <p className="text-sm text-slate-500 mt-1">
                  CID-10: {disease.icdCodes.slice(0, 3).join(', ')}
                  {disease.icdCodes.length > 3 && ` +${disease.icdCodes.length - 3}`}
                </p>
                <div className="flex items-center gap-1 mt-2 text-xs text-slate-400">
                  {disease.stages?.length ?? 0} estágios definidos
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-primary-500 transition-colors mt-1" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
