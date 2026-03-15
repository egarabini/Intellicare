import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

export interface TenantUser {
  id: number
  keycloak_id?: string | null
  email: string
  name: string
  role: 'gestor' | 'clinico' | 'recepcionista'
  unit_id?: number | null
  unit_name?: string | null
  status: 'active' | 'inactive'
  last_login_at?: string | null
  created_at?: string
}

export function useTenantUsers() {
  return useQuery<TenantUser[]>({
    queryKey: ['tenant-users'],
    queryFn: async () => {
      const { data } = await api.get<TenantUser[]>('/gestor/tenant-users')
      return data
    },
  })
}

export function useCreateTenantUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { email: string; name: string; role: string; unit_id?: number | null }) => {
      const { data } = await api.post<TenantUser>('/gestor/tenant-users', payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users'] }),
  })
}

export function useUpdateTenantUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<TenantUser> }) => {
      const { data } = await api.patch<TenantUser>(`/gestor/tenant-users/${id}`, payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users'] }),
  })
}

export function useDeleteTenantUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/gestor/tenant-users/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users'] }),
  })
}
