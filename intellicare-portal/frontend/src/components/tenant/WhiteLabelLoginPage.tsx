/**
 * WhiteLabelLoginPage — Custom branded login page for tenant subdomains.
 *
 * Displayed when:
 *   1. User visits {tenant}.saudeconectada.com.br
 *   2. User is NOT authenticated
 *   3. White-label branding was resolved from hostname
 *
 * Features:
 *   - Tenant-specific logo, colors, and name
 *   - Redirect to Keycloak with tenant context
 *   - Animated gradient background using tenant colors
 *   - Responsive design
 */

import { useEffect, useState } from 'react';
import type { WhiteLabelConfig } from '../../services/whiteLabelResolver';

interface WhiteLabelLoginPageProps {
    config: WhiteLabelConfig;
    onLogin: () => void;
}

export default function WhiteLabelLoginPage({ config, onLogin }: WhiteLabelLoginPageProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [animateIn, setAnimateIn] = useState(false);

    useEffect(() => {
        // Trigger entrance animation
        requestAnimationFrame(() => setAnimateIn(true));
    }, []);

    const handleLogin = async () => {
        setIsLoading(true);
        try {
            await onLogin();
        } catch (error) {
            console.error('[WhiteLabel] Login failed:', error);
            setIsLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex items-center justify-center relative overflow-hidden"
            style={{ background: config.backgroundGradient }}
        >
            {/* Animated background orbs */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div
                    className="absolute w-96 h-96 rounded-full blur-3xl opacity-20 animate-pulse"
                    style={{
                        background: config.primaryColor,
                        top: '-10%',
                        right: '-5%',
                        animationDuration: '4s',
                    }}
                />
                <div
                    className="absolute w-80 h-80 rounded-full blur-3xl opacity-15 animate-pulse"
                    style={{
                        background: config.secondaryColor,
                        bottom: '-10%',
                        left: '-5%',
                        animationDuration: '6s',
                        animationDelay: '1s',
                    }}
                />
                <div
                    className="absolute w-64 h-64 rounded-full blur-3xl opacity-10 animate-pulse"
                    style={{
                        background: config.accentColor,
                        top: '40%',
                        left: '60%',
                        animationDuration: '5s',
                        animationDelay: '2s',
                    }}
                />
            </div>

            {/* Login card */}
            <div
                className={`relative z-10 w-full max-w-md mx-4 transition-all duration-700 ease-out ${animateIn
                    ? 'opacity-100 translate-y-0 scale-100'
                    : 'opacity-0 translate-y-8 scale-95'
                    }`}
            >
                {/* Glass card */}
                <div
                    className="backdrop-blur-xl rounded-2xl p-8 shadow-2xl border"
                    style={{
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                    }}
                >
                    {/* Logo / Icon */}
                    <div className="text-center mb-8">
                        {config.logoUrl ? (
                            <img
                                src={config.logoUrl}
                                alt={config.displayName}
                                className="h-16 w-auto mx-auto mb-4 drop-shadow-lg"
                            />
                        ) : (
                            <div
                                className="w-16 h-16 mx-auto mb-4 rounded-xl flex items-center justify-center text-2xl font-bold text-white shadow-lg"
                                style={{
                                    background: `linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor})`,
                                }}
                            >
                                {config.displayName.charAt(0)}
                            </div>
                        )}

                        <h1 className="text-2xl font-bold text-white mb-1">
                            {config.displayName}
                        </h1>
                        <p className="text-sm text-gray-400">
                            Plataforma IntelliCare
                        </p>
                    </div>

                    {/* Divider */}
                    <div className="flex items-center gap-3 mb-6">
                        <div className="flex-1 h-px bg-white/10" />
                        <span className="text-xs text-gray-500 uppercase tracking-wider">
                            Acesso Seguro
                        </span>
                        <div className="flex-1 h-px bg-white/10" />
                    </div>

                    {/* Login button */}
                    <button
                        onClick={handleLogin}
                        disabled={isLoading}
                        className="w-full py-3.5 px-6 rounded-xl font-semibold text-white
                       transition-all duration-300 ease-out
                       hover:scale-[1.02] hover:shadow-xl
                       active:scale-[0.98]
                       disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100
                       flex items-center justify-center gap-3"
                        style={{
                            background: `linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor})`,
                            boxShadow: `0 4px 20px ${config.primaryColor}40`,
                        }}
                    >
                        {isLoading ? (
                            <>
                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                <span>Conectando...</span>
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                                </svg>
                                <span>Entrar com SSO</span>
                            </>
                        )}
                    </button>

                    {/* Help text */}
                    <p className="text-center text-xs text-gray-500 mt-6">
                        Autenticação segura via Keycloak SSO.
                        <br />
                        Seus dados estão protegidos.
                    </p>
                </div>

                {/* Footer */}
                <div className="text-center mt-6">
                    <p className="text-xs text-gray-600">
                        Powered by{' '}
                        <a
                            href="https://intellicare.ia.br"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-gray-400 transition-colors"
                            style={{ color: config.accentColor }}
                        >
                            IntelliCare
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}
