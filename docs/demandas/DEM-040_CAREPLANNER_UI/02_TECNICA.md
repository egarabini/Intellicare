---
tipo: especificacao-tecnica
demanda: DEM-040
titulo: CarePlanner UI Completo — GestorUI
sprint: "4.2"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
---

# DEM-040 — Especificação Técnica

> Base path: `C:\Users\egara\INTELLICARE\frontend\GestorUI\src\`

---

## PRÉ-CONDIÇÕES

- DEM-038 e DEM-039 commitadas e passando todos os testes.
- Container `intellicare-service` local rodando com os novos endpoints.
- Mantine UI 7, React Query (`@tanstack/react-query`) e React Router já instalados.
- `npm run dev` sobe o GestorUI em `http://localhost:5173`.

---

## BLOCO 1 — Rotas React

**Arquivo:** `App.tsx`

Adicionar a rota de detalhe (a rota `/careplanner` já existe):

```tsx
import { CareplannerJourneyDetail } from './pages/CareplannerJourneyDetail'

// dentro de <Routes>:
<Route path="/careplanner" element={<CareplannerDashboard />} />
<Route path="/careplanner/jornadas/:id" element={<CareplannerJourneyDetail />} />
```

Sem alterar a navegação do AppShell — o item "CarePlanner" já aponta para `/careplanner`.

---

## BLOCO 2 — Hooks (`hooks/useGestor.ts`)

Adicionar ao final do arquivo existente, sem alterar hooks já existentes:

```typescript
// ── Tipos ──────────────────────────────────────────────────────────────────

export interface CareTask {
  id: string;
  correlation_id: string;
  kestra_execution_id: string | null;
  patient_ref: string;
  task_type: string;
  status: string;
  channel: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface CareEvent {
  id: string;
  event_id: string;
  correlation_id: string;
  event_type: string;
  status: string | null;
  payload: Record<string, unknown>;
  recorded_at: string;
}

export interface CareConversation {
  id: string;
  correlation_id: string;
  channel: string;
  channel_conversation_id: number;
  rc_room_id: string | null;
  phone_e164: string | null;
  participant_role: string | null;
}

export interface CareTaskDetail {
  task: CareTask;
  conversation: CareConversation | null;
  events: CareEvent[];
}

export interface CareTaskList {
  items: CareTask[];
  page: number;
}

export interface TriggerJourneyPayload {
  patient_ref: string;
  task_type: string;
  template_code?: string;
  template_variables?: Record<string, string>;
  contact_phone_e164?: string;
  flow_id?: string;
  clinico_ref?: string;
}

export interface TriggerJourneyResult {
  ok: boolean;
  execution_id: string;
  flow_id: string;
  status: string;
}

export interface VideoSession {
  room_name: string;
  clinico_url: string;
  patient_url: string;
  expires_at: string;
  expired: boolean;
}

// ── Hooks ──────────────────────────────────────────────────────────────────

export function useCareplannerTasks(statusFilter: string | null, page: number) {
  return useQuery<CareTaskList>({
    queryKey: ['careplanner_tasks', statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status_filter', statusFilter);
      params.set('page', String(page));
      const { data } = await api.get(`/careplanner/tasks?${params.toString()}`);
      return data;
    },
    refetchInterval: 15_000,
  });
}

export function useCareplannerTask(correlationId: string) {
  return useQuery<CareTaskDetail>({
    queryKey: ['careplanner_task', correlationId],
    queryFn: async () => {
      const { data } = await api.get(`/careplanner/tasks/${correlationId}`);
      return data;
    },
    refetchInterval: 10_000,
  });
}

export function useVideoSession(correlationId: string, enabled: boolean) {
  return useQuery<VideoSession>({
    queryKey: ['careplanner_video', correlationId],
    queryFn: async () => {
      const { data } = await api.get(`/careplanner/consultations/video/${correlationId}`);
      return data;
    },
    enabled,
    retry: false,  // 404 = sem sessão de vídeo; não retry
  });
}

export function useTriggerJourney() {
  const queryClient = useQueryClient();
  return useMutation<TriggerJourneyResult, Error, TriggerJourneyPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/careplanner/journeys/trigger', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_tasks'] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_stats'] });
    },
  });
}

export function useCloseTask(correlationId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ ok: boolean; status: string }, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/careplanner/tasks/${correlationId}/close`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_task', correlationId] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_tasks'] });
      queryClient.invalidateQueries({ queryKey: ['careplanner_stats'] });
    },
  });
}
```

**Imports necessários** no topo de `useGestor.ts` (verificar se já existem):
```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
```

---

## BLOCO 3 — `CareplannerDashboard.tsx` (refatoração)

Substituir o bloco "Atividade Recente" pelo componente `<JourneyList>` inline.

```tsx
import {
  Box, Button, Card, Center, Group, Loader, Select, SimpleGrid,
  Stack, Text, ThemeIcon, Title, Badge, Pagination, ActionIcon,
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import { IconMessage, IconPlus, IconPlayerPlay } from '@tabler/icons-react';
import {
  useCareplannerStats, useCareplannerTasks, useTriggerJourney,
  type TriggerJourneyPayload,
} from '../hooks/useGestor';
import { TriggerJourneyModal } from '../components/TriggerJourneyModal';

const STATUS_META: Record<string, { color: string; label: string }> = {
  CREATED:    { color: 'gray',   label: 'Criadas' },
  DISPATCHED: { color: 'blue',   label: 'Disparadas' },
  SENT:       { color: 'cyan',   label: 'Entregues' },
  REPLIED:    { color: 'teal',   label: 'Respondidas' },
  CLOSED:     { color: 'green',  label: 'Fechadas' },
  FAILED:     { color: 'red',    label: 'Falhas' },
  EXPIRED:    { color: 'orange', label: 'Expiradas' },
};

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  ...Object.entries(STATUS_META).map(([v, m]) => ({ value: v, label: m.label })),
];

