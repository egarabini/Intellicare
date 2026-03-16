import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Group {
  id: number
  name: string
  specialty: string | null
  unit_id: number | null
  unit_name: string | null
  description: string | null
  status: string
  member_count: number
}

export interface GroupMember {
  professional_id: number
  name: string
  council_type: string
  council_number: string
  specialty: string
  added_at: string
}

export function useGroups() {
  return useQuery<Group[]>({
    queryKey: ['groups'],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/groups')
      return data
    },
  })
}

export function useGroup(id: number | string) {
  return useQuery<Group>({
    queryKey: ['group', id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/groups/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useGroupMembers(groupId: number | string) {
  return useQuery<GroupMember[]>({
    queryKey: ['group', groupId, 'members'],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/groups/${groupId}/members`)
      return data
    },
    enabled: !!groupId,
  })
}

export function useCreateGroup() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Partial<Group>) => {
      const { data } = await apiClient.post('/cuidado/groups', body)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['groups'] }),
  })
}

export function useUpdateGroup(id: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: Partial<Group>) => {
      const { data } = await apiClient.patch(`/cuidado/groups/${id}`, body)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['groups'] })
      qc.invalidateQueries({ queryKey: ['group', id] })
    },
  })
}

export function useToggleGroupStatus(id: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.patch(`/cuidado/groups/${id}/status`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['groups'] })
      qc.invalidateQueries({ queryKey: ['group', id] })
    },
  })
}

export function useAddMember(groupId: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (professionalId: number) => {
      const { data } = await apiClient.post(`/cuidado/groups/${groupId}/members`, {
        professional_id: professionalId,
      })
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['group', groupId, 'members'] })
      qc.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useRemoveMember(groupId: number | string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (professionalId: number) => {
      const { data } = await apiClient.delete(`/cuidado/groups/${groupId}/members/${professionalId}`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['group', groupId, 'members'] })
      qc.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}
