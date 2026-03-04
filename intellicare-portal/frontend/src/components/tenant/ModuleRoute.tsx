import React from 'react';
import { Navigate } from 'react-router-dom';
import { useTenantContext } from '../../contexts/TenantContext';

interface ModuleRouteProps {
    module: string;
    children: React.ReactNode;
}

export const ModuleRoute: React.FC<ModuleRouteProps> = ({ module, children }) => {
    const { tenantInfo, isLoading } = useTenantContext();

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-900 text-white">
                Validando acessos...
            </div>
        );
    }

    // If we have a tenant context loaded, check if the module is active
    if (tenantInfo && !tenantInfo.activeModules.includes(module)) {
        // If user tries to access a route they don't have the module for,
        // redirect them to the dashboard
        return <Navigate to="/" replace />;
    }

    // Allow access
    return <>{children}</>;
};
