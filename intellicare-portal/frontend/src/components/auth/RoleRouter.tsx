import React, { useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export default function RoleRouter() {
    const { roles, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login', { replace: true });
            return;
        }

        if (roles.includes("PLATFORM_ADMIN")) {
            navigate("/admin", { replace: true });
        } else if (roles.includes("TENANT_GESTOR")) {
            navigate("/gestor", { replace: true });
        } else if (roles.some(r => ["CLINICO", "MEDICO", "ENFERMEIRO"].includes(r))) {
            navigate("/dashboard", { replace: true });
        } else {
            navigate("/sem-permissao", { replace: true });
        }
    }, [roles, isAuthenticated, navigate]);

    return <div>Redirecionando...</div>;
}
