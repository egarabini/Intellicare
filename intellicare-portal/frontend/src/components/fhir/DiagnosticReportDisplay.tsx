/**
 * DiagnosticReportDisplay — exibe um DiagnosticReport FHIR com resultado,
 * conclusão e observações relacionadas.
 */

import { FileText, Calendar, User, ExternalLink } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import {
  FHIRDiagnosticReport,
  FHIRObservation,
  codingDisplay,
  fhirDate,
  fhirDateTime,
} from './types';

interface DiagnosticReportDisplayProps {
  report: FHIRDiagnosticReport;
  /** Related Observation resources (resolved from report.result) */
  observations?: FHIRObservation[];
  className?: string;
}

export function DiagnosticReportDisplay({
  report,
  observations = [],
  className,
}: DiagnosticReportDisplayProps) {
  const category = report.category?.[0] ? codingDisplay(report.category[0]) : null;
  const dateLabel = report.effectiveDateTime
    ? fhirDateTime(report.effectiveDateTime)
    : report.issued
    ? fhirDateTime(report.issued)
    : '—';

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-700/50">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">
                {codingDisplay(report.code)}
              </h3>
              {category && (
                <p className="text-xs text-slate-500 mt-0.5">{category}</p>
              )}
            </div>
          </div>
          <StatusBadge status={report.status} />
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-4 mt-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            {dateLabel}
          </span>
          {report.performer?.[0]?.display && (
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5" />
              {report.performer[0].display}
            </span>
          )}
          {report.id && (
            <span className="font-mono text-slate-600">ID: {report.id}</span>
          )}
        </div>
      </div>

      {/* Observations */}
      {observations.length > 0 && (
        <div className="px-6 py-4 border-b border-slate-700/50">
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">Resultados</h4>
          <div className="space-y-2">
            {observations.map((obs, idx) => {
              const value = obs.valueQuantity
                ? `${obs.valueQuantity.value} ${obs.valueQuantity.unit ?? ''}`
                : obs.valueString
                ? obs.valueString
                : obs.valueCodeableConcept
                ? codingDisplay(obs.valueCodeableConcept)
                : null;

              const ref = obs.referenceRange?.[0];
              const refText = ref
                ? ref.text ?? [
                    ref.low ? `${ref.low.value} ${ref.low.unit ?? ''}` : null,
                    ref.high ? `${ref.high.value} ${ref.high.unit ?? ''}` : null,
                  ].filter(Boolean).join(' – ')
                : null;

              return (
                <div
                  key={obs.id ?? idx}
                  className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
                >
                  <span className="text-sm text-slate-300">{codingDisplay(obs.code)}</span>
                  <div className="flex items-center gap-3">
                    {refText && (
                      <span className="text-xs text-slate-600">Ref: {refText}</span>
                    )}
                    <span className="text-sm font-mono font-medium text-white">
                      {value ?? '—'}
                    </span>
                    <StatusBadge status={obs.status} size="sm" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Conclusion */}
      {report.conclusion && (
        <div className="px-6 py-4">
          <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Conclusão</h4>
          <p className="text-sm text-slate-200 leading-relaxed">{report.conclusion}</p>
          {report.conclusionCode?.map((cc, i) => (
            <span key={i} className="inline-block mt-2 mr-2 px-2 py-0.5 rounded-md bg-slate-700 text-xs text-slate-300">
              {codingDisplay(cc)}
            </span>
          ))}
        </div>
      )}

      {/* Presented form (PDF link) */}
      {report.presentedForm?.map((form, i) => (
        form.url && (
          <div key={i} className="px-6 pb-4">
            <a
              href={form.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300"
            >
              <ExternalLink className="w-3 h-3" />
              {form.title ?? 'Ver documento original'}
            </a>
          </div>
        )
      ))}
    </div>
  );
}

export default DiagnosticReportDisplay;
