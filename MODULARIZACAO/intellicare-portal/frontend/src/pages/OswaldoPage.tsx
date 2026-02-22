import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, AlertTriangle, CheckCircle, Database, FileText, HeartPulse, Search, Server, Thermometer, History } from 'lucide-react';
import clsx from 'clsx';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface ExamRequest {
    paciente_cpf_hash: string;
    data_coleta: string;
    tipo_exame: string;
    valor: number;
    unidade: string;
    valor_referencia: string;
    laboratorio: string;
}

interface OswaldoResponse {
    sucesso: boolean;
    mensagem: string;
    condicao_id?: number;
    estadiamento_criado?: boolean;
    alerta_gerado?: boolean;
    alerta_id?: number;
    classificacao?: string;
    estagio?: string;
    cor?: string;
}

const mockHistoryData = [
    { date: 'Jan', value: 1.1 },
    { date: 'Fev', value: 1.2 },
    { date: 'Mar', value: 1.1 },
    { date: 'Abr', value: 1.3 },
    { date: 'Mai', value: 1.4 },
    { date: 'Jun', value: 1.5 },
];

export const OswaldoPage = () => {
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<OswaldoResponse | null>(null);
    const [creatinineValue, setCreatinineValue] = useState<string>('1.8');

    const addLog = (msg: string) => {
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
    };

    const processExam = async () => {
        setLoading(true);
        setResult(null);
        addLog('Iniciando processamento de exame Dr. Oswaldo...');

        const payload: ExamRequest = {
            paciente_cpf_hash: "mock_patient_123",
            data_coleta: new Date().toISOString(),
            tipo_exame: "creatinina",
            valor: parseFloat(creatinineValue),
            unidade: "mg/dL",
            valor_referencia: "0.7-1.3",
            laboratorio: "Demo Lab"
        };

        addLog(`Enviando POST /api/v1/oswaldo/exames/processar: ${JSON.stringify(payload)}`);

        try {
            const response = await fetch('http://localhost:8002/api/v1/oswaldo/exames/processar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                addLog(`Resposta Backend 200 OK: ${JSON.stringify(data)}`);

                const val = parseFloat(creatinineValue);
                const enhancedData = {
                    ...data,
                    classificacao: val > 1.2 ? 'DOENÇA RENAL CRÔNICA' : 'NORMAL',
                    estagio: val > 1.5 ? 'G3b' : (val > 1.2 ? 'G3a' : 'G1'),
                    cor: val > 1.5 ? 'text-red-400' : (val > 1.2 ? 'text-orange-400' : 'text-emerald-400')
                };
                setResult(enhancedData);
            } else {
                throw new Error(`Erro API: ${response.status}`);
            }
        } catch (error) {
            addLog(`❌ Erro de conexão com Oswaldo API: ${error}`);
            addLog('⚠️ Ativando MOCK de contingência para Demo...');

            setTimeout(() => {
                const val = parseFloat(creatinineValue);
                const isCritical = val > 1.5;
                const mockResult: OswaldoResponse = {
                    sucesso: true,
                    mensagem: "Processado via Mock de Contingência",
                    classificacao: isCritical ? "DOENÇA RENAL CRÔNICA" : "NORMAL",
                    estagio: isCritical ? "G3b" : "G2",
                    cor: isCritical ? "text-red-400" : "text-emerald-400",
                    alerta_gerado: isCritical
                };
                setResult(mockResult);
                addLog(`Resultado Mock Gerado: ${JSON.stringify(mockResult)}`);
                setLoading(false);
            }, 1500);
            return;
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-950 via-slate-950 to-slate-950 p-6 text-white font-sans selection:bg-indigo-500/30">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <header className="flex items-center justify-between mb-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-500/10 rounded-2xl border border-indigo-500/20 backdrop-blur-md shadow-[0_0_15px_rgba(99,102,241,0.3)]">
                            <Activity className="w-8 h-8 text-indigo-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                                Oswaldo
                            </h1>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                <p className="text-xs text-indigo-300/80 font-mono tracking-widest uppercase">
                                    Chronic Care Engine v0.6
                                </p>
                            </div>
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: Input & Patient (4 cols) */}
                    <div className="lg:col-span-4 space-y-6">

                        {/* Patient Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md shadow-xl"
                        >
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center border-2 border-slate-600 shadow-inner">
                                    <span className="font-bold text-xl text-slate-200">JS</span>
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">João da Silva</h2>
                                    <p className="text-sm text-slate-400">68 anos • Masc</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 mb-6">
                                <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-3">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Thermometer className="w-3 h-3 text-indigo-400" />
                                        <span className="text-xs font-semibold text-indigo-200">Diabetes</span>
                                    </div>
                                    <span className="text-xs text-slate-400">Tipo 2 (Controlado)</span>
                                </div>
                                <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-3">
                                    <div className="flex items-center gap-2 mb-1">
                                        <HeartPulse className="w-3 h-3 text-rose-400" />
                                        <span className="text-xs font-semibold text-rose-200">Hipertensão</span>
                                    </div>
                                    <span className="text-xs text-slate-400">Estágio 1</span>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                                    <Database className="w-4 h-4 text-indigo-400" />
                                    Novo Exame: Creatinina
                                </label>
                                <div className="relative group">
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={creatinineValue}
                                        onChange={(e) => setCreatinineValue(e.target.value)}
                                        className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-4 text-white text-2xl font-mono focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder-slate-600"
                                        placeholder="0.0"
                                    />
                                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 text-sm font-medium">mg/dL</span>
                                </div>

                                <button
                                    onClick={processExam}
                                    disabled={loading}
                                    className="w-full py-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-indigo-500/25 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 relative overflow-hidden group"
                                >
                                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                                    <span className="relative flex items-center gap-2">
                                        {loading ? <Activity className="w-5 h-5 animate-spin" /> : <Server className="w-5 h-5" />}
                                        {loading ? 'Processando...' : 'Analisar Protocolo'}
                                    </span>
                                </button>
                            </div>
                        </motion.div>

                        {/* History Mini Chart */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                                    <History className="w-4 h-4 text-slate-500" />
                                    Histórico Recente
                                </h3>
                                <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">Estável</span>
                            </div>
                            <div className="h-40 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={mockHistoryData}>
                                        <defs>
                                            <linearGradient id="colorCreatinine" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="date" hide />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                                            itemStyle={{ color: '#fff' }}
                                        />
                                        <Area type="monotone" dataKey="value" stroke="#818cf8" fillOpacity={1} fill="url(#colorCreatinine)" strokeWidth={2} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </motion.div>
                    </div>

                    {/* Right Column: Visualization (8 cols) */}
                    <div className="lg:col-span-8 flex flex-col gap-6">

                        {/* Main Analysis Panel */}
                        <div className="flex-1 bg-slate-900/60 border border-slate-800 rounded-3xl p-1 relative overflow-hidden shadow-2xl">
                            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-150"></div>

                            <div className="relative h-full bg-slate-950/50 rounded-[20px] p-8 flex flex-col items-center justify-center min-h-[400px]">
                                <AnimatePresence mode="wait">
                                    {!result && !loading && (
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            className="text-center space-y-6 max-w-md"
                                        >
                                            <div className="w-24 h-24 mx-auto rounded-full bg-slate-800/50 flex items-center justify-center border border-slate-700 dashed">
                                                <Search className="w-10 h-10 text-slate-600" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-medium text-slate-300">Aguardando Dados</h3>
                                                <p className="text-slate-500 mt-2">Os resultados da análise de protocolos do Dr. Oswaldo aparecerão aqui.</p>
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
                                                <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20"></div>
                                                <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
                                                <div className="absolute inset-0 flex items-center justify-center">
                                                    <Database className="w-10 h-10 text-indigo-400 animate-pulse" />
                                                </div>
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-bold text-white mb-2">Analisando KDIGO 2021</h3>
                                                <div className="flex items-center justify-center gap-2 text-indigo-300 font-mono text-sm">
                                                    <span className="w-2 h-2 bg-indigo-500 rounded-full animate-ping"></span>
                                                    Calculando eGFR CKD-EPI...
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
                                            <div className="flex flex-col md:flex-row gap-8 items-start">

                                                {/* Big Result Visual */}
                                                <div className="flex-1 space-y-6">
                                                    <div className={clsx(
                                                        "inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold tracking-wider border mb-4",
                                                        result.sucesso ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
                                                    )}>
                                                        {result.sucesso ? <CheckCircle className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                                                        PROTOCOLO FINALIZADO
                                                    </div>

                                                    <div>
                                                        <h2 className="text-4xl md:text-5xl font-bold text-white leading-tight mb-4">
                                                            {result.classificacao}
                                                        </h2>
                                                        <div className="flex items-center gap-6">
                                                            <div className={clsx(
                                                                "px-6 py-3 rounded-2xl bg-slate-800/50 border border-slate-700 flex items-center gap-3",
                                                                result.cor?.replace('text-', 'border-')
                                                            )}>
                                                                <span className="text-sm text-slate-400 uppercase tracking-widest">Estágio</span>
                                                                <span className={clsx("text-4xl font-black", result.cor)}>{result.estagio}</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {result.alerta_gerado && (
                                                        <motion.div
                                                            initial={{ y: 20, opacity: 0 }}
                                                            animate={{ y: 0, opacity: 1 }}
                                                            transition={{ delay: 0.2 }}
                                                            className="p-6 bg-red-500/5 border border-red-500/20 rounded-2xl flex gap-4 backdrop-blur-sm"
                                                        >
                                                            <div className="p-3 bg-red-500/10 rounded-full shrink-0 h-fit">
                                                                <AlertTriangle className="w-6 h-6 text-red-400" />
                                                            </div>
                                                            <div>
                                                                <h4 className="font-bold text-red-100 text-lg">Alerta Clínico</h4>
                                                                <p className="text-red-300/80 mt-1 leading-relaxed">
                                                                    Paciente apresenta declínio acentuado da função renal. Recomendado encaminhamento para nefrologia e revisão da medicação (nefrotóxicos).
                                                                </p>
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                </div>

                                                {/* Technical Details Card */}
                                                <div className="w-full md:w-72 bg-black/20 border border-white/5 rounded-2xl p-6 backdrop-blur-md">
                                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Metadados</h4>
                                                    <div className="space-y-4 font-mono text-sm">
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-500">Evento ID</span>
                                                            <span className="text-slate-300">#9283</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-500">Algoritmo</span>
                                                            <span className="text-slate-300">CKD-EPI</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-500">Confiança</span>
                                                            <span className="text-emerald-400">99.8%</span>
                                                        </div>
                                                        <div className="flex justify-between pt-4 border-t border-white/5">
                                                            <span className="text-slate-500">Latência</span>
                                                            <span className="text-slate-300">42ms</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>

                        {/* Logs Console */}
                        <div className="bg-black/80 border border-slate-800 rounded-2xl p-4 h-40 overflow-y-auto font-mono text-[10px] shadow-inner custom-scrollbar">
                            <div className="flex items-center gap-2 text-slate-500 mb-2 sticky top-0 bg-black/90 pb-2 w-full border-b border-white/10">
                                <FileText className="w-3 h-3" />
                                <span className="uppercase tracking-wider">Kernel Output Log</span>
                            </div>
                            <div className="space-y-1.5 opacity-80">
                                {logs.map((log, i) => (
                                    <div key={i} className="text-slate-400 break-all border-l-2 border-slate-800 pl-2 hover:border-indigo-500 transition-colors">
                                        <span className="text-indigo-500/50 mr-2">{'>'}</span>
                                        {log}
                                    </div>
                                ))}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default OswaldoPage;
