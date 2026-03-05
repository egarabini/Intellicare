import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { refreshToken, logout } from '../services/authService';

export function useAuth() {
    const { accessToken, user, roles, tenantId, expiry, clear } = useAuthStore();
    const [restoring, setRestoring] = useState(!accessToken && !!sessionStorage.getItem('refresh_token'));

    const isAuthenticated = !!accessToken;

    // Restore session on page refresh (F5) using refresh_token from sessionStorage
    useEffect(() => {
        if (!accessToken && sessionStorage.getItem('refresh_token')) {
            refreshToken().finally(() => setRestoring(false));
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!expiry) return;

        const timeout = expiry - Date.now();
        if (timeout <= 0) {
            // Already expired, try to refresh now
            refreshToken();
            return;
        }

        // Set a timer to refresh the token just before it expires
        const timer = setTimeout(() => {
            refreshToken();
        }, timeout);

        return () => clearTimeout(timer);
    }, [accessToken, expiry]);

    const hasRole = (role: string) => roles.includes(role);
    const hasAnyRole = (allowedRoles: string[]) => allowedRoles.some((r) => roles.includes(r));

    return {
        isAuthenticated,
        restoring,
        user,
        roles,
        tenantId,
        accessToken,
        hasRole,
        hasAnyRole,
        logout,
    };
}
