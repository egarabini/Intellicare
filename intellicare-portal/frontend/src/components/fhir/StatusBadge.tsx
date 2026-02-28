/**
 * StatusBadge — exibe o status de um recurso FHIR como chip colorido.
 * Suporta status de Observation, Condition, Encounter, MedicationRequest,
 * DiagnosticReport e AllergyIntolerance.
 */

import { cn } from '@utils/cn';

type StatusVariant =
  // Observation / DiagnosticReport
  | 'final' | 'preliminary' | 'registered' | 'amended' | 'corrected'
  | 'cancelled' | 'entered-in-error' | 'unknown'
  // Condition clinicalStatus
  | 'active' | 'recurrence' | 'relapse' | 'inactive' | 'remission' | 'resolved'
  // Encounter
  | 'planned' | 'arrived' | 'triaged' | 'in-progress' | 'onleave' | 'finished'
  // MedicationRequest
  | 'on-hold' | 'stopped' | 'draft' | 'completed'
  // AllergyIntolerance criticality
  | 'low' | 'high' | 'unable-to-assess'
  // Generic
  | string;

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  // Green — positive/final
  final:      { label: 'Final',      className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  active:     { label: 'Ativo',      className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  finished:   { label: 'Finalizado', className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  completed:  { label: 'Concluído',  className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  resolved:   { label: 'Resolvido',  className: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' },
  // Blue — in-progress / preliminary
  'in-progress': { label: 'Em andamento',  className: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
  preliminary:   { label: 'Preliminar',    className: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
  registered:    { label: 'Registrado',    className: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
  arrived:       { label: 'Chegou',        className: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
  triaged:       { label: 'Triagem',       className: 'bg-blue-500/15 text-blue-400 border-blue-500/30' },
  // Yellow — hold / warning
  planned:    { label: 'Planejado',   className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  'on-hold':  { label: 'Suspenso',    className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  onleave:    { label: 'Licença',     className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  draft:      { label: 'Rascunho',    className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  remission:  { label: 'Remissão',    className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  // Orange — moderate risk
  amended:    { label: 'Corrigido',   className: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  corrected:  { label: 'Retificado',  className: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  recurrence: { label: 'Recorrência', className: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  relapse:    { label: 'Recaída',     className: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  high:       { label: 'Alto risco',  className: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  // Red — cancelled / error / critical
  cancelled:          { label: 'Cancelado',       className: 'bg-red-500/15 text-red-400 border-red-500/30' },
  'entered-in-error': { label: 'Erro de registro', className: 'bg-red-500/15 text-red-400 border-red-500/30' },
  stopped:            { label: 'Interrompido',     className: 'bg-red-500/15 text-red-400 border-red-500/30' },
  inactive:           { label: 'Inativo',          className: 'bg-red-500/15 text-red-400 border-red-500/30' },
  // Slate — unknown
  unknown:            { label: 'Desconhecido',     className: 'bg-slate-500/15 text-slate-400 border-slate-500/30' },
  low:                { label: 'Baixo risco',      className: 'bg-slate-500/15 text-slate-400 border-slate-500/30' },
  'unable-to-assess': { label: 'Indeterminado',    className: 'bg-slate-500/15 text-slate-400 border-slate-500/30' },
};

interface StatusBadgeProps {
  status: StatusVariant;
  /** Override the display label */
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export function StatusBadge({ status, label, size = 'md', className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    className: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs',
        config.className,
        className,
      )}
    >
      {label ?? config.label}
    </span>
  );
}

export default StatusBadge;
