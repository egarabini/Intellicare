import { Settings as SettingsIcon } from 'lucide-react';
import Header from '@components/layout/Header';

export default function SettingsPage() {
  return (
    <div>
      <Header title="Configurações" subtitle="Preferências do dashboard de saúde" />
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-8">
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <SettingsIcon className="h-12 w-12 mb-4" />
          <p className="text-lg font-medium">Em breve</p>
          <p className="text-sm mt-1">
            Configurações de indicadores, alertas e integrações serão disponibilizadas aqui.
          </p>
        </div>
      </div>
    </div>
  );
}
