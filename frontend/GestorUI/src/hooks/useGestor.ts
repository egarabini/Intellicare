import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';

// types
export interface DashboardStats {
  patients_active: number;
  appointments_today: number;
  appointments_week: number;
  appointments_month: number;
  invoices_pending_count: number;
  invoices_pending_total: number;
  rag_documents_count: number;
  units_active: number;
  professionals_allocated: number;
  recent_activity: any[];
}

export interface CareplannerStats {
  total: number;
  by_status: Record<string, number>;
  recent_tasks: {
    correlation_id: string;
    patient_ref: string;
    task_type: string;
    status: string;
    updated_at: string | null;
  }[];
}

export interface Patient {
  id: string;
  name: string;
  cpf: string;
  birth_date: string;
  email?: string;
  phone?: string;
  health_plan?: string;
  active: boolean;
  created_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  clinician_id: string;
  scheduled_at: string;
  type: 'consulta' | 'retorno' | 'exame';
  status: 'agendado' | 'confirmado' | 'realizado' | 'cancelado';
  notes?: string;
}

export interface Invoice {
  id: string;
  amount: number;
  status: string;
  created_at: string;
  paid_at?: string;
}

export interface Program {
  id: string;
  name: string;
  description?: string;
  eligibility_criteria?: string;
  active: boolean;
}

// Hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard_stats'],
    queryFn: async () => {
      const { data } = await api.get<DashboardStats>('/gestor/dashboard/stats');
      return data;
    },
    refetchInterval: 60000,
  });
}

export function useCareplannerStats() {
  return useQuery<CareplannerStats>({
    queryKey: ['careplanner_stats'],
    queryFn: async () => {
      const { data } = await api.get('/careplanner/dashboard/stats');
      return data;
    },
    refetchInterval: 30_000,
  });
}

// Patients
export function usePatients(page = 1, size = 20, q = '') {
  return useQuery({
    queryKey: ['patients', page, size, q],
    queryFn: async () => {
      const { data } = await api.get<Patient[]>('/gestor/patients', { params: { page, size, q } });
      return data;
    },
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: ['patients', id],
    queryFn: async () => {
      const { data } = await api.get<Patient>(`/gestor/patients/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Patient>) => {
      const { data } = await api.post<Patient>('/gestor/patients', payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['patients'] }),
  });
}

export function useUpdatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<Patient> }) => {
      const { data } = await api.patch<Patient>(`/gestor/patients/${id}`, payload);
      return data;
    },
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['patients'] });
      qc.invalidateQueries({ queryKey: ['patients', id] });
    },
  });
}

export function useDeactivatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/gestor/patients/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['patients'] }),
  });
}

// Appointments
export function useAppointments(date?: string, clinician_id?: string) {
  return useQuery({
    queryKey: ['appointments', date, clinician_id],
    queryFn: async () => {
      const { data } = await api.get<Appointment[]>('/gestor/appointments', { params: { date, clinician_id } });
      return data;
    },
  });
}

export function useCreateAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Appointment>) => {
      const { data } = await api.post<Appointment>('/gestor/appointments', payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['appointments'] }),
  });
}

export function useUpdateAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<Appointment> }) => {
      const { data } = await api.patch<Appointment>(`/gestor/appointments/${id}`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['appointments'] }),
  });
}

export function useCancelAppointment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/gestor/appointments/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['appointments'] }),
  });
}

// Invoices
export function useInvoices(page = 1, size = 20, status?: string) {
  return useQuery({
    queryKey: ['invoices', page, size, status],
    queryFn: async () => {
      const params: any = { page, size };
      if (status) params.status = status;
      const { data } = await api.get<Invoice[]>('/gestor/invoices', { params });
      return data;
    },
  });
}

export function useMarkInvoicePaid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.patch(`/gestor/invoices/${id}/mark-paid`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invoices'] }),
  });
}

// Programs
export function usePrograms() {
  return useQuery({
    queryKey: ['programs'],
    queryFn: async () => {
      const { data } = await api.get<Program[]>('/gestor/programs');
      return data;
    },
  });
}

// Clinicians (using /gestor/users)
export function useClinicians() {
  return useQuery({
    queryKey: ['clinicians'],
    queryFn: async () => {
      const { data } = await api.get<any[]>('/gestor/users');
      return data;
    },
  });
}

export function useInviteClinician() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { email: string; name: string }) => {
      const { data } = await api.post('/gestor/users/invite', { ...payload, role: 'CLINICO' });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clinicians'] }),
  });
}

export function useDeactivateClinician() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/gestor/users/${id}/deactivate`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clinicians'] }),
  });
}
