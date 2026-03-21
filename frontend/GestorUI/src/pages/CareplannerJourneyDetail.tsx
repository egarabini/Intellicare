import { useState } from 'react';
import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Center,
  CopyButton,
  Divider,
  Group,
  Loader,
  Modal,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
  Tooltip,
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { IconArrowLeft, IconCalendar, IconCheck, IconCopy, IconFileTypePdf, IconMessage, IconPlayerStop, IconVideo } from '@tabler/icons-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCareplannerTask, useCloseTask, useCreateVideoSession, useVideoSession, VideoSessionCreate } from '../hooks/useGestor';

const STATUS_META: Record<string, { color: string }> = {
  CREATED: { color: 'gray' },
  DISPATCHED: { color: 'blue' },
  SENT: { color: 'cyan' },
  REPLIED: { color: 'teal' },
  CLOSED: { color: 'green' },
  FAILED: { color: 'red' },
  EXPIRED: { color: 'orange' },
};

const EVENT_LABELS: Record<string, string> = {
  MESSAGE_SENT: 'Mensagem enviada ao paciente',
  MESSAGE_FAILED: 'Falha no envio da mensagem',
  INBOUND_RECEIVED: 'Resposta recebida do paciente',
  ORPHAN_INBOUND: 'Mensagem sem correlação (órfã)',
  VIDEO_SESSION_OPENED: 'Sessão de vídeo aberta',
  TASK_CLOSED: 'Jornada encerrada',
};

export function CareplannerJourneyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useCareplannerTask(id!);
  const closeTask = useCloseTask(id!);

  const canHaveVideo = ['REPLIED', 'CLOSED', 'SENT'].includes(data?.task.status ?? '');
  const { data: video } = useVideoSession(id!, canHaveVideo);
  const createVideo = useCreateVideoSession(id!);
  const [videoCreated, setVideoCreated] = useState<VideoSessionCreate | null>(null);

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
          {' '}A sala Rocket.Chat será arquivada.
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
            <Text size="sm">
              {task.updated_at ? new Date(task.updated_at).toLocaleString('pt-BR') : '—'}
            </Text>
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

        <Group mt="md" gap="sm">
          <Button
            variant="light"
            leftSection={<IconFileTypePdf size={16} />}
            component="a"
            href={`/api/v1/careplanner/journeys/${id}/report.pdf`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Exportar PDF
          </Button>
          {canHaveVideo && (!video || video.expired) && (
            <Button
              leftSection={<IconVideo size={16} />}
              variant="light"
              color="violet"
              loading={createVideo.isPending}
              onClick={async () => {
                try {
                  const result = await createVideo.mutateAsync();
                  setVideoCreated(result);
                } catch {
                  notifications.show({
                    title: 'Erro ao criar videoconsulta',
                    message: 'Tente novamente.',
                    color: 'red',
                  });
                }
              }}
              data-testid="btn-criar-video"
            >
              Criar Videoconsulta
            </Button>
          )}
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

        {task.appointment_id && (
          <Alert icon={<IconCalendar size={16} />} color="blue" mt="md" data-testid="appointment-link">
            Agendamento vinculado:{' '}
            <Anchor href={`/gestor-ui/agendamentos/${task.appointment_id}`}>
              #{task.appointment_id}
            </Anchor>
          </Alert>
        )}
      </Card>

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
                  {event.event_type === 'INBOUND_RECEIVED' && typeof event.payload?.content === 'string' && (
                    <Text
                      size="sm"
                      c="dimmed"
                      mt={2}
                      style={{ whiteSpace: 'pre-wrap' }}
                      data-testid="event-content"
                    >
                      "{event.payload.content}"
                    </Text>
                  )}
                </div>
              </Group>
            ))}
          </Stack>
        )}
      </Card>

      <Modal
        opened={!!videoCreated}
        onClose={() => setVideoCreated(null)}
        title="Videoconsulta criada"
        size="md"
      >
        {videoCreated && (
          <Stack gap="md">
            <Text size="sm">A sala foi criada com sucesso. Compartilhe o link com o paciente.</Text>

            <div>
              <Text size="xs" c="dimmed" mb={4}>Link do paciente</Text>
              <Group gap="xs">
                <TextInput
                  value={videoCreated.patient_url}
                  readOnly
                  style={{ flex: 1 }}
                  styles={{ input: { fontFamily: 'monospace', fontSize: 12 } }}
                  data-testid="input-patient-url"
                />
                <CopyButton value={videoCreated.patient_url} timeout={2000}>
                  {({ copied, copy }) => (
                    <Tooltip label={copied ? 'Copiado!' : 'Copiar'} withArrow>
                      <ActionIcon color={copied ? 'teal' : 'gray'} variant="light" onClick={copy}>
                        {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                      </ActionIcon>
                    </Tooltip>
                  )}
                </CopyButton>
              </Group>
            </div>

            <Button
              component="a"
              href={videoCreated.clinico_url}
              target="_blank"
              leftSection={<IconVideo size={16} />}
              color="violet"
              fullWidth
              data-testid="btn-entrar-clinico"
            >
              Entrar como Clínico
            </Button>

            <Button variant="subtle" onClick={() => setVideoCreated(null)} fullWidth>
              Fechar
            </Button>
          </Stack>
        )}
      </Modal>
    </Box>
  );
}
