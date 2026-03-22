import { useState } from 'react'
import {
  Badge, Button, Card, Group, Loader, Stack, Text, Timeline, Title,
} from '@mantine/core'
import {
  IconStethoscope, IconNotes, IconPill, IconBell,
} from '@tabler/icons-react'
import { usePatientTimeline, TimelineEvent } from '../hooks/usePatientTimeline'

const EVENT_ICON: Record<string, React.ReactNode> = {
  encounter: <IconStethoscope size={16} />,
  clinical_note: <IconNotes size={16} />,
  prescription: <IconPill size={16} />,
  care_task: <IconBell size={16} />,
}

const EVENT_COLOR: Record<string, string> = {
  encounter: 'blue',
  clinical_note: 'teal',
  prescription: 'grape',
  care_task: 'orange',
}

const EVENT_LABEL: Record<string, string> = {
  encounter: 'Consulta',
  clinical_note: 'Nota Clínica',
  prescription: 'Prescrição',
  care_task: 'Jornada',
}

function handleOpenReceituario(prescriptionId: string) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
  window.open(
    `${baseUrl}/oswaldo/paciente/me/prescriptions/${prescriptionId}/receituario.pdf?type=simple`,
    '_blank',
  )
}

export function HistoricoPage() {
  const PAGE_SIZE = 20
  const [offset, setOffset] = useState(0)
  const [allItems, setAllItems] = useState<TimelineEvent[]>([])
  const { data, isLoading } = usePatientTimeline(PAGE_SIZE, offset)

  const items = offset === 0 ? (data?.items ?? []) : allItems
  const total = data?.total ?? 0

  // First load: sync items
  if (offset === 0 && data?.items && allItems.length === 0 && data.items.length > 0) {
    setAllItems(data.items)
  }

  const handleLoadMore = () => {
    const nextOffset = offset + PAGE_SIZE
    setOffset(nextOffset)
    if (data?.items) {
      setAllItems(prev => [...prev, ...data.items])
    }
  }

  const displayItems = offset === 0 ? (data?.items ?? []) : allItems
  const hasMore = displayItems.length < total

  return (
    <Stack gap="lg" data-testid="historico-page">
      <Title order={2}>Meu Histórico</Title>
      <Text size="sm" c="dimmed">
        Linha do tempo das suas consultas, notas clínicas, prescrições e jornadas de cuidado.
        A avaliação clínica interna não é exibida.
      </Text>

      {isLoading && offset === 0 ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !displayItems.length ? (
        <Card withBorder padding="lg"><Text c="dimmed">Nenhum registro encontrado.</Text></Card>
      ) : (
        <>
          <Timeline active={displayItems.length} bulletSize={28} lineWidth={2} data-testid="historico-timeline">
            {displayItems.map((event) => (
              <Timeline.Item
                key={`${event.event_type}-${event.event_id}`}
                bullet={EVENT_ICON[event.event_type] ?? <IconNotes size={16} />}
                color={EVENT_COLOR[event.event_type] ?? 'gray'}
                title={
                  <Group gap="xs">
                    <Text size="sm">
                      {new Date(event.occurred_at).toLocaleDateString('pt-BR')}
                    </Text>
                    <Badge size="xs" variant="light" color={EVENT_COLOR[event.event_type]}>
                      {EVENT_LABEL[event.event_type] ?? event.event_type}
                    </Badge>
                    {event.status && (
                      <Badge size="xs" variant="outline" color="gray">{event.status}</Badge>
                    )}
                  </Group>
                }
              >
                <Text size="sm" fw={600}>{event.title}</Text>
                {event.subtitle && (
                  <Text size="sm" c="dimmed" mt={2}>{event.subtitle}</Text>
                )}
                {event.metadata?.cid10_code && (
                  <Badge size="xs" color="blue" variant="light" mt={4}>
                    CID: {String(event.metadata.cid10_code)}
                  </Badge>
                )}
                {event.event_type === 'prescription' && (
                  <Button
                    variant="light"
                    size="xs"
                    mt="xs"
                    leftSection={<IconPill size={14} />}
                    onClick={() => handleOpenReceituario(event.event_id)}
                    data-testid={`btn-receituario-${event.event_id}`}
                  >
                    Baixar Receituário
                  </Button>
                )}
              </Timeline.Item>
            ))}
          </Timeline>

          {hasMore && (
            <Group justify="center">
              <Button variant="subtle" onClick={handleLoadMore} loading={isLoading}>
                Carregar mais
              </Button>
            </Group>
          )}
        </>
      )}
    </Stack>
  )
}
