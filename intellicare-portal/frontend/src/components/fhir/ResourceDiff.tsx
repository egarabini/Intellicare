/**
 * ResourceDiff — compara duas versões de um recurso FHIR (JSON diff visual).
 */

import { GitCompare, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { FHIRResource, fhirDateTime } from './types';

type DiffEntry =
  | { type: 'unchanged'; path: string; value: unknown }
  | { type: 'added'; path: string; newValue: unknown }
  | { type: 'removed'; path: string; oldValue: unknown }
  | { type: 'changed'; path: string; oldValue: unknown; newValue: unknown };

function diffObjects(
  oldObj: Record<string, unknown>,
  newObj: Record<string, unknown>,
  prefix = '',
): DiffEntry[] {
  const allKeys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)]);
  const entries: DiffEntry[] = [];

  for (const key of allKeys) {
    const path = prefix ? `${prefix}.${key}` : key;
    const hasOld = key in oldObj;
    const hasNew = key in newObj;

    if (!hasOld) {
      entries.push({ type: 'added', path, newValue: newObj[key] });
    } else if (!hasNew) {
      entries.push({ type: 'removed', path, oldValue: oldObj[key] });
    } else if (
      typeof oldObj[key] === 'object' && oldObj[key] !== null &&
      typeof newObj[key] === 'object' && newObj[key] !== null &&
      !Array.isArray(oldObj[key]) && !Array.isArray(newObj[key])
    ) {
      entries.push(...diffObjects(
        oldObj[key] as Record<string, unknown>,
        newObj[key] as Record<string, unknown>,
        path,
      ));
    } else {
      const oldStr = JSON.stringify(oldObj[key]);
      const newStr = JSON.stringify(newObj[key]);
      if (oldStr !== newStr) {
        entries.push({ type: 'changed', path, oldValue: oldObj[key], newValue: newObj[key] });
      } else {
        entries.push({ type: 'unchanged', path, value: oldObj[key] });
      }
    }
  }
  return entries;
}

function displayValue(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'string') return v;
  return JSON.stringify(v);
}

interface ResourceDiffProps {
  /** Previous version */
  oldResource: FHIRResource;
  /** Current version */
  newResource: FHIRResource;
  /** Whether to show unchanged fields (default: false) */
  showUnchanged?: boolean;
  className?: string;
}

export function ResourceDiff({
  oldResource,
  newResource,
  showUnchanged = false,
  className,
}: ResourceDiffProps) {
  const [expanded, setExpanded] = useState(true);

  const diffs = diffObjects(
    oldResource as Record<string, unknown>,
    newResource as Record<string, unknown>,
  );

  const changed = diffs.filter(d => d.type !== 'unchanged');
  const unchanged = diffs.filter(d => d.type === 'unchanged');
  const oldVersion = (oldResource as any).meta?.versionId;
  const newVersion = (newResource as any).meta?.versionId;
  const oldDate = (oldResource as any).meta?.lastUpdated;
  const newDate = (newResource as any).meta?.lastUpdated;

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-700/50 flex items-center gap-3">
        <GitCompare className="w-4 h-4 text-slate-400" />
        <span className="text-sm font-semibold text-white">Comparação de Versões</span>
        <div className="ml-auto flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-red-500/20 border border-red-500/30 inline-block" />
            v{oldVersion ?? '?'} {oldDate ? `— ${fhirDateTime(oldDate)}` : ''}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-emerald-500/20 border border-emerald-500/30 inline-block" />
            v{newVersion ?? '?'} {newDate ? `— ${fhirDateTime(newDate)}` : ''}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-5 py-3 border-b border-slate-700/30 flex items-center gap-4 text-xs">
        <span className="text-emerald-400">+{diffs.filter(d => d.type === 'added').length} adicionado(s)</span>
        <span className="text-red-400">-{diffs.filter(d => d.type === 'removed').length} removido(s)</span>
        <span className="text-yellow-400">~{diffs.filter(d => d.type === 'changed').length} alterado(s)</span>
      </div>

      {/* Changes */}
      <div className="divide-y divide-slate-700/20">
        {changed.map((diff, idx) => (
          <DiffRow key={idx} entry={diff} />
        ))}

        {changed.length === 0 && (
          <div className="px-5 py-6 text-center text-sm text-slate-500">
            Nenhuma diferença detectada entre as versões.
          </div>
        )}
      </div>

      {/* Unchanged (collapsible) */}
      {showUnchanged && unchanged.length > 0 && (
        <div className="border-t border-slate-700/30">
          <button
            onClick={() => setExpanded(s => !s)}
            className="w-full flex items-center gap-2 px-5 py-3 text-xs text-slate-500 hover:text-slate-300"
          >
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            {unchanged.length} campo(s) sem alteração
          </button>
          {expanded && unchanged.map((diff, idx) => (
            <DiffRow key={idx} entry={diff} />
          ))}
        </div>
      )}
    </div>
  );
}

function DiffRow({ entry }: { entry: DiffEntry }) {
  const rowClass = {
    added:     'bg-emerald-500/5 border-l-2 border-emerald-500/40',
    removed:   'bg-red-500/5 border-l-2 border-red-500/40',
    changed:   'bg-yellow-500/5 border-l-2 border-yellow-500/40',
    unchanged: '',
  }[entry.type];

  return (
    <div className={`px-5 py-2.5 flex items-start gap-4 ${rowClass}`}>
      <span className="text-xs font-mono text-slate-500 w-52 flex-shrink-0 truncate pt-0.5">
        {entry.path}
      </span>
      <div className="flex-1 flex items-start gap-3 text-xs font-mono">
        {entry.type === 'added' && (
          <span className="text-emerald-400">+ {displayValue(entry.newValue)}</span>
        )}
        {entry.type === 'removed' && (
          <span className="text-red-400">- {displayValue(entry.oldValue)}</span>
        )}
        {entry.type === 'changed' && (
          <>
            <span className="text-red-400 line-through opacity-60">{displayValue(entry.oldValue)}</span>
            <span className="text-slate-500">→</span>
            <span className="text-emerald-400">{displayValue(entry.newValue)}</span>
          </>
        )}
        {entry.type === 'unchanged' && (
          <span className="text-slate-600">{displayValue(entry.value)}</span>
        )}
      </div>
    </div>
  );
}

export default ResourceDiff;
