/**
 * ResourceTable — tabela genérica de recursos FHIR com busca e paginação.
 * Renderiza qualquer tipo de recurso com colunas configuráveis.
 */

import { useState } from 'react';
import { Search, ChevronLeft, ChevronRight, ExternalLink, Database } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { FHIRResource, fhirDate, fhirDateTime } from './types';

export interface ResourceColumn<T = FHIRResource> {
  key: string;
  header: string;
  render: (resource: T) => React.ReactNode;
  width?: string;
}

interface ResourceTableProps<T extends FHIRResource = FHIRResource> {
  resources: T[];
  columns: ResourceColumn<T>[];
  /** Number of items per page (default: 10) */
  pageSize?: number;
  /** Called when user clicks a row */
  onRowClick?: (resource: T) => void;
  /** Filter function for client-side search */
  filterFn?: (resource: T, query: string) => boolean;
  title?: string;
  isLoading?: boolean;
  className?: string;
}

export function ResourceTable<T extends FHIRResource = FHIRResource>({
  resources,
  columns,
  pageSize = 10,
  onRowClick,
  filterFn,
  title,
  isLoading,
  className,
}: ResourceTableProps<T>) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);

  const filtered = filterFn && query
    ? resources.filter(r => filterFn(r, query.toLowerCase()))
    : resources;

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages - 1);
  const pageItems = filtered.slice(currentPage * pageSize, (currentPage + 1) * pageSize);

  const handleSearch = (q: string) => {
    setQuery(q);
    setPage(0);
  };

  return (
    <div className={`bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden ${className ?? ''}`}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-700/50 flex items-center gap-3">
        {title && (
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-slate-400" />
            {title}
          </h3>
        )}
        <span className="text-xs text-slate-500 ml-auto">
          {filtered.length} recurso{filtered.length !== 1 ? 's' : ''}
        </span>
        {filterFn && (
          <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-1.5">
            <Search className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <input
              type="text"
              placeholder="Buscar..."
              value={query}
              onChange={e => handleSearch(e.target.value)}
              className="bg-transparent text-sm text-white placeholder-slate-600 outline-none w-32"
            />
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              {columns.map(col => (
                <th
                  key={col.key}
                  style={col.width ? { width: col.width } : undefined}
                  className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide"
                >
                  {col.header}
                </th>
              ))}
              {onRowClick && <th className="w-10" />}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length + (onRowClick ? 1 : 0)} className="py-10 text-center text-slate-500">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 rounded-full border-2 border-slate-600 border-t-blue-400 animate-spin" />
                    Carregando...
                  </div>
                </td>
              </tr>
            ) : pageItems.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (onRowClick ? 1 : 0)} className="py-10 text-center text-slate-500">
                  Nenhum recurso encontrado.
                </td>
              </tr>
            ) : (
              pageItems.map((resource, idx) => (
                <tr
                  key={(resource as any).id ?? idx}
                  onClick={() => onRowClick?.(resource)}
                  className={`transition-colors ${onRowClick ? 'cursor-pointer hover:bg-slate-700/20' : ''}`}
                >
                  {columns.map(col => (
                    <td key={col.key} className="px-5 py-3 text-slate-200">
                      {col.render(resource)}
                    </td>
                  ))}
                  {onRowClick && (
                    <td className="pr-4 text-slate-600">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-5 py-3 border-t border-slate-700/50 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Página {currentPage + 1} de {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <PagButton
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={currentPage === 0}
              icon={<ChevronLeft className="w-4 h-4" />}
            />
            <PagButton
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1}
              icon={<ChevronRight className="w-4 h-4" />}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function PagButton({
  onClick,
  disabled,
  icon,
}: {
  onClick: () => void;
  disabled: boolean;
  icon: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-1.5 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700 text-slate-400"
    >
      {icon}
    </button>
  );
}

export default ResourceTable;
