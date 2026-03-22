import { useMemo, useState } from 'react'
import {
  Accordion,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconArrowBackUp, IconCheck, IconPlus } from '@tabler/icons-react'

import {
  useActivatePrompt,
  useCreatePromptVersion,
  usePrompts,
  useRollbackPrompt,
} from '../hooks/usePrompts'

export function PromptsPage() {
  const { data, isLoading } = usePrompts()
  const createPromptVersion = useCreatePromptVersion()
  const activatePrompt = useActivatePrompt()
  const rollbackPrompt = useRollbackPrompt()

  const [opened, setOpened] = useState(false)
  const [promptKey, setPromptKey] = useState('')
  const [content, setContent] = useState('')
  const [notes, setNotes] = useState('')

  const keys = useMemo(() => (data?.items ?? []).map(item => item.prompt_key), [data])

  const handleCreate = async () => {
    try {
      await createPromptVersion.mutateAsync({
        prompt_key: promptKey.trim(),
        content: content.trim(),
        notes: notes.trim() || undefined,
      })
      notifications.show({ title: 'Versão criada', message: `Novo prompt salvo para ${promptKey}.`, color: 'green' })
      setOpened(false)
      setPromptKey('')
      setContent('')
      setNotes('')
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao criar versão do prompt.', color: 'red' })
    }
  }

  if (isLoading) {
    return <Center><Loader /></Center>
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <div>
          <Title order={2}>Prompt Versioning</Title>
          <Text c="dimmed">Gerencie versões ativas de Florence e Oswaldo com rollback explícito.</Text>
        </div>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setOpened(true)}>
          Nova versão
        </Button>
      </Group>

      <Paper withBorder p="md" radius="md">
        <Text size="sm" c="dimmed">
          Chaves conhecidas: {keys.length > 0 ? keys.join(', ') : 'nenhuma encontrada'}
        </Text>
      </Paper>

      <Accordion variant="separated">
        {(data?.items ?? []).map((group) => (
          <Accordion.Item key={group.prompt_key} value={group.prompt_key}>
            <Accordion.Control>
              <Group justify="space-between" wrap="nowrap">
                <Text fw={600}>{group.prompt_key}</Text>
                <Badge variant="light">ativa v{group.active_version ?? '-'}</Badge>
              </Group>
            </Accordion.Control>
            <Accordion.Panel>
              <Group justify="flex-end" mb="sm">
                <Button
                  size="xs"
                  variant="light"
                  leftSection={<IconArrowBackUp size={14} />}
                  onClick={() => void rollbackPrompt.mutateAsync(group.prompt_key)}
                  loading={rollbackPrompt.isPending}
                >
                  Rollback
                </Button>
              </Group>
              <Table highlightOnHover withTableBorder>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Versão</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Notas</Table.Th>
                    <Table.Th>Conteúdo</Table.Th>
                    <Table.Th>Ação</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {group.versions.map((version) => (
                    <Table.Tr key={version.id}>
                      <Table.Td>v{version.version}</Table.Td>
                      <Table.Td>
                        {version.is_active ? <Badge color="green">Ativa</Badge> : <Badge variant="light">Inativa</Badge>}
                      </Table.Td>
                      <Table.Td>{version.notes || '-'}</Table.Td>
                      <Table.Td>
                        <Text size="sm" lineClamp={4} ff="monospace">
                          {version.content}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Button
                          size="xs"
                          variant="subtle"
                          leftSection={<IconCheck size={14} />}
                          disabled={version.is_active}
                          onClick={() => void activatePrompt.mutateAsync({
                            promptKey: group.prompt_key,
                            version: version.version,
                          })}
                        >
                          Ativar
                        </Button>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Nova versão de prompt" size="lg">
        <Stack>
          <TextInput
            label="Prompt key"
            placeholder="ex: florence_soap"
            value={promptKey}
            onChange={(e) => setPromptKey(e.currentTarget.value)}
          />
          <Textarea
            label="Conteúdo"
            minRows={8}
            autosize
            value={content}
            onChange={(e) => setContent(e.currentTarget.value)}
          />
          <TextInput
            label="Notas"
            placeholder="Motivo da nova versão"
            value={notes}
            onChange={(e) => setNotes(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setOpened(false)}>Cancelar</Button>
            <Button onClick={() => void handleCreate()} loading={createPromptVersion.isPending}>
              Salvar versão
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
