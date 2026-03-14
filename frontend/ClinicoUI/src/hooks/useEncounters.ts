import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Encounter {
  id: number
  patient_id: number
  status: 'open' | 'closed'
  started_at: string
  ended_at: string | null
}

export interface Note {
  id: number
  encounter_id: number
  content: string
  created_at: string
}

export function useEncounterHistory(patientId: number) {
  return useQuery<Encounter[]>({
    queryKey: ['encounters', patientId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/patients/${patientId}/encounters`)
      return data
    },
  })
}

export function useOpenEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (patientId: number) =>
      apiClient.post('/cuidado/encounters', { patient_id: patientId }).then(r => r.data),
    onSuccess: (_: unknown, patientId: number) =>
      qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}

export function useAddNote(encounterId: number) {
  return useMutation({
    mutationFn: (content: string) =>
      apiClient
        .post(`/cuidado/encounters/${encounterId}/notes`, { content })
        .then(r => r.data),
  })
}

export function useCloseEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ encounterId, patientId }: { encounterId: number; patientId: number }) =>
      apiClient.post(`/cuidado/encounters/${encounterId}/close`).then(r => r.data),
    onSuccess: (_: unknown, { patientId }: { encounterId: number; patientId: number }) =>
      qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}
