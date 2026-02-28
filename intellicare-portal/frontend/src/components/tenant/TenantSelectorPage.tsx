/**
 * TenantSelectorPage — Tela de seleção de organização.
 * 
 * Exibida quando um usuário multi-org faz login e precisa
 * escolher em qual organização deseja acessar.
 * 
 * Exemplo: Dr. Luiz trabalha em Hospital Einstein, Hospital Sírio
 * e UBS Centro — esta tela mostra as 3 opções como cards.
 */

import { useState } from 'react';
import { Building2, ArrowRight, Loader2, Shield } from 'lucide-react';
import { useTenant } from './TenantProvider';

// ─── Styles ─────────────────────────────────────────────────

const styles = {
    container: {
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        padding: '2rem',
    } as React.CSSProperties,
    card: {
        background: 'rgba(30, 41, 59, 0.8)',
        backdropFilter: 'blur(20px)',
        borderRadius: '1.5rem',
        padding: '3rem',
        maxWidth: '600px',
        width: '100%',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    } as React.CSSProperties,
    title: {
        fontSize: '1.75rem',
        fontWeight: 700,
        color: '#f1f5f9',
        marginBottom: '0.5rem',
        textAlign: 'center' as const,
    },
    subtitle: {
        fontSize: '0.95rem',
        color: '#94a3b8',
        textAlign: 'center' as const,
        marginBottom: '2rem',
    },
    tenantCard: (isSelected: boolean, isLoading: boolean) => ({
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        padding: '1.25rem 1.5rem',
        borderRadius: '1rem',
        border: `2px solid ${isSelected ? '#6366f1' : 'rgba(148, 163, 184, 0.15)'}`,
        background: isSelected
            ? 'rgba(99, 102, 241, 0.1)'
            : 'rgba(15, 23, 42, 0.5)',
        cursor: isLoading ? 'wait' : 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: '0.75rem',
        opacity: isLoading && !isSelected ? 0.5 : 1,
    }) as React.CSSProperties,
    tenantIcon: {
        width: '48px',
        height: '48px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
    } as React.CSSProperties,
    tenantInfo: {
        flex: 1,
    },
    tenantName: {
        fontSize: '1.1rem',
        fontWeight: 600,
        color: '#f1f5f9',
    },
    tenantId: {
        fontSize: '0.8rem',
        color: '#64748b',
        fontFamily: 'monospace',
    },
    arrow: {
        color: '#6366f1',
        flexShrink: 0,
    },
    securityNote: {
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        fontSize: '0.8rem',
        color: '#64748b',
        marginTop: '1.5rem',
        textAlign: 'center' as const,
        justifyContent: 'center',
    },
};

// ─── Component ──────────────────────────────────────────────

function formatTenantName(tenantId: string): string {
    return tenantId
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function TenantSelectorPage() {
    const { availableTenants, selectTenant } = useTenant();
    const [selected, setSelected] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSelect = async (tenantId: string) => {
        setSelected(tenantId);
        setLoading(true);
        try {
            await selectTenant(tenantId);
        } catch (err) {
            console.error('Failed to select tenant:', err);
            setLoading(false);
            setSelected(null);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                    <Building2 size={40} color="#6366f1" />
                </div>

                <h1 style={styles.title}>Selecionar Organização</h1>
                <p style={styles.subtitle}>
                    Você tem acesso a múltiplas organizações. <br />
                    Escolha em qual deseja acessar agora.
                </p>

                <div>
                    {availableTenants.map((tenantId) => (
                        <div
                            key={tenantId}
                            style={styles.tenantCard(selected === tenantId, loading)}
                            onClick={() => !loading && handleSelect(tenantId)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => e.key === 'Enter' && !loading && handleSelect(tenantId)}
                        >
                            <div style={styles.tenantIcon}>
                                <Building2 size={24} color="white" />
                            </div>
                            <div style={styles.tenantInfo}>
                                <div style={styles.tenantName}>
                                    {formatTenantName(tenantId)}
                                </div>
                                <div style={styles.tenantId}>{tenantId}</div>
                            </div>
                            <div style={styles.arrow}>
                                {loading && selected === tenantId ? (
                                    <Loader2 size={20} className="animate-spin" />
                                ) : (
                                    <ArrowRight size={20} />
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <div style={styles.securityNote}>
                    <Shield size={14} />
                    <span>Você pode trocar de organização a qualquer momento.</span>
                </div>
            </div>
        </div>
    );
}
