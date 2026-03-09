import React, { useEffect, useState } from 'react';
import { Clock, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '../../../services/api';

interface TestLog {
    id: number;
    module_name: string;
    test_type: string;
    payload_key: string;
    status_code: number;
    latency_ms: number;
    success: boolean;
    created_at: string;
    error_message: string | null;
}

interface ModuleTestHistoryProps {
    moduleName: string;
}

const ModuleTestHistory: React.FC<ModuleTestHistoryProps> = ({ moduleName }) => {
    const [history, setHistory] = useState<TestLog[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/admin/modules/${moduleName}/history`);
            setHistory(response.data);
        } catch (error) {
            console.error('Failed to fetch module history:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [moduleName]);

    if (loading) {
        return <div className="p-4 text-center text-gray-500">Carregando histórico...</div>;
    }

    if (history.length === 0) {
        return (
            <div className="p-8 text-center text-gray-500 bg-gray-50 border border-gray-100 rounded-lg">
                Nenhum teste funcional registrado recentemente para este módulo.
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {history.map((log) => (
                <div key={log.id} className="flex flex-col bg-white border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center gap-2">
                            {log.success ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            ) : (
                                <AlertTriangle className="w-4 h-4 text-red-500" />
                            )}
                            <span className="font-semibold text-gray-800 text-sm">
                                {log.payload_key === 'custom' ? 'Payload Customizado' : `Padrão (${log.payload_key})`}
                            </span>
                        </div>
                        <span className="text-xs text-gray-400 font-medium font-mono">
                            {new Date(log.created_at).toLocaleString()}
                        </span>
                    </div>
                    <div className="flex gap-4 text-xs text-gray-600">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {log.latency_ms} ms</span>
                        <span className={`font-medium ${log.status_code >= 200 && log.status_code < 300 ? 'text-emerald-600' : 'text-red-600'}`}>
                            Status: {log.status_code}
                        </span>
                    </div>
                    {log.error_message && (
                        <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded truncate">
                            {log.error_message}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};

export default ModuleTestHistory;
