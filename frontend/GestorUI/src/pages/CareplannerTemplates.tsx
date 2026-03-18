import {
  ActionIcon, Badge, Box, Button, Card, Center, Divider, Group,
  Loader, Modal, Stack, Table, Text, Textarea, TextInput, Title, Tooltip,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { IconEdit, IconPlus, IconToggleLeft, IconToggleRight } from '@tabler/icons-react';
import {
  useTemplates, useCreateTemplate, useUpdateTemplate,
  useToggleTemplate, type CareTemplate, type CareTemplatePayload,
} from '../hooks/useGestor';

// ── Form de criação/edição ─────────────────────────────────────────────────

interface TemplateFormValues {
  template_code: string;
  content: string;
  variables_raw: string; // vírgula-separado, convertido para list[str] no submit
}

function TemplateModal({
  opened, onClose, editing,
}: {
  opened: boolean;
  onClose: () => void;
  editing: CareTemplate | null;
}) {
  const create = useCreateTemplate();
  const update = useUpdateTemplate();
  const [conflictError, setConflictError] = useState('');

  const form = useForm<TemplateFormValues>({
    initialValues: {
      template_code: editing?.template_code ?? '',
      content: editing?.content ?? '',
      variables_raw: editing?.variables.join(', ') ?? '',
    },
    validate: {
      template_code: (v) =>
        !editing && !/^[a-z0-9_]{2,64}$/.test(v)
          ? 'snake_case, 2–64 caracteres minúsculos'
          : null,
      content: (v) => (!v.trim() ? 'Conteúdo obrigatório' : null),
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    setConflictError('');
    const variables = values.variables_raw
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean);

    try {
      if (editing) {
        await update.mutateAsync({ id: editing.id, payload: { content: values.content, variables, active: editing.active } });
      } else {
        await create.mutateAsync({
          template_code: values.template_code,
          content: values.content,
          variables,
          active: true,
        } as CareTemplatePayload);
      }
      notifications.show({
        title: editing ? 'Template atualizado' : 'Template criado',
        color: 'teal',
        message: '',
      });
      form.reset();
      onClose();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setConflictError('Já existe um template com este código neste canal.');
      } else {
        notifications.show({ title: 'Erro', message: 'Tente novamente.', color: 'red' });
      }
    }
  });

  const isLoading = create.isPending || update.isPending;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={editing ? 'Editar Template' : 'Novo Template'}
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <Stack>
          <TextInput
            label="Código do Template"
            placeholder="ex. boas_vindas"
            required
            disabled={!!editing}
            description="snake_case, apenas letras minúsculas, números e _"
            data-testid="input-template-code"
            {...form.getInputProps('template_code')}
          />
          {conflictError && (
            <Text size="sm" c="red">{conflictError}</Text>
          )}
          <Textarea
            label="Conteúdo da Mensagem"
            placeholder="Olá! Estamos iniciando seu acompanhamento..."
            required
            autosize
            minRows={4}
            maxRows={10}
            data-testid="input-template-content"
            {...form.getInputProps('content')}
          />
          <TextInput
            label="Variáveis (opcional)"
            placeholder="nome_paciente, data_consulta"
            description="Nomes das variáveis separados por vírgula"
            {...form.getInputProps('variables_raw')}
          />
          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" onClick={onClose} disabled={isLoading}>
              Cancelar
            </Button>
            <Button type="submit" loading={isLoading} data-testid="btn-salvar-template">
              {editing ? 'Salvar' : 'Criar Template'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

// ── Página principal ───────────────────────────────────────────────────────

export function CareplannerTemplates() {
  const { data, isLoading } = useTemplates();
  const toggle = useToggleTemplate();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<CareTemplate | null>(null);

  const openCreate = () => { setEditing(null); setModalOpen(true); };
  const openEdit = (t: CareTemplate) => { setEditing(t); setModalOpen(true); };
  const closeModal = () => { setEditing(null); setModalOpen(false); };

  if (isLoading) return <Center h="100%"><Loader /></Center>;

  const templates = data ?? [];

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>Templates de Mensagem</Title>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={openCreate}
          data-testid="btn-novo-template"
        >
          Novo Template
        </Button>
      </Group>

      <Card withBorder>
        {templates.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">
            Nenhum template cadastrado. Clique em "Novo Template" para começar.
          </Text>
        ) : (
          <Table highlightOnHover data-testid="table-templates">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Código</Table.Th>
                <Table.Th>Canal</Table.Th>
                <Table.Th>Conteúdo</Table.Th>
                <Table.Th>Variáveis</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Ações</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {templates.map((t) => (
                <Table.Tr key={t.id} data-testid={`row-template-${t.template_code}`}>
                  <Table.Td>
                    <Text ff="monospace" size="sm">{t.template_code}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge variant="light" color="blue" size="sm">
                      {t.channel}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" lineClamp={1} maw={300}>
                      {t.content}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {t.variables.length > 0 ? t.variables.join(', ') : '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={t.active ? 'teal' : 'gray'} variant="light">
                      {t.active ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Editar">
                        <ActionIcon
                          variant="subtle"
                          onClick={() => openEdit(t)}
                          data-testid={`btn-edit-${t.template_code}`}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label={t.active ? 'Desativar' : 'Ativar'}>
                        <ActionIcon
                          variant="subtle"
                          color={t.active ? 'orange' : 'teal'}
                          loading={toggle.isPending}
                          onClick={() => toggle.mutate(t.id)}
                          data-testid={`btn-toggle-${t.template_code}`}
                        >
                          {t.active
                            ? <IconToggleRight size={16} />
                            : <IconToggleLeft size={16} />
                          }
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      <TemplateModal opened={modalOpen} onClose={closeModal} editing={editing} />
    </Box>
  );
}
