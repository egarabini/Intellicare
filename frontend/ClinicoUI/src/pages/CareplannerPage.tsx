import { useState } from 'react'
import { Box, Title, Table, Badge, Group, Text, Switch,
         Loader, Center, Pagination, Card } from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { useAuth } from 'react-oidc-context'
import { useCareplannerTasks } from '../hooks/useCareplanner'

const STATUS_COLOR: Record<string, string> = {
  CREATED: 'gray', DISPATCHED: 'blue', SENT: 'cyan',
  REPLIED: 'teal', CLOSED: 'green', FAILED: 'red', EXPIRED: 'orange',
}

export function CareplannerPage() {
  const [page, setPage] = useState(1)
  const [minhas, setMinhas] = useState(false)
  const navigate = useNavigate()
  const auth = useAuth()
  const myId = auth.user?.profile?.sub ?? ''

  const { data, isLoading } = useCareplannerTasks(undefined, page)

  const items = minhas
    ? (data?.items ?? []).filter(t => t.clinico_ref === myId)
    : (data?.items ?? [])

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group mb="md" justify="space-between">
        <Title order={2}>Jornadas CarePlanner</Title>
        <Switch
          label="Minhas Jornadas"
          checked={minhas}
          onChange={e => { setMinhas(e.currentTarget.checked); setPage(1) }}
        />
      </Group>

      <Card withBorder radius="md" p={0}>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Paciente</Table.Th>
              <Table.Th>Tipo</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Atualizado em</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((task) => (
              <Table.Tr
                key={task.correlation_id}
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/careplanner/${task.correlation_id}`)}
              >
                <Table.Td>{task.patient_ref}</Table.Td>
                <Table.Td>{task.task_type}</Table.Td>
                <Table.Td>
                  <Badge color={STATUS_COLOR[task.status] ?? 'gray'} variant="light">
                    {task.status}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">
                    {task.updated_at
                      ? new Date(task.updated_at).toLocaleString('pt-BR')
                      : '—'}
                  </Text>
                </Table.Td>
              </Table.Tr>
            ))}
            {items.length === 0 && (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Text c="dimmed" ta="center" py="md">Nenhuma jornada encontrada.</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Card>

      {data && data.total > 10 && (
        <Pagination
          mt="md"
          value={page}
          onChange={setPage}
          total={Math.ceil(data.total / 10)}
        />
      )}
    </Box>
  )
}
