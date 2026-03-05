import React from 'react';
import { useNavigate } from 'react-router-dom';
import { logout } from '../services/authService';

export default function SemPermissao() {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4 text-center">
            <h1 className="text-4xl font-extrabold text-red-600 mb-4">Acesso Negado</h1>
            <p className="text-lg text-gray-600 mb-8">
                Sua conta atual não possui permissões para acessar esta área.
            </p>

            <div className="space-x-4">
                <button
                    onClick={() => navigate('/')}
                    className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                    Voltar à Tela Inicial
                </button>
                <button
                    onClick={() => logout()}
                    className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                    Sair
                </button>
            </div>
        </div>
    );
}
