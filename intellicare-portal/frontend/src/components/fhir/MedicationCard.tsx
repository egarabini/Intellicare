/**
 * MedicationCard — exibe uma prescrição médica (MedicationRequest) FHIR.
 */

import { Pill, Clock, User, FileText } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { FHIRMedicationRequest, codingDisplay, fhirDate } from './types';

interface MedicationCardProps {
  medication: FHIRMedicationRequest;
  className?: string;
}

export function MedicationCard({ medication, className }: MedicationCardProps) {
  const name = medication.medicationCodeableConcept
    ? codingDisplay(medication.medicationCodeableConcept)
    : medication.medicationReference?.display ?? 'Medicamento não especificado';

  const dosages = medication.dosageInstruction ?? [];
  const firstDosage = dosages[0];
  const timing = firstDosage?.timing?.repeat;
  const frequencyLabel = timing
    ? `${timing.frequency ?? 1}x / ${timing.period ?? 1} ${timing.periodUnit ?? 'd'}`
    : null;

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden ${className ?? ''}`}>
      <div className="px-4 py-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex-shrink-0">
              <Pill className="w-4 h-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white leading-tight">{name}</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {medication.intent === 'order' ? 'Prescrição' : medication.intent}
              </p>
            </div>
          </div>
          <StatusBadge status={medication.status} size="sm" />
        </div>

        {/* Dosage info */}
        {firstDosage && (
          <div className="space-y-1.5 pl-11">
            {firstDosage.text && (
              <p className="text-sm text-slate-300">{firstDosage.text}</p>
            )}
            <div className="flex flex-wrap gap-3 text-xs text-slate-500">
              {frequencyLabel && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {frequencyLabel}
                </span>
              )}
              {firstDosage.doseAndRate?.[0]?.doseQuantity && (
                <span className="font-mono text-slate-300">
                  {firstDosage.doseAndRate[0].doseQuantity.value}{' '}
                  {firstDosage.doseAndRate[0].doseQuantity.unit ?? ''}
                </span>
              )}
              {firstDosage.route && (
                <span>{codingDisplay(firstDosage.route)}</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 bg-slate-900/30 border-t border-slate-700/50 flex items-center gap-4 text-xs text-slate-600">
        {medication.requester?.display && (
          <span className="flex items-center gap-1">
            <User className="w-3 h-3" />
            {medication.requester.display}
          </span>
        )}
        {medication.authoredOn && (
          <span className="flex items-center gap-1 ml-auto">
            <FileText className="w-3 h-3" />
            {fhirDate(medication.authoredOn)}
          </span>
        )}
      </div>
    </div>
  );
}

export default MedicationCard;
