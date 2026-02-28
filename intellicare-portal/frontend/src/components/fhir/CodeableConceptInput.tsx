/**
 * CodeableConceptInput — input de códigos médicos com busca e autocomplete.
 * Suporta CID-10, LOINC, SNOMED CT e terminologias locais.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, X, Tag } from 'lucide-react';
import { Coding, CodeableConcept } from './types';

export interface CodeOption {
  system: string;
  code: string;
  display: string;
}

interface CodeableConceptInputProps {
  value?: CodeableConcept;
  onChange: (value: CodeableConcept | null) => void;
  /** Custom search function — if provided, replaces built-in static options */
  onSearch?: (query: string) => Promise<CodeOption[]>;
  /** Static options to search in (used when onSearch is not provided) */
  options?: CodeOption[];
  placeholder?: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  /** Show system badge on selected value */
  showSystem?: boolean;
  className?: string;
}

const SYSTEM_SHORT: Record<string, string> = {
  'http://hl7.org/fhir/sid/icd-10':          'CID-10',
  'http://loinc.org':                         'LOINC',
  'http://snomed.info/sct':                   'SNOMED',
  'http://www.ans.gov.br/':                   'TUSS',
  'http://terminology.hl7.org/CodeSystem/v3-ActCode': 'HL7',
};

function systemLabel(system?: string): string {
  if (!system) return '';
  return SYSTEM_SHORT[system] ?? system.split('/').pop() ?? system;
}

export function CodeableConceptInput({
  value,
  onChange,
  onSearch,
  options = [],
  placeholder = 'Buscar código...',
  label,
  required,
  disabled,
  showSystem = true,
  className,
}: CodeableConceptInputProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CodeOption[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedCoding = value?.coding?.[0];

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return; }
    setIsSearching(true);
    try {
      if (onSearch) {
        const res = await onSearch(q);
        setResults(res.slice(0, 10));
      } else {
        const q_lower = q.toLowerCase();
        setResults(
          options
            .filter(o =>
              o.code.toLowerCase().includes(q_lower) ||
              o.display.toLowerCase().includes(q_lower),
            )
            .slice(0, 10),
        );
      }
    } finally {
      setIsSearching(false);
    }
  }, [onSearch, options]);

  useEffect(() => {
    const timer = setTimeout(() => search(query), 200);
    return () => clearTimeout(timer);
  }, [query, search]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (!dropdownRef.current?.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const select = (opt: CodeOption) => {
    onChange({
      coding: [{ system: opt.system, code: opt.code, display: opt.display }],
      text: opt.display,
    });
    setQuery('');
    setIsOpen(false);
  };

  const clear = () => {
    onChange(null);
    setQuery('');
    inputRef.current?.focus();
  };

  return (
    <div className={`space-y-1 ${className ?? ''}`} ref={dropdownRef}>
      {label && (
        <label className="text-xs font-medium text-slate-400">
          {label}
          {required && <span className="text-red-400 ml-0.5">*</span>}
        </label>
      )}

      {/* Selected value display */}
      {selectedCoding ? (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-slate-800 border border-slate-600">
          <Tag className="w-4 h-4 text-blue-400 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="text-sm text-white font-medium">{selectedCoding.display ?? selectedCoding.code}</span>
            {showSystem && selectedCoding.system && (
              <span className="ml-2 text-xs text-slate-500 font-mono">
                [{systemLabel(selectedCoding.system)}] {selectedCoding.code}
              </span>
            )}
          </div>
          {!disabled && (
            <button onClick={clear} className="text-slate-500 hover:text-slate-300 flex-shrink-0">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      ) : (
        // Search input
        <div className="relative">
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700 focus-within:border-blue-500/50 transition-colors">
            <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => { setQuery(e.target.value); setIsOpen(true); }}
              onFocus={() => { if (query) setIsOpen(true); }}
              placeholder={placeholder}
              disabled={disabled}
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-600 outline-none disabled:opacity-50"
            />
            {isSearching && (
              <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-600 border-t-blue-400 animate-spin flex-shrink-0" />
            )}
          </div>

          {/* Dropdown */}
          {isOpen && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-slate-800 border border-slate-600 rounded-xl shadow-xl overflow-hidden">
              <ul className="max-h-52 overflow-y-auto divide-y divide-slate-700/50">
                {results.map((opt, idx) => (
                  <li key={`${opt.system}|${opt.code}`}>
                    <button
                      type="button"
                      onClick={() => select(opt)}
                      className="w-full flex items-start gap-3 px-4 py-2.5 text-left hover:bg-slate-700 transition-colors"
                    >
                      <span className="flex-shrink-0 mt-0.5 px-1.5 py-0.5 rounded text-xs font-mono bg-slate-700 text-slate-400">
                        {systemLabel(opt.system)}
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm text-white">{opt.display}</p>
                        <p className="text-xs text-slate-500 font-mono">{opt.code}</p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CodeableConceptInput;
