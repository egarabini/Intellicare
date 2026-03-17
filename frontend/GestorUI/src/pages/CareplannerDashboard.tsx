import {
  Box, Card, Center, Group, Loader, SimpleGrid,
  Stack, Text, ThemeIcon, Title, Badge,
} from '@mantine/core';
import { IconMessage } from '@tabler/icons-react';
import { useCareplannerStats } from '../hooks/useGestor';

const STATUS_META: Record<string, { color: string; label: string }> = {
  CREATED: { color: 'gray', label: 'Criadas' },
  DISPATCHED: { color: 'blue', label: 'Disparadas' },
  SENT: { color: 'cyan', label: 'Entregues' },
  REPLIED: { color: 'teal', label: 'Respondidas' },
  CLOSED: { color: 'green', label: 'Fechadas' },
  FAILED: { color: 'red', label: 'Falhas' },
  EXPIRED: { color: 'orange', label: 'Expiradas' },
};

export function CareplannerDashboard() {
  const { data, isLoading, error } = useCareplannerStats();

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (error) return <Text c="red">Erro ao carregar CarePlanner.</Text>;
  if (!data) return null;

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>CarePlanner — Jornadas</Title>
        <Text c="dimmed" size="sm">Total: {data.total} jornadas</Text>
      </Group>

      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md" mb="xl">
        {Object.entries(STATUS_META).map(([status, meta]) => (
          <Card key={status} withBorder padding="md" radius="md">
            <Group justify="space-between">
              <div>
                <Text c="dimmed" tt="uppercase" fw={700} fz="xs">{meta.label}</Text>
                <Text fw={700} fz="xl">{data.by_status[status] ?? 0}</Text>
              </div>
              <Badge color={meta.color} variant="light" size="lg">
                {status}
              </Badge>
            </Group>
          </Card>
        ))}
      </SimpleGrid>

      <Title order={3} mb="md">Atividade Recente</Title>
      <Card withBorder>
        {data.recent_tasks.length === 0 ? (
          <Text c="dimmed">Nenhuma jornada recente.</Text>
        ) : (
          <Stack gap="sm">
            {data.recent_tasks.map((task) => (
              <Group key={task.correlation_id} wrap="nowrap" justify="space-between">
                <Group wrap="nowrap">
                  <ThemeIcon
                    variant="light"
                    radius="xl"
                    color={STATUS_META[task.status]?.color ?? 'gray'}
                  >
                    <IconMessage size={16} />
                  </ThemeIcon>
                  <div>
                    <Text size="sm" fw={500}>{task.patient_ref}</Text>
                    <Text size="xs" c="dimmed">{task.task_type}</Text>
                  </div>
                </Group>
                <Group>
                  <Badge color={STATUS_META[task.status]?.color ?? 'gray'} variant="light">
                    {task.status}
                  </Badge>
                  <Text size="xs" c="dimmed">
                    {task.updated_at ? new Date(task.updated_at).toLocaleString('pt-BR') : '—'}
                  </Text>
                </Group>
              </Group>
            ))}
          </Stack>
        )}
      </Card>
    </Box>
  );
}
