import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Patient {
  id: string
  full_name: string
  birth_date: string
  cpf: string
  phone: string | null
  active?: boolean
  sex?: string
}

export interface PatientProfileData extends Patient {
  email?: string
  health_plan?: string
  allergies?: string
  medications?: string
  last_encounter?: string | null
  encounter_count: number
  programs: string[]
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

export function usePatientProfile(id: string) {
  return useQuery<PatientProfileData>({
    queryKey: ['patient', id, 'profile'],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/patients/${id}/profile`)
      return data
    },
    enabled: !!id,
  })
}

export function usePatientHistory(id: string) {
  return useQuery<any[]>({
    queryKey: ['patient', id, 'history'],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/patients/${id}/history`)
      return data
    },
    enabled: !!id,
  })
}

// ── DEM-071: Clinical Timeline ──────────────────────────────────────────

export interface TimelineEvent {
  event_type: 'encounter' | 'clinical_note' | 'prescription' | 'care_task'
  event_id: string
  occurred_at: string
  title: string
  subtitle: string | null
  status: string | null
  metadata: Record<string, any> | null
}

export interface ClinicalTimelineData {
  patient_id: string
  total: number
  items: TimelineEvent[]
}

export function useClinicalTimeline(patientId: string, limit = 50, offset = 0) {
  return useQuery<ClinicalTimelineData>({
    queryKey: ['patient', patientId, 'clinical-timeline', limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/cuidado/patients/${patientId}/clinical-timeline`,
        { params: { limit, offset } },
      )
      return data
    },
    enabled: !!patientId,
  })
}

export function useUpdatePatientClinical() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { allergies?: string; medications?: string } }) => {
      const resp = await apiClient.patch(`/cuidado/patients/${id}/clinical`, data)
      return resp.data
    },
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['patient', variables.id, 'profile'] })
    },
  })
}
