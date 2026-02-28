/**
 * WhiteLabelResolver — Resolve tenant from browser hostname.
 *
 * Used BEFORE authentication to determine which tenant's branding
 * to show on the login page. This runs client-side by inspecting
 * `window.location.hostname`.
 *
 * Flow:
 *   1. User visits hospital-abc.saudeconectada.com.br
 *   2. WhiteLabelResolver extracts "hospital-abc" from hostname
 *   3. Normalizes to "hospital_abc" (hyphen → underscore)
 *   4. Fetches branding config from API or cache
 *   5. TenantProvider applies branding (logo, colors, name)
 */

// ── Reserved subdomains (not tenant slugs) ────────────────────

const RESERVED_SUBDOMAINS = new Set([
    'www', 'admin', 'portal', 'api', 'keycloak', 'traefik',
    'grafana', 'prometheus', 'docs', 'status', 'mail', 'smtp',
    // Módulos IntelliCare
    'florence', 'oswaldo', 'zilda', 'donabedian', 'wanda',
    'comunicacao', 'geralda', 'grahame', 'minerva', 'pierre',
]);

// ── Known domains ─────────────────────────────────────────────

const PLATFORM_DOMAINS = [
    'intellicare.ia.br',
];

const MODULE_DOMAINS = [
    'saudeconectada.com.br',
];

const ALL_DOMAINS = [...PLATFORM_DOMAINS, ...MODULE_DOMAINS];

// ── Types ─────────────────────────────────────────────────────

export interface WhiteLabelConfig {
    /** Tenant slug (normalized, with underscores) */
    tenantId: string;
    /** Display name */
    displayName: string;
    /** Logo URL */
    logoUrl?: string;
    /** Primary brand color */
    primaryColor: string;
    /** Secondary brand color */
    secondaryColor: string;
    /** Accent color */
    accentColor: string;
    /** Background gradient (CSS) */
    backgroundGradient: string;
    /** Custom Keycloak realm (if tenant-specific) */
    keycloakRealm?: string;
    /** Favicon URL */
    faviconUrl?: string;
    /** Custom page title */
    pageTitle?: string;
}

export interface ResolvedWhiteLabel {
    /** Whether a tenant was resolved from the hostname */
    isWhiteLabel: boolean;
    /** Raw subdomain extracted */
    subdomain: string | null;
    /** Normalized tenant slug */
    tenantSlug: string | null;
    /** Source domain (platform or module) */
    sourceDomain: string | null;
    /** Branding config (loaded async) */
    config: WhiteLabelConfig | null;
}

// ── Default branding ──────────────────────────────────────────

const DEFAULT_BRANDING: Omit<WhiteLabelConfig, 'tenantId' | 'displayName'> = {
    primaryColor: '#6366f1',     // Indigo
    secondaryColor: '#8b5cf6',   // Violet
    accentColor: '#22d3ee',      // Cyan
    backgroundGradient: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
};

// ── Resolver ──────────────────────────────────────────────────

/**
 * Resolve tenant from current browser hostname.
 * This runs synchronously and does NOT require authentication.
 */
export function resolveWhiteLabelFromHostname(
    hostname: string = window.location.hostname
): ResolvedWhiteLabel {
    const host = hostname.toLowerCase().split(':')[0]; // Remove port

    for (const domain of ALL_DOMAINS) {
        if (host.endsWith(`.${domain}`)) {
            const subdomain = host.slice(0, -(domain.length + 1));

            // Skip reserved subdomains
            if (RESERVED_SUBDOMAINS.has(subdomain)) {
                return {
                    isWhiteLabel: false,
                    subdomain,
                    tenantSlug: null,
                    sourceDomain: domain,
                    config: null,
                };
            }

            // Normalize: hyphens → underscores
            const tenantSlug = subdomain.replace(/-/g, '_');

            // Validate slug format
            if (/^[a-z0-9][a-z0-9_]{2,63}$/.test(tenantSlug)) {
                return {
                    isWhiteLabel: true,
                    subdomain,
                    tenantSlug,
                    sourceDomain: domain,
                    config: null, // Will be loaded async
                };
            }
        }
    }

    // Root domain or unknown → not white-label
    return {
        isWhiteLabel: false,
        subdomain: null,
        tenantSlug: null,
        sourceDomain: null,
        config: null,
    };
}

