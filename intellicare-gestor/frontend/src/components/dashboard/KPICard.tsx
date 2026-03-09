import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, formatNumber, formatPercent } from '@utils/formatters';
import type { KPIData } from '@/types/index';

interface KPICardProps {
  data: KPIData;
  className?: string;
}

export default function KPICard({ data, className }: KPICardProps) {
  const displayValue =
    data.format === 'percent'
      ? formatPercent(data.value)
      : data.unit
        ? `${formatNumber(data.value)} ${data.unit}`
        : formatNumber(data.value);

  const trendPercent =
    data.previousValue && data.previousValue > 0
      ? (((data.value - data.previousValue) / data.previousValue) * 100).toFixed(1)
      : null;

  const TrendIcon =
    data.trend === 'up' ? TrendingUp : data.trend === 'down' ? TrendingDown : Minus;

  const trendColorClass =
    data.trend === 'stable'
      ? 'text-slate-400'
      : data.trendIsGood
        ? 'text-emerald-500'
        : 'text-red-500';

  return (
    <div
      className={cn(
        'rounded-xl bg-white p-5 shadow-sm border border-slate-100 hover:shadow-md transition-shadow',
        className,
      )}
    >
      <p className="text-sm font-medium text-slate-500 mb-1">{data.label}</p>
      <div className="flex items-end justify-between">
        <p
          className="text-2xl font-bold tracking-tight"
          style={{ color: data.color ?? '#1e293b' }}
        >
          {displayValue}
        </p>
        {trendPercent && (
          <div className={cn('flex items-center gap-1 text-xs font-medium', trendColorClass)}>
            <TrendIcon className="h-3.5 w-3.5" />
            <span>{trendPercent}%</span>
          </div>
        )}
      </div>
    </div>
  );
}
