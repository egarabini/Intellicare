import { Badge, Center, Loader, Paper, Stack, Text, Title } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'

import apiClient from '../api/client'

interface UsageData {
  period_start: string | null
  period_end: string | null
  total_queries: number
  avg_latency_ms: number
  top_queries: string[]
}

export function UsageReport() {
  const { data, isLoading } = useQuery<UsageData>({
    queryKey: ['usage-report'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/reports/usage')
      return data
    },
  })

  if (isLoading) return <Center><Loader /></Center>

  return (
    <Stack>
      <Title order={2}>Relatorio de Uso</Title>
      <Paper withBorder p="lg" radius="md">
        <Stack>
          <Text>
            <strong>Periodo:</strong>{' '}
            {data?.period_start
              ? `${new Date(data.period_start).toLocaleDateString('pt-BR')} — ${new Date(data.period_end!).toLocaleDateString('pt-BR')}`
              : 'Sem dados'}
          </Text>
          <Text><strong>Total de consultas:</strong> {data?.total_queries ?? 0}</Text>
          <Text>
            <strong>Tempo medio de resposta:</strong>{' '}
            {data?.avg_latency_ms ? `${Math.round(data.avg_latency_ms)} ms` : '—'}
          </Text>
          <Text fw={500}>Topicos mais consultados:</Text>
          <Stack gap={4}>
            {data?.top_queries?.length ? (
              data.top_queries.map((t, i) => (
                <Badge key={i} variant="light" size="sm">{t}</Badge>
              ))
            ) : (
              <Text size="sm" c="dimmed">Nenhuma query registrada no periodo.</Text>
            )}
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  )
}
