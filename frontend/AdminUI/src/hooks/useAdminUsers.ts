import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface AdminUser {
  id: number
  keycloak_id: string | null
  email: string
  name: string
  role: 'admin' | 'financ' | 'coordenador'
  status: 'active' | 'inactive'
  last_login_at: string | null
  created_at: string
  temporary_password?: string
}

export interface AdminUserPayload {
  email: string
  name: string
  role: AdminUser['role']
  status: AdminUser['status']
}

export function useAdminUsers() {
  return useQuery<AdminUser[]>({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/users')
      return data
    },
  })
}

export function useCreateAdminUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AdminUserPayload) => apiClient.post('/admin/users', payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}

export function useUpdateAdminUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Omit<AdminUserPayload, 'email'>> }) =>
      apiClient.patch(`/admin/users/${id}`, payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}

export function useDeleteAdminUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/admin/users/${id}`),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}
