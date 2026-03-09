import React, { useState, useEffect } from 'react';
import { RefreshCw, Activity, AlertTriangle, X } from 'lucide-react';
import ModuleGrid from './ModuleGrid';
import ModuleTestPanel from './ModuleTestPanel';
import IntegrationTests from './IntegrationTests';
import api from '../../../services/api';

export interface ModuleProbe {
    name: string;
    display_name: string;
    description: string;
    base_url: string;
    port: number;
    probe: {
        health: 'healthy' | 'degraded' | 'unhealthy' | 'unreachable';
        status_code?: number;
        latency_ms: number;
        version: string;
        uptime_seconds: number;
        dependencies: Record<string, string>;
        last_checked: string;
        error?: string;
    };
}

const DiagnosticoAdmin: React.FC = () => {
    const [modules, setModules] = useState<ModuleProbe[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [refreshInterval, setRefreshInterval] = useState<number>(0);
    const [selectedModule, setSelectedModule] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'probes' | 'integrations'>('probes');

    const fetchModules = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get('/admin/modules');
            setModules(response.data);
        } catch (err: unknown) {
            console.error('Error fetching modules probe:', err);
            const errMsg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
                || 'Erro ao comunicar com a controladora central (Admin).';
            setError(errMsg);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchModules();
    }, []);

    useEffect(() => {
        if (refreshInterval > 0) {
            const timer = setInterval(() => {
                fetchModules();
            }, refreshInterval * 1000);
            return () => clearInterval(timer);
        }
    }, [refreshInterval]);

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                        <Activity className="w-8 h-8 text-primary-600" />
                        Console de Diagnóstico Modular
                    </h1>
                    <p className="text-gray-600">
                        Visão de saúde e latência estrutural de ponta a ponta dos microserviços.
                    </p>
                </div>

                <div className="flex flex-wrap gap-4 items-center bg-white p-3 rounded-xl shadow-sm border border-gray-100">
                    <div className="flex flex-col">
                        <label className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Auto-Refresh</label>
                        <select
                            className="bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2"
                            value={refreshInterval}
                            onChange={(e) => setRefreshInterval(Number(e.target.value))}
                        >
                            <option value={0}>Desligado</option>
                            <option value={15}>A cada 15s</option>
                            <option value={30}>A cada 30s</option>
                            <option value={60}>A cada 1 min</option>
                        </select>
                    </div>

                    <button
                        onClick={fetchModules}
                        disabled={loading}
                        className="mt-5 flex items-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        {loading ? 'Sondando...' : 'Atualizar Tudo'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-semibold text-red-800">Falha ao buscar diagnóstico</h3>
                        <p className="text-red-700 text-sm">{error}</p>
                    </div>
                </div>
            )}

            <div className="flex border-b border-gray-200 mb-6">
                <button
                    onClick={() => setActiveTab('probes')}
                    className={`py-3 px-6 text-sm font-semibold transition-colors ${activeTab === 'probes' ? 'text-primary-700 border-b-2 border-primary-600 bg-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    Módulos Individuais
                </button>
                <button
                    onClick={() => setActiveTab('integrations')}
                    className={`py-3 px-6 text-sm font-semibold transition-colors ${activeTab === 'integrations' ? 'text-primary-700 border-b-2 border-primary-600 bg-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                    Esteiras de Integração E2E
                </button>
            </div>

            {activeTab === 'probes' ? (
                <>
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                        <ModuleGrid
                            modules={modules}
                            loading={loading}
                            onTestFuncional={(name: string) => setSelectedModule(name)}
                        />
                    </div>

                    {selectedModule && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
                            <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
                                <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                                    <h3 className="font-bold text-lg text-gray-800">
                                        Diagnóstico Ativo: <span className="text-primary-600">{selectedModule}</span>
                                    </h3>
                                    <button
                                        onClick={() => setSelectedModule(null)}
                                        className="p-1.5 rounded-full hover:bg-gray-200 text-gray-500 transition-colors"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="p-6 overflow-y-auto">
                                    <ModuleTestPanel moduleName={selectedModule} />
                                </div>
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <IntegrationTests />
            )}
        </div>
    );
};

export default DiagnosticoAdmin;
