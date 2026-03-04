import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Cpu, User, ArrowLeft, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

const mockResponses: Record<string, string> = {
    default: "Estou analisando sua solicitação nos protocolos clínicos vigentes (KDIGO 2024, ADA 2025)...",
    ckd: "**Análise de Protocolo KDIGO 2024:**\n\nPara pacientes com DRC Estágio 3b (TFG 30-44ml/min):\n1.  **Monitoramento:** Anual de Albuminúria (ACR) e trimestral de Creatinina.\n2.  **Farmacologia:**\n    *   Iniciaria iSGLT2 (Dapagliflozina 10mg) independente de diabetes.\n    *   Manteria IECA/BRA dose máxima tolerada.\n3.  **Nutrição:** Restrição proteica leve (0.8g/kg/dia).\n\n*Fonte: KDIGO 2024 Guideline for CKD Evaluation and Management.*",
    potassio: "**Alerta Clínico:** Níveis de potássio > 5.5 mEq/L exigem atenção imediata.\nOswaldo sugere revisar prescrição de Espironolactona ou IECA. \n\nRecomendo solicitar ECG para descartar alterações de repolarização.",
};

const PierreChat = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: 'Olá, sou **Pierre**. Tenho acesso a *35 milhões* de artigos no PubMed e guidelines em tempo real.\n\nComo posso ajudar na decisão clínica hoje?',
            timestamp: new Date()
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        // Mock Intelligence Delay
        setTimeout(() => {
            const lowerInput = userMsg.content.toLowerCase();
            let responseText = mockResponses.default;

            if (lowerInput.includes('renal') || lowerInput.includes('rim') || lowerInput.includes('drc') || lowerInput.includes('kdigo')) {
                responseText = mockResponses.ckd;
            } else if (lowerInput.includes('potassio') || lowerInput.includes('hipercalemia')) {
                responseText = mockResponses.potassio;
            }

            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: responseText,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, aiMsg]);
            setIsTyping(false);
        }, 2000); // 2s thinking time
    };

    return (
        <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
            {/* Header */}
            <header className="flex items-center gap-4 border-b border-white/10 bg-slate-900/50 p-4 backdrop-blur-md">
                <Link to="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400">
                        <Cpu className="h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold">Pierre</h1>
                        <div className="flex items-center gap-2 text-xs text-emerald-400">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            Conectado ao Tavily & PubMed
                        </div>
                    </div>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
                {messages.map((msg) => (
                    <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={clsx(
                            "flex gap-4 max-w-3xl",
                            msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
                        )}
                    >
                        <div className={clsx(
                            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                            msg.role === 'user' ? "bg-slate-700" : "bg-indigo-500/20 text-indigo-400"
                        )}>
                            {msg.role === 'user' ? <User className="h-5 w-5" /> : <Cpu className="h-5 w-5" />}
                        </div>

                        <div className={clsx(
                            "rounded-2xl p-4 shadow-sm",
                            msg.role === 'user'
                                ? "bg-indigo-600 text-white rounded-tr-sm"
                                : "bg-slate-800/80 border border-white/5 text-slate-200 rounded-tl-sm"
                        )}>
                            <div className="prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                            <div className="mt-2 text-[10px] opacity-50 text-right uppercase">
                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                    </motion.div>
                ))}

                {isTyping && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center gap-3 text-sm text-slate-400 pl-12"
                    >
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Consultando Tavily...</span>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-white/10 bg-slate-900/80 p-4 backdrop-blur-md">
                <div className="mx-auto max-w-3xl flex gap-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Pergunte sobre protocolos, medicamentos ou casos clínicos..."
                        className="flex-1 rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder:text-slate-600"
                        autoFocus
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim()}
                        className="rounded-xl bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="h-5 w-5" />
                    </button>
                </div>
                <div className="mt-2 text-center text-[10px] text-slate-600">
                    Super Z pode cometer erros. Verifique informações críticas.
                </div>
            </div>
        </div>
    );
};

export default PierreChat;
