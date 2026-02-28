/**
 * PatientTimeline — linha do tempo de eventos clínicos de um paciente.
 * Aceita uma lista heterogênea de recursos FHIR e os ordena cronologicamente.
 */

import { Activity, Pill, Stethoscope, FileText, AlertTriangle, ClipboardList } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import {
  FHIRResource,
  FHIRObservation,
  FHIRCondition,
  FHIREncounter,
  FHIRMedicationRequest,
  FHIRDiagnosticReport,
  codingDisplay,
  fhirDate,
  fhirDateTime,
} from './types';

interface TimelineEvent {
  id: string;
  resourceType: string;
  date: Date;
  title: string;
  subtitle?: string;
  status?: string;
  resource: FHIRResource;
}

function extractEvent(resource: FHIRResource): TimelineEvent | null {
  const id = (resource as any).id ?? Math.random().toString(36).slice(2);

  switch (resource.resourceType) {
    case 'Observation': {
      const obs = resource as FHIRObservation;
      const dateStr = obs.effectiveDateTime ?? obs.meta?.lastUpdated;
      if (!dateStr) return null;
      const qty = obs.valueQuantity;
      const valueLabel = qty
        ? `${qty.value} ${qty.unit ?? ''}`
        : obs.valueString ?? obs.valueCodeableConcept?.text ?? '';
      return {
        id,
        resourceType: 'Observation',
        date: new Date(dateStr),
        title: codingDisplay(obs.code),
        subtitle: valueLabel || undefined,
        status: obs.status,
        resource,
      };
    }
    case 'Condition': {
      const cond = resource as FHIRCondition;
      const dateStr = cond.onsetDateTime ?? cond.recordedDate ?? cond.meta?.lastUpdated;
      if (!dateStr) return null;
      return {
        id,
        resourceType: 'Condition',
        date: new Date(dateStr),
        title: codingDisplay(cond.code),
        subtitle: codingDisplay(cond.clinicalStatus),
        status: cond.clinicalStatus?.coding?.[0]?.code,
        resource,
      };
    }
    case 'Encounter': {
      const enc = resource as FHIREncounter;
      const dateStr = enc.period?.start ?? enc.meta?.lastUpdated;
      if (!dateStr) return null;
      return {
        id,
        resourceType: 'Encounter',
        date: new Date(dateStr),
        title: enc.type?.[0] ? codingDisplay(enc.type[0]) : 'Encontro',
        subtitle: enc.reasonCode?.[0] ? codingDisplay(enc.reasonCode[0]) : undefined,
        status: enc.status,
        resource,
      };
    }
    case 'MedicationRequest': {
      const med = resource as FHIRMedicationRequest;
      const dateStr = med.authoredOn ?? med.meta?.lastUpdated;
      if (!dateStr) return null;
      return {
        id,
        resourceType: 'MedicationRequest',
        date: new Date(dateStr),
        title: codingDisplay(med.medicationCodeableConcept) || 'Medicamento',
        subtitle: med.dosageInstruction?.[0]?.text,
        status: med.status,
        resource,
      };
    }
    case 'DiagnosticReport': {
      const dr = resource as FHIRDiagnosticReport;
      const dateStr = dr.effectiveDateTime ?? dr.issued ?? dr.meta?.lastUpdated;
      if (!dateStr) return null;
      return {
        id,
        resourceType: 'DiagnosticReport',
        date: new Date(dateStr),
        title: codingDisplay(dr.code),
        subtitle: dr.conclusion?.slice(0, 80),
        status: dr.status,
        resource,
      };
    }
    default:
      return null;
  }
}

const RESOURCE_ICON: Record<string, React.ReactNode> = {
  Observation:       <Activity className="w-4 h-4" />,
  Condition:         <AlertTriangle className="w-4 h-4" />,
  Encounter:         <Stethoscope className="w-4 h-4" />,
  MedicationRequest: <Pill className="w-4 h-4" />,
  DiagnosticReport:  <FileText className="w-4 h-4" />,
};

const RESOURCE_COLOR: Record<string, string> = {
  Observation:       'bg-blue-500/15 text-blue-400 border-blue-500/30',
  Condition:         'bg-orange-500/15 text-orange-400 border-orange-500/30',
  Encounter:         'bg-purple-500/15 text-purple-400 border-purple-500/30',
  MedicationRequest: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  DiagnosticReport:  'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
};

interface PatientTimelineProps {
  resources: FHIRResource[];
  /** Maximum number of events to show (default: all) */
  maxItems?: number;
  /** Called when user clicks on an event */
  onSelect?: (resource: FHIRResource) => void;
  className?: string;
}

export function PatientTimeline({
  resources,
  maxItems,
  onSelect,
  className,
}: PatientTimelineProps) {
  const events = resources
    .map(extractEvent)
    .filter((e): e is TimelineEvent => e !== null)
    .sort((a, b) => b.date.getTime() - a.date.getTime())
    .slice(0, maxItems);

  if (events.length === 0) {
    return (
      <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-8 text-center ${className ?? ''}`}>
        <ClipboardList className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-500 text-sm">Nenhum evento clínico registrado.</p>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      <div className="px-6 py-4 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-slate-400" />
          Timeline Clínica
          <span className="ml-auto text-xs text-slate-500">{events.length} evento{events.length !== 1 ? 's' : ''}</span>
        </h3>
      </div>

      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[2.35rem] top-0 bottom-0 w-px bg-slate-700/50" />

        <ul className="divide-y divide-slate-700/30">
          {events.map((event, idx) => {
            const colorClass = RESOURCE_COLOR[event.resourceType] ?? 'bg-slate-500/15 text-slate-400 border-slate-500/30';
            const icon = RESOURCE_ICON[event.resourceType] ?? <Activity className="w-4 h-4" />;
            return (
              <li
                key={`${event.id}-${idx}`}
                onClick={() => onSelect?.(event.resource)}
                className={`flex gap-4 px-6 py-4 transition-colors ${onSelect ? 'cursor-pointer hover:bg-slate-700/20' : ''}`}
              >
                {/* Icon */}
                <div className={`relative z-10 w-8 h-8 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5 ${colorClass}`}>
                  {icon}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-white leading-tight">{event.title}</p>
                    {event.status && (
                      <StatusBadge status={event.status} size="sm" />
                    )}
                  </div>
                  {event.subtitle && (
                    <p className="text-xs text-slate-400 mt-0.5 truncate">{event.subtitle}</p>
                  )}
                  <p className="text-xs text-slate-600 mt-1">
                    {fhirDateTime(event.date.toISOString())}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

export default PatientTimeline;
