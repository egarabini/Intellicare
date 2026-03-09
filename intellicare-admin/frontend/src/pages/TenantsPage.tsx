import { Building2, Users, Globe } from 'lucide-react';
import Header from '@components/layout/Header';

const MOCK_TENANTS = [
  { id: 'sms-bsb', name: 'SMS Brasília', patients: 12450, controlRate: 58.3, status: 'active' },
  { id: 'sms-mc', name: 'SMS Montes Claros', patients: 6230, controlRate: 52.1, status: 'active' },
  { id: 'sms-sp', name: 'SMS São Paulo', patients: 45800, controlRate: 61.7, status: 'active' },
  { id: 'sms-rj', name: 'SMS Rio de Janeiro', patients: 38200, controlRate: 55.9, status: 'active' },
  { id: 'sms-bh', name: 'SMS Belo Horizonte', patients: 22100, controlRate: 49.8, status: 'trial' },
];

export default function TenantsPage() {
  return (
    <div>
      <Header title="Tenants / Secretarias" subtitle="Visão cross-tenant dos programas de saúde" />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="flex items-center gap-4 p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center">
            <Building2 className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">{MOCK_TENANTS.length}</p>
            <p className="text-xs text-slate-500">Secretarias Ativas</p>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
            <Users className="h-6 w-6 text-emerald-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">
              {MOCK_TENANTS.reduce((sum, t) => sum + t.patients, 0).toLocaleString('pt-BR')}
            </p>
            <p className="text-xs text-slate-500">Pacientes Totais</p>
          </div>
        </div>
        <div className="flex items-center gap-4 p-5 bg-white rounded-xl border border-slate-100 shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
            <Globe className="h-6 w-6 text-amber-600" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-800">
              {(MOCK_TENANTS.reduce((sum, t) => sum + t.controlRate, 0) / MOCK_TENANTS.length).toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500">Taxa de Controle Média</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50">
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Secretaria</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Pacientes</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Taxa de Controle</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="text-center px-5 py-3 text-xs font-semibold text-slate-500 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {MOCK_TENANTS.map((tenant) => (
              <tr key={tenant.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-5 py-4 font-medium text-slate-700">{tenant.name}</td>
                <td className="px-5 py-4 text-slate-600">{tenant.patients.toLocaleString('pt-BR')}</td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${tenant.controlRate}%`,
                          backgroundColor: tenant.controlRate >= 60 ? '#22c55e' : tenant.controlRate >= 45 ? '#f59e0b' : '#ef4444',
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">{tenant.controlRate}%</span>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${tenant.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                    {tenant.status === 'active' ? 'Ativo' : 'Trial'}
                  </span>
                </td>
                <td className="px-5 py-4 text-center">
                  <button className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                    Ver Dashboard
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
