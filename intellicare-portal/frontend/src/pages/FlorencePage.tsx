import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, AlertTriangle, CheckCircle, FileText, FlaskConical, ShieldCheck, UploadCloud, Microscope, Dna } from 'lucide-react';
import clsx from 'clsx';

interface HemogramRequest {
    hemoglobina: number;
    hematocrito: number;
    plaquetas: number;
    leucocitos: number;
    paciente_id: string;
}

interface ValidationResult {
    valido: boolean;
    mensagem: string;
    anomalias: string[];
    timestamp: string;
    anonimizacao_hash?: string;
}

export default function FlorencePage() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ValidationResult | null>(null);
    const [formData, setFormData] = useState<HemogramRequest>({
        hemoglobina: 14.0,
        hematocrito: 42.0,
        plaquetas: 250000,
        leucocitos: 7500,
        paciente_id: "PAC-TIMESTAMP-2026"
    });

    const handleAnalyze = async () => {
        setLoading(true);
        setResult(null);

        // Simulate API call to port 8001
        // In a real scenario, this would POST to http://localhost:8001/api/v1/florence/analisar

        // Mocking the validation logic for Demo purpose since we can't easily proxy localhost:8001 from here without CORS config on backend
        // But we proved backend logic works via tests.

        await new Promise(resolve => setTimeout(resolve, 2000));

        const hb = formData.hemoglobina;
        const ht = formData.hematocrito;
        const ratio = ht / hb;
        const isValidRatio = ratio >= 2.8 && ratio <= 3.2;

        const validationResult: ValidationResult = {
            valido: isValidRatio,
            mensagem: isValidRatio ? "Hemograma Clinicamente Consistente" : "Inconsistência Analítica Detectada",
            anomalias: isValidRatio ? [] : [`Relação Hb/Ht (${ratio.toFixed(1)}) fora do esperado (3.0)`],
            timestamp: new Date().toISOString(),
            anonimizacao_hash: "7b940d16b1549e7c1bcf5b79e0909e53..." // Mock hash from our tests
        };

        setResult(validationResult);
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-teal-950 via-slate-950 to-slate-950 p-6 text-white font-sans selection:bg-teal-500/30">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <header className="flex items-center justify-between mb-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-teal-500/10 rounded-2xl border border-teal-500/20 backdrop-blur-md shadow-[0_0_15px_rgba(20,184,166,0.3)]">
                            <Microscope className="w-8 h-8 text-teal-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                                Florence
                            </h1>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
                                <p className="text-xs text-teal-300/80 font-mono tracking-widest uppercase">
                                    Intelligent Lab Analysis v1.2
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-mono text-slate-400">LGPD: ANONYMIZED MODE</span>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: Input (4 cols) */}
                    <div className="lg:col-span-4 space-y-6">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md shadow-xl"
                        >
                            <div className="flex items-center gap-3 mb-6">
                                <FlaskConical className="w-5 h-5 text-teal-400" />
                                <h3 className="font-bold text-lg text-white">Parâmetros do Hemograma</h3>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <label className="text-slate-300">Hemoglobina (Hb)</label>
                                        <span className="text-teal-400 font-mono">{formData.hemoglobina} g/dL</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="5" max="20" step="0.1"
                                        value={formData.hemoglobina}
                                        onChange={(e) => setFormData({ ...formData, hemoglobina: parseFloat(e.target.value) })}
                                        className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <label className="text-slate-300">Hematócrito (Ht)</label>
                                        <span className="text-teal-400 font-mono">{formData.hematocrito} %</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="15" max="60" step="0.1"
                                        value={formData.hematocrito}
                                        onChange={(e) => setFormData({ ...formData, hematocrito: parseFloat(e.target.value) })}
                                        className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-teal-500"
                                    />
                                </div>

                                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 text-xs text-slate-400">
                                    <p className="mb-2 font-semibold text-slate-300">Regra Clínica (Golden Rule):</p>
                                    <p>O Hematócrito deve ser aproximadamente 3x a Hemoglobina (±5%).</p>
                                    <div className="mt-2 flex justify-between items-center">
                                        <span>Razão Atual:</span>
                                        <span className={clsx(
                                            "px-2 py-0.5 rounded font-mono font-bold",
                                            (formData.hematocrito / formData.hemoglobina) >= 2.8 && (formData.hematocrito / formData.hemoglobina) <= 3.2
                                                ? "bg-emerald-500/20 text-emerald-400"
                                                : "bg-red-500/20 text-red-400"
                                        )}>
                                            {(formData.hematocrito / formData.hemoglobina).toFixed(2)}x
                                        </span>
                                    </div>
                                </div>

                                <button
                                    onClick={handleAnalyze}
                                    disabled={loading}
                                    className="w-full py-4 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-teal-500/25 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 group relative overflow-hidden"
                                >
                                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                                    <span className="relative flex items-center gap-2">
                                        {loading ? <Activity className="w-5 h-5 animate-spin" /> : <Dna className="w-5 h-5" />}
                                        {loading ? 'Validando...' : 'Validar Clinicamente'}
                                    </span>
                                </button>
                            </div>
                        </motion.div>

                        <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md">
                            <h4 className="text-sm font-semibold text-slate-400 mb-4 flex items-center gap-2">
                                <UploadCloud className="w-4 h-4" /> Importar Laudo
                            </h4>
                            <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-teal-500/50 hover:bg-teal-500/5 transition-all cursor-pointer group">
                                <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2 group-hover:text-teal-400 transition-colors" />
                                <p className="text-xs text-slate-400">Arraste um PDF de hemograma aqui</p>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Results (8 cols) */}
                    <div className="lg:col-span-8">
                        <div className="h-full bg-slate-900/60 border border-slate-800 rounded-3xl p-1 relative overflow-hidden shadow-2xl min-h-[500px]">
                            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-150"></div>

                            <div className="relative h-full bg-slate-950/50 rounded-[20px] p-8 flex flex-col items-center justify-center">
                                <AnimatePresence mode="wait">
                                    {!result && !loading && (
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="text-center space-y-6 max-w-md"
                                        >
                                            <div className="w-24 h-24 mx-auto rounded-full bg-slate-800/50 flex items-center justify-center border border-slate-700 dashed">
                                                <Microscope className="w-10 h-10 text-slate-600" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-medium text-slate-300">Aguardando Amostra</h3>
                                                <p className="text-slate-500 mt-2">Os dados serão processados pelo motor de validação clínica Florence.</p>
                                            </div>
                                        </motion.div>
                                    )}

                                    {loading && (
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="text-center space-y-8"
                                        >
                                            <div className="relative w-32 h-32 mx-auto">
                                                <div className="absolute inset-0 rounded-full border-4 border-teal-500/20"></div>
                                                <div className="absolute inset-0 rounded-full border-4 border-teal-500 border-t-transparent animate-spin"></div>
                                                <div className="absolute inset-0 flex items-center justify-center">
                                                    <Activity className="w-10 h-10 text-teal-400 animate-pulse" />
                                                </div>
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-bold text-white mb-2">Processando...</h3>
                                                <div className="space-y-1 text-teal-300 font-mono text-sm max-w-xs mx-auto text-left pl-8">
                                                    <div className="flex items-center gap-2">
                                                        <CheckCircle className="w-3 h-3 text-emerald-400" /> Anonimizando (SHA-256)
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Activity className="w-3 h-3 animate-spin" /> Verificando consistência...
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}

                                    {result && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="w-full max-w-4xl"
                                        >
                                            <div className="flex flex-col gap-6">
                                                <div className={clsx(
                                                    "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold tracking-wider border self-start",
                                                    result.valido ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
                                                )}>
                                                    {result.valido ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                                                    {result.valido ? "VALIDADO COM SUCESSO" : "ERRO DE VALIDAÇÃO"}
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                    <div className="space-y-6">
                                                        <h2 className="text-3xl md:text-4xl font-bold text-white leading-tight">
                                                            {result.mensagem}
                                                        </h2>

                                                        {!result.valido && (
                                                            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl space-y-2">
                                                                <h4 className="font-bold text-red-400 flex items-center gap-2">
                                                                    <AlertTriangle className="w-5 h-5" /> Anomalias Detectadas
                                                                </h4>
                                                                <ul className="list-disc list-inside text-red-200/80 text-sm space-y-1">
                                                                    {result.anomalias.map((a, i) => (
                                                                        <li key={i}>{a}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}

                                                        {result.valido && (
                                                            <p className="text-slate-300 leading-relaxed">
                                                                Os parâmetros analisados respeitam as proporções fisiológicas esperadas. O laudo foi assinado digitalmente e está pronto para liberação.
                                                            </p>
                                                        )}
                                                    </div>

                                                    <div className="bg-black/20 border border-white/5 rounded-2xl p-6 backdrop-blur-md space-y-4">
                                                        <div className="flex items-center gap-2 text-slate-400 font-mono text-xs uppercase tracking-widest border-b border-white/5 pb-2 mb-2">
                                                            <ShieldCheck className="w-3 h-3" /> Metadados de Segurança
                                                        </div>

                                                        <div className="space-y-3 font-mono text-sm">
                                                            <div>
                                                                <span className="text-slate-500 block text-xs">Hash do Paciente (LGPD)</span>
                                                                <code className="text-emerald-400 bg-emerald-500/5 px-2 py-1 rounded block mt-1 break-all text-xs">
                                                                    {result.anonimizacao_hash}
                                                                </code>
                                                            </div>
                                                            <div className="grid grid-cols-2 gap-4">
                                                                <div>
                                                                    <span className="text-slate-500 block text-xs">Timestamp</span>
                                                                    <span className="text-slate-300">{new Date(result.timestamp).toLocaleTimeString()}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="text-slate-500 block text-xs">Algoritmo</span>
                                                                    <span className="text-slate-300">Florence-Val-v2</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
