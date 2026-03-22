/**
 * DEM-071 — Linha do Tempo Clínica
 * View temporal unificada: Encounters + Florence Notes + Oswaldo Prescriptions + CarePlanner Tasks
 */
import { useState } from 'react'
import {
  Timeline, Text, Badge, Card, Group, Stack, Loader, Center,
  Button, Select, Box, Tooltip, ThemeIcon, Pagination,
} from '@mantine/core'
import {
  IconStethoscope, IconNotes, IconPill, IconMessage,
  IconFilter, IconCalendar,
} from '@tabler/icons-react'
import { useClinicalTimeline, type TimelineEvent } from '../hooks/usePatients'

const PAGE_SIZE = 50

const EVENT_CONFIG: Record<string, { icon: typeof IconStethoscope; color: string; label: string }> = {
  encounter:     { icon: IconStethoscope, color: 'blue',   label: 'Consulta' },
  clinical_note: { icon: IconNotes,       color: 'teal',   label: 'Nota Clínica' },
  prescription:  { icon: IconPill,        color: 'violet',  label: 'Prescrição' },
  care_task:     { icon: IconMessage,     color: 'orange', label: 'Jornada' },
}

function statusColor(status: string | null): string {
  if (!status) return 'gray'
  const s = status.toLowerCase()
  if (s === 'open' || s === 'active' || s === 'sent' || s === 'replied') return 'green'
  if (s === 'closed' || s === 'completed') return 'blue'
  if (s === 'draft' || s === 'created' || s === 'dispatched') return 'yellow'
  if (s === 'failed' || s === 'expired') return 'red'
  return 'gray'
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

interface Props {
  patientId: string
}

export function ClinicalTimeline({ patientId }: Props) {
  const [filter, setFilter] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const offset = (page - 1) * PAGE_SIZE

  const { data, isLoading, isError } = useClinicalTimeline(patientId, PAGE_SIZE, offset)

  if (isLoading) return <Center py="xl"><Loader /></Center>
  if (isError || !data) return <Text c="red">Erro ao carregar linha do tempo.</Text>

  const filtered = filter
    ? data.items.filter((e) => e.event_type === filter)
    : data.items

  const totalPages = Math.ceil((filter ? filtered.length : data.total) / PAGE_SIZE)

  // Group events by date for visual separation
  const grouped = new Map<string, TimelineEvent[]>()
  for (const ev of filtered) {
    const dateKey = formatDate(ev.occurred_at)
    const arr = grouped.get(dateKey) ?? []
    arr.push(ev)
    grouped.set(dateKey, arr)
  }

  return (
    <Stack gap="md">
      {/* Filter bar */}
      <Group justify="space-between">
        <Group gap="xs">
          <IconFilter size={16} />
          <Select
            placeholder="Todos os tipos"
            clearable
            size="xs"
            w={200}
            value={filter}
            onChange={setFilter}
            data={[
              { value: 'encounter',     label: 'Consultas' },
              { value: 'clinical_note', label: 'Notas Clínicas' },
              { value: 'prescription',  label: 'Prescrições' },
              { value: 'care_task',     label: 'Jornadas' },
            ]}
          />
        </Group>
        <Text size="sm" c="dimmed">{data.total} eventos no total</Text>
      </Group>

      {filtered.length === 0 ? (
        <Text c="dimmed" ta="center" py="xl">Nenhum evento clínico registrado.</Text>
      ) : (
        <>
          {Array.from(grouped.entries()).map(([dateLabel, events]) => (
            <Box key={dateLabel}>
              <Group gap="xs" mb="xs">
                <IconCalendar size={14} color="gray" />
                <Text size="sm" fw={600} c="dimmed">{dateLabel}</Text>
              </Group>

              <Timeline active={events.length - 1} bulletSize={28} lineWidth={2} ml="sm">
                {events.map((ev) => {
                  const cfg = EVENT_CONFIG[ev.event_type] ?? EVENT_CONFIG.encounter
                  const Icon = cfg.icon
                  return (
                    <Timeline.Item
                      key={`${ev.event_type}-${ev.event_id}`}
                      bullet={
                        <Tooltip label={cfg.label}>
                          <ThemeIcon size={28} variant="light" color={cfg.color} radius="xl">
                            <Icon size={14} />
                          </ThemeIcon>
                        </Tooltip>
                      }
                    >
                      <Card withBorder shadow="xs" radius="sm" p="sm">
                        <Group justify="space-between" wrap="nowrap">
                          <Box style={{ flex: 1, minWidth: 0 }}>
                            <Group gap="xs">
                              <Text size="sm" fw={600} truncate>{ev.title}</Text>
                              {ev.status && (
                                <Badge size="xs" color={statusColor(ev.status)} variant="light">
                                  {ev.status}
                                </Badge>
                              )}
                            </Group>
                            {ev.subtitle && (
                              <Text size="xs" c="dimmed" lineClamp={2} mt={2}>
                                {ev.subtitle}
                              </Text>
                            )}
                          </Box>
                          <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                            {formatTime(ev.occurred_at)}
                          </Text>
                        </Group>
                        {ev.metadata?.cid10_code && (
                          <Badge size="xs" color="cyan" mt={4}>
                            CID: {ev.metadata.cid10_code}
                          </Badge>
                        )}
                        {ev.metadata?.item_count != null && (
                          <Text size="xs" c="dimmed" mt={2}>
                            {ev.metadata.item_count} {ev.metadata.item_count === 1 ? 'medicamento' : 'medicamentos'}
                          </Text>
                        )}
                      </Card>
                    </Timeline.Item>
                  )
                })}
              </Timeline>
            </Box>
          ))}

          {totalPages > 1 && (
            <Center>
              <Pagination total={totalPages} value={page} onChange={setPage} size="sm" />
            </Center>
          )}
        </>
      )}
    </Stack>
  )
}
