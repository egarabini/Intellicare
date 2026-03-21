import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended' | 'trial'
  gestor_email?: string
  created_at: string
  updated_at: string
}

export interface TenantUser {
  keycloak_id: string
  username: string
  email: string
  roles: string[]
  enabled: boolean
}

export interface TenantCreateRequest {
  name: string
  slug: string
  gestor_email: string
}

export interface PagedResult<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export function useTenants(page = 1, size = 20) {
  return useQuery<PagedResult<Tenant>>({
    queryKey: ['tenants', page, size],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/tenants', {
        params: { page, size },
      })
      return data
    },
  })
}

export function useTenant(slug: string) {
  return useQuery<Tenant>({
    queryKey: ['tenant', slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/admin/tenants/${slug}`)
      return data
    },
    enabled: !!slug,
  })
}

export function useCreateTenant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TenantCreateRequest) => apiClient.post('/admin/tenants', body).then((r) => r.data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
  })
}

export function useUpdateTenant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, body }: { slug: string; body: { name?: string; gestor_email?: string } }) =>
      apiClient.put(`/admin/tenants/${slug}`, body).then((r) => r.data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['tenants'] })
      void queryClient.invalidateQueries({ queryKey: ['tenant', variables.slug] })
    },
  })
}

export function useUpdateTenantStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, status }: { slug: string; status: string }) =>
      apiClient.patch(`/admin/tenants/${slug}/status`, { status }).then((r) => r.data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['tenants'] })
      void queryClient.invalidateQueries({ queryKey: ['tenant', variables.slug] })
    },
  })
}

export function useTenantUsers(slug: string) {
  return useQuery<{ tenant_slug: string; users: TenantUser[]; total: number }>({
    queryKey: ['tenant-users', slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/admin/tenants/${slug}/users`)
      return data
    },
    enabled: !!slug,
  })
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/admin/dashboard/stats').then(r => r.data),
    refetchInterval: 30_000,
  })
}

export function useInviteUser(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; name: string; role: string }) =>
      apiClient.post(`/admin/tenants/${slug}/users/invite`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users', slug] }),
  })
}

export function useDeactivateUser(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.patch(`/admin/tenants/${slug}/users/${userId}/deactivate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users', slug] }),
  })
}

export function useDeleteTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiClient.delete(`/admin/tenants/${slug}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  })
}

export function useSuspendTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiClient.post(`/admin/tenants/${slug}/suspend`).then(r => r.data),
    onSuccess: (_, slug) => {
      void qc.invalidateQueries({ queryKey: ['tenants'] })
      void qc.invalidateQueries({ queryKey: ['tenant', slug] })
    },
  })
}

export function useReactivateTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiClient.post(`/admin/tenants/${slug}/reactivate`).then(r => r.data),
    onSuccess: (_, slug) => {
      void qc.invalidateQueries({ queryKey: ['tenants'] })
      void qc.invalidateQueries({ queryKey: ['tenant', slug] })
    },
  })
}

export function useProvisionTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { slug: string; name: string; gestor_email: string }) =>
      apiClient.post('/admin/tenants/provision', body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  })
}

export interface TenantConfig {
  key: string
  value: string
}

export function useTenantConfig(slug: string) {
  return useQuery<{ tenant_slug: string; configs: TenantConfig[] }>({
    queryKey: ['tenant-config', slug],
    queryFn: () => apiClient.get(`/admin/tenants/${slug}/config`).then(r => r.data),
    enabled: !!slug,
  })
}

export function useSetTenantConfig(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: TenantConfig) =>
      apiClient.put(`/admin/tenants/${slug}/config/${body.key}`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-config', slug] }),
  })
}

export function useAuditLog(page = 1, action?: string) {
  return useQuery({
    queryKey: ['audit-log', page, action],
    queryFn: () => apiClient.get('/admin/audit', {
      params: { page, size: 50, action }
    }).then(r => r.data),
  })
}
