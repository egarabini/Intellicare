/**
 * ProblemList — lista de condições/problemas ativos de um paciente FHIR.
 */

import { AlertCircle, Clock } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { FHIRCondition, codingDisplay, fhirDate } from './types';

interface ProblemListProps {
  conditions: FHIRCondition[];
  /** Only show active conditions when true (default: false = show all) */
  activeOnly?: boolean;
  className?: string;
}

const SEVERITY_COLOR: Record<string, string> = {
  severe:   'text-red-400 bg-red-500/10 border-red-500/20',
  moderate: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  mild:     'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
};

export function ProblemList({ conditions, activeOnly = false, className }: ProblemListProps) {
  const filtered = activeOnly
    ? conditions.filter(c => c.clinicalStatus?.coding?.[0]?.code === 'active')
    : conditions;

  if (filtered.length === 0) {
    return (
      <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 text-center ${className ?? ''}`}>
        <AlertCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-500">Nenhum problema registrado.</p>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      <div className="px-5 py-3.5 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-orange-400" />
          Lista de Problemas
          <span className="ml-auto text-xs text-slate-500">{filtered.length}</span>
        </h3>
      </div>
      <ul className="divide-y divide-slate-700/30">
        {filtered.map((cond, idx) => {
          const status = cond.clinicalStatus?.coding?.[0]?.code ?? 'unknown';
          const severityCode = cond.severity?.coding?.[0]?.code?.toLowerCase();
          const severityClass = severityCode ? SEVERITY_COLOR[severityCode] : null;
          const onsetLabel = cond.onsetDateTime
            ? fhirDate(cond.onsetDateTime)
            : cond.recordedDate
            ? fhirDate(cond.recordedDate)
            : null;

          return (
            <li key={cond.id ?? idx} className="px-5 py-3.5 flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5 min-w-0">
                {severityClass && (
                  <span className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 border ${severityClass}`} />
                )}
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white leading-tight truncate">
                    {codingDisplay(cond.code)}
                  </p>
                  {cond.category?.[0] && (
                    <p className="text-xs text-slate-500 mt-0.5">{codingDisplay(cond.category[0])}</p>
                  )}
                  {onsetLabel && (
                    <p className="text-xs text-slate-600 mt-0.5 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Início: {onsetLabel}
                    </p>
                  )}
                </div>
              </div>
              <StatusBadge status={status} size="sm" />
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default ProblemList;
