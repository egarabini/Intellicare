import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

export interface AgendaItem {
  id: string;
  patient_id: string;
  patient_name: string;
  scheduled_at: string;
  type: string;
  status: string;
  encounter_id: string | null;
}

export function useMyAgenda(date?: string, from?: string, to?: string) {
  return useQuery({
    queryKey: ['agenda', date, from, to],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (date) params.append('date', date);
      if (from) params.append('from_', from);
      if (to) params.append('to', to);
      const { data } = await api.get<AgendaItem[]>(`/cuidado/my-agenda?${params.toString()}`);
      return data;
    }
  });
}
