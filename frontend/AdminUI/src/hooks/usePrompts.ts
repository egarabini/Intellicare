import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface PromptTemplateVersion {
  id: string
  prompt_key: string
  version: number
  content: string
  notes?: string | null
  is_active: boolean
  created_at: string
  created_by?: string | null
  created_by_email?: string | null
  activated_at?: string | null
  activated_by?: string | null
  activated_by_email?: string | null
}

export interface PromptTemplateGroup {
  prompt_key: string
  active_version?: number | null
  versions: PromptTemplateVersion[]
}

export function usePrompts() {
  return useQuery<{ items: PromptTemplateGroup[] }>({
    queryKey: ['prompts'],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/prompts')
      return data
    },
  })
}

export function useCreatePromptVersion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { prompt_key: string; content: string; notes?: string }) =>
      apiClient.post('/admin/prompts', body).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['prompts'] }),
  })
}

export function useActivatePrompt() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ promptKey, version }: { promptKey: string; version: number }) =>
      apiClient.post(`/admin/prompts/${promptKey}/activate`, { version }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['prompts'] }),
  })
}

export function useRollbackPrompt() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (promptKey: string) =>
      apiClient.post(`/admin/prompts/${promptKey}/rollback`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['prompts'] }),
  })
}
