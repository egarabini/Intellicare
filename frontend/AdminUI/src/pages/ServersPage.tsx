import { useState } from 'react'
import {
  ActionIcon,
  Button,
  Card,
  Group,
  Loader,
  NumberInput,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core'
import { IconDeviceFloppy, IconPencil, IconTrash, IconX } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'

import { StatusBadge } from '../components/StatusBadge'
import { Server, ServerPayload, useCreateServer, useDeleteServer, useServers, useUpdateServer } from '../hooks/useServers'

const SERVER_TYPE_OPTIONS = [
  { value: 'vps', label: 'VPS' },
  { value: 'dedicated', label: 'Dedicated' },
  { value: 'cloud', label: 'Cloud' },
]

const SERVER_STATUS_OPTIONS = [
  { value: 'active', label: 'Ativo' },
  { value: 'inactive', label: 'Inativo' },
  { value: 'maintenance', label: 'Manutencao' },
]

function emptyForm(): ServerPayload {
  return {
    name: '',
    type: 'vps',
    provider: '',
    region: '',
    hostname: '',
    vcpu: 2,
    ram_gb: 4,
    disk_gb: 40,
    cost_brl: 0,
    status: 'active',
    notes: '',
  }
}

export function ServersPage() {
  const { data, isLoading } = useServers()
  const createServer = useCreateServer()
  const updateServer = useUpdateServer()
  const deleteServer = useDeleteServer()
  const [editing, setEditing] = useState<Server | null>(null)
  const [form, setForm] = useState<ServerPayload>(emptyForm())

  const reset = () => {
    setEditing(null)
    setForm(emptyForm())
  }

  const startEdit = (server: Server) => {
    setEditing(server)
    setForm({
      name: server.name,
      type: server.type,
      provider: server.provider,
      region: server.region,
      hostname: server.hostname,
      vcpu: server.vcpu,
      ram_gb: server.ram_gb,
      disk_gb: server.disk_gb,
      cost_brl: server.cost_brl,
      status: server.status,
      notes: server.notes,
    })
  }

  const save = async () => {
    try {
      if (editing) {
        await updateServer.mutateAsync({ id: editing.id, payload: form })
      } else {
        await createServer.mutateAsync(form)
      }
      notifications.show({ title: 'Servidor salvo', message: 'Cadastro atualizado com sucesso.', color: 'green' })
      reset()
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar servidor.', color: 'red' })
      console.error(error)
    }
  }

  const remove = async (id: number) => {
    try {
      await deleteServer.mutateAsync(id)
      notifications.show({ title: 'Servidor removido', message: 'Registro excluido com sucesso.', color: 'green' })
      if (editing?.id === id) {
        reset()
      }
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao excluir servidor.', color: 'red' })
      console.error(error)
    }
  }

  if (isLoading) {
    return <Loader />
  }

  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={2}>Servidores</Title>
        <Text c="dimmed">Inventario da infraestrutura da plataforma e custo mensal por host.</Text>
      </Stack>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Group justify="space-between">
            <Title order={4}>{editing ? 'Editar servidor' : 'Novo servidor'}</Title>
            {editing && (
              <Button variant="subtle" color="gray" leftSection={<IconX size={16} />} onClick={reset}>
                Cancelar edicao
              </Button>
            )}
          </Group>
          <SimpleGrid cols={{ base: 1, md: 3 }}>
            <TextInput label="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.currentTarget.value })} />
            <Select label="Tipo" data={SERVER_TYPE_OPTIONS} value={form.type} onChange={(value) => value && setForm({ ...form, type: value as ServerPayload['type'] })} />
            <Select label="Status" data={SERVER_STATUS_OPTIONS} value={form.status} onChange={(value) => value && setForm({ ...form, status: value as ServerPayload['status'] })} />
            <TextInput label="Provider" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.currentTarget.value })} />
            <TextInput label="Regiao" value={form.region} onChange={(e) => setForm({ ...form, region: e.currentTarget.value })} />
            <TextInput label="Hostname" value={form.hostname ?? ''} onChange={(e) => setForm({ ...form, hostname: e.currentTarget.value })} />
            <NumberInput label="vCPU" min={1} value={form.vcpu} onChange={(value) => setForm({ ...form, vcpu: Number(value) || 1 })} />
            <NumberInput label="RAM (GB)" min={1} value={form.ram_gb} onChange={(value) => setForm({ ...form, ram_gb: Number(value) || 1 })} />
            <NumberInput label="Disco (GB)" min={1} value={form.disk_gb} onChange={(value) => setForm({ ...form, disk_gb: Number(value) || 1 })} />
            <NumberInput label="Custo mensal (centavos)" min={0} value={form.cost_brl} onChange={(value) => setForm({ ...form, cost_brl: Number(value) || 0 })} />
          </SimpleGrid>
          <Textarea label="Notas" value={form.notes ?? ''} onChange={(e) => setForm({ ...form, notes: e.currentTarget.value })} minRows={2} />
          <Group justify="flex-end">
            <Button leftSection={<IconDeviceFloppy size={16} />} onClick={() => void save()} loading={createServer.isPending || updateServer.isPending}>
              {editing ? 'Salvar alteracoes' : 'Cadastrar servidor'}
            </Button>
          </Group>
        </Stack>
      </Card>

      <Table withTableBorder striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Infra</Table.Th>
            <Table.Th>Custo</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Acoes</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {(data ?? []).map((server) => (
            <Table.Tr key={server.id}>
              <Table.Td>
                <Stack gap={0}>
                  <Text fw={600}>{server.name}</Text>
                  <Text size="sm" c="dimmed">{server.hostname || `${server.provider} / ${server.region}`}</Text>
                </Stack>
              </Table.Td>
              <Table.Td>{server.type}</Table.Td>
              <Table.Td>{server.vcpu} vCPU / {server.ram_gb} GB / {server.disk_gb} GB</Table.Td>
              <Table.Td>{server.cost_brl_display.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</Table.Td>
              <Table.Td><StatusBadge status={server.status} /></Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <ActionIcon variant="subtle" onClick={() => startEdit(server)}>
                    <IconPencil size={16} />
                  </ActionIcon>
                  <ActionIcon variant="subtle" color="red" onClick={() => void remove(server.id)}>
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  )
}
