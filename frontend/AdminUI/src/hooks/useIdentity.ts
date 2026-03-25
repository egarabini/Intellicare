import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface IdentityTenantStats {
  slug: string
  status: string
  patients_linked: number
  patients_total: number
  professionals_linked: number
  professionals_total: number
  coverage_pct: number
}

export interface IdentityStatsResponse {
  total_pessoas: number
  patients_linked: number
  patients_total: number
  professionals_linked: number
  professionals_total: number
  coverage_pct: number
  tenants: IdentityTenantStats[]
}

export interface IdentityReconcileResult {
  processed: number
  linked: number
  skipped: number
  errors: Array<{
    tenant_slug: string
    scope: string
    record_id: string
    error: string
  }>
}

export function useIdentityStats() {
  return useQuery<IdentityStatsResponse>({
    queryKey: ['identity-stats'],
    queryFn: async () => {
      const { data } = await apiClient.get('/identity/admin/stats')
      return data
    },
  })
}

export function useReconcileIdentity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (scope: 'patients' | 'professionals' | 'all') => {
      const { data } = await apiClient.post(`/identity/admin/reconcile?scope=${scope}`)
      return data as IdentityReconcileResult
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['identity-stats'] })
    },
  })
}
