import React from 'react';
import { Grid, Skeleton, Box } from '@mui/material';
import ModuleCard from './ModuleCard';
import { ModuleProbe } from './index';

interface ModuleGridProps {
    modules: ModuleProbe[];
    loading: boolean;
    onTestFuncional: (moduleName: string) => void;
}

const ModuleGrid: React.FC<ModuleGridProps> = ({ modules, loading, onTestFuncional }) => {

    if (loading && modules.length === 0) {
        return (
            <Grid container spacing={3}>
                {[1, 2, 3, 4].map(idx => (
                    <Grid item xs={12} sm={6} md={4} key={`skeleton-${idx}`}>
                        <Skeleton variant="rectangular" height={260} sx={{ borderRadius: 2 }} />
                    </Grid>
                ))}
            </Grid>
        );
    }

    return (
        <Grid container spacing={3}>
            {modules.map((moduleItem) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={moduleItem.name}>
                    <ModuleCard
                        moduleItem={moduleItem}
                        loading={loading}
                        onTestFuncional={() => onTestFuncional(moduleItem.name)}
                    />
                </Grid>
            ))}
        </Grid>
    );
};

export default ModuleGrid;
