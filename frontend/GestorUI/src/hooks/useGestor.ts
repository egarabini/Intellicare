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

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface CareTask {
  id: string;
  correlation_id: string;
  kestra_execution_id: string | null;
  patient_ref: string;
  task_type: string;
  status: string;
  channel: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface CareEvent {
  id: string;
  event_id: string;
  correlation_id: string;
  event_type: string;
  status: string | null;
  payload: Record<string, unknown>;
  recorded_at: string;
}

export interface CareConversation {
  id: string;
  correlation_id: string;
  channel: string;
  channel_conversation_id: number;
  rc_room_id: string | null;
  phone_e164: string | null;
  participant_role: string | null;
}

export interface CareTaskDetail {
  task: CareTask;
  conversation: CareConversation | null;
  events: CareEvent[];
}

export interface CareTaskList {
  items: CareTask[];
  page: number;
}

export interface TriggerJourneyPayload {
  patient_ref: string;
  task_type: string;
  template_code?: string;
  template_variables?: Record<string, string>;
  contact_phone_e164?: string;
  channel?: string;
  flow_id?: string;
  clinico_ref?: string;
}

export interface TriggerJourneyResult {
  ok: boolean;
  execution_id: string;
  flow_id: string;
  status: string;
}

export interface VideoSession {
  room_name: string;
  clinico_url: string;
  patient_url: string;
  expires_at: string;
  expired: boolean;
}

// ── Hooks ──────────────────────────────────────────────────────────────────

export function useCareplannerTasks(statusFilter: string | null, page: number) {
  return useQuery<CareTaskList>({
    queryKey: ['careplanner_tasks', statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status_filter', statusFilter);
      params.set('page', String(page));
      const { data } = await api.get(`/careplanner/tasks?${params.toString()}`);
      return data;
    },
    refetchInterval: 15_000,
  });
}

export function useCareplannerTask(correlationId: string) {
  return useQuery<CareTaskDetail>({
    queryKey: ['careplanner_task', correlationId],
    queryFn: async () => {
      const { data } = await api.get(`/careplanner/tasks/${correlationId}`);
      return data;
    },
    refetchInterval: 10_000,
  });
}

export interface VideoSessionCreate {
  correlation_id: string;
  clinico_url: string;
  patient_url: string;
  room_name: string;
  expires_at: string;
}

export function useVideoSession(correlationId: string, enabled: boolean) {
  return useQuery<VideoSession>({
    queryKey: ['careplanner_video', correlationId],
    queryFn: async () => {
      const { data } = await api.get(`/careplanner/consultations/video/${correlationId}`);
      return data;
    },
    enabled,
    retry: false,
  });
}

export function useCreateVideoSession(correlationId: string) {
  const queryClient = useQueryClient();
  return useMutation<VideoSessionCreate, Error>({
    mutationFn: async () => {
      const res = await api.post('/careplanner/consultations/video', {
        correlation_id: correlationId,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_video', correlationId] });
    },
  });
}

export function useTriggerJourney() {
  const queryClient = useQueryClient();
  return useMutation<TriggerJourneyResult, Error, TriggerJourneyPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/careplanner/journeys/trigger', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_tasks'] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_stats'] });
    },
  });
}

export function useCloseTask(correlationId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ ok: boolean; status: string }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/careplanner/tasks/${correlationId}/close`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_task', correlationId] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_tasks'] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_stats'] });
    },
  });
}

// ── Templates ─────────────────────────────────────────────────────────────

export interface CareTemplate {
  id: string;
  template_code: string;
  channel: string;
  content: string;
  variables: string[];
  active: boolean;
  tenant_slug: string;
  created_at: string;
  updated_at: string | null;
}

export interface CareTemplatePayload {
  template_code: string;
  channel?: string;
  content: string;
  variables: string[];
  active: boolean;
}

export function useTemplates(activeOnly = false) {
  return useQuery({
    queryKey: ['careplanner_templates', activeOnly],
    queryFn: async () => {
      const qs = activeOnly ? '?active=true' : '';
      const { data } = await api.get<{ items: CareTemplate[] }>(`/careplanner/templates${qs}`);
      return data.items;
    },
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CareTemplatePayload) => {
      const { data } = await api.post<CareTemplate>('/careplanner/templates', payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['careplanner_templates'] }),
  });
}

export function useUpdateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Omit<CareTemplatePayload, 'template_code' | 'channel'> }) => {
      const { data } = await api.put<CareTemplate>(`/careplanner/templates/${id}`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['careplanner_templates'] }),
  });
}

export function useToggleTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.patch<{ id: string; active: boolean }>(`/careplanner/templates/${id}/toggle`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['careplanner_templates'] }),
  });
}
