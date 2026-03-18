import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Select,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
  Badge,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconMessage, IconPlus } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import {
  useCareplannerStats,
  useCareplannerTasks,
  useTriggerJourney,
  type TriggerJourneyPayload,
} from '../hooks/useGestor';
import { TriggerJourneyModal } from '../components/TriggerJourneyModal';

const STATUS_META: Record<string, { color: string; label: string }> = {
  CREATED: { color: 'gray', label: 'Criadas' },
  DISPATCHED: { color: 'blue', label: 'Disparadas' },
  SENT: { color: 'cyan', label: 'Entregues' },
  REPLIED: { color: 'teal', label: 'Respondidas' },
  CLOSED: { color: 'green', label: 'Fechadas' },
  FAILED: { color: 'red', label: 'Falhas' },
  EXPIRED: { color: 'orange', label: 'Expiradas' },
};

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  ...Object.entries(STATUS_META).map(([value, meta]) => ({ value, label: meta.label })),
];

export function CareplannerDashboard() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [triggerOpen, setTriggerOpen] = useState(false);

  const { data: stats, isLoading: statsLoading, error: statsError } = useCareplannerStats();
  const { data: tasks, isLoading: tasksLoading, error: tasksError } = useCareplannerTasks(statusFilter, page);
  const trigger = useTriggerJourney();

  const handleTrigger = async (payload: TriggerJourneyPayload) => {
    try {
      const result = await trigger.mutateAsync(payload);
      setTriggerOpen(false);
      notifications.show({
        title: 'Jornada iniciada',
        message: `Execution: ${result.execution_id}`,
        color: 'teal',
      });
    } catch {
      notifications.show({
        title: 'Erro ao iniciar jornada',
        message: 'Kestra indisponível ou credenciais inválidas.',
        color: 'red',
      });
    }
  };

  if (statsLoading) return <Center h="100%"><Loader /></Center>;
  if (statsError) return <Text c="red">Erro ao carregar CarePlanner.</Text>;

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>CarePlanner — Jornadas</Title>
        <Group>
          <Text c="dimmed" size="sm">Total: {stats?.total ?? 0} jornadas</Text>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setTriggerOpen(true)}
            data-testid="btn-nova-jornada"
          >
            Nova Jornada
          </Button>
        </Group>
      </Group>

      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md" mb="xl">
        {Object.entries(STATUS_META).map(([status, meta]) => (
          <Card
            key={status}
            withBorder
            padding="md"
            radius="md"
            style={{ cursor: 'pointer' }}
            onClick={() => {
              setStatusFilter(status);
              setPage(1);
            }}
          >
            <Group justify="space-between">
              <div>
                <Text c="dimmed" tt="uppercase" fw={700} fz="xs">{meta.label}</Text>
                <Text fw={700} fz="xl">{stats?.by_status[status] ?? 0}</Text>
              </div>
              <Badge color={meta.color} variant="light" size="lg">{status}</Badge>
            </Group>
          </Card>
        ))}
      </SimpleGrid>

      <Group justify="space-between" mb="sm">
        <Title order={3}>Jornadas</Title>
        <Select
          data={STATUS_OPTIONS}
          value={statusFilter ?? ''}
          onChange={(value) => {
            setStatusFilter(value || null);
            setPage(1);
          }}
          w={200}
          placeholder="Filtrar por status"
          data-testid="select-status"
        />
      </Group>

      <Card withBorder mb="md">
        {tasksLoading ? (
          <Center py="xl"><Loader /></Center>
        ) : tasksError ? (
          <Text c="red" ta="center" py="xl">Erro ao carregar jornadas.</Text>
        ) : !tasks || tasks.items.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">Nenhuma jornada encontrada.</Text>
        ) : (
          <Stack gap="xs">
            {tasks.items.map((task) => (
              <Group
                key={task.correlation_id}
                justify="space-between"
                py="xs"
                px="sm"
                style={{ borderRadius: 6, cursor: 'pointer' }}
                className="hover-row"
                onClick={() => navigate(`/careplanner/jornadas/${task.correlation_id}`)}
                data-testid={`row-${task.correlation_id}`}
              >
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

      <Group justify="center">
        <Button
          variant="subtle"
          disabled={page <= 1}
          onClick={() => setPage((current) => current - 1)}
        >
          Anterior
        </Button>
        <Text size="sm">Página {page}</Text>
        <Button
          variant="subtle"
          disabled={!tasks || tasks.items.length < 10}
          onClick={() => setPage((current) => current + 1)}
        >
          Próxima
        </Button>
      </Group>

      <TriggerJourneyModal
        opened={triggerOpen}
        onClose={() => setTriggerOpen(false)}
        onSubmit={handleTrigger}
        loading={trigger.isPending}
      />
    </Box>
  );
}
