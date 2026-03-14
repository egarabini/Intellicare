import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Patient {
  id: number
  full_name: string
  birth_date: string
  cpf: string
  phone: string | null
}

export function usePatients(search: string) {
  return useQuery<Patient[]>({
    queryKey: ['patients', search],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/patients', {
        params: { q: search, limit: 20 },
      })
      return data
    },
    enabled: search.length >= 3,
    staleTime: 30_000,
  })
}
