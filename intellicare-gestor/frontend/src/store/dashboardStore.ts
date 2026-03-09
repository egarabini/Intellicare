import { create } from 'zustand';
import type { DashboardFilters, DiseaseCode } from '@/types/index';

interface DashboardState {
  filters: DashboardFilters;
  setDisease: (disease: DiseaseCode) => void;
  setPeriod: (period: DashboardFilters['period']) => void;
  setEstablishment: (establishment: string | undefined) => void;
  setRegion: (region: string | undefined) => void;
  setStage: (stage: string | undefined) => void;
  setStatus: (status: string | undefined) => void;
  setSearch: (search: string) => void;
  setPage: (page: number) => void;
  resetFilters: () => void;
}

const DEFAULT_FILTERS: DashboardFilters = {
  disease: 'drc',
  period: '90d',
  page: 1,
  pageSize: 20,
};

export const useDashboardStore = create<DashboardState>((set) => ({
  filters: { ...DEFAULT_FILTERS },
  setDisease: (disease) => set((s) => ({ filters: { ...s.filters, disease, page: 1 } })),
  setPeriod: (period) => set((s) => ({ filters: { ...s.filters, period, page: 1 } })),
  setEstablishment: (establishment) =>
    set((s) => ({ filters: { ...s.filters, establishment, page: 1 } })),
  setRegion: (region) => set((s) => ({ filters: { ...s.filters, region, page: 1 } })),
  setStage: (stage) => set((s) => ({ filters: { ...s.filters, stage, page: 1 } })),
  setStatus: (status) => set((s) => ({ filters: { ...s.filters, status, page: 1 } })),
  setSearch: (search) => set((s) => ({ filters: { ...s.filters, search, page: 1 } })),
  setPage: (page) => set((s) => ({ filters: { ...s.filters, page } })),
  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),
}));
