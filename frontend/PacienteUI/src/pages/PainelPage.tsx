import {
  Card, Group, Loader, SimpleGrid, Stack, Text, Title, Badge, ThemeIcon,
} from '@mantine/core'
import { IconCalendar, IconHistory, IconHeartbeat } from '@tabler/icons-react'
import { usePainel } from '../hooks/usePaciente'

export function PainelPage() {
  const { data, isLoading } = usePainel()

  if (isLoading) return <Group justify="center" mt="xl"><Loader /></Group>

  const d = data ?? {}

  return (
    <Stack gap="lg">
      <Title order={2}>Olá, {d.patient_name ?? 'Paciente'}</Title>

      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        <Card withBorder radius="md" padding="lg">
          <Group gap="sm" mb="xs">
            <ThemeIcon variant="light" color="blue" size="lg"><IconCalendar size={20} /></ThemeIcon>
            <Text fw={500}>Próxima consulta</Text>
          </Group>
          {d.next_appointment ? (
            <>
              <Text size="lg" fw={700}>
                {new Date(d.next_appointment.scheduled_at).toLocaleDateString('pt-BR')}
              </Text>
              <Text size="sm" c="dimmed">
                {new Date(d.next_appointment.scheduled_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                {' — '}{d.next_appointment.type}
              </Text>
              <Text size="sm" mt={4}>
                {d.next_appointment.clinician_name || 'Equipe clínica'}
              </Text>
            </>
          ) : (
            <Text size="sm" c="dimmed">Nenhuma consulta agendada</Text>
          )}
        </Card>

        <Card withBorder radius="md" padding="lg">
          <Group gap="sm" mb="xs">
            <ThemeIcon variant="light" color="teal" size="lg"><IconCalendar size={20} /></ThemeIcon>
            <Text fw={500}>Agendamentos</Text>
          </Group>
          <Text size="lg" fw={700}>{d.upcoming_count ?? 0}</Text>
          <Text size="sm" c="dimmed">consultas futuras</Text>
        </Card>

        <Card withBorder radius="md" padding="lg">
          <Group gap="sm" mb="xs">
            <ThemeIcon variant="light" color="grape" size="lg"><IconHistory size={20} /></ThemeIcon>
            <Text fw={500}>Histórico</Text>
          </Group>
          <Text size="lg" fw={700}>{d.past_count ?? 0}</Text>
          <Text size="sm" c="dimmed">consultas realizadas</Text>
        </Card>
      </SimpleGrid>

      {d.clinic_notice && (
        <Card withBorder radius="md" padding="md">
          <Group gap="xs">
            <Badge color="yellow" variant="light">Aviso</Badge>
            <Text size="sm">{d.clinic_notice}</Text>
          </Group>
        </Card>
      )}
    </Stack>
  )
}
