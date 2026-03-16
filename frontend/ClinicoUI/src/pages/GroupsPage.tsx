import { useState } from 'react'
import {
  Box, Title, Group, Button, Table, Badge, Modal, TextInput, Select, Textarea, Loader, Center,
} from '@mantine/core'
import { IconPlus } from '@tabler/icons-react'
import { useGroups, useCreateGroup, useToggleGroupStatus, type Group as GroupType } from '../hooks/useGroups'
import { useNavigate } from 'react-router-dom'
import { notifications } from '@mantine/notifications'

export function GroupsPage() {
  const navigate = useNavigate()
  const { data: groups, isLoading } = useGroups()
  const createGroup = useCreateGroup()
  const [opened, setOpened] = useState(false)
  const [form, setForm] = useState({ name: '', specialty: '', unit_id: '', description: '' })

  const handleCreate = () => {
    createGroup.mutate(
      {
        name: form.name,
        specialty: form.specialty || null,
        unit_id: form.unit_id ? Number(form.unit_id) : null,
        description: form.description || null,
      },
      {
        onSuccess: () => {
          setOpened(false)
          setForm({ name: '', specialty: '', unit_id: '', description: '' })
          notifications.show({ title: 'Sucesso', message: 'Grupo criado', color: 'green' })
        },
        onError: () => notifications.show({ title: 'Erro', message: 'Falha ao criar grupo', color: 'red' }),
      },
    )
  }

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Grupos de Profissionais</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setOpened(true)}>
          Criar Grupo
        </Button>
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Especialidade</Table.Th>
            <Table.Th>Unidade</Table.Th>
            <Table.Th>Membros</Table.Th>
            <Table.Th>Status</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {groups?.map((g: GroupType) => (
            <Table.Tr key={g.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/groups/${g.id}`)}>
              <Table.Td>{g.name}</Table.Td>
              <Table.Td>{g.specialty || '—'}</Table.Td>
              <Table.Td>{g.unit_name || '—'}</Table.Td>
              <Table.Td>{g.member_count}</Table.Td>
              <Table.Td>
                <Badge color={g.status === 'active' ? 'green' : 'gray'} variant="dot">
                  {g.status === 'active' ? 'Ativo' : 'Inativo'}
                </Badge>
              </Table.Td>
            </Table.Tr>
          ))}
          {groups?.length === 0 && (
            <Table.Tr><Table.Td colSpan={5} style={{ textAlign: 'center' }}>Nenhum grupo cadastrado.</Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Criar Grupo">
        <TextInput label="Nome" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} mb="sm" />
        <TextInput label="Especialidade" value={form.specialty} onChange={e => setForm(f => ({ ...f, specialty: e.target.value }))} mb="sm" />
        <Textarea label="Descrição" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} mb="sm" />
        <Button fullWidth onClick={handleCreate} loading={createGroup.isPending} mt="md">Salvar</Button>
      </Modal>
    </Box>
  )
}
