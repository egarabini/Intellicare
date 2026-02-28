/**
 * SearchControl — barra de busca FHIR com filtros configuráveis.
 * Gera os parâmetros de busca para envio ao /api/v2/fhir/:resourceType.
 */

import { useState } from 'react';
import { Search, Filter, X, ChevronDown } from 'lucide-react';

export interface SearchFilter {
  key: string;
  label: string;
  placeholder?: string;
  type?: 'text' | 'select' | 'date';
  options?: Array<{ value: string; label: string }>;
}

export interface SearchParams {
  _count?: number;
  _offset?: number;
  [key: string]: string | number | undefined;
}

interface SearchControlProps {
  /** FHIR resource type being searched */
  resourceType?: string;
  /** Available filter fields */
  filters?: SearchFilter[];
  /** Called when user submits search (button or Enter) */
  onSearch: (params: SearchParams) => void;
  /** Default _count value */
  defaultCount?: number;
  className?: string;
}

export function SearchControl({
  resourceType,
  filters = [],
  onSearch,
  defaultCount = 20,
  className,
}: SearchControlProps) {
  const [query, setQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [showFilters, setShowFilters] = useState(false);
  const [count, setCount] = useState(defaultCount);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const params: SearchParams = { _count: count };
    if (query) params._text = query;  // free text
    Object.entries(activeFilters).forEach(([k, v]) => {
      if (v) params[k] = v;
    });
    onSearch(params);
  };

  const setFilter = (key: string, value: string) => {
    setActiveFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilter = (key: string) => {
    setActiveFilters(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const clearAll = () => {
    setQuery('');
    setActiveFilters({});
    onSearch({ _count: count });
  };

  const activeCount = Object.values(activeFilters).filter(Boolean).length;

  return (
    <div className={`space-y-3 ${className ?? ''}`}>
      {/* Main search bar */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-2.5 focus-within:border-blue-500/50 transition-colors">
          <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <input
            type="text"
            placeholder={`Buscar ${resourceType ?? 'recursos'}...`}
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-600 outline-none"
          />
          {query && (
            <button type="button" onClick={() => setQuery('')} className="text-slate-600 hover:text-slate-400">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter toggle */}
        {filters.length > 0 && (
          <button
            type="button"
            onClick={() => setShowFilters(s => !s)}
            className={`flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border text-sm font-medium transition-colors ${
              showFilters || activeCount > 0
                ? 'bg-blue-600/20 border-blue-500/50 text-blue-400'
                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
            }`}
          >
            <Filter className="w-4 h-4" />
            {activeCount > 0 && (
              <span className="w-5 h-5 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
                {activeCount}
              </span>
            )}
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        )}

        {/* Search button */}
        <button
          type="submit"
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors"
        >
          Buscar
        </button>
      </form>

      {/* Filter panel */}
      {showFilters && filters.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {filters.map(filter => (
              <div key={filter.key}>
                <label className="text-xs text-slate-500 block mb-1">{filter.label}</label>
                {filter.type === 'select' && filter.options ? (
                  <div className="relative">
                    <select
                      value={activeFilters[filter.key] ?? ''}
                      onChange={e => setFilter(filter.key, e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white outline-none appearance-none"
                    >
                      <option value="">Todos</option>
                      {filter.options.map(o => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div className="relative">
                    <input
                      type={filter.type === 'date' ? 'date' : 'text'}
                      placeholder={filter.placeholder}
                      value={activeFilters[filter.key] ?? ''}
                      onChange={e => setFilter(filter.key, e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-600 outline-none focus:border-blue-500/50"
                    />
                    {activeFilters[filter.key] && (
                      <button
                        type="button"
                        onClick={() => clearFilter(filter.key)}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Count selector */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-700/50">
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-500">Resultados:</label>
              <select
                value={count}
                onChange={e => setCount(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white outline-none"
              >
                {[10, 20, 50, 100].map(n => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            {activeCount > 0 && (
              <button
                type="button"
                onClick={clearAll}
                className="text-xs text-slate-500 hover:text-slate-300 underline"
              >
                Limpar filtros
              </button>
            )}
          </div>
        </div>
      )}

      {/* Active filter chips */}
      {activeCount > 0 && !showFilters && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(activeFilters)
            .filter(([, v]) => v)
            .map(([key, value]) => {
              const filterDef = filters.find(f => f.key === key);
              const displayValue = filterDef?.type === 'select'
                ? filterDef.options?.find(o => o.value === value)?.label ?? value
                : value;
              return (
                <span
                  key={key}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400"
                >
                  {filterDef?.label ?? key}: {displayValue}
                  <button onClick={() => clearFilter(key)} className="hover:text-blue-200">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              );
            })}
        </div>
      )}
    </div>
  );
}

export default SearchControl;
