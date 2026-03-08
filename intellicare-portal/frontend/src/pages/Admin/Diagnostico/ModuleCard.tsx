import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Button, Divider } from '@mui/material';
import { ModuleProbe } from './index';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import DesktopAccessDisabledIcon from '@mui/icons-material/DesktopAccessDisabled';

interface ModuleCardProps {
    moduleItem: ModuleProbe;
    loading: boolean;
    onTestFuncional: () => void;
}

const getStatusConfig = (health: string) => {
    switch (health) {
        case 'healthy':
            return { color: 'success' as const, icon: <CheckCircleOutlineIcon />, label: 'Healthy' };
        case 'degraded':
            return { color: 'warning' as const, icon: <WarningAmberIcon />, label: 'Degraded' };
        case 'unhealthy':
            return { color: 'error' as const, icon: <ErrorOutlineIcon />, label: 'Unhealthy' };
        case 'unreachable':
        default:
            return { color: 'default' as const, icon: <DesktopAccessDisabledIcon />, label: 'Unreachable' };
    }
};

const ModuleCard: React.FC<ModuleCardProps> = ({ moduleItem, loading, onTestFuncional }) => {
    const { name, display_name, description, port, probe } = moduleItem;
    const status = getStatusConfig(probe.health);

    return (
        <Card
            elevation={2}
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 }
            }}
        >
            <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" fontWeight="bold">
                        {display_name}
                    </Typography>
                    <Chip
                        icon={status.icon}
                        label={status.label}
                        color={status.color}
                        size="small"
                        variant="filled"
                    />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                    {description}
                </Typography>

                <Divider sx={{ mb: 2 }} />

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">Porta Interna</Typography>
                        <Typography variant="caption" fontWeight="medium">{port}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">Latência</Typography>
                        <Typography variant="caption" fontWeight="medium" color={probe.latency_ms > 500 ? 'warning.main' : 'text.primary'}>
                            {probe.latency_ms >= 0 ? `${probe.latency_ms} ms` : 'N/A'}
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">Versão API</Typography>
                        <Typography variant="caption" fontWeight="medium">{probe.version}</Typography>
                    </Box>
                </Box>

                {probe.error && (
                    <Typography variant="caption" color="error" sx={{ display: 'block', mt: 2, bgcolor: 'error.main', color: 'error.contrastText', p: 1, borderRadius: 1 }}>
                        {probe.error.substring(0, 100)}{probe.error.length > 100 ? '...' : ''}
                    </Typography>
                )}
            </CardContent>

            <Box sx={{ p: 2, pt: 0 }}>
                <Button
                    variant="outlined"
                    size="small"
                    fullWidth
                    onClick={onTestFuncional}
                    disabled={probe.health === 'unreachable'}
                >
                    Diagnóstico / Teste
                </Button>
            </Box>
        </Card>
    );
};

export default ModuleCard;