export function CareplannerDashboard() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [triggerOpen, setTriggerOpen] = useState(false);

  const { data: stats, isLoading: statsLoading } = useCareplannerStats();
  const { data: tasks, isLoading: tasksLoading } = useCareplannerTasks(statusFilter, page);
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

  return (
    <Box>
      {/* ── Cabeçalho ── */}
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

      {/* ── Cards de status ── */}
      <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="md" mb="xl">
        {Object.entries(STATUS_META).map(([status, meta]) => (
          <Card
            key={status}
            withBorder
            padding="md"
            radius="md"
            style={{ cursor: 'pointer' }}
            onClick={() => { setStatusFilter(status); setPage(1); }}
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

      {/* ── Lista de jornadas ── */}
      <Group justify="space-between" mb="sm">
        <Title order={3}>Jornadas</Title>
        <Select
          data={STATUS_OPTIONS}
          value={statusFilter ?? ''}
          onChange={(v) => { setStatusFilter(v || null); setPage(1); }}
          w={200}
          placeholder="Filtrar por status"
          data-testid="select-status"
        />
      </Group>

      <Card withBorder mb="md">
        {tasksLoading ? (
          <Center py="xl"><Loader /></Center>
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

      {/* ── Paginação ── */}
      <Group justify="center">
        <Button
          variant="subtle"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Anterior
        </Button>
        <Text size="sm">Página {page}</Text>
        <Button
          variant="subtle"
          disabled={!tasks || tasks.items.length < 10}
          onClick={() => setPage((p) => p + 1)}
        >
          Próxima
        </Button>
      </Group>

      {/* ── Modal Nova Jornada ── */}
      <TriggerJourneyModal
        opened={triggerOpen}
        onClose={() => setTriggerOpen(false)}
        onSubmit={handleTrigger}
        loading={trigger.isPending}
      />
    </Box>
  );
}
```

Adicionar `useState` aos imports React se ainda não estiver.

---

## BLOCO 4 — `components/TriggerJourneyModal.tsx` (novo)

```tsx
import { Button, Group, Modal, Select, Stack, Switch, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import type { TriggerJourneyPayload } from '../hooks/useGestor';

interface Props {
  opened: boolean;
  onClose: () => void;
  onSubmit: (payload: TriggerJourneyPayload) => Promise<void>;
  loading: boolean;
}

const TASK_TYPES = [
  { value: 'ADESAO',        label: 'Adesão ao Tratamento' },
  { value: 'MONITORAMENTO', label: 'Monitoramento' },
  { value: 'CHECK_IN',      label: 'Check-in de Saúde' },
  { value: 'TELECONSULTA',  label: 'Teleconsulta' },
];

export function TriggerJourneyModal({ opened, onClose, onSubmit, loading }: Props) {
  const form = useForm<{
    patient_ref: string;
    task_type: string;
    template_code: string;
    contact_phone_e164: string;
    include_video: boolean;
    clinico_ref: string;
  }>({
    initialValues: {
      patient_ref: '',
      task_type: 'CHECK_IN',
      template_code: '',
      contact_phone_e164: '',
      include_video: false,
      clinico_ref: '',
    },
    validate: {
      patient_ref: (v) => (!v.trim() ? 'Referência do paciente obrigatória' : null),
      task_type: (v) => (!v ? 'Tipo de jornada obrigatório' : null),
      clinico_ref: (v, values) =>
        values.include_video && !v.trim()
          ? 'Referência do clínico obrigatória para videoconsulta'
          : null,
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    await onSubmit({
      patient_ref: values.patient_ref.trim(),
      task_type: values.task_type,
      template_code: values.template_code.trim() || undefined,
      contact_phone_e164: values.contact_phone_e164.trim() || undefined,
      flow_id: values.include_video ? 'careplanner_jornada_video' : 'careplanner_jornada_basica',
      clinico_ref: values.include_video ? values.clinico_ref.trim() : undefined,
    });
    form.reset();
  });

  return (
    <Modal opened={opened} onClose={onClose} title="Nova Jornada CarePlanner" size="md">
      <form onSubmit={handleSubmit}>
        <Stack>
          <TextInput
            label="Referência do Paciente"
            placeholder="keycloak-uuid-do-paciente"
            required
            data-testid="input-patient-ref"
            {...form.getInputProps('patient_ref')}
          />
          <Select
            label="Tipo de Jornada"
            data={TASK_TYPES}
            required
            data-testid="select-task-type"
            {...form.getInputProps('task_type')}
          />
          <TextInput
            label="Código do Template"
            placeholder="ex. boas_vindas (opcional)"
            {...form.getInputProps('template_code')}
          />
          <TextInput
            label="Telefone (E.164)"
            placeholder="+5511999999999 (opcional)"
            {...form.getInputProps('contact_phone_e164')}
          />
          <Switch
            label="Incluir videoconsulta após resposta"
            data-testid="switch-video"
            {...form.getInputProps('include_video', { type: 'checkbox' })}
          />
          {form.values.include_video && (
            <TextInput
              label="Referência do Clínico"
              placeholder="keycloak-uuid-do-clinico"
              required
              {...form.getInputProps('clinico_ref')}
            />
          )}
          <Group justify="flex-end" mt="md">
            <Button variant="subtle" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button
              type="submit"
              loading={loading}
              data-testid="btn-submit-trigger"
            >
              Iniciar Jornada
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
```

Adicionar `@mantine/form` se não estiver em `package.json`:
```bash
npm install @mantine/form
```

---

## BLOCO 5 — `pages/CareplannerJourneyDetail.tsx` (novo)

```tsx
import {
  Badge, Box, Button, Card, Center, Divider, Group, Loader, Stack,
  Text, ThemeIcon, Title, Anchor,
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { useNavigate, useParams } from 'react-router-dom';
import { IconArrowLeft, IconMessage, IconPlayerStop, IconVideo } from '@tabler/icons-react';
import {
  useCareplannerTask, useCloseTask, useVideoSession,
} from '../hooks/useGestor';

const STATUS_META: Record<string, { color: string }> = {
  CREATED:    { color: 'gray' },
  DISPATCHED: { color: 'blue' },
  SENT:       { color: 'cyan' },
  REPLIED:    { color: 'teal' },
  CLOSED:     { color: 'green' },
  FAILED:     { color: 'red' },
  EXPIRED:    { color: 'orange' },
};

const EVENT_LABELS: Record<string, string> = {
  MESSAGE_SENT:       'Mensagem enviada ao paciente',
  MESSAGE_FAILED:     'Falha no envio da mensagem',
  INBOUND_RECEIVED:   'Resposta recebida do paciente',
  ORPHAN_INBOUND:     'Mensagem sem correlação (órfã)',
  VIDEO_SESSION_OPENED: 'Sessão de vídeo aberta',
  TASK_CLOSED:        'Jornada encerrada',
};

export function CareplannerJourneyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useCareplannerTask(id!);
  const closeTask = useCloseTask(id!);

  const canHaveVideo = ['REPLIED', 'CLOSED', 'SENT'].includes(data?.task.status ?? '');
  const { data: video } = useVideoSession(id!, canHaveVideo);

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (error || !data) return <Text c="red">Jornada não encontrada.</Text>;

  const { task, conversation, events } = data;
  const canClose = ['SENT', 'REPLIED'].includes(task.status);

  const handleClose = () => {
    modals.openConfirmModal({
      title: 'Encerrar jornada',
      children: (
        <Text size="sm">
          Tem certeza que deseja encerrar a jornada de <strong>{task.patient_ref}</strong>?
          A sala Rocket.Chat será arquivada.
        </Text>
      ),
      labels: { confirm: 'Encerrar', cancel: 'Cancelar' },
      confirmProps: { color: 'red' },
      onConfirm: async () => {
        try {
          await closeTask.mutateAsync();
          notifications.show({
            title: 'Jornada encerrada',
            message: 'Status atualizado para CLOSED.',
            color: 'green',
          });
        } catch {
          notifications.show({
            title: 'Erro ao encerrar',
            message: 'Tente novamente.',
            color: 'red',
          });
        }
      },
    });
  };

  return (
    <Box>
      {/* ── Cabeçalho ── */}
      <Group mb="md">
        <Button
          variant="subtle"
          leftSection={<IconArrowLeft size={16} />}
          onClick={() => navigate('/careplanner')}
        >
          Voltar
        </Button>
        <Title order={2}>Detalhe da Jornada</Title>
      </Group>

      {/* ── Card principal ── */}
      <Card withBorder mb="md">
        <Group justify="space-between" mb="xs">
          <Stack gap={2}>
            <Text fw={700} size="lg">{task.patient_ref}</Text>
            <Text c="dimmed" size="sm">{task.task_type}</Text>
          </Stack>
          <Badge
            color={STATUS_META[task.status]?.color ?? 'gray'}
            variant="filled"
            size="xl"
            data-testid="badge-status"
          >
            {task.status}
          </Badge>
        </Group>

        <Divider my="sm" />

        <Group gap="xl">
          <div>
            <Text size="xs" c="dimmed">Criada em</Text>
            <Text size="sm">{new Date(task.created_at).toLocaleString('pt-BR')}</Text>
          </div>
          <div>
            <Text size="xs" c="dimmed">Atualizada em</Text>
            <Text size="sm">{task.updated_at ? new Date(task.updated_at).toLocaleString('pt-BR') : '—'}</Text>
          </div>
          {conversation?.phone_e164 && (
            <div>
              <Text size="xs" c="dimmed">Telefone</Text>
              <Text size="sm">{conversation.phone_e164}</Text>
            </div>
          )}
          {task.kestra_execution_id && (
            <div>
              <Text size="xs" c="dimmed">Execution Kestra</Text>
              <Text size="sm" ff="monospace" fz="xs">{task.kestra_execution_id}</Text>
            </div>
          )}
        </Group>

        {/* ── Ações ── */}
        <Group mt="md" gap="sm">
          {video && !video.expired && (
            <Button
              component="a"
              href={video.clinico_url}
              target="_blank"
              leftSection={<IconVideo size={16} />}
              variant="light"
              color="violet"
            >
              Entrar na Videoconsulta
            </Button>
          )}
          {canClose && (
            <Button
              leftSection={<IconPlayerStop size={16} />}
              color="red"
              variant="light"
              onClick={handleClose}
              loading={closeTask.isPending}
              data-testid="btn-encerrar"
            >
              Encerrar Jornada
            </Button>
          )}
        </Group>
      </Card>

      {/* ── Timeline de eventos ── */}
      <Title order={3} mb="sm">Timeline de Eventos</Title>
      <Card withBorder>
        {events.length === 0 ? (
          <Text c="dimmed">Nenhum evento registrado.</Text>
        ) : (
          <Stack gap="sm" data-testid="event-timeline">
            {events.map((event) => (
              <Group key={event.id} wrap="nowrap" align="flex-start">
                <ThemeIcon
                  variant="light"
                  radius="xl"
                  color={event.event_type === 'INBOUND_RECEIVED' ? 'teal' : 'blue'}
                  mt={2}
                >
                  <IconMessage size={14} />
                </ThemeIcon>
                <div style={{ flex: 1 }}>
                  <Group justify="space-between">
                    <Text size="sm" fw={500}>
                      {EVENT_LABELS[event.event_type] ?? event.event_type}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {new Date(event.recorded_at).toLocaleString('pt-BR')}
                    </Text>
                  </Group>
                  {/* Conteúdo do paciente (INBOUND_RECEIVED) */}
                  {event.event_type === 'INBOUND_RECEIVED' && event.payload?.content && (
                    <Text
                      size="sm"
                      c="dimmed"
                      mt={2}
                      style={{ whiteSpace: 'pre-wrap' }}
                      data-testid="event-content"
                    >
                      "{String(event.payload.content)}"
                    </Text>
                  )}
                </div>
              </Group>
            ))}
          </Stack>
        )}
      </Card>
    </Box>
  );
}
```

---

## BLOCO 6 — Testes Playwright (`e2e/careplanner.spec.ts`)

Adicionar 3 novos testes ao arquivo existente (não substituir os 4 já existentes):

```typescript
// ── NOVOS TESTES DEM-040 ────────────────────────────────────────────────────

test('DEM040-01: lista de jornadas com filtro de status', async ({ page }) => {
  // Mock GET /careplanner/tasks
  await page.route('**/careplanner/tasks*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'uuid-1',
            correlation_id: 'corr-uuid-1',
            kestra_execution_id: 'exec-1',
            patient_ref: 'paciente.teste',
            task_type: 'CHECK_IN',
            status: 'REPLIED',
            channel: 'rocketchat',
            metadata: {},
            created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T01:00:00Z',
          },
        ],
        page: 1,
      }),
    });
  });

  await page.goto('/careplanner');
  await page.getByTestId('select-status').click();
  await page.getByText('Respondidas').click();
  await expect(page.getByText('paciente.teste')).toBeVisible();
  await expect(page.getByText('CHECK_IN')).toBeVisible();
});

test('DEM040-02: detalhe da jornada com timeline de eventos', async ({ page }) => {
  const correlationId = 'corr-uuid-detalhe';

  await page.route(`**/careplanner/tasks/${correlationId}`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        task: {
          id: 'uuid-t',
          correlation_id: correlationId,
          kestra_execution_id: 'exec-k',
          patient_ref: 'paciente.detalhe',
          task_type: 'MONITORAMENTO',
          status: 'REPLIED',
          channel: 'rocketchat',
          metadata: {},
          created_at: '2026-03-18T00:00:00Z',
          updated_at: '2026-03-18T01:30:00Z',
        },
        conversation: null,
        events: [
          {
            id: 'ev-1',
            event_id: 'evt-001',
            correlation_id: correlationId,
            event_type: 'MESSAGE_SENT',
            status: 'SENT',
            payload: {},
            recorded_at: '2026-03-18T00:05:00Z',
          },
          {
            id: 'ev-2',
            event_id: 'evt-002',
            correlation_id: correlationId,
            event_type: 'INBOUND_RECEIVED',
            status: 'REPLIED',
            payload: { content: 'Sim, estou tomando o remédio.' },
            recorded_at: '2026-03-18T01:30:00Z',
          },
        ],
      }),
    });
  });

  await page.route(`**/careplanner/consultations/video/${correlationId}`, (route) => {
    route.fulfill({ status: 404 });
  });

  await page.goto(`/careplanner/jornadas/${correlationId}`);
  await expect(page.getByTestId('badge-status')).toHaveText('REPLIED');
  await expect(page.getByTestId('event-timeline')).toBeVisible();
  await expect(page.getByTestId('event-content')).toContainText('Sim, estou tomando');
  await expect(page.getByTestId('btn-encerrar')).toBeVisible();
});

