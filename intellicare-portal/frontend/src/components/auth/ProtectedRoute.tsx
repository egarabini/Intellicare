import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
    requiredRole?: string;
    allowedRoles?: string[];
}

export default function ProtectedRoute({ requiredRole, allowedRoles }: ProtectedRouteProps) {
    const { isAuthenticated, restoring, hasRole, hasAnyRole } = useAuth();
    const location = useLocation();

    // Wait for session restore (refresh_token → new access_token) before making auth decisions
    if (restoring) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        sessionStorage.setItem("redirect_after", location.pathname + location.search);
        return <Navigate to="/login" replace />;
    }

    if (requiredRole && !hasRole(requiredRole)) {
        return <Navigate to="/sem-permissao" replace />;
    }

    if (allowedRoles && allowedRoles.length > 0 && !hasAnyRole(allowedRoles)) {
        return <Navigate to="/sem-permissao" replace />;
    }

    return <Outlet />;
}
