import { useState, useEffect, useCallback } from 'react';
import { donabedianApi } from '@services/donabedian';
import { useDashboardStore } from '@store/dashboardStore';
import type { DiseaseDashboardData } from '@/types/index';
import { generateMockDashboardData } from '@utils/mockData';

/**
 * Hook to fetch disease dashboard data based on current filters.
 * Falls back to mock data when the API is unavailable.
 */
export function useDiseaseData() {
  const { filters } = useDashboardStore();
  const [data, setData] = useState<DiseaseDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await donabedianApi.getDashboard(filters);
      setData(result);
    } catch (err) {
      console.warn('[useDiseaseData] API unavailable, using mock data:', err);
      // Fallback to mock data for development
      const mockData = generateMockDashboardData(filters.disease, filters.period);
      setData(mockData);
      setError(null); // Don't show error when mocks are available
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
