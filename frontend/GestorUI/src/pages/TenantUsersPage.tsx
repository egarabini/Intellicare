import { useState } from 'react'
import {
  Box, Title, Button, Group, Table, Badge, TextInput, Select, Modal, Stack, Loader, Center, Text,
  ActionIcon, Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconEdit, IconTrash, IconSearch } from '@tabler/icons-react'
import { useTenantUsers, useCreateTenantUser, useUpdateTenantUser, useDeleteTenantUser, type TenantUser } from '../hooks/useTenantUsers'
import { useUnits } from '../hooks/useUnits'

const ROLE_LABELS: Record<string, string> = {
  gestor: 'Gestor',
  clinico: 'Clínico',
  recepcionista: 'Recepcionista',
}

const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }))

export function TenantUsersPage() {
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<TenantUser | null>(null)

  // form
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<string>('clinico')
  const [unitId, setUnitId] = useState<string | null>(null)

  const { data: users, isLoading } = useTenantUsers()
  const { data: units } = useUnits('active')
  const createUser = useCreateTenantUser()
  const updateUser = useUpdateTenantUser()
  const deleteUser = useDeleteTenantUser()

  const unitOptions = (units ?? []).map(u => ({ value: String(u.id), label: u.name }))

  const filtered = (users ?? []).filter(u =>
    !search || u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setEditing(null)
    setName(''); setEmail(''); setRole('clinico'); setUnitId(null)
    setModalOpen(true)
  }

  function openEdit(u: TenantUser) {
    setEditing(u)
    setName(u.name); setEmail(u.email); setRole(u.role); setUnitId(u.unit_id ? String(u.unit_id) : null)
    setModalOpen(true)
  }

  async function handleSubmit() {
    try {
      if (editing) {
        await updateUser.mutateAsync({
          id: editing.id,
          payload: { name: name || undefined, role: role as TenantUser['role'], unit_id: unitId ? Number(unitId) : null },
        })
        notifications.show({ title: 'Sucesso', message: 'Usuário atualizado', color: 'green' })
      } else {
        await createUser.mutateAsync({ email, name, role, unit_id: unitId ? Number(unitId) : undefined })
        notifications.show({ title: 'Sucesso', message: 'Usuário convidado', color: 'green' })
      }
      setModalOpen(false)
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar usuário', color: 'red' })
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteUser.mutateAsync(id)
      notifications.show({ title: 'Removido', message: 'Usuário removido', color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao remover', color: 'red' })
    }
  }

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>Usuários do Tenant</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={openCreate}>Convidar</Button>
      </Group>

      <Group mb="md">
        <TextInput placeholder="Buscar nome ou e-mail..." leftSection={<IconSearch size={16} />} value={search} onChange={e => setSearch(e.currentTarget.value)} style={{ flex: 1 }} />
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>E-mail</Table.Th>
            <Table.Th>Perfil</Table.Th>
            <Table.Th>Unidade</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {filtered.map(u => (
            <Table.Tr key={u.id}>
              <Table.Td>{u.name}</Table.Td>
              <Table.Td>{u.email}</Table.Td>
              <Table.Td><Badge variant="light">{ROLE_LABELS[u.role] ?? u.role}</Badge></Table.Td>
              <Table.Td>{u.unit_name ?? '—'}</Table.Td>
              <Table.Td>
                <Badge color={u.status === 'active' ? 'green' : 'gray'}>{u.status === 'active' ? 'Ativo' : 'Inativo'}</Badge>
              </Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <Tooltip label="Editar"><ActionIcon variant="subtle" onClick={() => openEdit(u)}><IconEdit size={16} /></ActionIcon></Tooltip>
                  <Tooltip label="Remover"><ActionIcon variant="subtle" color="red" onClick={() => handleDelete(u.id)}><IconTrash size={16} /></ActionIcon></Tooltip>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
          {filtered.length === 0 && (
            <Table.Tr><Table.Td colSpan={6}><Text c="dimmed" ta="center">Nenhum usuário encontrado.</Text></Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Editar Usuário' : 'Convidar Usuário'} size="md">
        <Stack>
          <TextInput label="Nome" required value={name} onChange={e => setName(e.currentTarget.value)} />
          <TextInput label="E-mail" required disabled={!!editing} value={email} onChange={e => setEmail(e.currentTarget.value)} />
          <Select label="Perfil" required data={ROLE_OPTIONS} value={role} onChange={v => setRole(v ?? 'clinico')} />
          <Select label="Unidade" clearable data={unitOptions} value={unitId} onChange={setUnitId} placeholder="Selecione..." />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit} loading={createUser.isPending || updateUser.isPending}>
              {editing ? 'Salvar' : 'Convidar'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  )
}
