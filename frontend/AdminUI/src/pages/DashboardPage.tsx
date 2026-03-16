import { Grid, Loader, Paper, SimpleGrid, Stack, Text, Title, Card } from '@mantine/core'

import { useDashboardStats } from '../hooks/useTenants'
import { TenantList } from './TenantList'
import { useDownloadPdf } from '../hooks/useDownloadPdf'
import { Button, Group } from '@mantine/core'
import { IconFileTypePdf } from '@tabler/icons-react'

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
  const { downloadPdf, isDownloading } = useDownloadPdf()

  if (isLoading) {
    return <Loader />
  }

  return (
    <Stack gap="xl">
      <Group justify="space-between" align="flex-start">
        <Stack gap={4}>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed">Visao geral da plataforma e dos tenants provisionados.</Text>
        </Stack>
        <Button
          leftSection={<IconFileTypePdf size={16} />}
          variant="light"
          color="red"
          loading={isDownloading}
          onClick={() => void downloadPdf('/admin/relatorios/tenants', 'tenants-ativos.pdf')}
        >
          Exportar Tenants (PDF)
        </Button>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <StatCard label="Total de tenants" value={stats?.total_tenants ?? 0} accent="#0f766e" />
        <StatCard label="Tenants ativos" value={stats?.active_tenants ?? 0} accent="#16a34a" />
        <StatCard label="Tenants suspensos" value={stats?.suspended_tenants ?? 0} accent="#ea580c" />
        <StatCard label="Receita Mensal" value={stats?.monthly_revenue ?? 0} accent="#2563eb" isCurrency />
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <StatCard label="Servidores ativos" value={stats?.servers_active ?? 0} accent="#7c3aed" />
        <StatCard label="Custo infra mensal" value={stats?.infra_cost_monthly ?? 0} accent="#b45309" isCurrency />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={12}>
          <TenantList embedded />
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
