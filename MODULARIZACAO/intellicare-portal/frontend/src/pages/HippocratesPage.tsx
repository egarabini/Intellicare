import { MessageSquare, Heart, ShieldCheck, Users, Lock } from 'lucide-react';

export default function HippocratesPage() {
    return (
        <div className="min-h-screen bg-slate-900 text-slate-200 font-sans p-6">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <div className="p-3 bg-sky-600/20 rounded-xl border border-sky-500/30">
                        <MessageSquare className="w-8 h-8 text-sky-400" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-white">HIPÓCRATES</h1>
                        <p className="text-slate-400">Comunicação e Ética Médica</p>
                    </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 backdrop-blur-sm text-center">
                    <div className="w-20 h-20 bg-sky-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Heart className="w-10 h-10 text-sky-400" />
                    </div>

                    <h2 className="text-2xl font-bold text-white mb-4">Módulo em Desenvolvimento</h2>
                    <p className="text-slate-400 max-w-lg mx-auto mb-8">
                        O Agente Hipócrates garantirá que toda comunicação seja
                        <strong> Clara, Ética e Segura</strong>, honrando o juramento de "Primeiro, não prejudicar" (Primum non nocere).
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto">
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <Users className="w-6 h-6 text-sky-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Diálogo</h3>
                            <p className="text-xs text-slate-500 mt-1">Interação humanizada entre médico e paciente.</p>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <ShieldCheck className="w-6 h-6 text-sky-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Ética</h3>
                            <p className="text-xs text-slate-500 mt-1">Validação de conduta e consentimento informado.</p>
                        </div>
                        <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                            <Lock className="w-6 h-6 text-sky-400 mb-2" />
                            <h3 className="font-bold text-white text-sm">Privacidade</h3>
                            <p className="text-xs text-slate-500 mt-1">Proteção de dados sensíveis na mensageria.</p>
                        </div>
                    </div>

                    <div className="mt-8">
                        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-300 text-sm font-medium">
                            <span className="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></span>
                            Aguarde novidades na Versão 2.0
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
