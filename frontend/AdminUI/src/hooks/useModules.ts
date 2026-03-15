import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface PlatformModule {
  id: number
  slug: string
  name: string
  description: string | null
  version: string
  status: 'active' | 'inactive' | 'dev'
  tenant_count: number
}

export interface TenantModule {
  tenant_slug: string
  module_slug: string
  name: string
  description: string | null
  version: string
  status: 'active' | 'inactive' | 'dev'
  enabled: boolean
  enabled_at: string | null
}

export function useModules() {
  return useQuery<PlatformModule[]>({
    queryKey: ['platform-modules'],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/modules')
      return data
    },
  })
}

export function useUpdateModuleStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, status }: { slug: string; status: PlatformModule['status'] }) =>
      apiClient.patch(`/admin/modules/${slug}/status`, { status }).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['platform-modules'] }),
  })
}

export function useTenantModules(tenantSlug: string) {
  return useQuery<TenantModule[]>({
    queryKey: ['tenant-modules', tenantSlug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/admin/tenants/${tenantSlug}/modules`)
      return data
    },
    enabled: !!tenantSlug,
  })
}

export function useUpdateTenantModule(tenantSlug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ moduleSlug, enabled }: { moduleSlug: string; enabled: boolean }) =>
      apiClient
        .patch(`/admin/tenants/${tenantSlug}/modules/${moduleSlug}`, { enabled })
        .then((r) => r.data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['tenant-modules', tenantSlug] })
      void qc.invalidateQueries({ queryKey: ['platform-modules'] })
    },
  })
}
