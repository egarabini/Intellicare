import React, { useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate, useLocation } from 'react-router-dom';

export default function RoleRouter() {
    const { roles, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login', { state: { from: location }, replace: true });
            return;
        }

        if (
            roles.includes("PLATFORM_ADMIN") ||
            roles.includes("PLATFORM_SUPPORT") ||
            roles.includes("PLATFORM_BILLING")
        ) {
            navigate("/admin", { replace: true });
        } else if (roles.includes("TENANT_GESTOR")) {
            navigate("/gestor", { replace: true });
        } else if (
            roles.some(r => ["MEDICO", "CLINICO", "ENFERMEIRO", "RECEPCIONISTA"].includes(r))
        ) {
            navigate("/dashboard", { replace: true });
        } else if (roles.includes("PACIENTE")) {
            navigate("/paciente", { replace: true });
        } else {
            navigate("/sem-permissao", { replace: true });
        }
    }, [roles, isAuthenticated, navigate, location]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600 text-lg">Analisando Perfil e Permissões...</p>
        </div>
    );
}