// ── Branding Loader ───────────────────────────────────────────

// Cache for branding configs
const brandingCache = new Map<string, WhiteLabelConfig>();

/**
 * Load branding config for a tenant.
 * Tries API first, falls back to generated defaults.
 */
export async function loadWhiteLabelConfig(
    tenantSlug: string,
    apiBaseUrl?: string,
): Promise<WhiteLabelConfig> {
    // Check cache
    const cached = brandingCache.get(tenantSlug);
    if (cached) return cached;

    // Try loading from API
    if (apiBaseUrl) {
        try {
            const response = await fetch(
                `${apiBaseUrl}/api/v1/tenants/${tenantSlug}/branding`,
                { headers: { 'Accept': 'application/json' } }
            );
            if (response.ok) {
                const data = await response.json();
                const config: WhiteLabelConfig = {
                    tenantId: tenantSlug,
                    displayName: data.display_name || formatTenantName(tenantSlug),
                    logoUrl: data.logo_url,
                    primaryColor: data.primary_color || DEFAULT_BRANDING.primaryColor,
                    secondaryColor: data.secondary_color || DEFAULT_BRANDING.secondaryColor,
                    accentColor: data.accent_color || DEFAULT_BRANDING.accentColor,
                    backgroundGradient: data.background_gradient || DEFAULT_BRANDING.backgroundGradient,
                    keycloakRealm: data.keycloak_realm,
                    faviconUrl: data.favicon_url,
                    pageTitle: data.page_title,
                };
                brandingCache.set(tenantSlug, config);
                return config;
            }
        } catch (error) {
            console.warn(`[WhiteLabel] Failed to load branding for ${tenantSlug}:`, error);
        }
    }

    // Fallback: generate config from tenant slug
    const config = generateDefaultConfig(tenantSlug);
    brandingCache.set(tenantSlug, config);
    return config;
}

/**
 * Generate a unique branding config from tenant slug.
 * Uses a hash-based color generation for visual distinction.
 */
function generateDefaultConfig(tenantSlug: string): WhiteLabelConfig {
    const hash = simpleHash(tenantSlug);
    const hue = hash % 360;

    return {
        tenantId: tenantSlug,
        displayName: formatTenantName(tenantSlug),
        primaryColor: `hsl(${hue}, 65%, 55%)`,
        secondaryColor: `hsl(${(hue + 30) % 360}, 60%, 50%)`,
        accentColor: `hsl(${(hue + 180) % 360}, 70%, 60%)`,
        backgroundGradient: `linear-gradient(135deg, hsl(${hue}, 30%, 8%) 0%, hsl(${(hue + 30) % 360}, 25%, 12%) 50%, hsl(${hue}, 30%, 8%) 100%)`,
    };
}

/**
 * Simple hash for generating deterministic colors from strings.
 */
function simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit
    }
    return Math.abs(hash);
}

/**
 * Format tenant slug into a display name.
 * "hospital_sao_paulo" → "Hospital São Paulo"
 */
function formatTenantName(slug: string): string {
    if (!slug) return 'IntelliCare';

    return slug
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

// ── CSS Variable Injection ────────────────────────────────────

/**
 * Apply white-label branding to the document via CSS custom properties.
 * Call this after loading the config.
 */
export function applyWhiteLabelCSS(config: WhiteLabelConfig): void {
    const root = document.documentElement;

    root.style.setProperty('--wl-primary', config.primaryColor);
    root.style.setProperty('--wl-secondary', config.secondaryColor);
    root.style.setProperty('--wl-accent', config.accentColor);
    root.style.setProperty('--wl-bg-gradient', config.backgroundGradient);

    if (config.pageTitle) {
        document.title = config.pageTitle;
    }

    if (config.faviconUrl) {
        const link = document.querySelector<HTMLLinkElement>("link[rel~='icon']");
        if (link) {
            link.href = config.faviconUrl;
        }
    }
}

/**
 * Remove white-label CSS variables (restore defaults).
 */
export function removeWhiteLabelCSS(): void {
    const root = document.documentElement;
    root.style.removeProperty('--wl-primary');
    root.style.removeProperty('--wl-secondary');
    root.style.removeProperty('--wl-accent');
    root.style.removeProperty('--wl-bg-gradient');
}
