import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface TimelineEvent {
  event_type: 'encounter' | 'clinical_note' | 'prescription' | 'care_task'
  event_id: string
  occurred_at: string
  title: string
  subtitle: string | null
  status: string | null
  metadata: Record<string, unknown> | null
}

export interface PatientTimelineData {
  patient_id: string
  total: number
  items: TimelineEvent[]
}

export function usePatientTimeline(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['paciente', 'timeline', limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get<PatientTimelineData>(
        '/cuidado/paciente/me/timeline',
        { params: { limit, offset } },
      )
      return data
    },
  })
}
