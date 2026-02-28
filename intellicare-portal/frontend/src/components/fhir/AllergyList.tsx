/**
 * AllergyList — lista de alergias e intolerâncias de um paciente FHIR.
 */

import { ShieldAlert } from 'lucide-react';
import { FHIRAllergyIntolerance, codingDisplay } from './types';

const CRITICALITY_CONFIG = {
  high: { label: 'Alto risco', className: 'bg-red-500/15 text-red-400 border-red-500/30' },
  low:  { label: 'Baixo risco', className: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  'unable-to-assess': { label: 'Indeterminado', className: 'bg-slate-500/15 text-slate-400 border-slate-500/30' },
};

const CATEGORY_LABEL: Record<string, string> = {
  food:        'Alimento',
  medication:  'Medicamento',
  environment: 'Ambiente',
  biologic:    'Biológico',
};

const SEVERITY_COLOR: Record<string, string> = {
  mild:     'text-yellow-400',
  moderate: 'text-orange-400',
  severe:   'text-red-400',
};

interface AllergyListProps {
  allergies: FHIRAllergyIntolerance[];
  className?: string;
}

export function AllergyList({ allergies, className }: AllergyListProps) {
  if (allergies.length === 0) {
    return (
      <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 text-center ${className ?? ''}`}>
        <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-500">Nenhuma alergia registrada.</p>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      <div className="px-5 py-3.5 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-400" />
          Alergias e Intolerâncias
          <span className="ml-auto text-xs text-slate-500">{allergies.length}</span>
        </h3>
      </div>
      <ul className="divide-y divide-slate-700/30">
        {allergies.map((allergy, idx) => {
          const criticality = allergy.criticality ?? 'unable-to-assess';
          const critConfig = CRITICALITY_CONFIG[criticality] ?? CRITICALITY_CONFIG['unable-to-assess'];
          const categories = (allergy.category ?? []).map(c => CATEGORY_LABEL[c] ?? c);
          const manifestations = allergy.reaction?.flatMap(r =>
            (r.manifestation ?? []).map(m => codingDisplay(m)),
          ) ?? [];
          const severity = allergy.reaction?.[0]?.severity;

          return (
            <li key={allergy.id ?? idx} className="px-5 py-3.5 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-white leading-tight">
                  {codingDisplay(allergy.code)}
                </p>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {categories.map(cat => (
                    <span key={cat} className="text-xs px-2 py-0.5 rounded-md bg-slate-700 text-slate-400">
                      {cat}
                    </span>
                  ))}
                  {allergy.type && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-slate-700 text-slate-400">
                      {allergy.type === 'allergy' ? 'Alergia' : 'Intolerância'}
                    </span>
                  )}
                </div>
                {manifestations.length > 0 && (
                  <p className="text-xs text-slate-500 mt-1">
                    Reação: {manifestations.join(', ')}
                    {severity && (
                      <span className={`ml-1.5 font-medium ${SEVERITY_COLOR[severity] ?? ''}`}>
                        ({severity === 'mild' ? 'leve' : severity === 'moderate' ? 'moderada' : 'grave'})
                      </span>
                    )}
                  </p>
                )}
              </div>
              <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium flex-shrink-0 ${critConfig.className}`}>
                {critConfig.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default AllergyList;
