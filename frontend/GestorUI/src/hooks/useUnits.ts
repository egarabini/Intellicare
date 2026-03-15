import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

export interface Unit {
  id: number
  name: string
  type: 'ubs' | 'hospital' | 'clinic' | 'secretary' | 'other'
  cnes?: string | null
  address?: string | null
  city?: string | null
  state?: string | null
  phone?: string | null
  email?: string | null
  manager_user_id?: string | null
  status: 'active' | 'inactive'
  professional_count: number
  patient_count: number
  created_at?: string
  updated_at?: string
}

export interface UnitProfessional {
  professional_id: number
  name: string
  specialty?: string | null
  role_in_unit?: string | null
  workload_hours?: number | null
  allocated_at?: string
}

export function useUnits(status?: string) {
  return useQuery<Unit[]>({
    queryKey: ['units', status],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (status) params.status = status
      const { data } = await api.get<Unit[]>('/gestor/units', { params })
      return data
    },
  })
}

export function useUnit(id: number) {
  return useQuery<Unit>({
    queryKey: ['units', id],
    queryFn: async () => {
      const { data } = await api.get<Unit>(`/gestor/units/${id}`)
      return data
    },
    enabled: id > 0,
  })
}

export function useCreateUnit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Partial<Unit>) => {
      const { data } = await api.post<Unit>('/gestor/units', payload)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['units'] })
      qc.invalidateQueries({ queryKey: ['dashboard_stats'] })
    },
  })
}

export function useUpdateUnit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Partial<Unit> }) => {
      const { data } = await api.patch<Unit>(`/gestor/units/${id}`, payload)
      return data
    },
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['units'] })
      qc.invalidateQueries({ queryKey: ['units', id] })
      qc.invalidateQueries({ queryKey: ['dashboard_stats'] })
    },
  })
}

export function useToggleUnitStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.patch<Unit>(`/gestor/units/${id}/status`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['units'] })
      qc.invalidateQueries({ queryKey: ['dashboard_stats'] })
    },
  })
}

// Unit Professionals

export function useUnitProfessionals(unitId: number) {
  return useQuery<UnitProfessional[]>({
    queryKey: ['unit-professionals', unitId],
    queryFn: async () => {
      const { data } = await api.get<UnitProfessional[]>(`/gestor/units/${unitId}/professionals`)
      return data
    },
    enabled: unitId > 0,
  })
}

export function useAllocateProfessional() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ unitId, payload }: { unitId: number; payload: { professional_id: number; role_in_unit?: string; workload_hours?: number } }) => {
      const { data } = await api.post<UnitProfessional>(`/gestor/units/${unitId}/professionals`, payload)
      return data
    },
    onSuccess: (_, { unitId }) => {
      qc.invalidateQueries({ queryKey: ['unit-professionals', unitId] })
      qc.invalidateQueries({ queryKey: ['units'] })
    },
  })
}

export function useRemoveProfessional() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ unitId, profId }: { unitId: number; profId: number }) => {
      await api.delete(`/gestor/units/${unitId}/professionals/${profId}`)
    },
    onSuccess: (_, { unitId }) => {
      qc.invalidateQueries({ queryKey: ['unit-professionals', unitId] })
      qc.invalidateQueries({ queryKey: ['units'] })
    },
  })
}
