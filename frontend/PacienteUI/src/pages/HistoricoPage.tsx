import {
  Card, Group, Loader, Stack, Text, Timeline, Title,
} from '@mantine/core'
import { IconClipboardHeart } from '@tabler/icons-react'
import { useClinicalNotes } from '../hooks/usePaciente'

export function HistoricoPage() {
  const limit = 20
  const { data, isLoading } = useClinicalNotes(limit)
  const items = data ?? []

  return (
    <Stack gap="lg">
      <Title order={2}>Histórico Clínico</Title>
      <Text size="sm" c="dimmed">
        Resumo das anotações clínicas compartilháveis. A avaliação clínica interna não é exibida ao paciente.
      </Text>

      {isLoading ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !items.length ? (
        <Card withBorder padding="lg"><Text c="dimmed">Nenhum registro encontrado.</Text></Card>
      ) : (
        <Timeline active={items.length} bulletSize={28} lineWidth={2}>
          {items.map((note, index) => (
            <Timeline.Item
              key={`${note.encounter_date}-${index}`}
              bullet={<IconClipboardHeart size={16} />}
              title={new Date(note.encounter_date).toLocaleDateString('pt-BR')}
            >
              <Text size="sm" fw={600}>{note.professional_name}</Text>
              <Text size="sm" c="dimmed" mt={4}>{note.summary || 'Consulta registrada.'}</Text>
            </Timeline.Item>
          ))}
        </Timeline>
      )}
    </Stack>
  )
}
