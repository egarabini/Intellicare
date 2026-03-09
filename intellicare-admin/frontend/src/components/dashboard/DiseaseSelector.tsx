import { DISEASE_PROGRAMS } from '@config/diseases';
import type { DiseaseCode } from '@/types/index';
import { cn } from '@utils/formatters';
import {
  Droplets,
  Activity,
  HeartPulse,
  Ribbon,
} from 'lucide-react';

interface DiseaseSelectorProps {
  selected: DiseaseCode;
  onChange: (code: DiseaseCode) => void;
}

const ICON_MAP: Record<string, React.ElementType> = {
  Droplets,
  Activity,
  HeartPulse,
  Ribbon,
};

export default function DiseaseSelector({ selected, onChange }: DiseaseSelectorProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      {DISEASE_PROGRAMS.map((disease) => {
        const Icon = ICON_MAP[disease.icon] ?? Activity;
        const isActive = selected === disease.code;

        return (
          <button
            key={disease.code}
            onClick={() => onChange(disease.code)}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border-2 transition-all',
              isActive
                ? 'shadow-md scale-[1.02]'
                : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:shadow-sm',
            )}
            style={
              isActive
                ? {
                    borderColor: disease.color,
                    backgroundColor: `${disease.color}10`,
                    color: disease.color,
                  }
                : undefined
            }
          >
            <Icon className="h-4 w-4" />
            {disease.name}
          </button>
        );
      })}
    </div>
  );
}
