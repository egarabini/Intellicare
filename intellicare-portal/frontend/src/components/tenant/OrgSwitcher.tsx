/**
 * OrgSwitcher — Botão para trocar de organização.
 * 
 * Aparece no Header quando o usuário pertence a múltiplas organizações.
 * Permite trocar de organização sem fazer re-login.
 */

import { useState, useRef, useEffect } from 'react';
import { Building2, ChevronDown, Check, RefreshCw } from 'lucide-react';
import { useTenant } from './TenantProvider';

// ─── Styles ─────────────────────────────────────────────────

const styles = {
    wrapper: {
        position: 'relative' as const,
        display: 'inline-block',
    },
    trigger: {
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.5rem 0.75rem',
        borderRadius: '0.75rem',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        background: 'rgba(99, 102, 241, 0.1)',
        color: '#c7d2fe',
        cursor: 'pointer',
        fontSize: '0.85rem',
        fontWeight: 500,
        transition: 'all 0.2s ease',
    } as React.CSSProperties,
    triggerHover: {
        background: 'rgba(99, 102, 241, 0.2)',
        borderColor: 'rgba(99, 102, 241, 0.5)',
    } as React.CSSProperties,
    dropdown: {
        position: 'absolute' as const,
        top: 'calc(100% + 0.5rem)',
        right: 0,
        minWidth: '240px',
        background: 'rgba(30, 41, 59, 0.95)',
        backdropFilter: 'blur(20px)',
        borderRadius: '1rem',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
        padding: '0.5rem',
        zIndex: 50,
    } as React.CSSProperties,
    dropdownItem: (isActive: boolean) => ({
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.75rem 1rem',
        borderRadius: '0.5rem',
        cursor: 'pointer',
        transition: 'background 0.15s ease',
        background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
        color: isActive ? '#c7d2fe' : '#94a3b8',
    }) as React.CSSProperties,
    label: {
        fontSize: '0.75rem',
        color: '#64748b',
        padding: '0.5rem 1rem 0.25rem',
        fontWeight: 600,
        textTransform: 'uppercase' as const,
        letterSpacing: '0.05em',
    },
    orgName: {
        fontSize: '0.85rem',
        fontWeight: 500,
        flex: 1,
    },
};

// ─── Helpers ────────────────────────────────────────────────

function formatTenantName(tenantId: string): string {
    return tenantId
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ─── Component ──────────────────────────────────────────────

export default function OrgSwitcher() {
    const { tenant, availableTenants, isMultiOrg, selectTenant } = useTenant();
    const [open, setOpen] = useState(false);
    const [hover, setHover] = useState(false);
    const [switching, setSwitching] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    // Se não é multi-org, não renderiza
    if (!isMultiOrg || !tenant) return null;

    // Fechar dropdown ao clicar fora
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false);
            }
        }
        if (open) document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [open]);

    const handleSwitch = async (tenantId: string) => {
        if (tenantId === tenant.tenantId) {
            setOpen(false);
            return;
        }
        setSwitching(true);
        try {
            await selectTenant(tenantId);
        } catch (err) {
            console.error('Failed to switch org:', err);
        }
        setSwitching(false);
        setOpen(false);
    };

    return (
        <div style={styles.wrapper} ref={ref}>
            <button
                style={{ ...styles.trigger, ...(hover ? styles.triggerHover : {}) }}
                onClick={() => setOpen(!open)}
                onMouseEnter={() => setHover(true)}
                onMouseLeave={() => setHover(false)}
                title="Trocar organização"
            >
                <Building2 size={16} />
                <span>{formatTenantName(tenant.tenantId)}</span>
                <ChevronDown
                    size={14}
                    style={{
                        transition: 'transform 0.2s',
                        transform: open ? 'rotate(180deg)' : 'none',
                    }}
                />
            </button>

            {open && (
                <div style={styles.dropdown}>
                    <div style={styles.label}>Organizações</div>
                    {availableTenants.map((id) => (
                        <div
                            key={id}
                            style={styles.dropdownItem(id === tenant.tenantId)}
                            onClick={() => handleSwitch(id)}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => e.key === 'Enter' && handleSwitch(id)}
                        >
                            <Building2 size={16} />
                            <span style={styles.orgName}>
                                {formatTenantName(id)}
                            </span>
                            {id === tenant.tenantId && <Check size={16} color="#6366f1" />}
                            {switching && id !== tenant.tenantId && (
                                <RefreshCw size={14} className="animate-spin" />
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
