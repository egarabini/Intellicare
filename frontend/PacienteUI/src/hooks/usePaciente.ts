import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface PacientePainel {
  patient_name: string
  next_appointment: {
    scheduled_at: string
    clinician_name: string
    type: string
  } | null
  clinic_notice: string | null
  upcoming_count: number
  past_count: number
}

export interface PacienteAppointment {
  id: string
  scheduled_at: string
  clinician_name: string
  type: string
  status: string
}

export interface PacienteJourney {
  correlation_id: string
  channel: string
  status: string
  template_name: string | null
  opened_at: string
  closed_at: string | null
}

export interface PacienteClinicalNote {
  encounter_date: string
  professional_name: string
  summary: string
}

export function usePainel() {
  return useQuery({
    queryKey: ['paciente', 'painel'],
    queryFn: async () => {
      const { data } = await apiClient.get<PacientePainel>('/cuidado/paciente/painel')
      return data
    },
    refetchInterval: 30_000,
  })
}

export function useAppointments(status: 'upcoming' | 'past') {
  return useQuery({
    queryKey: ['paciente', 'appointments', status],
    queryFn: async () => {
      const { data } = await apiClient.get<PacienteAppointment[]>('/cuidado/paciente/appointments', { params: { status } })
      return data
    },
    refetchInterval: 30_000,
  })
}

export function useConfirmAppointment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (apptId: string) => {
      const { data } = await apiClient.patch(`/cuidado/paciente/appointments/${apptId}/confirm`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['paciente', 'appointments'] })
      qc.invalidateQueries({ queryKey: ['paciente', 'painel'] })
    },
  })
}

export function useCancelAppointment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (apptId: string) => {
      const { data } = await apiClient.delete(`/cuidado/paciente/appointments/${apptId}`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['paciente', 'appointments'] })
      qc.invalidateQueries({ queryKey: ['paciente', 'painel'] })
    },
  })
}

export function useHistorico(page: number, size: number) {
  return useQuery({
    queryKey: ['paciente', 'history', page, size],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/history', { params: { page, size } })
      return data
    },
  })
}

export function useJourneys(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['paciente', 'journeys', limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get<PacienteJourney[]>('/cuidado/paciente/me/journeys', {
        params: { limit, offset },
      })
      return data
    },
  })
}

export function useClinicalNotes(limit = 20) {
  return useQuery({
    queryKey: ['paciente', 'clinical-notes', limit],
    queryFn: async () => {
      const { data } = await apiClient.get<PacienteClinicalNote[]>('/cuidado/paciente/me/clinical-notes', {
        params: { limit },
      })
      return data
    },
  })
}

export function usePrograms() {
  return useQuery({
    queryKey: ['paciente', 'programs'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/programs')
      return data
    },
  })
}

export function useMe() {
  return useQuery({
    queryKey: ['paciente', 'me'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/me')
      return data
    },
  })
}

export function useUpdateMe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { email?: string; phone?: string }) => {
      const { data } = await apiClient.patch('/cuidado/paciente/me', body)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['paciente', 'me'] }),
  })
}

export function useClinicInfo() {
  return useQuery({
    queryKey: ['paciente', 'clinic-info'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/clinic-info')
      return data
    },
  })
}
