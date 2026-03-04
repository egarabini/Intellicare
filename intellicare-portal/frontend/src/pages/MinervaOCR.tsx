import { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, FileText, Upload, CheckCircle, ArrowLeft, Loader2, FileJson, Cpu } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';

const mockOcrResult = {
    document_type: "lab_report",
    patient_id: "e4d909c290d0fb1ca068ffaddf22cbd0",
    date: "2026-02-18",
    results: {
        creatinine: { value: 2.1, unit: "mg/dL", status: "high" },
        egfr: { value: 38.0, unit: "mL/min/1.73m2", status: "low" },
        potassium: { value: 5.8, unit: "mEq/L", status: "critical" },
        urea: { value: 82.0, unit: "mg/dL", status: "high" }
    },
    metadata: {
        lab: "Laboratório Fleury",
        confidence: 0.94,
        processing_time: "1.2s"
    }
};

const MinervaOCR = () => {
    const [file, setFile] = useState<File | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<any | null>(null);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResult(null);
        }
    };

    const handleProcess = () => {
        if (!file) return;
        setIsProcessing(true);

        // Simulate OCR processing delay
        setTimeout(() => {
            setResult(mockOcrResult);
            setIsProcessing(false);
        }, 2500);
    };

    return (
        <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
            {/* Header */}
            <header className="flex items-center gap-4 border-b border-white/10 bg-slate-900/50 p-4 backdrop-blur-md">
                <Link to="/" className="rounded-lg p-2 hover:bg-white/10 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                        <Eye className="h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold">Minerva</h1>
                        <p className="text-xs text-slate-400">Extração Estruturada de Documentos Médicos</p>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Left Panel: Upload/Preview */}
                <div className="flex w-1/2 flex-col border-r border-white/10 bg-slate-900/30 p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-400">
                            <FileText className="h-4 w-4" />
                            Documento Original
                        </h2>
                        {file && (
                            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                                {file.name}
                            </span>
                        )}
                    </div>

                    <div className="flex-1 rounded-xl border-2 border-dashed border-slate-700 bg-slate-800/20 transition-colors hover:bg-slate-800/40 relative">
                        {!file ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                                <Upload className="mb-4 h-12 w-12 opacity-50" />
                                <p className="font-medium">Arraste um PDF ou Imagem</p>
                                <p className="text-xs opacity-70">ou clique para selecionar</p>
                                <input
                                    type="file"
                                    className="absolute inset-0 cursor-pointer opacity-0"
                                    onChange={handleFileUpload}
                                    accept=".pdf,.png,.jpg,.jpeg"
                                />
                            </div>
                        ) : (
                            <div className="flex h-full flex-col items-center justify-center p-8 text-center animate-fade-in">
                                <div className="h-24 w-20 rounded bg-white shadow-lg mb-4 flex items-center justify-center">
                                    <span className="text-slate-900 font-bold text-xs">PDF</span>
                                </div>
                                <p className="text-emerald-400 font-medium">Arquivo Pronto para Análise</p>
                                <button
                                    onClick={() => setFile(null)}
                                    className="mt-4 text-xs text-red-400 hover:text-red-300 underline"
                                >
                                    Remover
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="mt-6">
                        <button
                            onClick={handleProcess}
                            disabled={!file || isProcessing}
                            className={clsx(
                                "flex w-full items-center justify-center gap-2 rounded-xl py-4 font-bold transition-all",
                                !file
                                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                    : isProcessing
                                        ? "bg-emerald-600/50 text-white cursor-wait"
                                        : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg hover:shadow-emerald-500/25"
                            )}
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                    Processando via Tesseract...
                                </>
                            ) : (
                                <>
                                    <Eye className="h-5 w-5" />
                                    Processar com Minerva
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Right Panel: JSON Result */}
                <div className="flex w-1/2 flex-col bg-slate-950 p-6">
                    <div className="mb-4 flex items-center justify-between">
                        <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-400">
                            <FileJson className="h-4 w-4" />
                            Dados Estruturados
                        </h2>
                        {result && (
                            <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                                <CheckCircle className="h-3 w-3" />
                                Confidence: {result.metadata.confidence * 100}%
                            </span>
                        )}
                    </div>

                    <div className="flex-1 overflow-auto rounded-xl border border-white/5 bg-slate-900 p-4 font-mono text-sm shadow-inner">
                        {!result ? (
                            <div className="flex h-full flex-col items-center justify-center text-slate-600 opacity-50">
                                <Cpu className="mb-4 h-12 w-12" />
                                <p>Aguardando processamento...</p>
                            </div>
                        ) : (
                            <motion.pre
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="text-emerald-300"
                            >
                                <code>{JSON.stringify(result, null, 2)}</code>
                            </motion.pre>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MinervaOCR;
