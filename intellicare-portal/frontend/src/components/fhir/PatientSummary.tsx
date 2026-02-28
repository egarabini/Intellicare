/**
 * PatientSummary — cartão de visão consolidada de um paciente FHIR.
 * Exibe dados demográficos, identificadores e status.
 */

import { User, Calendar, Phone, MapPin, Hash, Activity } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import {
  FHIRPatient,
  patientName,
  fhirDate,
  ageFromBirthDate,
  codingDisplay,
} from './types';

const GENDER_LABEL: Record<string, string> = {
  male:    'Masculino',
  female:  'Feminino',
  other:   'Outro',
  unknown: 'Não informado',
};

interface PatientSummaryProps {
  patient: FHIRPatient;
  /** Show last updated meta info */
  showMeta?: boolean;
  className?: string;
}

export function PatientSummary({ patient, showMeta = false, className }: PatientSummaryProps) {
  const name = patientName(patient.name);
  const age = ageFromBirthDate(patient.birthDate);
  const phone = patient.telecom?.find(t => t.system === 'phone')?.value;
  const email = patient.telecom?.find(t => t.system === 'email')?.value;
  const address = patient.address?.[0];
  const cpf = patient.identifier?.find(i => i.system?.includes('cpf'))?.value;
  const cns = patient.identifier?.find(i => i.system?.includes('cns') || i.system?.includes('rnds'))?.value;

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm ${className ?? ''}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
            <User className="w-7 h-7 text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{name}</h2>
            <p className="text-sm text-slate-400 font-mono mt-0.5">
              {patient.id ? `ID: ${patient.id}` : 'Sem ID'}
            </p>
          </div>
        </div>
        <StatusBadge status={patient.active !== false ? 'active' : 'inactive'} />
      </div>

      {/* Demographics grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {patient.gender && (
          <InfoItem
            icon={<Activity className="w-3.5 h-3.5" />}
            label="Sexo"
            value={GENDER_LABEL[patient.gender] ?? patient.gender}
          />
        )}
        {patient.birthDate && (
          <InfoItem
            icon={<Calendar className="w-3.5 h-3.5" />}
            label="Nascimento"
            value={`${fhirDate(patient.birthDate)}${age !== null ? ` (${age} anos)` : ''}`}
          />
        )}
        {phone && (
          <InfoItem
            icon={<Phone className="w-3.5 h-3.5" />}
            label="Telefone"
            value={phone}
          />
        )}
        {email && (
          <InfoItem
            icon={<Phone className="w-3.5 h-3.5" />}
            label="E-mail"
            value={email}
          />
        )}
        {address && (
          <InfoItem
            icon={<MapPin className="w-3.5 h-3.5" />}
            label="Endereço"
            value={[address.city, address.state].filter(Boolean).join(', ') || address.line?.[0] || '—'}
            className="col-span-2"
          />
        )}
      </div>

      {/* Identifiers */}
      {(cpf || cns) && (
        <div className="flex flex-wrap gap-2 pt-4 border-t border-slate-700/50">
          {cpf && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/50 border border-slate-700 text-xs font-mono text-slate-300">
              <Hash className="w-3 h-3 text-slate-500" />
              CPF: {cpf}
            </span>
          )}
          {cns && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/50 border border-slate-700 text-xs font-mono text-slate-300">
              <Hash className="w-3 h-3 text-slate-500" />
              CNS: {cns}
            </span>
          )}
        </div>
      )}

      {/* Meta info */}
      {showMeta && patient.meta?.lastUpdated && (
        <p className="text-xs text-slate-600 mt-3">
          Atualizado em: {fhirDate(patient.meta.lastUpdated)}
        </p>
      )}
    </div>
  );
}

// ── Sub-component ─────────────────────────────────────────────────────────────

function InfoItem({
  icon,
  label,
  value,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={`flex items-start gap-2 ${className ?? ''}`}>
      <span className="text-slate-500 mt-0.5">{icon}</span>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-sm text-slate-200 truncate">{value}</p>
      </div>
    </div>
  );
}

export default PatientSummary;
