import { Grid, Loader, Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core'

import { useTenants } from '../hooks/useTenants'
import { TenantList } from './TenantList'

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <Paper withBorder radius="lg" p="lg" style={{ borderTop: `4px solid ${accent}` }}>
      <Stack gap={4}>
        <Text size="sm" c="dimmed">
          {label}
        </Text>
        <Title order={2}>{value}</Title>
      </Stack>
    </Paper>
  )
}

export function DashboardPage() {
  const { data, isLoading } = useTenants(1, 100)

  if (isLoading) {
    return <Loader />
  }

  const items = data?.items ?? []
  const active = items.filter((item) => item.status === 'active').length
  const suspended = items.filter((item) => item.status === 'suspended').length

  return (
    <Stack gap="xl">
      <Stack gap={4}>
        <Title order={2}>Dashboard</Title>
        <Text c="dimmed">Visao geral da plataforma e dos tenants provisionados.</Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, md: 3 }}>
        <StatCard label="Total de tenants" value={items.length} accent="#0f766e" />
        <StatCard label="Tenants ativos" value={active} accent="#16a34a" />
        <StatCard label="Tenants suspensos" value={suspended} accent="#ea580c" />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={12}>
          <TenantList embedded />
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
