import {
  Center,
  Grid,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { useQuery } from '@tanstack/react-query'

import apiClient from '../api/client'
import { useDocuments } from '../hooks/useDocuments'
import { useUsers } from '../hooks/useUsers'

interface UsageData {
  total_queries: number
  avg_latency_ms: number
  period_start: string | null
  period_end: string | null
  top_queries: string[]
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent: string }) {
  return (
    <Paper withBorder radius="lg" p="lg" style={{ borderTop: `4px solid ${accent}` }}>
      <Stack gap={4}>
        <Text size="sm" c="dimmed">{label}</Text>
        <Title order={2}>{value}</Title>
      </Stack>
    </Paper>
  )
}

export function Dashboard() {
  const { data: users, isLoading: loadingUsers } = useUsers()
  const { data: docs, isLoading: loadingDocs } = useDocuments()
  const { data: usage, isLoading: loadingUsage } = useQuery<UsageData>({
    queryKey: ['usage-report'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/reports/usage')
      return data
    },
  })

  if (loadingUsers || loadingDocs || loadingUsage) {
    return <Center mt="xl"><Loader /></Center>
  }

  return (
    <Stack gap="xl">
      <Stack gap={4}>
        <Title order={2}>Dashboard</Title>
        <Text c="dimmed">Visao geral da unidade de saude.</Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, md: 3 }}>
        <StatCard label="Usuarios" value={users?.length ?? 0} accent="#0f766e" />
        <StatCard label="Documentos RAG" value={docs?.length ?? 0} accent="#2563eb" />
        <StatCard label="Queries SLM (30d)" value={usage?.total_queries ?? 0} accent="#7c3aed" />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Paper withBorder p="lg" radius="md">
            <Stack gap="sm">
              <Title order={4}>Latencia media</Title>
              <Text size="xl" fw={700}>
                {usage?.avg_latency_ms ? `${Math.round(usage.avg_latency_ms)} ms` : '—'}
              </Text>
            </Stack>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Paper withBorder p="lg" radius="md">
            <Stack gap="sm">
              <Title order={4}>Top queries</Title>
              {usage?.top_queries?.length ? (
                usage.top_queries.map((q, i) => (
                  <Text key={i} size="sm" c="dimmed">{i + 1}. {q}</Text>
                ))
              ) : (
                <Text size="sm" c="dimmed">Nenhuma query registrada.</Text>
              )}
            </Stack>
          </Paper>
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
