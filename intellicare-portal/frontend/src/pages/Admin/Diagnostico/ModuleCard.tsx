import React from 'react';
import { ModuleProbe } from './index';
import { CheckCircle, AlertTriangle, XCircle, HelpCircle, Server, Clock, GitCommit, Activity } from 'lucide-react';

interface ModuleCardProps {
    moduleItem: ModuleProbe;
    loading: boolean;
    onTestFuncional: () => void;
}

const getStatusConfig = (health: string) => {
    switch (health) {
        case 'healthy':
            return {
                bg: 'bg-emerald-50',
                border: 'border-emerald-200',
                text: 'text-emerald-700',
                icon: <CheckCircle className="w-4 h-4 mr-1.5" />,
                label: 'Healthy'
            };
        case 'degraded':
            return {
                bg: 'bg-amber-50',
                border: 'border-amber-200',
                text: 'text-amber-700',
                icon: <AlertTriangle className="w-4 h-4 mr-1.5" />,
                label: 'Degraded'
            };
        case 'unhealthy':
            return {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-700',
                icon: <XCircle className="w-4 h-4 mr-1.5" />,
                label: 'Unhealthy'
            };
        case 'unreachable':
        default:
            return {
                bg: 'bg-gray-100',
                border: 'border-gray-200',
                text: 'text-gray-600',
                icon: <HelpCircle className="w-4 h-4 mr-1.5" />,
                label: 'Unreachable'
            };
    }
};

const ModuleCard: React.FC<ModuleCardProps> = ({ moduleItem, loading, onTestFuncional }) => {
    const { name, display_name, description, port, probe } = moduleItem;
    const status = getStatusConfig(probe.health);

    const isLatencyHigh = probe.latency_ms > 500;
    const isOffline = probe.health === 'unreachable';

    return (
        <div className={`flex flex-col overflow-hidden bg-white rounded-xl shadow-sm border transition-all duration-200 hover:shadow-md hover:-translate-y-1 ${status.border} ${isOffline ? 'opacity-80 grayscale-[20%]' : ''}`}>

            <div className={`px-5 py-4 border-b ${status.border} ${status.bg} flex justify-between items-start`}>
                <div>
                    <h3 className="text-lg font-bold text-gray-900 tracking-tight">{display_name}</h3>
                    <p className="text-xs font-mono text-gray-500 mt-0.5">{name}</p>
                </div>
                <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${status.border} ${status.text} bg-white shadow-sm`}>
                    {status.icon}
                    {status.label}
                </div>
            </div>

            <div className="p-5 flex-grow flex flex-col">
                <p className="text-sm text-gray-600 mb-5 min-h-[40px] leading-relaxed">
                    {description}
                </p>

                <div className="mt-auto space-y-2.5 bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div className="flex justify-between items-center text-sm">
                        <div className="flex items-center text-gray-500">
                            <Server className="w-4 h-4 mr-2" />
                            Porta Interna
                        </div>
                        <span className="font-mono font-medium text-gray-700">{port}</span>
                    </div>

                    <div className="flex justify-between items-center text-sm">
                        <div className="flex items-center text-gray-500">
                            <Activity className="w-4 h-4 mr-2" />
                            Latência
                        </div>
                        <span className={`font-mono font-medium flex items-center ${isLatencyHigh ? 'text-amber-600' : 'text-gray-700'}`}>
                            {probe.latency_ms >= 0 ? `${probe.latency_ms} ms` : 'N/A'}
                            {isLatencyHigh && <span className="relative flex h-2 w-2 ml-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                            </span>}
                        </span>
                    </div>

                    <div className="flex justify-between items-center text-sm">
                        <div className="flex items-center text-gray-500">
                            <GitCommit className="w-4 h-4 mr-2" />
                            Versão API
                        </div>
                        <span className="font-mono text-xs bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded">{probe.version}</span>
                    </div>
                </div>

                {probe.error && (
                    <div className="mt-4 text-xs bg-red-50 text-red-700 p-2.5 rounded border border-red-100 font-mono break-words max-h-24 overflow-y-auto">
                        <strong>Erro: </strong>
                        {probe.error}
                    </div>
                )}
            </div>

            <div className="p-4 pt-0 bg-white">
                <button
                    onClick={onTestFuncional}
                    disabled={isOffline}
                    className="w-full py-2.5 px-4 rounded-lg text-sm font-medium border-2 border-primary-100 text-primary-700 hover:bg-primary-50 hover:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:border-gray-200 disabled:text-gray-500"
                >
                    Diagnóstico / Teste
                </button>
            </div>
        </div>
    );
};

export default ModuleCard;
