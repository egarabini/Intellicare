import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface ClinicalUser {
  id: number
  keycloak_id: string
  name: string
  email: string | null
  role: string
  status: string
}

export function useClinicalUsers() {
  return useQuery<ClinicalUser[]>({
    queryKey: ['clinical-users'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/clinical-users')
      return data
    },
  })
}

export function useTeamStats() {
  return useQuery<{ professionals_active: number; groups_active: number }>({
    queryKey: ['team-stats'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/dashboard-team-stats')
      return data
    },
  })
}
