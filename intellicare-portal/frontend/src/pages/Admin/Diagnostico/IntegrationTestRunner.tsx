import React, { useState } from 'react';
import { Play, CheckCircle2, AlertTriangle, Clock, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../../../services/api';
import { IntegrationFlowDef } from './IntegrationTests';

interface StepResult {
    module: string;
    payload_key: string;
    success: boolean;
    status_code: number;
    latency_ms: number;
    response?: any;
    error?: any;
}

interface RunnerProps {
    flow: IntegrationFlowDef;
}

const IntegrationTestRunner: React.FC<RunnerProps> = ({ flow }) => {
    const [isExecuting, setIsExecuting] = useState(false);
    const [results, setResults] = useState<StepResult[] | null>(null);
    const [overallStatus, setOverallStatus] = useState<'success' | 'failed' | null>(null);
    const [totalTime, setTotalTime] = useState<number | null>(null);
    const [expandedStep, setExpandedStep] = useState<number | null>(null);

    const runFlow = async () => {
        setIsExecuting(true);
        setResults(null);
        setOverallStatus(null);
        setTotalTime(null);
        setExpandedStep(null);

        try {
            const response = await api.post(`/admin/integration-flows/${flow.id}/run`);
            setResults(response.data.steps_results);
            setOverallStatus(response.data.status);
            setTotalTime(response.data.total_latency_ms);
        } catch (err: unknown) {
            console.error('Flow execution failed', err);
            setOverallStatus('failed');
        } finally {
            setIsExecuting(false);
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col h-full max-h-[80vh]">
            <div className="p-5 border-b bg-gray-50 flex justify-between items-center">
                <div>
                    <h3 className="font-bold text-gray-900">Runner: {flow.name}</h3>
                    <p className="text-xs text-gray-500 font-mono mt-1">ID: {flow.id}</p>
                </div>
                <button
                    onClick={runFlow}
                    disabled={isExecuting}
                    className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white py-2 px-5 rounded-lg font-medium transition-colors"
                >
                    {isExecuting ? (
                        <RefreshCw className="w-4 h-4 animate-spin outline-none" />
                    ) : (
                        <Play className="w-4 h-4 fill-current outline-none" />
                    )}
                    {isExecuting ? 'Executando...' : 'Iniciar Teste'}
                </button>
            </div>

            <div className="p-5 flex-grow overflow-y-auto">
                <div className="mb-6">
                    <h4 className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wider">Cronograma de Execução</h4>
                    <div className="relative pl-6">
                        {/* Timeline Line */}
                        <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-gray-200"></div>

                        {flow.steps.map((step, idx) => {
                            const result = results ? results.find(r => r.module === step.module && r.payload_key === step.payload_key) || results[idx] : null;
                            const isSuccess = result?.success;
                            const isFail = result && !result.success;
                            const isPending = !result && !isExecuting;
                            const isRunning = isExecuting && !result; // Simple assumption for UI, though backend might execute parallel

                            return (
                                <div key={idx} className="relative mb-6 last:mb-0">
                                    {/* Timeline Dot */}
                                    <div className={`absolute -left-6 w-3 h-3 rounded-full mt-1.5 ring-4 ring-white ${isSuccess ? 'bg-emerald-500' :
                                            isFail ? 'bg-red-500' :
                                                isRunning ? 'bg-indigo-500 animate-pulse' : 'bg-gray-300'
                                        }`}></div>

                                    <div className={`bg-white border rounded-lg overflow-hidden transition-all ${expandedStep === idx ? 'ring-2 ring-indigo-500' : 'hover:border-gray-300'
                                        } ${isSuccess ? 'border-emerald-200 shadow-sm' :
                                            isFail ? 'border-red-200 shadow-sm' : 'border-gray-200'
                                        }`}>
                                        <div
                                            className={`p-3 cursor-pointer flex justify-between items-center ${isSuccess ? 'bg-emerald-50' :
                                                    isFail ? 'bg-red-50' : 'bg-white'
                                                }`}
                                            onClick={() => setExpandedStep(expandedStep === idx ? null : idx)}
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="font-mono text-sm font-bold text-gray-700 bg-white px-2 py-0.5 rounded border shadow-sm">
                                                    {step.module.toUpperCase()}
                                                </span>
                                                <span className="text-sm text-gray-600 truncate max-w-[200px]">
                                                    {step.payload_key}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-4">
                                                {result && (
                                                    <span className="flex items-center gap-1 text-xs font-mono text-gray-500">
                                                        <Clock className="w-3 h-3" /> {result.latency_ms}ms
                                                    </span>
                                                )}
                                                {result && (
                                                    <span className={`text-xs font-bold px-2 py-1 rounded bg-white border ${result.status_code < 300 ? 'text-emerald-700 border-emerald-200' : 'text-red-700 border-red-200'
                                                        }`}>
                                                        {result.status_code}
                                                    </span>
                                                )}
                                                {expandedStep === idx ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                            </div>
                                        </div>

                                        {expandedStep === idx && result && (
                                            <div className="p-3 bg-gray-900 border-t border-gray-200">
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="text-xs font-semibold text-gray-400">Response / Error Body</span>
                                                </div>
                                                <pre className="text-[11px] font-mono text-green-400 overflow-x-auto max-h-48 scrollbar-thin scrollbar-thumb-gray-700">
                                                    {JSON.stringify(result.response || result.error, null, 2)}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {overallStatus && (
                <div className={`p-4 border-t flex justify-between items-center ${overallStatus === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'
                    }`}>
                    <div className="flex items-center gap-2 font-bold">
                        {overallStatus === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                        Flow {overallStatus === 'success' ? 'Succeeded' : 'Failed'}
                    </div>
                    {totalTime && (
                        <div className="text-sm font-medium bg-black/20 px-3 py-1 rounded-full">
                            Tempo Total: {(totalTime / 1000).toFixed(2)}s
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default IntegrationTestRunner;
