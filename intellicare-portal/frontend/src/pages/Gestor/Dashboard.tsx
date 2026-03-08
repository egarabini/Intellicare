import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../services/api';
import {
    Users, UserCheck, ShieldPlus, Home,
    Activity, Clock, FileWarning, PlusCircle
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

interface DashboardMetrics {
    users: { total: number; active: number; inactive: number };
    patients: { total: number };
    professionals: { total: number };
    roles: { total: number };
    sectors: { active: number };
    recent_activity: ActivityLog[];
}

interface ActivityLog {
    action: string;
    resource_type: string;
    resource_id: string;
    created_at: string;
}

export default function GestorDashboard() {
    const { tenantId, user } = useAuth();
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                // Uses the configured Axios instance which handles multi-tenant auth correctly
                const response = await api.get('/gestor/dashboard');
                setMetrics(response.data);
            } catch (err) {
                console.error("Failed to load dashboard metrics", err);
                setError("Não foi possível carregar os dados do painel no momento.");
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, [tenantId]);

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
                            <FileWarning className="h-5 w-5 text-red-500" />
                        </div>
                        <div className="ml-3">
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Prepara dados para os gráficos
    const userStatusData = [
        { name: 'Ativos', value: metrics?.users.active || 0, fill: '#10B981' }, // emerald-500
        { name: 'Inativos', value: metrics?.users.inactive || 0, fill: '#6B7280' }, // gray-500
    ];

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">

            {/* HEADER */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900">Visão Geral do Polo</h1>
                <p className="mt-2 text-lg text-gray-600">
                    Você está gerenciando a unidade: <span className="font-semibold text-primary-700 bg-primary-50 px-2 py-1 rounded">{tenantId}</span>
                </p>
            </div>

            {/* KPI GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                {/* KPI 1 - Unidades */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                        <Home size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Unidades/Setores</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.sectors.active || 0}</h3>
                    </div>
                </div>

                {/* KPI 2 - Pacientes (New Postgres Table) */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                        <Users size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Pacientes</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.patients.total || 0}</h3>
                    </div>
                </div>

                {/* KPI 3 - Profissionais */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                        <UserCheck size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Profissionais Clínicos</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.professionals.total || 0}</h3>
                    </div>
                </div>

                {/* KPI 4 - Permissoes/Roles */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center space-x-4">
                    <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                        <ShieldPlus size={28} />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-gray-500">Roles Ativos</p>
                        <h3 className="text-2xl font-bold text-gray-900">{metrics?.roles.total || 0}</h3>
                    </div>
                </div>

            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* CHARTS CONTAINER */}
                <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6">Status da Base de Usuários</h2>
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={userStatusData}
                                margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                                barSize={50}
                            >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} />
                                <YAxis axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'transparent' }}
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                />
                                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* ACTIVITY TIMELINE */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-semibold text-gray-900">Timeline de Atividades</h2>
                        <Activity className="text-gray-400 h-5 w-5" />
                    </div>

                    <div className="space-y-6">
                        {metrics?.recent_activity?.length ? (
                            metrics.recent_activity.map((log, i) => (
                                <div key={i} className="flex relative items-start pb-4">
                                    {i !== metrics.recent_activity.length - 1 && (
                                        <span
                                            className="absolute top-8 left-4 -ml-px h-full w-0.5 bg-gray-200"
                                            aria-hidden="true"
                                        />
                                    )}
                                    <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 ring-8 ring-white flex-shrink-0">
                                        <PlusCircle className="h-4 w-4 text-primary-600" />
                                    </div>
                                    <div className="ml-4 min-w-0 flex-1">
                                        <div className="text-sm font-medium text-gray-900 capitalize">
                                            {log.action} <span className="font-normal text-gray-500">em</span> {log.resource_type}
                                        </div>
                                        <p className="mt-0.5 text-xs text-gray-500">
                                            ID: {log.resource_id.substring(0, 8)}...
                                        </p>
                                        <div className="mt-1 flex items-center text-xs text-gray-400">
                                            <Clock className="mr-1 h-3 w-3" />
                                            {new Date(log.created_at).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-gray-500 text-center py-8">Nenhuma atividade recente.</p>
                        )}
                    </div>
                </div>

            </div>

        </div>
    );
}
