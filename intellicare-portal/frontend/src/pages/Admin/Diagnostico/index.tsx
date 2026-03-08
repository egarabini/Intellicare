import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, FormControl, InputLabel, Select, MenuItem, Paper, Alert } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
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
            // using the backend proxy endpoint
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
        <Box sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
                <Box>
                    <Typography variant="h4" fontWeight={700} color="text.primary" gutterBottom>
                        Console de Diagnóstico Modular
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Visão de saúde e latência estrutural de ponta a ponta dos microserviços.
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <FormControl size="small" sx={{ minWidth: 160 }}>
                        <InputLabel>Auto-Refresh</InputLabel>
                        <Select
                            value={refreshInterval}
                            label="Auto-Refresh"
                            onChange={(e) => setRefreshInterval(Number(e.target.value))}
                        >
                            <MenuItem value={0}>Off</MenuItem>
                            <MenuItem value={15}>A cada 15s</MenuItem>
                            <MenuItem value={30}>A cada 30s</MenuItem>
                            <MenuItem value={60}>A cada 1 min</MenuItem>
                        </Select>
                    </FormControl>
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<RefreshIcon />}
                        onClick={fetchModules}
                        disabled={loading}
                    >
                        Atualizar Tudo
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 4 }}>
                    {error}
                </Alert>
            )}

            <ModuleGrid modules={modules} loading={loading} onTestFuncional={(name) => console.log('Test Phase 2 for:', name)} />

        </Box>
    );
};

export default DiagnosticoAdmin;
