import { useState } from 'react';
import { Calendar, CheckCircle, Clock, Heart, Pill, ChevronRight, Stethoscope, User, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';
import { ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface Task {
    id: string;
    description: string;
    category: string;
    status: string;
    time?: string;
}



const mockTasks = [
    { id: '1', description: 'Tomar Metformina 850mg', category: 'medication', status: 'completed', time: '08:00' },
    { id: '2', description: 'Caminhada leve (30 min)', category: 'exercise', status: 'pending', time: '09:00' },
    { id: '3', description: 'Medir Glicemia Capilar', category: 'measurement', status: 'pending', time: '12:00' },
    { id: '4', description: 'Tomar Losartana 50mg', category: 'medication', status: 'pending', time: '20:00' },
];

const adherenceData = [
    { name: 'Completed', value: 85 },
    { name: 'Missed', value: 15 },
];

const COLORS = ['#10b981', '#334155'];

export default function GeraldaPage() {
    const [tasks, setTasks] = useState<Task[]>(mockTasks);

    const toggleTask = (id: string) => {
        setTasks(prev => prev.map(t =>
            t.id === id ? { ...t, status: t.status === 'completed' ? 'pending' : 'completed' } : t
        ));
    };

    return (
        <div className="min-h-screen bg-slate-950 p-6 text-white font-sans selection:bg-rose-500/30">
            <div className="max-w-7xl mx-auto">

                {/* Header */}
                <header className="flex items-center justify-between mb-10">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-rose-500/10 rounded-2xl border border-rose-500/20 backdrop-blur-md shadow-[0_0_15px_rgba(244,63,94,0.3)]">
                            <Heart className="w-8 h-8 text-rose-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                                Geralda
                            </h1>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                                <p className="text-xs text-rose-300/80 font-mono tracking-widest uppercase">
                                    Primary Care Engine v0.1
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right hidden md:block">
                            <p className="text-sm font-bold text-white">João da Silva</p>
                            <p className="text-xs text-slate-400">Plano de Cuidado Ativo</p>
                        </div>
                        <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                            <User className="w-5 h-5 text-slate-400" />
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Left Column: Timeline (4 cols) */}
                    <div className="lg:col-span-4 space-y-6">
                        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-md">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                                    <Calendar className="w-5 h-5 text-rose-400" />
                                    Hoje, 18 Fev
                                </h3>
                                <span className="text-xs font-mono text-slate-500 bg-slate-800 px-2 py-1 rounded">4 Tarefas</span>
                            </div>

                            <div className="space-y-4">
                                {tasks.map((task) => (
                                    <div
                                        key={task.id}
                                        onClick={() => toggleTask(task.id)}
                                        className={clsx(
                                            "relative p-4 rounded-2xl border transition-all cursor-pointer group",
                                            task.status === 'completed'
                                                ? "bg-emerald-950/20 border-emerald-500/20 opacity-70"
                                                : "bg-slate-800/40 border-slate-700 hover:bg-slate-800/60 hover:border-slate-600"
                                        )}
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className={clsx(
                                                "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors mt-1",
                                                task.status === 'completed'
                                                    ? "bg-emerald-500 border-emerald-500"
                                                    : "border-slate-500 group-hover:border-rose-400"
                                            )}>
                                                {task.status === 'completed' && <CheckCircle className="w-4 h-4 text-white" />}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex justify-between items-start">
                                                    <p className={clsx(
                                                        "font-medium transition-all",
                                                        task.status === 'completed' ? "text-slate-500 line-through" : "text-slate-200"
                                                    )}>
                                                        {task.description}
                                                    </p>
                                                    <span className="text-xs font-mono text-slate-500">{task.time}</span>
                                                </div>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <span className={clsx(
                                                        "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border",
                                                        task.category === 'medication' ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" :
                                                            task.category === 'exercise' ? "bg-orange-500/10 text-orange-400 border-orange-500/20" :
                                                                "bg-blue-500/10 text-blue-400 border-blue-500/20"
                                                    )}>
                                                        {task.category}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-md">
                            <h4 className="text-sm font-semibold text-slate-400 mb-4 flex items-center gap-2">
                                <Stethoscope className="w-4 h-4" /> Plano Terapêutico
                            </h4>
                            <div className="space-y-3">
                                <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700 flex justify-between items-center">
                                    <span className="text-sm text-slate-300">Diabetes Tipo 2</span>
                                    <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded border border-emerald-500/20">Controlado</span>
                                </div>
                                <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700 flex justify-between items-center">
                                    <span className="text-sm text-slate-300">Hipertensão</span>
                                    <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-1 rounded border border-amber-500/20">Atenção</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Analytics (8 cols) */}
                    <div className="lg:col-span-8 space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Adherence Chart */}
                            <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center relative overflow-hidden">
                                <h3 className="text-slate-400 text-sm font-bold uppercase tracking-widest absolute top-6 left-6">Adesão Semanal</h3>
                                <div className="w-56 h-56 relative mt-4">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={adherenceData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={80}
                                                paddingAngle={5}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                {adherenceData.map((_entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-4xl font-bold text-white">85%</span>
                                        <span className="text-xs text-slate-500 uppercase">Regular</span>
                                    </div>
                                </div>
                            </div>

                            {/* Notifications */}
                            <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 backdrop-blur-md">
                                <h3 className="text-slate-400 text-sm font-bold uppercase tracking-widest mb-6">Alertas & Lembretes</h3>
                                <div className="space-y-4">
                                    <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex gap-3">
                                        <Clock className="w-5 h-5 text-rose-400 shrink-0" />
                                        <div>
                                            <h4 className="font-bold text-rose-200 text-sm">Consulta Agendada</h4>
                                            <p className="text-xs text-rose-300/70 mt-1">Amanhã, 14:00 - Cardiologista (Dr. Santos)</p>
                                        </div>
                                    </div>
                                    <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex gap-3">
                                        <Pill className="w-5 h-5 text-indigo-400 shrink-0" />
                                        <div>
                                            <h4 className="font-bold text-indigo-200 text-sm">Renovação de Receita</h4>
                                            <p className="text-xs text-indigo-300/70 mt-1">Losartana 50mg está acabando (3 dias)</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Education Section */}
                        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 relative overflow-hidden group hover:border-rose-500/30 transition-colors cursor-pointer">
                            <div className="absolute top-0 right-0 p-12 opacity-5 scale-150 group-hover:scale-125 transition-transform duration-700">
                                <Heart className="w-64 h-64" />
                            </div>
                            <div className="relative z-10">
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 text-xs font-bold mb-4 border border-rose-500/20">
                                    <ShieldCheck className="w-3 h-3" /> EDUCAÇÃO EM SAÚDE
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2">Vivendo bem com Diabetes</h2>
                                <p className="text-slate-400 max-w-lg mb-6">Aprenda dicas essenciais sobre nutrição, monitoramento e como evitar complicações a longo prazo.</p>
                                <button className="flex items-center gap-2 text-rose-400 font-bold hover:text-rose-300 transition-colors">
                                    Ler Material <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
