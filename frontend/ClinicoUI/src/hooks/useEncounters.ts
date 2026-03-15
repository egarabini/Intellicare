import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Encounter {
  id: string
  patient_id: string
  status: 'open' | 'closed'
  opened_at: string
  closed_at: string | null
  cid10_code: string | null
  prescription: string | null
}

export interface Note {
  id: number
  encounter_id: string
  content: string
  created_at: string
}

export function useEncounterHistory(patientId: string) {
  return useQuery<Encounter[]>({
    queryKey: ['encounters', patientId],
    queryFn: async () => {
      // The old route was patients/:id/encounters, but wait, the profile returns history inside a tab, and before it was 'patients/{id}/history'.
      // Looking at usePatientHistory, it hits patients/{id}/history. Let's use that one.
      const { data } = await apiClient.get(`/cuidado/patients/${patientId}/history`)
      return data
    },
    enabled: !!patientId,
  })
}

export function useOpenEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (patientId: string) =>
      apiClient.post('/cuidado/encounters', { patient_id: patientId }).then(r => r.data),
    onSuccess: (_: unknown, patientId: string) =>
      qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}

export function useAddNote(encounterId: string) {
  return useMutation({
    mutationFn: (content: string) =>
      apiClient
        // Actually the backend consumes { subjective, objective, assessment, plan }. The old UI sent { content }.
        // I will map content to subjective to preserve compatibility with existing backend schema for testing, or adapt appropriately later.
        .post(`/cuidado/encounters/${encounterId}/notes`, { subjective: content })
        .then(r => r.data),
  })
}

export function useCloseEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ encounterId, patientId }: { encounterId: string; patientId: string }) =>
      apiClient.post(`/cuidado/encounters/${encounterId}/close`).then(r => r.data),
    onSuccess: (_: unknown, { patientId }: { encounterId: string; patientId: string }) =>
      qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}

export function useUpdateEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ encounterId, data }: { encounterId: string; data: any }) =>
      apiClient.patch(`/cuidado/encounters/${encounterId}`, data).then(r => r.data),
    onSuccess: (_: unknown, { encounterId }: { encounterId: string; data: any }) =>
      qc.invalidateQueries({ queryKey: ['encounters'] }),
  })
}

export function useSearchCid10(search: string) {
  return useQuery({
    queryKey: ['cid10', search],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/cid10?q=${search}&limit=20`)
      return data as { code: string; description: string }[]
    },
    enabled: search.length >= 2,
    staleTime: 60000,
  })
}
