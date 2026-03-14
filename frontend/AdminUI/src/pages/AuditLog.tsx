import { useState } from 'react'
import { Title, Stack, Table, Text, Select, Group, Badge, Pagination } from '@mantine/core'
import { useAuditLog } from '../hooks/useTenants'

const ACTION_COLORS: Record<string, string> = {
  TENANT_CREATED:    'green',
  TENANT_SUSPENDED:  'orange',
  TENANT_ACTIVATED:  'blue',
  TENANT_DELETED:    'red',
  USER_INVITED:      'teal',
  USER_DEACTIVATED:  'red',
}

export function AuditLog() {
  const [page, setPage] = useState(1)
  const [filterAction, setFilterAction] = useState<string | null>(null)
  const { data } = useAuditLog(page, filterAction ?? undefined)

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Audit Log</Title>
        <Select
          placeholder="Filtrar por ação"
          clearable
          data={Object.keys(ACTION_COLORS)}
          value={filterAction}
          onChange={setFilterAction}
          w={220}
        />
      </Group>

      <Table withTableBorder striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Data/Hora</Table.Th>
            <Table.Th>Ator</Table.Th>
            <Table.Th>Ação</Table.Th>
            <Table.Th>Alvo</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {data?.items.map((entry: any) => (
            <Table.Tr key={entry.id}>
              <Table.Td>
                <Text size="sm">{new Date(entry.created_at).toLocaleString('pt-BR')}</Text>
              </Table.Td>
              <Table.Td>
                <Text size="sm" ff="monospace">{entry.actor_email ?? entry.actor_id}</Text>
              </Table.Td>
              <Table.Td>
                <Badge color={ACTION_COLORS[entry.action] ?? 'gray'} variant="light">
                  {entry.action}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Text size="sm">{entry.target_id ?? '—'}</Text>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <Pagination
        total={Math.ceil((data?.total ?? 0) / 50)}
        value={page}
        onChange={setPage}
      />
    </Stack>
  )
}
