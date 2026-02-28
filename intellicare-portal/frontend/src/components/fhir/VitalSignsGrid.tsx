/**
 * VitalSignsGrid — grade de sinais vitais mais recentes de um paciente.
 * Interpreta Observations por código LOINC e exibe em cards compactos.
 */

import { Heart, Thermometer, Wind, Activity, Droplets, Scale } from 'lucide-react';
import { FHIRObservation } from './types';

// LOINC codes for common vitals
const VITAL_CODES: Record<string, {
  label: string;
  unit: string;
  icon: React.ReactNode;
  color: string;
  refLow?: number;
  refHigh?: number;
}> = {
  '8867-4':  { label: 'FC',        unit: 'bpm',    icon: <Heart className="w-4 h-4" />,        color: 'text-red-400',     refLow: 60,   refHigh: 100  },
  '9279-1':  { label: 'FR',        unit: '/min',   icon: <Wind className="w-4 h-4" />,         color: 'text-cyan-400',    refLow: 12,   refHigh: 20   },
  '8310-5':  { label: 'Temp',      unit: '°C',     icon: <Thermometer className="w-4 h-4" />,  color: 'text-orange-400',  refLow: 36.0, refHigh: 37.5 },
  '59408-5': { label: 'SpO₂',      unit: '%',      icon: <Droplets className="w-4 h-4" />,     color: 'text-blue-400',    refLow: 95                   },
  '29463-7': { label: 'Peso',      unit: 'kg',     icon: <Scale className="w-4 h-4" />,        color: 'text-emerald-400'                               },
  '8302-2':  { label: 'Altura',    unit: 'cm',     icon: <Activity className="w-4 h-4" />,     color: 'text-purple-400'                               },
  // Blood pressure — uses component
  '55284-4': { label: 'PA',        unit: 'mmHg',   icon: <Activity className="w-4 h-4" />,     color: 'text-pink-400',    refHigh: 120                 },
  '8480-6':  { label: 'PAS',       unit: 'mmHg',   icon: <Activity className="w-4 h-4" />,     color: 'text-pink-400',    refHigh: 120                 },
  '8462-4':  { label: 'PAD',       unit: 'mmHg',   icon: <Activity className="w-4 h-4" />,     color: 'text-pink-300',    refHigh: 80                  },
};

function getLoincCode(obs: FHIRObservation): string | null {
  return obs.code?.coding?.find(c => c.system === 'http://loinc.org')?.code
    ?? obs.code?.coding?.[0]?.code
    ?? null;
}

function getValueLabel(obs: FHIRObservation): string {
  if (obs.valueQuantity?.value !== undefined) {
    return String(obs.valueQuantity.value);
  }
  // Blood pressure component
  const systolic = obs.component?.find(c =>
    c.code?.coding?.some(cd => cd.code === '8480-6'),
  )?.valueQuantity;
  const diastolic = obs.component?.find(c =>
    c.code?.coding?.some(cd => cd.code === '8462-4'),
  )?.valueQuantity;
  if (systolic && diastolic) {
    return `${systolic.value}/${diastolic.value}`;
  }
  return obs.valueString ?? '—';
}

function isOutOfRange(obs: FHIRObservation, config: typeof VITAL_CODES[string]): boolean {
  const v = obs.valueQuantity?.value;
  if (v === undefined) return false;
  if (config.refLow !== undefined && v < config.refLow) return true;
  if (config.refHigh !== undefined && v > config.refHigh) return true;
  return false;
}

interface VitalSignsGridProps {
  observations: FHIRObservation[];
  className?: string;
}

export function VitalSignsGrid({ observations, className }: VitalSignsGridProps) {
  // Pick the latest observation per code
  const latestByCode = new Map<string, FHIRObservation>();
  for (const obs of observations) {
    const code = getLoincCode(obs);
    if (!code) continue;
    const existing = latestByCode.get(code);
    if (!existing || (obs.effectiveDateTime ?? '') > (existing.effectiveDateTime ?? '')) {
      latestByCode.set(code, obs);
    }
  }

  const vitals = Array.from(latestByCode.entries())
    .map(([code, obs]) => ({ code, obs, config: VITAL_CODES[code] }))
    .filter(v => v.config);

  if (vitals.length === 0) {
    return (
      <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl p-6 text-center ${className ?? ''}`}>
        <Activity className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-500">Nenhum sinal vital disponível.</p>
      </div>
    );
  }

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      <div className="px-5 py-3.5 border-b border-slate-700/50">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-pink-400" />
          Sinais Vitais
        </h3>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-slate-700/30">
        {vitals.map(({ code, obs, config }) => {
          const outOfRange = isOutOfRange(obs, config);
          return (
            <div key={code} className="bg-slate-800/50 p-4">
              <div className={`flex items-center gap-2 mb-2 ${config.color}`}>
                {config.icon}
                <span className="text-xs font-medium text-slate-400">{config.label}</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className={`text-2xl font-bold font-mono ${outOfRange ? 'text-red-400' : 'text-white'}`}>
                  {getValueLabel(obs)}
                </span>
                <span className="text-xs text-slate-500">{config.unit}</span>
              </div>
              {outOfRange && (
                <p className="text-xs text-red-400 mt-1">Fora do normal</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VitalSignsGrid;
