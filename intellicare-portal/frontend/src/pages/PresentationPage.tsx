import { motion } from 'framer-motion';
import { Bot, Cpu, Eye, Activity, Stethoscope, ShieldCheck, Share2, Database, Flame, MessageSquare, BarChart, FileText } from 'lucide-react';

export default function PresentationPage() {
    const modules = [
        { name: 'Pierre', role: 'Super Z', icon: Cpu, desc: 'Cérebro central que sintetiza conhecimentos.' },
        { name: 'Minerva', role: 'OCR', icon: Eye, desc: 'Extração estruturada de documentos e laudos.' },
        { name: 'Oswaldo', role: 'Protocolos', icon: Activity, desc: 'Gestão de crônicos e protocolos clínicos (SBN, ADA).' },
        { name: 'Florence', role: 'Análise Clínica', icon: Stethoscope, desc: 'Interpretação laboratorial profunda.' },
        { name: 'Geralda', role: 'Acompanhamento', icon: ShieldCheck, desc: 'Cuidado longitudinal e planos de prevenção.' },
        { name: 'Nise', role: 'Orquestração', icon: Share2, desc: 'Gestão de fluxos e processos com Kestra.' },
        { name: 'Zilda', role: 'Saúde Pública', icon: Database, desc: 'Dados territoriais, CNES e epidemiologia.' },
        { name: 'Grahame', role: 'Interoperabilidade', icon: Flame, desc: 'Padrão FHIR para troca de dados.' },
        { name: 'Hipócrates', role: 'Comunicação', icon: MessageSquare, desc: 'Ética médica e humanização do contato.' },
        { name: 'Wanda', role: 'Sistematização', icon: FileText, desc: 'SAE, NANDA-I, NIC/NOC e processos de enfermagem.' },
        { name: 'Donabedian', role: 'Qualidade', icon: BarChart, desc: 'Auditoria: Estrutura, Processo e Resultados.' },
    ];

    return (
        <div className="min-h-screen bg-slate-50 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 z-0 opacity-5">
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:20px_20px]" />
            </div>

            <div className="container mx-auto px-4 py-12 relative z-10">
                <div className="flex flex-col md:flex-row items-center gap-12 mb-16">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="w-full md:w-1/3 flex justify-center"
                    >
                        <div className="relative">
                            <div className="absolute inset-0 bg-indigo-500 blur-3xl opacity-20 rounded-full" />
                            <img
                                src="/agents/wanda_cartoon.png"
                                alt="Wanda - Agente de Enfermagem"
                                className="w-64 h-64 object-contain relative z-10 drop-shadow-2xl hover:scale-105 transition-transform duration-300"
                            />
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="w-full md:w-2/3"
                    >
                        <div className="inline-flex items-center space-x-2 bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm font-semibold mb-4">
                            <Bot className="w-4 h-4" />
                            <span>Apresentação Oficial</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
                            Conheça a Liga da <span className="text-indigo-600">IntelliCare</span>
                        </h1>
                        <p className="text-lg text-slate-600 leading-relaxed mb-6">
                            Olá! Eu sou a <strong>Wanda</strong>, responsável pela Sistematização da Assistência.
                            É um prazer guiar você por nossa plataforma. Cada agente aqui foi desenhado por especialistas
                            para resolver dores específicas da saúde pública e suplementar.
                        </p>
                        <p className="text-lg text-slate-600 leading-relaxed">
                            Nossa missão é unir tecnologia de ponta com a humanização necessária para salvar vidas.
                            Abaixo, apresento meus colegas de trabalho:
                        </p>
                    </motion.div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {modules.map((mod, index) => (
                        <motion.div
                            key={mod.name}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            viewport={{ once: true }}
                            className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow group"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-slate-50 rounded-xl group-hover:bg-indigo-50 transition-colors">
                                    <mod.icon className="w-8 h-8 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                                </div>
                                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{mod.role}</span>
                            </div>
                            <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-indigo-700 transition-colors">
                                {mod.name}
                            </h3>
                            <p className="text-slate-500 text-sm">
                                {mod.desc}
                            </p>
                        </motion.div>
                    ))}
                </div>

                <div className="mt-16 text-center">
                    <p className="text-slate-500 mb-6">Gostou do que viu?</p>
                    <a
                        href="/solicitacao"
                        className="inline-flex items-center justify-center px-8 py-4 text-base font-bold text-white transition-all duration-200 bg-indigo-600 border border-transparent rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 shadow-lg shadow-indigo-500/30"
                    >
                        Solicitar Participação no Piloto
                    </a>
                </div>
            </div>
        </div>
    );
}
