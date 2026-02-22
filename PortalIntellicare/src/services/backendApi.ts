import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1';

const backendApi: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

backendApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

backendApi.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface ApiErrorResponse {
  success: false;
  error: string;
  details?: unknown;
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

export interface CnesEstablishment {
  cnes: string;
  cnpj: string | null;
  razaoSocial: string;
  nomeFantasia: string | null;
  tipoUnidade: string;
  uf: string;
  municipio: string;
  endereco: string | null;
  telefone: string | null;
  latitude: number | null;
  longitude: number | null;
  recursos: {
    centroCirurgico: boolean;
    centroObstetrico: boolean;
    centroNeonatal: boolean;
    atendimentoHospitalar: boolean;
    servicoApoio: boolean;
    atendimentoAmbulatorial: boolean;
  };
}

export interface CreateRequestData {
  requesterName: string;
  requesterEmail: string;
  requesterPhone?: string;
  requesterDocument?: string;
  cnes: string;
  cnpj?: string;
  establishmentName: string;
  establishmentType?: string;
  uf: string;
  municipality: string;
  address?: string;
  phone?: string;
  requestType: 'ACCESS_REQUEST' | 'DATA_CORRECTION' | 'TECHNICAL_SUPPORT' | 'INTEGRATION_REQUEST' | 'OTHER';
  description: string;
  priority?: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
}

export interface RequestResponse {
  id: string;
  protocol: string;
  status: string;
  message: string;
}

export interface RequestLog {
  status: string;
  message: string;
  createdAt: string;
}

export interface RequestStatus {
  protocol: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  emailVerified: boolean;
  requesterName: string;
  requesterEmail: string;
  establishmentName: string;
  requestType: string;
  description: string;
  logs: RequestLog[];
}

export const cnesApi = {
  validate: async (cnes: string): Promise<ApiSuccessResponse<CnesEstablishment>> => {
    const response = await backendApi.get(`/cnes/validate/${cnes}`);
    return response.data;
  },

  searchEstablishments: async (params: {
    uf?: string;
    municipio?: string;
    tipo?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiSuccessResponse<unknown[]>> => {
    const response = await backendApi.get('/cnes/establishments', { params });
    return response.data;
  },

  getUnitTypes: async (): Promise<ApiSuccessResponse<unknown[]>> => {
    const response = await backendApi.get('/cnes/unit-types');
    return response.data;
  },
};

export const requestsApi = {
  create: async (data: CreateRequestData): Promise<ApiSuccessResponse<RequestResponse>> => {
    const response = await backendApi.post('/requests', data);
    return response.data;
  },

  verifyToken: async (protocol: string, token: string): Promise<ApiSuccessResponse<{ protocol: string; status: string; message: string }>> => {
    const response = await backendApi.post('/requests/verify', { protocol, token });
    return response.data;
  },

  resendToken: async (protocol: string): Promise<ApiSuccessResponse<{ message: string }>> => {
    const response = await backendApi.post('/requests/resend-token', { protocol });
    return response.data;
  },

  getStatus: async (protocol: string): Promise<ApiSuccessResponse<RequestStatus>> => {
    const response = await backendApi.get(`/requests/${protocol}`);
    return response.data;
  },

  getByEmail: async (email: string): Promise<ApiSuccessResponse<Array<{
    protocol: string;
    status: string;
    createdAt: string;
    updatedAt: string;
    establishmentName: string;
    requestType: string;
  }>>> => {
    const response = await backendApi.get(`/requests/by-email/${email}`);
    return response.data;
  },
};

export const authApi = {
  login: async (email: string, protocol: string): Promise<ApiSuccessResponse<{ token: string; protocol: string; email: string }>> => {
    const response = await backendApi.post('/auth/login', { email, protocol });
    return response.data;
  },
};

export const statusApi = {
  getStatus: async (): Promise<ApiSuccessResponse<{
    api: string;
    version: string;
    timestamp: string;
    requests: {
      total: number;
      byStatus: Record<string, number>;
    };
  }>> => {
    const response = await backendApi.get('/status');
    return response.data;
  },

  getStats: async (): Promise<ApiSuccessResponse<{
    totalRequests: number;
    verifiedRequests: number;
    pendingVerification: number;
    requestsToday: number;
  }>> => {
    const response = await backendApi.get('/status/stats');
    return response.data;
  },
};

export { backendApi };
export default backendApi;
