import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import type { TrendSeries } from '@/types/index';
import { formatDateShort } from '@utils/formatters';

interface TrendChartProps {
  series: TrendSeries[];
  title?: string;
  height?: number;
}

export default function TrendChart({ series, title, height = 300 }: TrendChartProps) {
  if (!series.length) return null;

  // Merge all data points by date
  const dateMap = new Map<string, Record<string, number>>();
  series.forEach((s) => {
    s.data.forEach((pt) => {
      const existing = dateMap.get(pt.date) ?? {};
      existing[s.id] = pt.value;
      if (pt.target !== undefined) existing[`${s.id}_target`] = pt.target;
      dateMap.set(pt.date, existing);
    });
  });

  const chartData = Array.from(dateMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, values]) => ({ date, ...values }));

  const hasTarget = series.some((s) => s.data.some((d) => d.target !== undefined));

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
      {title && <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDateShort}
            tick={{ fontSize: 12, fill: '#94a3b8' }}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={{ stroke: '#e2e8f0' }} />
          <Tooltip
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
            }}
            labelFormatter={(label) => `Data: ${formatDateShort(label as string)}`}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((s) => (
            <Line
              key={s.id}
              type="monotone"
              dataKey={s.id}
              name={s.label}
              stroke={s.color}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
          {hasTarget && (
            <ReferenceLine
              y={70}
              stroke="#22c55e"
              strokeDasharray="5 5"
              label={{ value: 'Meta', fill: '#22c55e', fontSize: 11 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
