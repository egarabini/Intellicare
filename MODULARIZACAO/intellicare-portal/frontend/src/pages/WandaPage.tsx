import { FileText, ClipboardList, AlertCircle, CheckCircle, Activity } from 'lucide-react';

export default function WandaPage() {
    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans p-6">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <div className="p-3 bg-indigo-600/20 rounded-xl border border-indigo-500/30">
                        <FileText className="w-8 h-8 text-indigo-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">WANDA</h1>
                        <p className="text-slate-400">Sistematização da Assistência de Enfermagem (SAE)</p>
                    </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur-sm text-center">
                    <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                        <ClipboardList className="w-10 h-10 text-indigo-400" />
                    </div>

                    <h2 className="text-2xl font-bold text-white mb-4">Módulo em Desenvolvimento</h2>
                    <p className="text-slate-400 max-w-lg mx-auto mb-8">
                        A Agente Wanda está sendo treinada para automatizar a <strong>Coleta de Dados</strong>,
                        o <strong>Diagnóstico de Enfermagem (NANDA-I)</strong> e o <strong>Planejamento (NIC/NOC)</strong>.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto">
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <Activity className="w-6 h-6 text-indigo-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Histórico</h3>
                            <p className="text-xs text-slate-500 mt-1">Anamnese e Exame Físico estruturados.</p>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <AlertCircle className="w-6 h-6 text-indigo-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Diagnósticos</h3>
                            <p className="text-xs text-slate-500 mt-1">Identificação automática de riscos.</p>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <CheckCircle className="w-6 h-6 text-indigo-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Prescrições</h3>
                            <p className="text-xs text-slate-500 mt-1">Planos de cuidado sugeridos.</p>
                        </div>
                    </div>

                    <div className="mt-8">
                        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium">
                            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                            Aguarde novidades na Versão 2.0
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
