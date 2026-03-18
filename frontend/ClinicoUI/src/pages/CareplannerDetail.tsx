import { Box, Title, Card, Badge, Group, Text, Loader, Center, Stack, ThemeIcon, Button, Divider } from '@mantine/core';
import { IconArrowLeft, IconMessage, IconVideo } from '@tabler/icons-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCareplannerTask, useVideoSessionClinico } from '../hooks/useCareplanner';

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

export function CareplannerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useCareplannerTask(id!);

  const canHaveVideo = ['REPLIED', 'CLOSED', 'SENT'].includes(data?.task.status ?? '');
  const { data: video } = useVideoSessionClinico(id!, canHaveVideo);

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (error || !data) return <Text c="red">Jornada não encontrada.</Text>;

  const { task, conversation, events } = data;

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

        {(video && !video.expired) && (
          <Group mt="md">
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
          </Group>
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
                  {event.event_type === 'INBOUND_RECEIVED' && event.payload && typeof event.payload.content === 'string' && (
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
    </Box>
  );
}
