import { createApiClient, moduleUrls } from './base';

const geraldaClient = createApiClient(moduleUrls.geralda);

export interface GeraldaPlan {
  id: string;
  patient_id: string;
  patient_name: string;
  goals: string[];
  conditions: string[];
  status: string;
}

export interface GeraldaTask {
  id: string;
  description: string;
  category: string;
  status: string;
  due_time?: string;
}

export const geraldaApi = {
  health: () => geraldaClient.request<{ status: string; version: string }>('/api/v1/health'),
  listPlans: (patientId?: string) =>
    geraldaClient.request<{ success: boolean; data: GeraldaPlan[]; total: number }>('/api/v1/plans', {
      query: { patient_id: patientId },
    }),
  listTasks: (planId: string) =>
    geraldaClient.request<{ success: boolean; data: GeraldaTask[]; total: number }>(`/api/v1/plans/${planId}/tasks`),
  adherence: (planId: string) =>
    geraldaClient.request<{ success: boolean; data: { completed_tasks: number; pending_tasks: number; adherence_rate: number } }>(
      `/api/v1/adherence/${planId}`,
    ),
  educationConditions: () =>
    geraldaClient.request<{ success: boolean; data: string[]; total: number }>('/api/v1/education/conditions'),
};
