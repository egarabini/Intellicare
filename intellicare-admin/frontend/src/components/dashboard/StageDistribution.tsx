import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { useState } from 'react';
import type { StageDistribution as StageDistType } from '@/types/index';
import { formatNumber } from '@utils/formatters';

interface StageDistributionProps {
  data: StageDistType[];
  title?: string;
}

type ViewMode = 'bar' | 'pie';

export default function StageDistribution({ data, title }: StageDistributionProps) {
  const [view, setView] = useState<ViewMode>('bar');

  if (!data.length) return null;

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between mb-4">
        {title && <h3 className="text-sm font-semibold text-slate-700">{title}</h3>}
        <div className="flex gap-1 bg-slate-100 rounded-lg p-0.5">
          <button
            onClick={() => setView('bar')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              view === 'bar' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-500'
            }`}
          >
            Barras
          </button>
          <button
            onClick={() => setView('pie')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              view === 'pie' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-500'
            }`}
          >
            Pizza
          </button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        {view === 'bar' ? (
          <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={{ stroke: '#e2e8f0' }} />
            <Tooltip
              contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
              formatter={(value: unknown) => [formatNumber(Number(value)), 'Pacientes']}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={48}>
              {data.map((entry, idx) => (
                <Cell key={idx} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        ) : (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              dataKey="count"
              nameKey="label"
              label={(props) => `${(props as any).label}: ${(props as any).percentage}%`}
              labelLine={true}
            >
              {data.map((entry, idx) => (
                <Cell key={idx} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value: unknown) => [formatNumber(Number(value)), 'Pacientes']} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
