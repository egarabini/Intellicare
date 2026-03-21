import {
  Badge, Card, Group, Loader, Stack, Table, Text, ThemeIcon, Title,
} from '@mantine/core'
import {
  IconBrandWhatsapp, IconMail, IconMessageCircle, IconMessageDots, IconPhone,
} from '@tabler/icons-react'
import { useJourneys } from '../hooks/usePaciente'

const CHANNEL_META: Record<string, { color: string; icon: typeof IconMessageCircle }> = {
  WHATSAPP: { color: 'green', icon: IconBrandWhatsapp },
  EMAIL: { color: 'blue', icon: IconMail },
  SMS: { color: 'orange', icon: IconPhone },
  ROCKETCHAT: { color: 'grape', icon: IconMessageDots },
}

const STATUS_COLORS: Record<string, string> = {
  CREATED: 'gray',
  OPEN: 'blue',
  DISPATCHED: 'cyan',
  SENT: 'teal',
  REPLIED: 'green',
  CLOSED: 'dark',
  EXPIRED: 'gray',
  FAILED: 'red',
}

export function JornadasPage() {
  const { data, isLoading } = useJourneys()
  const items = data ?? []

  return (
    <Stack gap="lg" data-testid="jornadas-page">
      <Title order={2}>Minhas Jornadas</Title>
      <Text size="sm" c="dimmed">
        Acompanhe os contatos do CarePlanner por canal, status e data de abertura.
      </Text>

      {isLoading ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !items.length ? (
        <Card withBorder padding="lg"><Text c="dimmed">Nenhuma jornada encontrada.</Text></Card>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Canal</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Template</Table.Th>
              <Table.Th>Abertura</Table.Th>
              <Table.Th>Fechamento</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {items.map((journey) => {
              const channel = CHANNEL_META[journey.channel] ?? { color: 'gray', icon: IconMessageCircle }
              const ChannelIcon = channel.icon
              return (
                <Table.Tr key={journey.correlation_id}>
                  <Table.Td>
                    <Group gap="xs">
                      <ThemeIcon variant="light" color={channel.color} size="md">
                        <ChannelIcon size={16} />
                      </ThemeIcon>
                      <Text size="sm">{journey.channel}</Text>
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLORS[journey.status] ?? 'gray'} variant="light">
                      {journey.status}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{journey.template_name ?? '—'}</Table.Td>
                  <Table.Td>{new Date(journey.opened_at).toLocaleString('pt-BR')}</Table.Td>
                  <Table.Td>{journey.closed_at ? new Date(journey.closed_at).toLocaleString('pt-BR') : '—'}</Table.Td>
                </Table.Tr>
              )
            })}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  )
}
