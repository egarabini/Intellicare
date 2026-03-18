import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

export interface CareTask {
  correlation_id: string
  task_type: string
  status: string
  patient_ref: string
  clinico_ref: string | null
  created_at: string
  updated_at: string | null
  kestra_execution_id: string | null
}

export interface CareEvent {
  id: number
  event_type: string
  recorded_at: string
  payload: Record<string, unknown> | null
}

export interface CareTaskDetail {
  task: CareTask
  conversation: { phone_e164: string | null } | null
  events: CareEvent[]
}

export interface CareTaskList {
  items: CareTask[]
  total: number
  page: number
}

export function useCareplannerTasks(statusFilter?: string, page = 1) {
  return useQuery<CareTaskList>({
    queryKey: ['cp-tasks-clinico', statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      const res = await api.get(`/careplanner/tasks?${params}`)
      return res.data
    },
  })
}

export function useCareplannerTask(correlationId: string) {
  return useQuery<CareTaskDetail>({
    queryKey: ['cp-task-clinico', correlationId],
    queryFn: async () => {
      const res = await api.get(`/careplanner/tasks/${correlationId}`)
      return res.data
    },
    enabled: !!correlationId,
  })
}

export function useVideoSessionClinico(correlationId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['cp-video-clinico', correlationId],
    queryFn: async () => {
      const res = await api.get(`/careplanner/consultations/video/${correlationId}`)
      return res.data as { clinico_url: string; patient_url: string; expired: boolean }
    },
    enabled,
  })
}
