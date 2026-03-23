import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

export interface ClinicalKPIsResponse {
  encounters: number;
  notes: number;
  prescriptions: number;
  interactions_detected: number;
  journeys: Record<string, number>;
  top_professionals: { name: string; total: number }[];
  interactions_by_day: { day: string; total: number }[];
}

export function useClinicalKPIs(start: string, end: string, professional_id?: string) {
  return useQuery({
    queryKey: ['clinical_kpis', start, end, professional_id],
    queryFn: async () => {
      const params = new URLSearchParams({ start, end });
      if (professional_id) {
        params.set('professional_id', professional_id);
      }
      const { data } = await api.get<ClinicalKPIsResponse>(`/admin/kpis/clinical?${params.toString()}`);
      return data;
    },
    enabled: !!start && !!end,
  });
}
