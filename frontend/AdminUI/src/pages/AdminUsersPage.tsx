import { useState } from 'react'
import {
  ActionIcon,
  Alert,
  Button,
  Card,
  Code,
  CopyButton,
  Group,
  Loader,
  Modal,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { IconCheck, IconCopy, IconDeviceFloppy, IconInfoCircle, IconPencil, IconTrash, IconX } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'

import { StatusBadge } from '../components/StatusBadge'
import { AdminUser, AdminUserPayload, useAdminUsers, useCreateAdminUser, useDeleteAdminUser, useUpdateAdminUser } from '../hooks/useAdminUsers'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Administrador' },
  { value: 'financ', label: 'Financeiro' },
  { value: 'coordenador', label: 'Coordenador' },
]

const STATUS_OPTIONS = [
  { value: 'active', label: 'Ativo' },
  { value: 'inactive', label: 'Inativo' },
]

function emptyUser(): AdminUserPayload {
  return {
    email: '',
    name: '',
    role: 'coordenador',
    status: 'active',
  }
}

export function AdminUsersPage() {
  const usersQuery = useAdminUsers()
  const createUser = useCreateAdminUser()
  const updateUser = useUpdateAdminUser()
  const deleteUser = useDeleteAdminUser()
  const [editing, setEditing] = useState<AdminUser | null>(null)
  const [form, setForm] = useState<AdminUserPayload>(emptyUser())
  const [tempPassword, setTempPassword] = useState<string | null>(null)

  const reset = () => {
    setEditing(null)
    setForm(emptyUser())
  }

  const save = async () => {
    try {
      if (editing) {
        await updateUser.mutateAsync({
          id: editing.id,
          payload: { name: form.name, role: form.role, status: form.status },
        })
        notifications.show({ title: 'Usuario salvo', message: 'Cadastro administrativo atualizado.', color: 'green' })
      } else {
        const result = await createUser.mutateAsync(form)
        if (result.temporary_password) {
          setTempPassword(result.temporary_password)
        }
      }
      reset()
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Falha ao salvar usuario admin.'
      notifications.show({ title: 'Erro', message, color: 'red' })
      console.error(error)
    }
  }

  const startEdit = (user: AdminUser) => {
    setEditing(user)
    setForm({
      email: user.email,
      name: user.name,
      role: user.role,
      status: user.status,
    })
  }

  const remove = async (id: number) => {
    try {
      await deleteUser.mutateAsync(id)
      notifications.show({ title: 'Usuario removido', message: 'Registro excluido com sucesso.', color: 'green' })
      if (editing?.id === id) {
        reset()
      }
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao remover usuario admin.', color: 'red' })
      console.error(error)
    }
  }

  if (usersQuery.isLoading) {
    return <Loader />
  }

  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={2}>Usuarios Admin</Title>
        <Text c="dimmed">Operadores internos com acesso administrativo ao tenant platform.</Text>
      </Stack>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Group justify="space-between">
            <Title order={4}>{editing ? 'Editar usuario admin' : 'Novo usuario admin'}</Title>
            {editing && (
              <Button variant="subtle" color="gray" leftSection={<IconX size={16} />} onClick={reset}>
                Cancelar edicao
              </Button>
            )}
          </Group>
          <SimpleGrid cols={{ base: 1, md: 4 }}>
            <TextInput label="Email" disabled={!!editing} value={form.email} onChange={(e) => setForm({ ...form, email: e.currentTarget.value })} />
            <TextInput label="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.currentTarget.value })} />
            <Select label="Perfil" data={ROLE_OPTIONS} value={form.role} onChange={(value) => value && setForm({ ...form, role: value as AdminUserPayload['role'] })} />
            <Select label="Status" data={STATUS_OPTIONS} value={form.status} onChange={(value) => value && setForm({ ...form, status: value as AdminUserPayload['status'] })} />
          </SimpleGrid>
          <Group justify="flex-end">
            <Button leftSection={<IconDeviceFloppy size={16} />} onClick={() => void save()} loading={createUser.isPending || updateUser.isPending}>
              {editing ? 'Salvar alteracoes' : 'Criar usuario admin'}
            </Button>
          </Group>
        </Stack>
      </Card>

      <Modal
        opened={!!tempPassword}
        onClose={() => setTempPassword(null)}
        title="Usuário criado com sucesso"
        centered
      >
        <Stack gap="md">
          <Text size="sm">Senha temporária de primeiro acesso:</Text>
          <Group gap="xs">
            <Code fz="lg" style={{ flex: 1 }}>{tempPassword}</Code>
            <CopyButton value={tempPassword ?? ''} timeout={2000}>
              {({ copied, copy }) => (
                <Button
                  size="xs"
                  color={copied ? 'teal' : 'blue'}
                  leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                  onClick={copy}
                >
                  {copied ? 'Copiado' : 'Copiar'}
                </Button>
              )}
            </CopyButton>
          </Group>
          <Alert color="orange" variant="light" icon={<IconInfoCircle size={16} />}>
            Esta senha não será exibida novamente. Anote antes de fechar.
          </Alert>
          <Group justify="flex-end">
            <Button onClick={() => setTempPassword(null)}>Fechar</Button>
          </Group>
        </Stack>
      </Modal>

      <Table withTableBorder striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Email</Table.Th>
            <Table.Th>Perfil</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ultimo login</Table.Th>
            <Table.Th>Acoes</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {(usersQuery.data ?? []).map((user) => (
            <Table.Tr key={user.id}>
              <Table.Td>{user.name}</Table.Td>
              <Table.Td>{user.email}</Table.Td>
              <Table.Td>{user.role}</Table.Td>
              <Table.Td><StatusBadge status={user.status} /></Table.Td>
              <Table.Td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString('pt-BR') : 'Nunca'}</Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <ActionIcon variant="subtle" onClick={() => startEdit(user)}>
                    <IconPencil size={16} />
                  </ActionIcon>
                  <ActionIcon variant="subtle" color="red" onClick={() => void remove(user.id)}>
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
