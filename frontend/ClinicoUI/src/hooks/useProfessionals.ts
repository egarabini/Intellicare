import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Professional {
  id: number
  name: string
  council_type: string
  council_number: string
  specialty: string
  unit_id: number | null
  unit_name: string | null
  groups: string[]
  status: string
  keycloak_id: string | null
}

export function useProfessionals(filters?: {
  unit_id?: number; specialty?: string; group_id?: number; status?: string
}) {
  return useQuery<Professional[]>({
    queryKey: ['professionals', filters],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (filters?.unit_id) params.unit_id = String(filters.unit_id)
      if (filters?.specialty) params.specialty = filters.specialty
      if (filters?.group_id) params.group_id = String(filters.group_id)
      if (filters?.status) params.status = filters.status
      const { data } = await apiClient.get('/cuidado/professionals', { params })
      return data
    },
  })
}

export function useProfessional(id: number | string) {
  return useQuery<Professional>({
    queryKey: ['professional', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/professionals/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateProfessional() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Partial<Professional>) => {
      const { data } = await apiClient.post('/cuidado/professionals', body)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['professionals'] }),
  })
}

export function useUpdateProfessional(id: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Partial<Professional>) => {
      const { data } = await apiClient.patch(`/cuidado/professionals/${id}`, body)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['professionals'] })
      qc.invalidateQueries({ queryKey: ['professional', id] })
    },
  })
}

export function useToggleProfessionalStatus(id: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.patch(`/cuidado/professionals/${id}/status`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['professionals'] })
      qc.invalidateQueries({ queryKey: ['professional', id] })
    },
  })
}
