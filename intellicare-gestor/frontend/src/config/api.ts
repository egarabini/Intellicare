/** API base URLs — resolved from environment or defaults */
export const API_CONFIG = {
  /** Gestor backend */
  gestorUrl: import.meta.env.VITE_GESTOR_API_URL ?? '/api/v1/gestor',
  /** Donabedian backend (quality indicators + disease dashboards) */
  donabedianUrl: import.meta.env.VITE_DONABEDIAN_API_URL ?? '/api/v1/donabedian',
  /** Keycloak */
  keycloakUrl: import.meta.env.VITE_KEYCLOAK_URL ?? 'https://auth.intellicare.ia.br',
  keycloakRealm: import.meta.env.VITE_KEYCLOAK_REALM ?? 'bemcuidar',
  keycloakClientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? 'intellicare-gestor',
} as const;
