import api, { handleApiError } from './api';
import type { SolicitacaoSecretaria } from '@/types/index';

export const secretariatService = {
  async create(data: Omit<SolicitacaoSecretaria, 'id' | 'status' | 'createdAt' | 'updatedAt'>) {
    try {
      const response = await api.post<SolicitacaoSecretaria>('/secretariats', data);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getAll() {
    try {
      const response = await api.get<SolicitacaoSecretaria[]>('/secretariats');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getById(id: string) {
    try {
      const response = await api.get<SolicitacaoSecretaria>(`/secretariats/${id}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async update(id: string, data: Partial<SolicitacaoSecretaria>) {
    try {
      const response = await api.put<SolicitacaoSecretaria>(`/secretariats/${id}`, data);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async delete(id: string) {
    try {
      await api.delete(`/secretariats/${id}`);
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },
};