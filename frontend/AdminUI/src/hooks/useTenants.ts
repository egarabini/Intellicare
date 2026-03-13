import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended' | 'trial'
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
