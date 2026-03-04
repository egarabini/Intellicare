import React from 'react';
import { useTenantContext } from '../../contexts/TenantContext';
import { getTenantsArray } from '../../utils/jwt';
import { useAuthStore } from '../../store/authStore';

const OrgSwitcher: React.FC = () => {
    const { tenantInfo, changeTenant, isLoading } = useTenantContext();
    const { token } = useAuthStore();

    const availableTenants = token ? getTenantsArray(token) : [];

    if (!token || availableTenants.length <= 1) {
        return null; // Don't show switcher if user only has 1 organization
    }

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newTenant = e.target.value;
        if (newTenant && newTenant !== tenantInfo?.tenantId) {
            changeTenant(newTenant);
        }
    };

    return (
        <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-100 text-primary-700 font-bold text-sm">
                🏥
            </div>
            <select
                className="form-select block w-full rounded-md border-gray-300 py-1.5 pl-3 pr-10 text-sm focus:border-primary-500 focus:outline-none focus:ring-primary-500 bg-gray-50 text-gray-800 disabled:opacity-50"
                value={tenantInfo?.tenantId || ''}
                onChange={handleChange}
                disabled={isLoading}
            >
                <option value="" disabled>Selecionando...</option>
                {availableTenants.map((id) => (
                    <option key={id} value={id}>
                        Organização {id}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default OrgSwitcher;
