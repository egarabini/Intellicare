import React, { useState } from 'react';
import { Send, Clock, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../../../services/api';

import ModuleTestHistory from './ModuleTestHistory';

interface TestResponse {
    status_code: number;
    latency_ms: number;
    success: boolean;
    response: any;
    error: any;
}

interface ModuleTestPanelProps {
    moduleName: string;
}

const ModuleTestPanel: React.FC<ModuleTestPanelProps> = ({ moduleName }) => {
    const [payloadType, setPayloadType] = useState<'default' | 'custom'>('default');
    const [customJson, setCustomJson] = useState<string>('{\n  "query": "teste"\n}');
    const [isExecuting, setIsExecuting] = useState(false);
    const [result, setResult] = useState<TestResponse | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const [activeTab, setActiveTab] = useState<'execute' | 'history'>('execute');

    const executeTest = async () => {
        setIsExecuting(true);
        setResult(null);
        try {
            let customPayload = null;
            if (payloadType === 'custom') {
                try {
                    customPayload = JSON.parse(customJson);
                } catch (e) {
                    alert('JSON Customizado Inválido');
                    setIsExecuting(false);
                    return;
                }
            }

            const response = await api.post(`/admin/modules/${moduleName}/test`, {
                payload_key: payloadType === 'default' ? 'default' : 'custom',
                custom_payload: customPayload
            });
            setResult(response.data);
        } catch (err: unknown) {
            console.error('Test Execution failed:', err);
            setResult({
                success: false,
                status_code: 500,
                latency_ms: -1,
                error: (err as any).message || 'Server connection error',
                response: null
            });
        } finally {
            setIsExecuting(false);
        }
    };

    return (
        <div className="bg-white border text-left border-gray-200 rounded-lg overflow-hidden">
            <div className="flex border-b border-gray-200 bg-gray-50">
                <button
                    onClick={() => setActiveTab('execute')}
                    className={`flex-1 py-3 text-sm font-semibold transition-colors ${activeTab === 'execute' ? 'text-primary-700 border-b-2 border-primary-600 bg-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    Executar Teste
                </button>
                <button
                    onClick={() => setActiveTab('history')}
                    className={`flex-1 py-3 text-sm font-semibold transition-colors ${activeTab === 'history' ? 'text-primary-700 border-b-2 border-primary-600 bg-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    Histórico de Diagnósticos
                </button>
            </div>

            {activeTab === 'execute' ? (
                <div className="p-5">
                    <div className="mb-4">
                        <label className="text-sm font-semibold text-gray-600 mb-2 block">Payload Configuration</label>
                        <div className="flex gap-4 mb-3">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="payloadConfig"
                                    checked={payloadType === 'default'}
                                    onChange={() => setPayloadType('default')}
                                    className="text-primary-600 focus:ring-primary-500"
                                />
                                <span className="text-sm">Padrão do Módulo</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="radio"
                                    name="payloadConfig"
                                    checked={payloadType === 'custom'}
                                    onChange={() => setPayloadType('custom')}
                                    className="text-primary-600 focus:ring-primary-500"
                                />
                                <span className="text-sm">JSON Customizado</span>
                            </label>
                        </div>

                        {payloadType === 'custom' && (
                            <div className="mt-2">
                                <textarea
                                    value={customJson}
                                    onChange={(e) => setCustomJson(e.target.value)}
                                    className="w-full h-32 p-3 font-mono text-sm bg-gray-50 border border-gray-200 rounded-md focus:ring-1 focus:ring-primary-500"
                                    spellCheck={false}
                                />
                            </div>
                        )}
                    </div>

                    <button
                        onClick={executeTest}
                        disabled={isExecuting}
                        className="w-full flex justify-center items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                        {isExecuting ? (
                            <>
                                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                                Executando /analyze...
                            </>
                        ) : (
                            <>
                                <Send className="w-4 h-4" />
                                Disparar Teste
                            </>
                        )}
                    </button>

                    {result && (
                        <div className="mt-5 border border-gray-100 bg-gray-50 rounded-lg overflow-hidden">
                            <div className={`p-3 border-b flex justify-between items-center ${result.success ? 'bg-emerald-50 border-emerald-100 text-emerald-800' : 'bg-red-50 border-red-100 text-red-800'}`}>
                                <div className="flex items-center gap-2 font-semibold">
                                    {result.success ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <AlertTriangle className="w-5 h-5 text-red-600" />}
                                    Test {result.success ? 'Successful' : 'Failed'}
                                </div>
                                <div className="flex gap-4 text-sm font-medium">
                                    <span>Status: {result.status_code}</span>
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-4 h-4" /> {result.latency_ms} ms
                                    </span>
                                </div>
                            </div>
                            <div className="p-3">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-semibold text-gray-500 uppercase">Response Body</span>
                                    <button onClick={() => setShowRaw(!showRaw)} className="text-xs text-primary-600 hover:underline">
                                        {showRaw ? 'Hide Payload' : 'Show Payload'}
                                    </button>
                                </div>

                                {showRaw && (
                                    <pre className="text-xs font-mono bg-gray-900 text-green-400 p-3 rounded overflow-x-auto max-h-64">
                                        {JSON.stringify(result.response || result.error, null, 2)}
                                    </pre>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <div className="p-5 bg-gray-50/50">
                    <ModuleTestHistory moduleName={moduleName} />
                </div>
            )}
        </div>
    );
};

export default ModuleTestPanel;
