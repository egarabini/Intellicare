import React, { useEffect } from 'react';
import { iniciarLogin } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export default function Login() {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/router', { replace: true });
        }
    }, [isAuthenticated, navigate]);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="mt-6 text-center text-3xl font-extrabold text-blue-600">
                    IntelliCare
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    Bem-vindo ao portal unificado de saúde.
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 text-center">
                    <button
                        onClick={() => iniciarLogin()}
                        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                    >
                        Entrar com sua conta
                    </button>

                    <div className="mt-6 text-xs text-gray-400">
                        suporte@intellicare.ia.br | v2.0.2
                    </div>
                </div>
            </div>
        </div>
    );
}
