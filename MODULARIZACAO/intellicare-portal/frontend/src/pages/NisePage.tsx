import { useState, useEffect, useRef } from 'react';
import { Activity, Bot, Play, AlertTriangle, RefreshCw, Send } from 'lucide-react';
import clsx from 'clsx';

// --- Types ---

interface WorkflowExecution {
    execution_id: string;
    workflow_id: string;
    namespace: string;
    status: string;
    start_date: string;
    end_date?: string;
    inputs: Record<string, any>;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

// --- Components ---

const StatusBadge = ({ status }: { status: string }) => {
    const styles = {
        SUCCESS: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        RUNNING: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        FAILED: "bg-red-500/10 text-red-400 border-red-500/20",
        CREATED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    };

    // Default to CREATED style if status is unknown
    const style = styles[status as keyof typeof styles] || styles.CREATED;

    return (
        <span className={clsx("px-2 py-1 rounded text-xs font-mono border", style)}>
            {status}
        </span>
    );
};

export default function NisePage() {
    // Workflow State
    const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
    const [loadingWorkflows, setLoadingWorkflows] = useState(true);

    // Chat State
    const [messages, setMessages] = useState<ChatMessage[]>([
        { role: 'assistant', content: 'Olá! Sou o Dr. Nise. Como posso ajudar com os protocolos clínicos hoje?', timestamp: new Date() }
    ]);
    const [input, setInput] = useState('');
    const [sending, setSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // --- Effects ---

    useEffect(() => {
        fetchWorkflows();
        const interval = setInterval(fetchWorkflows, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // --- Actions ---

    const fetchWorkflows = async () => {
        try {
            // Using localhost:8000 directly (assuming proxy or direct access)
            const res = await fetch('http://localhost:8000/api/v1/workflows/executions?limit=10');
            if (res.ok) {
                const data = await res.json();
                setExecutions(data);
            }
        } catch (error) {
            console.error("Failed to fetch workflows:", error);
        } finally {
            setLoadingWorkflows(false);
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || sending) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg, timestamp: new Date() }]);
        setSending(true);

        try {
            const res = await fetch('http://localhost:8000/api/v1/chatbot/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMsg })
            });

            if (res.ok) {
                const data = await res.json();
                setMessages(prev => [...prev, { role: 'assistant', content: data.text, timestamp: new Date() }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: "Desculpe, tive um erro ao processar sua mensagem.", timestamp: new Date() }]);
            }
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Erro de conexão com o Dr. Nise.", timestamp: new Date() }]);
        } finally {
            setSending(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const triggerWorkflow = async (flowId: string) => {
        try {
            await fetch('http://localhost:8000/api/v1/workflows/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workflow_id: flowId,
                    namespace: 'intellicare',
                    inputs: { manual_trigger: 'true' }
                })
            });
            fetchWorkflows();
        } catch (error) {
            console.error("Trigger error:", error);
        }
    };

