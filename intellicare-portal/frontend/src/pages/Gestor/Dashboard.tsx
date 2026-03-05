import React from 'react';
import { useAuth } from '../../hooks/useAuth';

export default function GestorDashboard() {
    const { tenantId } = useAuth();

    return (
        <div className="p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Gestor de Tenant</h1>
            <p className="text-lg text-gray-600">
                Bem-vindo ao painel Gestor. Seu Tenant Atual é: <span className="font-semibold text-blue-600">{tenantId || 'Vazio'}</span>
            </p>
        </div>
    );
}
