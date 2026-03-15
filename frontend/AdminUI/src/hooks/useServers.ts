import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface Server {
  id: number
  name: string
  type: 'vps' | 'dedicated' | 'cloud'
  provider: string
  region: string
  hostname: string | null
  vcpu: number
  ram_gb: number
  disk_gb: number
  cost_brl: number
  cost_brl_display: number
  status: 'active' | 'inactive' | 'maintenance'
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ServerPayload {
  name: string
  type: 'vps' | 'dedicated' | 'cloud'
  provider: string
  region: string
  hostname?: string | null
  vcpu: number
  ram_gb: number
  disk_gb: number
  cost_brl: number
  status: 'active' | 'inactive' | 'maintenance'
  notes?: string | null
}

export function useServers() {
  return useQuery<Server[]>({
    queryKey: ['servers'],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/servers')
      return data
    },
  })
}

export function useCreateServer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ServerPayload) => apiClient.post('/admin/servers', payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['servers'] }),
  })
}

export function useUpdateServer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ServerPayload> }) =>
      apiClient.patch(`/admin/servers/${id}`, payload).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['servers'] }),
  })
}

export function useDeleteServer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/admin/servers/${id}`),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['servers'] }),
  })
}
