import { Grid, Loader, Paper, SimpleGrid, Stack, Text, Title, Card } from '@mantine/core'

import { useDashboardStats } from '../hooks/useTenants'
import { TenantList } from './TenantList'

function StatCard({ label, value, accent, isCurrency = false }: { label: string; value: number; accent: string, isCurrency?: boolean }) {
  const displayValue = isCurrency 
    ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
    : value;

  return (
    <Card withBorder radius="lg" p="lg" style={{ borderTop: `4px solid ${accent}` }}>
      <Stack gap={4}>
        <Text size="sm" c="dimmed">
          {label}
        </Text>
        <Title order={2}>{displayValue}</Title>
      </Stack>
    </Card>
  )
}

export function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()

  if (isLoading) {
    return <Loader />
  }

  return (
    <Stack gap="xl">
      <Stack gap={4}>
        <Title order={2}>Dashboard</Title>
        <Text c="dimmed">Visao geral da plataforma e dos tenants provisionados.</Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <StatCard label="Total de tenants" value={stats?.total_tenants ?? 0} accent="#0f766e" />
        <StatCard label="Tenants ativos" value={stats?.active_tenants ?? 0} accent="#16a34a" />
        <StatCard label="Tenants suspensos" value={stats?.suspended_tenants ?? 0} accent="#ea580c" />
        <StatCard label="Receita Mensal" value={stats?.monthly_revenue ?? 0} accent="#2563eb" isCurrency />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={12}>
          <TenantList embedded />
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
