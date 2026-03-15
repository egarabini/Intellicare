import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import apiClient from '../api/client'

export interface FinanceiroDashboard {
  receita_mes: number
  despesa_mes: number
  resultado_mes: number
  inadimplencia: number
  historico: Array<{
    mes: string
    receita: number
    despesa: number
    resultado: number
  }>
}

export interface Invoice {
  id: string
  contract_id: string
  tenant_slug: string
  amount_brl: number
  amount_brl_display: number
  due_date: string
  paid_at: string | null
  status: 'paid' | 'overdue' | 'cancelled' | 'pending'
  period_start: string
  period_end: string
  created_at: string
}

export interface Expense {
  id: number
  category: 'infrastructure' | 'license' | 'personnel' | 'other'
  description: string
  amount_brl: number
  amount_brl_display: number
  expense_date: string
  tenant_slug: string | null
  created_at: string
}

export interface PagedResult<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface ExpensePayload {
  category: Expense['category']
  description: string
  amount_brl: number
  expense_date: string
  tenant_slug?: string | null
}

export function useFinanceiroDashboard() {
  return useQuery<FinanceiroDashboard>({
    queryKey: ['financeiro-dashboard'],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/financeiro/dashboard')
      return data
    },
  })
}

export function useInvoices(page = 1, size = 20, status?: string, tenantSlug?: string) {
  return useQuery<PagedResult<Invoice>>({
    queryKey: ['invoices', page, size, status, tenantSlug],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/invoices', {
        params: { page, size, status, tenant_slug: tenantSlug },
      })
      return data
    },
  })
}

export function useUpdateInvoiceStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: Invoice['status'] }) =>
      apiClient.patch(`/admin/invoices/${id}/status`, { status }).then((r) => r.data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['invoices'] }),
  })
}

export function useExpenses(page = 1, size = 20) {
  return useQuery<PagedResult<Expense>>({
    queryKey: ['expenses', page, size],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/expenses', { params: { page, size } })
      return data
    },
  })
}

export function useCreateExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ExpensePayload) => apiClient.post('/admin/expenses', payload).then((r) => r.data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['expenses'] })
      void qc.invalidateQueries({ queryKey: ['financeiro-dashboard'] })
    },
  })
}

export function useUpdateExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ExpensePayload> }) =>
      apiClient.patch(`/admin/expenses/${id}`, payload).then((r) => r.data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['expenses'] })
      void qc.invalidateQueries({ queryKey: ['financeiro-dashboard'] })
    },
  })
}

export function useDeleteExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiClient.delete(`/admin/expenses/${id}`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['expenses'] })
      void qc.invalidateQueries({ queryKey: ['financeiro-dashboard'] })
    },
  })
}
