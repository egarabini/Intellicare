import { useState } from 'react';
import { Search, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import type { PatientRecord } from '@/types/index';
import { STATUS_LABELS, STATUS_COLORS } from '@config/diseases';
import { formatDate, maskCPF, cn } from '@utils/formatters';

interface PatientTableProps {
  patients: PatientRecord[];
  totalPatients: number;
  totalPages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  onSearch: (query: string) => void;
  onPatientClick?: (patient: PatientRecord) => void;
}

export default function PatientTable({
  patients,
  totalPatients,
  totalPages,
  currentPage,
  onPageChange,
  onSearch,
  onPatientClick,
}: PatientTableProps) {
  const [searchInput, setSearchInput] = useState('');

  const handleSearch = () => {
    onSearch(searchInput);
  };

  const statusBadge = (status: PatientRecord['status']) => {
    const color = STATUS_COLORS[status];
    const label = STATUS_LABELS[status];
    return (
      <span
        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
        style={{ backgroundColor: `${color}20`, color }}
      >
        <span className="w-1.5 h-1.5 rounded-full mr-1.5" style={{ backgroundColor: color }} />
        {label}
      </span>
    );
  };

  return (
    <div className="rounded-xl bg-white shadow-sm border border-slate-100">
      {/* Header + Search */}
      <div className="p-5 border-b border-slate-100">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-700">Pacientes</h3>
            <p className="text-xs text-slate-400 mt-0.5">{totalPatients} registros</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar por nome ou CPF..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-9 pr-4 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 w-64"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50">
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Paciente
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Idade
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Estágio
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Status
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Estabelecimento
              </th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Última Consulta
              </th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {patients.map((patient) => (
              <tr
                key={patient.id}
                className="hover:bg-slate-50/50 transition-colors cursor-pointer"
                onClick={() => onPatientClick?.(patient)}
              >
                <td className="px-5 py-3.5">
                  <div>
                    <p className="font-medium text-slate-700">{patient.name}</p>
                    <p className="text-xs text-slate-400">{maskCPF(patient.cpf)}</p>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-slate-600">
                  {patient.age} anos
                  <span className="text-slate-400 ml-1">({patient.gender})</span>
                </td>
                <td className="px-5 py-3.5">
                  <span className="font-medium text-slate-600">{patient.stage}</span>
                </td>
                <td className="px-5 py-3.5">{statusBadge(patient.status)}</td>
                <td className="px-5 py-3.5 text-slate-600 text-xs">{patient.establishment}</td>
                <td className="px-5 py-3.5 text-slate-600">{formatDate(patient.lastVisit)}</td>
                <td className="px-5 py-3.5 text-center">
                  <button
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-primary-600 transition-colors"
                    title="Ver detalhes"
                    onClick={(e) => {
                      e.stopPropagation();
                      onPatientClick?.(patient);
                    }}
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-5 py-3.5 border-t border-slate-100">
        <p className="text-xs text-slate-400">
          Página {currentPage} de {totalPages}
        </p>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className={cn(
              'p-1.5 rounded-lg transition-colors',
              currentPage <= 1
                ? 'text-slate-300 cursor-not-allowed'
                : 'text-slate-500 hover:bg-slate-100',
            )}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const page =
              totalPages <= 5
                ? i + 1
                : currentPage <= 3
                  ? i + 1
                  : currentPage >= totalPages - 2
                    ? totalPages - 4 + i
                    : currentPage - 2 + i;
            return (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={cn(
                  'w-8 h-8 text-xs font-medium rounded-lg transition-colors',
                  page === currentPage
                    ? 'bg-primary-600 text-white'
                    : 'text-slate-500 hover:bg-slate-100',
                )}
              >
                {page}
              </button>
            );
          })}
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className={cn(
              'p-1.5 rounded-lg transition-colors',
              currentPage >= totalPages
                ? 'text-slate-300 cursor-not-allowed'
                : 'text-slate-500 hover:bg-slate-100',
            )}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
