import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface UnitProfile {
  id: string
  name: string
  address: string | null
  city: string | null
  state: string | null
  unit_type: 'ubs' | 'clinic' | 'hospital' | 'specialty'
  phone: string | null
  email: string | null
  updated_at: string
}

export interface UnitProfileUpdate {
  name: string
  address?: string | null
  city?: string | null
  state?: string | null
  unit_type?: 'ubs' | 'clinic' | 'hospital' | 'specialty'
  phone?: string | null
  email?: string | null
}

export function useProfile() {
  return useQuery<UnitProfile>({
    queryKey: ['gestor-profile'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/profile')
      return data
    },
    retry: (count, error) => {
      if ((error as { response?: { status?: number } })?.response?.status === 404) return false
      return count < 2
    },
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: UnitProfileUpdate) => {
      const { data } = await apiClient.put('/gestor/profile', payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['gestor-profile'] }),
  })
}
