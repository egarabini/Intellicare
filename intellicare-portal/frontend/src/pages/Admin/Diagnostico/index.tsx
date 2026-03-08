import React, { useState, useEffect } from 'react';
import { RefreshCw, Activity, CheckCircle, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import ModuleGrid from './ModuleGrid';
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

            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <ModuleGrid
                    modules={modules}
                    loading={loading}
                    onTestFuncional={(name) => console.log('Test Phase 2 for:', name)}
                />
            </div>

        </div>
    );
};

export default DiagnosticoAdmin;
