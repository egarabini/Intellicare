import React, { useEffect, useState } from 'react';
import { handleCallback } from '../../services/authService';
import { useNavigate } from 'react-router-dom';

export default function AuthCallback() {
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const processCallback = async () => {
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            const err = urlParams.get('error');

            if (err) {
                setError(urlParams.get('error_description') || 'Authentication failed');
                return;
            }

            if (!code) {
                navigate('/login', { replace: true });
                return;
            }

            try {
                await handleCallback(code);
                const redirectAfter = sessionStorage.getItem("redirect_after") || "/router";
                navigate(redirectAfter, { replace: true });
            } catch (e: any) {
                setError(e.message || 'Validation error');
            }
        };

        processCallback();
    }, [navigate]);

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4 text-center">
                <h2 className="text-2xl text-red-600 font-bold mb-4">Erro na Autenticação</h2>
                <p className="text-gray-700 mb-6">{error}</p>
                <button
                    onClick={() => navigate('/login')}
                    className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                    Voltar ao Login
                </button>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600 text-lg">Autenticando...</p>
        </div>
    );
}
