import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export function usePainel() {
  return useQuery({
    queryKey: ['paciente', 'painel'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/painel')
      return data
    },
  })
}

export function useAppointments(status: 'upcoming' | 'past') {
  return useQuery({
    queryKey: ['paciente', 'appointments', status],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/paciente/appointments', { params: { status } })
      return data
    },
  })
}

export function useConfirmAppointment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (apptId: string) => {
      const { data } = await apiClient.patch(`/cuidado/paciente/appointments/${apptId}/confirm`)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['paciente', 'appointments'] }),
  })
}

export function useCancelAppointment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (apptId: string) => {
      const { data } = await apiClient.delete(`/cuidado/paciente/appointments/${apptId}`)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['paciente', 'appointments'] }),
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