    return (
        <div className="min-h-screen bg-[#0F172A] text-slate-200 font-sans p-6 selection:bg-cyan-500/30">
            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-80px)]">

                {/* Header / Sidebar Area */}
                <div className="lg:col-span-3 mb-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Bot className="w-8 h-8 text-cyan-400" />
                            NISE <span className="text-sm font-mono text-cyan-500/50 mt-2">Nucleus of Intelligence</span>
                        </h1>
                        <p className="text-slate-400 text-sm mt-1">Orquestração Clínica & Assistente Virtual</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-lg border border-slate-700">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                            <span className="text-xs font-mono text-emerald-400">SYSTEM ONLINE</span>
                        </div>
                    </div>
                </div>

                {/* Left Panel: Workflow Monitor (2/3 width) */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    {/* Active Workflows Card */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex-1 backdrop-blur-sm overflow-hidden flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                <Activity className="w-5 h-5 text-cyan-400" />
                                Kestra Workflows
                            </h2>
                            <button
                                onClick={fetchWorkflows}
                                className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                                title="Refresh"
                            >
                                <RefreshCw className={clsx("w-4 h-4", loadingWorkflows && "animate-spin")} />
                            </button>
                        </div>

                        <div className="overflow-auto flex-1">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-wider">
                                        <th className="p-3 font-medium">Fluxo</th>
                                        <th className="p-3 font-medium">Execução ID</th>
                                        <th className="p-3 font-medium">Status</th>
                                        <th className="p-3 font-medium">Início</th>
                                    </tr>
                                </thead>
                                <tbody className="text-sm">
                                    {executions.map((exec) => (
                                        <tr key={exec.execution_id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                                            <td className="p-3 font-medium text-white">{exec.workflow_id}</td>
                                            <td className="p-3 font-mono text-slate-400 text-xs">{exec.execution_id.substring(0, 8)}...</td>
                                            <td className="p-3"><StatusBadge status={exec.status} /></td>
                                            <td className="p-3 text-slate-400 text-xs">
                                                {new Date(exec.start_date).toLocaleTimeString()}
                                            </td>
                                        </tr>
                                    ))}
                                    {executions.length === 0 && !loadingWorkflows && (
                                        <tr>
                                            <td colSpan={4} className="p-8 text-center text-slate-500">
                                                Nenhum workflow ativo no momento.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => triggerWorkflow('alerta-critico-notificacao')}
                            className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all text-left group"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle className="w-5 h-5 text-amber-400" />
                                <span className="font-bold text-slate-200 group-hover:text-cyan-400">Simular Alerta Crítico</span>
                            </div>
                            <p className="text-xs text-slate-500">Dispara fluxo de notificação para equipe médica.</p>
                        </button>
                        <button
                            onClick={() => triggerWorkflow('analise-lab-florence')}
                            className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all text-left group"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <Play className="w-5 h-5 text-emerald-400" />
                                <span className="font-bold text-slate-200 group-hover:text-cyan-400">Revalidação Lab</span>
                            </div>
                            <p className="text-xs text-slate-500">Inicia reprocessamento de exames pendentes.</p>
                        </button>
                    </div>
                </div>

                {/* Right Panel: Chatbot (1/3 width) */}
                <div className="lg:col-span-1 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col overflow-hidden backdrop-blur-md shadow-2xl">
                    <div className="p-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30">
                                <Bot className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white text-sm">Dr. Nise Assistant</h3>
                                <p className="text-xs text-cyan-400/80 flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full"></span> Online
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.map((msg, i) => (
                            <div key={i} className={clsx("flex gap-3", msg.role === 'user' ? "flex-row-reverse" : "")}>
                                <div className={clsx(
                                    "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1",
                                    msg.role === 'user' ? "bg-slate-700" : "bg-cyan-900/30 border border-cyan-500/20"
                                )}>
                                    {msg.role === 'user' ? <UserIcon /> : <Bot className="w-4 h-4 text-cyan-400" />}
                                </div>
                                <div className={clsx(
                                    "p-3 rounded-2xl text-sm max-w-[85%]",
                                    msg.role === 'user'
                                        ? "bg-slate-700 text-white rounded-tr-sm"
                                        : "bg-slate-800/80 text-slate-200 border border-slate-700 rounded-tl-sm shadow-sm"
                                )}>
                                    {msg.content}
                                    <div className="mt-1 text-[10px] opacity-40 text-right">
                                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    <form onSubmit={handleSendMessage} className="p-3 bg-slate-900 border-t border-slate-800">
                        <div className="relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Pergunte sobre um paciente..."
                                className="w-full bg-slate-800 text-white placeholder-slate-500 text-sm rounded-xl py-3 pl-4 pr-12 border border-slate-700 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                                disabled={sending}
                            />
                            <button
                                type="submit"
                                disabled={sending || !input.trim()}
                                className="absolute right-2 top-2 p-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-slate-300">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
);
