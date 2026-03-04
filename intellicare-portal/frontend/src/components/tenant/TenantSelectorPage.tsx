import React from 'react';
import { useTenantContext } from '../../contexts/TenantContext';
import { getTenantsArray } from '../../utils/jwt';
import { useAuthStore } from '../../store/authStore';

export const TenantSelectorPage: React.FC = () => {
    const { changeTenant, isLoading } = useTenantContext();
    const { token } = useAuthStore();

    const availableTenants = token ? getTenantsArray(token) : [];

    const handleSelect = (tenantId: string) => {
        changeTenant(tenantId);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-900 p-4">
            <div className="w-full max-w-md rounded-2xl bg-gray-800 p-8 shadow-2xl ring-1 ring-white/10">
                <div className="mb-8 text-center">
                    <h1 className="text-2xl font-bold text-white">Selecione a Organização</h1>
                    <p className="mt-2 text-gray-400">
                        Sua conta possui acesso a múltiplos ambientes. Selecione qual você deseja acessar agora.
                    </p>
                </div>

                {isLoading ? (
                    <div className="flex justify-center p-8">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {availableTenants.map((tenantId) => (
                            <button
                                key={tenantId}
                                onClick={() => handleSelect(tenantId)}
                                className="w-full flex items-center justify-between rounded-xl bg-gray-700 p-4 text-left transition-all hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <div>
                                    <h3 className="font-semibold text-white">Organização {tenantId}</h3>
                                    <p className="text-sm text-gray-400">Acessar portal</p>
                                </div>
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 text-blue-400">
                                    →
                                </div>
                            </button>
                        ))}
                    </div>
                )}

                <div className="mt-8 text-center text-sm text-gray-500">
                    Você poderá alterar a organização mais tarde através do menu superior.
                </div>
            </div>
        </div>
    );
};
