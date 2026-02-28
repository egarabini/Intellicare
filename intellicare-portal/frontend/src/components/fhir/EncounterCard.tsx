/**
 * EncounterCard — cartão de resumo de um Encounter FHIR.
 */

import { Stethoscope, Calendar, User, Building, Clock } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { FHIREncounter, codingDisplay, fhirDate, fhirDateTime } from './types';

const CLASS_LABEL: Record<string, string> = {
  AMB:  'Ambulatorial',
  IMP:  'Internação',
  EMER: 'Emergência',
  HH:   'Home Care',
  VR:   'Virtual',
};

interface EncounterCardProps {
  encounter: FHIREncounter;
  onClick?: () => void;
  className?: string;
}

export function EncounterCard({ encounter, onClick, className }: EncounterCardProps) {
  const encounterType = encounter.type?.[0] ? codingDisplay(encounter.type[0]) : null;
  const classLabel = encounter.class?.code ? CLASS_LABEL[encounter.class.code] ?? encounter.class.code : null;
  const reason = encounter.reasonCode?.[0] ? codingDisplay(encounter.reasonCode[0]) : null;
  const practitioner = encounter.participant?.find(
    p => !p.type || p.type.some(t => t.coding?.some(c => c.code === 'PART' || c.code === 'ATND')),
  )?.individual;
  const start = encounter.period?.start;
  const end = encounter.period?.end;
  const duration = start && end
    ? (() => {
        const mins = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60000);
        return mins < 60 ? `${mins} min` : `${Math.round(mins / 60)}h`;
      })()
    : null;

  return (
    <div
      onClick={onClick}
      className={`bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden transition-colors ${onClick ? 'cursor-pointer hover:border-slate-600' : ''} ${className ?? ''}`}
    >
      {/* Header */}
      <div className="px-4 py-4 flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 flex-shrink-0">
            <Stethoscope className="w-4 h-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">
              {encounterType ?? 'Encontro Clínico'}
            </p>
            {classLabel && (
              <p className="text-xs text-slate-500 mt-0.5">{classLabel}</p>
            )}
          </div>
        </div>
        <StatusBadge status={encounter.status} size="sm" />
      </div>

      {/* Details */}
      <div className="px-4 pb-3 space-y-1.5 pl-[3.75rem]">
        {reason && (
          <p className="text-xs text-slate-400 flex items-start gap-1.5">
            <span className="text-slate-600 flex-shrink-0 mt-0.5">Motivo:</span>
            {reason}
          </p>
        )}
        {practitioner?.display && (
          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <User className="w-3 h-3 text-slate-600 flex-shrink-0" />
            {practitioner.display}
          </p>
        )}
        {encounter.serviceProvider?.display && (
          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <Building className="w-3 h-3 text-slate-600 flex-shrink-0" />
            {encounter.serviceProvider.display}
          </p>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 bg-slate-900/30 border-t border-slate-700/50 flex items-center gap-4 text-xs text-slate-600">
        {start && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {fhirDate(start)}
          </span>
        )}
        {duration && (
          <span className="flex items-center gap-1 ml-auto">
            <Clock className="w-3 h-3" />
            {duration}
          </span>
        )}
      </div>
    </div>
  );
}

export default EncounterCard;
