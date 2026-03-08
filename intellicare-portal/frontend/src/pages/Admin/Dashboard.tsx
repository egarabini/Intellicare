import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../services/api';
import {
    Building2, Activity, AlertOctagon, CheckCircle2,
    Users, ServerCrash, Clock, ActivitySquare
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

interface AdminDashboardMetrics {
    totais: {
        tenants: number;
        ativos: number;
        suspensos: number;
        trial: number;
    };
    modulos_mais_usados: Array<{ nome: string; tenants_ativos: number }>;
    gestores_totais: number;
    ultimas_atividades: Array<{
        id: string;
        acao: string;
        recurso: string | null;
        operador: string;
        tenant_id: string;
        data: string | null;
    }>;
}

export default function AdminDashboard() {
    const { user } = useAuth();
    const [metrics, setMetrics] = useState<AdminDashboardMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAdminDashboard = async () => {
            try {
                setLoading(true);
                const response = await api.get('/admin/dashboard');
                setMetrics(response.data);
            } catch (err) {
                console.error("Failed to load admin dashboard", err);
                setError("Não foi possível carregar as métricas da plataforma.");
            } finally {
                setLoading(false);
            }
        };

        fetchAdminDashboard();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8 h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded shadow-sm">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <ServerCrash className="h-5 w-5 text-red-500" />
                        </div>
                        <div className="ml-3">
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">

            {/* HEADER */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900">Plataforma Admin</h1>
                <p className="mt-2 text-lg text-gray-600">
                    Visão global do ecossistema IntelliCare.
                </p>
            </div>

            {/* KPI GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                {/* KPI 1 - Tenants Ativos */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                        <CheckCircle2 size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Tenants Ativos</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.totais.ativos || 0}   <span className="text-sm font-normal text-gray-400">/ {metrics?.totais.tenants || 0}</span></h3>
                    </div>
                </div>

                {/* KPI 2 - Tenants Trial */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                        <ActivitySquare size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Em Trial</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.totais.trial || 0}</h3>
                    </div>
                </div>

                {/* KPI 3 - Suspensos */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-red-50 text-red-600 rounded-lg">
                        <AlertOctagon size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Suspensos</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.totais.suspensos || 0}</h3>
                    </div>
                </div>

                {/* KPI 4 - Gestores Globais */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                        <Users size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Gestores Operacionais</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.gestores_totais || 0}</h3>
                    </div>
                </div>

            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* CHARTS CONTAINER: Modulos */}
                <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6">Módulos Mais Utilizados</h2>
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={metrics?.modulos_mais_usados || []}
                                margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                                barSize={40}
                            >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="nome" axisLine={false} tickLine={false} />
                                <YAxis axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                    formatter={(value: any) => [`${value} Tenants`, 'Uso']}
                                />
                                <Bar dataKey="tenants_ativos" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* ACTIVITY LOGS FEED */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-semibold text-gray-900">Auditoria Global</h2>
                        <Activity className="text-gray-400 h-5 w-5" />
                    </div>

                    <div className="space-y-4 overflow-y-auto flex-1 pr-2">
                        {metrics?.ultimas_atividades?.length ? (
                            metrics.ultimas_atividades.map((log) => {
                                const isCreate = log.acao.includes('CREATE') || log.acao.includes('ADD');
                                const isDelete = log.acao.includes('DELETE') || log.acao.includes('REMOVE');

                                return (
                                    <div key={log.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className={`text-xs font-semibold px-2 py-0.5 rounded
                        ${isCreate ? 'bg-green-100 text-green-700' :
                                                    isDelete ? 'bg-red-100 text-red-700' :
                                                        'bg-blue-100 text-blue-700'}`}
                                            >
                                                {log.acao}
                                            </span>
                                            {log.data && (
                                                <div className="flex items-center text-[10px] text-gray-400">
                                                    <Clock className="w-3 h-3 mr-1" />
                                                    {new Date(log.data).toLocaleTimeString()}
                                                </div>
                                            )}
                                        </div>
                                        <p className="text-sm font-medium text-gray-800 break-all">{log.recurso || 'N/A'}</p>
                                        <div className="mt-2 text-xs text-gray-500 flex justify-between">
                                            <span>👤 {log.operador.substring(0, 8)}</span>
                                            <span>🏢 {log.tenant_id}</span>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <p className="text-sm text-gray-500 text-center py-8">Sem logs recentes.</p>
                        )}
                    </div>
                </div>

            </div>

        </div>
    );
}
