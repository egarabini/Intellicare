/**
 * ObservationChart — gráfico de tendência para séries de Observations FHIR.
 * Utiliza Recharts (já disponível no portal) para renderizar linha temporal.
 */

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';
import { FHIRObservation, codingDisplay, fhirDate } from './types';

interface ChartPoint {
  date: string;
  dateLabel: string;
  value: number;
}

interface ObservationChartProps {
  observations: FHIRObservation[];
  /** Display label for the chart (e.g. "Creatinina sérica") */
  title?: string;
  /** Unit label for Y axis */
  unit?: string;
  /** Normal range low */
  refLow?: number;
  /** Normal range high */
  refHigh?: number;
  /** Color for the line (Tailwind hex equivalent) */
  color?: string;
  /** Chart height in pixels (default: 200) */
  height?: number;
  className?: string;
}

export function ObservationChart({
  observations,
  title,
  unit,
  refLow,
  refHigh,
  color = '#60a5fa',
  height = 200,
  className,
}: ObservationChartProps) {
  const data = useMemo<ChartPoint[]>(() => {
    return observations
      .filter(o => o.valueQuantity?.value !== undefined)
      .map(o => ({
        date: o.effectiveDateTime ?? o.meta?.lastUpdated ?? '',
        dateLabel: fhirDate(o.effectiveDateTime ?? o.meta?.lastUpdated),
        value: o.valueQuantity!.value!,
      }))
      .filter(p => p.date)
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [observations]);

  const displayTitle = title ?? (observations[0]?.code ? codingDisplay(observations[0].code) : 'Observação');
  const displayUnit = unit ?? observations[0]?.valueQuantity?.unit ?? '';

  // Trend calculation
  const trend = useMemo(() => {
    if (data.length < 2) return 'stable';
    const first = data[0].value;
    const last = data[data.length - 1].value;
    const pct = ((last - first) / first) * 100;
    if (pct > 5) return 'up';
    if (pct < -5) return 'down';
    return 'stable';
  }, [data]);

  const latestValue = data[data.length - 1]?.value;

  if (data.length === 0) {
    return (
      <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 flex items-center justify-center ${className ?? ''}`} style={{ height }}>
        <div className="text-center">
          <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Sem dados numéricos disponíveis.</p>
        </div>
      </div>
    );
  }

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-orange-400' : trend === 'down' ? 'text-blue-400' : 'text-slate-400';

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-5 ${className ?? ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-semibold text-white">{displayTitle}</h4>
          {displayUnit && <p className="text-xs text-slate-500 mt-0.5">{displayUnit}</p>}
        </div>
        <div className="flex items-center gap-2">
          {latestValue !== undefined && (
            <span className="text-xl font-bold text-white font-mono">
              {latestValue}
              {displayUnit && <span className="text-sm text-slate-400 ml-1">{displayUnit}</span>}
            </span>
          )}
          <TrendIcon className={`w-5 h-5 ${trendColor}`} />
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="dateLabel"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '0.5rem',
              fontSize: '0.75rem',
              color: '#e2e8f0',
            }}
            // @ts-ignore - Recharts type compatibility issue
            formatter={(value: number) => [`${value} ${displayUnit}`, displayTitle]}
            // @ts-ignore - Recharts type compatibility issue
            labelFormatter={(label: string) => `Data: ${label}`}
          />
          {refLow !== undefined && (
            <ReferenceLine y={refLow} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
          )}
          {refHigh !== undefined && (
            <ReferenceLine y={refHigh} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ fill: color, strokeWidth: 0, r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Reference range label */}
      {(refLow !== undefined || refHigh !== undefined) && (
        <p className="text-xs text-slate-600 mt-2 text-right">
          Referência: {refLow ?? '?'} – {refHigh ?? '?'} {displayUnit}
        </p>
      )}
    </div>
  );
}

export default ObservationChart;