test('DEM040-03: modal Nova Jornada — submit com sucesso', async ({ page }) => {
  await page.route('**/careplanner/journeys/trigger', (route) => {
    route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: true,
        execution_id: 'exec-novo-123',
        flow_id: 'careplanner_jornada_basica',
        status: 'CREATED',
      }),
    });
  });

  await page.goto('/careplanner');
  await page.getByTestId('btn-nova-jornada').click();
  await page.getByTestId('input-patient-ref').fill('paciente-novo-ref');
  await page.getByTestId('select-task-type').click();
  await page.getByText('Check-in de Saúde').click();
  await page.getByTestId('btn-submit-trigger').click();
  await expect(page.getByText('exec-novo-123')).toBeVisible();
});
```

---

## Estrutura de Arquivos — Resumo

```
frontend/GestorUI/src/
  App.tsx                              ← adicionar rota /careplanner/jornadas/:id
  hooks/
    useGestor.ts                       ← adicionar 6 hooks + tipos
  pages/
    CareplannerDashboard.tsx           ← refatorar (manter cards, substituir lista)
    CareplannerJourneyDetail.tsx       ← NOVO
  components/
    TriggerJourneyModal.tsx            ← NOVO
  e2e/
    careplanner.spec.ts                ← adicionar 3 testes (não substituir os 4)
```

---

## Comandos de Validação

```bash
# Testes unitários Python (garantir não-regressão)
pytest packages/intellicare-core/tests/ -q

# Build do GestorUI
cd frontend/GestorUI && npm run build

# Testes E2E (todos os 7 devem passar: 4 existentes + 3 novos)
npm run test:e2e
```
