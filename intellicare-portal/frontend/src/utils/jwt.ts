import { jwtDecode } from 'jwt-decode';

export interface DecodedToken {
  sub: string;
  email?: string;
  name?: string;
  preferred_username?: string;
  tenant_id?: string;
  tenants?: string[];
  realm_access?: {
    roles: string[];
  };
  resource_access?: Record<string, { roles: string[] }>;
  exp: number;
}

export const decodeToken = (token: string): DecodedToken | null => {
  try {
    return jwtDecode<DecodedToken>(token);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
};

export const hasRole = (token: string, role: string, resource?: string): boolean => {
  const decoded = decodeToken(token);
  if (!decoded) return false;

  if (resource && decoded.resource_access?.[resource]) {
    return decoded.resource_access[resource].roles.includes(role);
  }

  return decoded.realm_access?.roles.includes(role) || false;
};

export const getTenantId = (token: string): string | undefined => {
  return decodeToken(token)?.tenant_id;
};

export const getTenantsArray = (token: string): string[] => {
  return decodeToken(token)?.tenants || [];
};
