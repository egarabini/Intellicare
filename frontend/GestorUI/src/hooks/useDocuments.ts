import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface DocumentStat {
  source_path: string
  chunk_count: number
  last_ingested_at: string
}

export function useDocuments() {
  return useQuery<DocumentStat[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/documents')
      return data
    },
  })
}

export function useUploadDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const { data } = await apiClient.post('/gestor/documents/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (path: string) => {
      const { data } = await apiClient.delete(`/gestor/documents/${encodeURIComponent(path)}`)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}
