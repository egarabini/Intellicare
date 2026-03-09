import React, { useState, useEffect } from 'react';
import { Activity, Play, Settings, RefreshCw, AlertTriangle } from 'lucide-react';
import api from '../../../services/api';
import IntegrationTestRunner from './IntegrationTestRunner';

export interface IntegrationFlowDef {
    id: string;
    name: string;
    description: string;
    type: 'sequential' | 'parallel';
    steps: {
        module: string;
        payload_key: string;
        custom_payload?: any;
    }[];
}

const IntegrationTests: React.FC = () => {
    const [flows, setFlows] = useState<IntegrationFlowDef[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedFlow, setSelectedFlow] = useState<IntegrationFlowDef | null>(null);

    const fetchFlows = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/admin/integration-flows');
            setFlows(response.data);
        } catch (err: unknown) {
            console.error('Failed to fetch integration flows', err);
            setError('Falha ao carregar fluxos de integração.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFlows();
    }, []);

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                        <Settings className="w-8 h-8 text-indigo-600" />
                        Testes de Integração (Flows)
                    </h1>
                    <p className="text-gray-600">
                        Validação sistêmica End-to-End da orquestração entre microserviços.
                    </p>
                </div>

                <button
                    onClick={fetchFlows}
                    disabled={loading}
                    className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors shadow-sm"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Atualizar Fluxos
                </button>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <span className="text-red-700 font-medium">{error}</span>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-800 border-b pb-2">Workflows Disponíveis</h3>

                    {loading ? (
                        <div className="animate-pulse space-y-4">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="bg-white p-5 rounded-xl border border-gray-100 h-32"></div>
                            ))}
                        </div>
                    ) : (
                        flows.map((flow) => (
                            <div
                                key={flow.id}
                                className={`bg-white rounded-xl border-2 transition-all p-5 cursor-pointer ${selectedFlow?.id === flow.id
                                        ? 'border-indigo-500 shadow-md ring-1 ring-indigo-500/20'
                                        : 'border-gray-100 hover:border-indigo-200 hover:shadow-sm'
                                    }`}
                                onClick={() => setSelectedFlow(flow)}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="text-lg font-bold text-gray-900">{flow.name}</h4>
                                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${flow.type === 'parallel' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'
                                        }`}>
                                        {flow.type.toUpperCase()}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600 mb-4">{flow.description}</p>

                                <div className="flex flex-wrap gap-2">
                                    {flow.steps.map((step, idx) => (
                                        <span key={idx} className="flex items-center gap-1.5 text-xs font-medium text-gray-500 bg-gray-50 border border-gray-200 px-2 py-1 rounded">
                                            <span className="w-4 h-4 flex items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-[10px]">
                                                {idx + 1}
                                            </span>
                                            {step.module.toUpperCase()}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="sticky top-24 h-fit">
                    {selectedFlow ? (
                        <IntegrationTestRunner flow={selectedFlow} />
                    ) : (
                        <div className="bg-gray-50 border border-gray-100 rounded-xl p-8 text-center flex flex-col items-center justify-center h-64">
                            <Activity className="w-12 h-12 text-gray-300 mb-4" />
                            <h3 className="text-lg font-medium text-gray-700">Nenhum fluxo selecionado</h3>
                            <p className="text-gray-500 text-sm mt-1">Selecione um workflow clínico à esquerda para simular a esteira.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default IntegrationTests;
