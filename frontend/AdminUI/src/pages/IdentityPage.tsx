import { useMemo, useState } from 'react'
import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconRefresh } from '@tabler/icons-react'

import { useIdentityStats, useReconcileIdentity } from '../hooks/useIdentity'

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Paper withBorder p="md" radius="md">
      <Text size="sm" c="dimmed">{label}</Text>
      <Title order={3}>{value}</Title>
    </Paper>
  )
}

export function IdentityPage() {
  const { data, isLoading } = useIdentityStats()
  const reconcile = useReconcileIdentity()
  const [opened, setOpened] = useState(false)

  const totalLinked = useMemo(
    () => (data?.patients_linked ?? 0) + (data?.professionals_linked ?? 0),
    [data],
  )

  const handleReconcile = async (scope: 'patients' | 'professionals' | 'all') => {
    try {
      const result = await reconcile.mutateAsync(scope)
      notifications.show({
        title: 'Reconciliação concluída',
        message: `processed=${result.processed}, linked=${result.linked}, skipped=${result.skipped}`,
        color: 'green',
      })
      setOpened(false)
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Falha ao executar reconciliação de identidades.',
        color: 'red',
      })
    }
  }

  if (isLoading) {
    return <Center><Loader /></Center>
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <div>
          <Title order={2}>Identidade Centralizada</Title>
          <Text c="dimmed">
            Monitore cobertura de pessoa_id e rode o backfill dos registros legados.
          </Text>
        </div>
        <Button
          leftSection={<IconRefresh size={16} />}
          onClick={() => setOpened(true)}
          loading={reconcile.isPending}
        >
          Reconciliar
        </Button>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <StatCard label="Total pessoas" value={data?.total_pessoas ?? 0} />
        <StatCard label="Vinculos pacientes" value={`${data?.patients_linked ?? 0} / ${data?.patients_total ?? 0}`} />
        <StatCard label="Vinculos profissionais" value={`${data?.professionals_linked ?? 0} / ${data?.professionals_total ?? 0}`} />
        <StatCard label="Cobertura geral" value={`${data?.coverage_pct ?? 0}%`} />
      </SimpleGrid>

      <Paper withBorder p="md" radius="md">
        <Text size="sm" c="dimmed">
          Registros vinculados no ecossistema: {totalLinked}
        </Text>
      </Paper>

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Tenant</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Pacientes</Table.Th>
            <Table.Th>Profissionais</Table.Th>
            <Table.Th>Cobertura</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {(data?.tenants ?? []).map((tenant) => (
            <Table.Tr key={tenant.slug}>
              <Table.Td>{tenant.slug}</Table.Td>
              <Table.Td>
                <Badge color={tenant.status === 'active' ? 'green' : 'gray'} variant="light">
                  {tenant.status}
                </Badge>
              </Table.Td>
              <Table.Td>{tenant.patients_linked} / {tenant.patients_total}</Table.Td>
              <Table.Td>{tenant.professionals_linked} / {tenant.professionals_total}</Table.Td>
              <Table.Td>{tenant.coverage_pct}%</Table.Td>
            </Table.Tr>
          ))}
          {(data?.tenants ?? []).length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={5}>
                <Text ta="center" c="dimmed">Nenhum tenant encontrado.</Text>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Reconciliar identidades">
        <Stack>
          <Text size="sm" c="dimmed">
            Essa ação processa registros legados com CPF preenchido e pessoa_id nulo.
          </Text>
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setOpened(false)}>Cancelar</Button>
            <Button variant="light" onClick={() => void handleReconcile('patients')} loading={reconcile.isPending}>
              Pacientes
            </Button>
            <Button variant="light" onClick={() => void handleReconcile('professionals')} loading={reconcile.isPending}>
              Profissionais
            </Button>
            <Button onClick={() => void handleReconcile('all')} loading={reconcile.isPending}>
              Tudo
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
