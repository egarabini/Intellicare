import { PERIOD_OPTIONS } from '@config/diseases';
import type { DashboardFilters } from '@/types/index';
import { cn } from '@utils/formatters';

interface PeriodSelectorProps {
  selected: DashboardFilters['period'];
  onChange: (period: DashboardFilters['period']) => void;
}

export default function PeriodSelector({ selected, onChange }: PeriodSelectorProps) {
  return (
    <div className="flex gap-1 bg-slate-100 rounded-lg p-0.5">
      {PERIOD_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            'px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap',
            selected === opt.value
              ? 'bg-white text-slate-700 shadow-sm'
              : 'text-slate-500 hover:text-slate-700',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
