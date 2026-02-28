import { useCallback, useEffect, useState, type DependencyList } from 'react';

import { florenceApi, geraldaApi, grahameApi, wandaApi } from '@/services/moduleApi';

interface QueryState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function useAsyncData<T>(load: () => Promise<T>, deps: DependencyList): QueryState<T> {
  const [state, setState] = useState<QueryState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    load()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : 'Falha na requisição';
          setState({ data: null, loading: false, error: message });
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}

export function usePatient(patientId: string) {
  const load = useCallback(() => grahameApi.getResource('Patient', patientId), [patientId]);
  return useAsyncData(load, [load]);
}

export function useCarePlan(patientId: string) {
  const load = useCallback(async () => {
    const plans = await geraldaApi.listPlans(patientId);
    return plans.data;
  }, [patientId]);
  return useAsyncData(load, [load]);
}

export function useAlerts(patientId?: string) {
  const load = useCallback(async () => {
    const queue = await wandaApi.alertQueue(patientId);
    return queue.alerts || [];
  }, [patientId]);
  return useAsyncData(load, [load]);
}

export function useClinicalSummary() {
  const load = useCallback(() => florenceApi.panels(), []);
  return useAsyncData(load, [load]);
}
