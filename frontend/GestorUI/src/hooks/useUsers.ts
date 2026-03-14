import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface TenantUser {
  id: string
  username: string
  email: string
  firstName?: string
  lastName?: string
  enabled: boolean
}

export interface InviteUserRequest {
  email: string
  name: string
  role: 'CLINICO' | 'PACIENTE'
}

export function useUsers() {
  return useQuery<TenantUser[]>({
    queryKey: ['gestor-users'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/users')
      return data
    },
  })
}

export function useInviteUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: InviteUserRequest) => {
      const { data } = await apiClient.post('/gestor/users/invite', payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gestor-users'] }),
  })
}

export function useDeactivateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      const { data } = await apiClient.patch(`/gestor/users/${userId}/deactivate`)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gestor-users'] }),
  })
}
