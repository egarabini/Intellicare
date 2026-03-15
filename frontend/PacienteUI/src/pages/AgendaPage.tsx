import { useState } from 'react'
import {
  Badge, Button, Card, Group, Loader, SegmentedControl, Stack, Table, Text, Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useAppointments, useConfirmAppointment, useCancelAppointment } from '../hooks/usePaciente'

const STATUS_COLOR: Record<string, string> = {
  agendado: 'blue',
  confirmado: 'green',
  cancelado: 'red',
  concluido: 'gray',
}

export function AgendaPage() {
  const [tab, setTab] = useState<'upcoming' | 'past'>('upcoming')
  const { data, isLoading } = useAppointments(tab)
  const confirm = useConfirmAppointment()
  const cancel = useCancelAppointment()

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Title order={2}>Agenda</Title>
        <SegmentedControl
          value={tab}
          onChange={(v) => setTab(v as 'upcoming' | 'past')}
          data={[
            { label: 'Próximas', value: 'upcoming' },
            { label: 'Anteriores', value: 'past' },
          ]}
        />
      </Group>

      {isLoading ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !data?.length ? (
        <Card withBorder padding="lg"><Text c="dimmed">Nenhum agendamento encontrado.</Text></Card>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Data</Table.Th>
              <Table.Th>Horário</Table.Th>
              <Table.Th>Tipo</Table.Th>
              <Table.Th>Status</Table.Th>
              {tab === 'upcoming' && <Table.Th>Ações</Table.Th>}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data.map((a: any) => (
              <Table.Tr key={a.id}>
                <Table.Td>{new Date(a.scheduled_at).toLocaleDateString('pt-BR')}</Table.Td>
                <Table.Td>{new Date(a.scheduled_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</Table.Td>
                <Table.Td>{a.type ?? 'consulta'}</Table.Td>
                <Table.Td>
                  <Badge color={STATUS_COLOR[a.status] ?? 'gray'} variant="light">{a.status}</Badge>
                </Table.Td>
                {tab === 'upcoming' && (
                  <Table.Td>
                    <Group gap="xs">
                      {a.status === 'agendado' && (
                        <Button
                          size="xs" variant="light" color="green"
                          loading={confirm.isPending}
                          onClick={() => confirm.mutate(a.id, {
                            onSuccess: () => notifications.show({ message: 'Confirmado!', color: 'green' }),
                          })}
                        >
                          Confirmar
                        </Button>
                      )}
                      {['agendado', 'confirmado'].includes(a.status) && (
                        <Button
                          size="xs" variant="light" color="red"
                          loading={cancel.isPending}
                          onClick={() => cancel.mutate(a.id, {
                            onSuccess: () => notifications.show({ message: 'Cancelado', color: 'orange' }),
                          })}
                        >
                          Cancelar
                        </Button>
                      )}
                    </Group>
                  </Table.Td>
                )}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  )
}

