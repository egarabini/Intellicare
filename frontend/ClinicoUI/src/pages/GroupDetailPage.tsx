import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box, Title, Group, Button, Table, Badge, Card, Text, Modal, Select, Loader, Center, ActionIcon,
} from '@mantine/core'
import { IconPlus, IconTrash } from '@tabler/icons-react'
import { useGroup, useGroupMembers, useAddMember, useRemoveMember, useToggleGroupStatus } from '../hooks/useGroups'
import { useProfessionals } from '../hooks/useProfessionals'
import { notifications } from '@mantine/notifications'

export function GroupDetailPage() {
  const { id } = useParams<{ id: string }>()
  const groupId = Number(id)
  const { data: group, isLoading: loadingGroup } = useGroup(groupId)
  const { data: members, isLoading: loadingMembers } = useGroupMembers(groupId)
  const { data: allProfs } = useProfessionals()
  const addMember = useAddMember(groupId)
  const removeMember = useRemoveMember(groupId)
  const toggleStatus = useToggleGroupStatus(groupId)

  const [addOpen, setAddOpen] = useState(false)
  const [selectedProf, setSelectedProf] = useState<string | null>(null)

  if (loadingGroup || loadingMembers) return <Center h="100%"><Loader /></Center>
  if (!group) return <Text c="dimmed">Grupo não encontrado.</Text>

  const memberIds = new Set(members?.map(m => m.professional_id) || [])
  const availableProfs = (allProfs || [])
    .filter(p => !memberIds.has(p.id) && p.status === 'active')
    .map(p => ({ value: String(p.id), label: `${p.name} — ${p.council_type} ${p.council_number}` }))

  const handleAdd = () => {
    if (!selectedProf) return
    addMember.mutate(Number(selectedProf), {
      onSuccess: () => {
        setAddOpen(false)
        setSelectedProf(null)
        notifications.show({ title: 'Sucesso', message: 'Membro adicionado', color: 'green' })
      },
      onError: () => notifications.show({ title: 'Erro', message: 'Falha ao adicionar membro', color: 'red' }),
    })
  }

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>{group.name}</Title>
          <Text c="dimmed" size="sm">
            {group.specialty || 'Sem especialidade'} · {group.unit_name || 'Sem unidade'}
          </Text>
        </div>
        <Group>
          <Badge color={group.status === 'active' ? 'green' : 'gray'} size="lg" variant="dot">
            {group.status === 'active' ? 'Ativo' : 'Inativo'}
          </Badge>
          <Button
            variant="light"
            color={group.status === 'active' ? 'orange' : 'green'}
            onClick={() => toggleStatus.mutate()}
            loading={toggleStatus.isPending}
          >
            {group.status === 'active' ? 'Desativar' : 'Ativar'}
          </Button>
        </Group>
      </Group>

      {group.description && (
        <Card withBorder mb="md" p="sm">
          <Text size="sm">{group.description}</Text>
        </Card>
      )}

      <Group justify="space-between" mb="sm">
        <Title order={4}>Membros ({members?.length || 0})</Title>
        <Button size="xs" leftSection={<IconPlus size={14} />} onClick={() => setAddOpen(true)}>
          Adicionar
        </Button>
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Conselho</Table.Th>
            <Table.Th>Número</Table.Th>
            <Table.Th>Especialidade</Table.Th>
            <Table.Th>Adicionado em</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {members?.map(m => (
            <Table.Tr key={m.professional_id}>
              <Table.Td>{m.name}</Table.Td>
              <Table.Td>{m.council_type}</Table.Td>
              <Table.Td>{m.council_number}</Table.Td>
              <Table.Td>{m.specialty}</Table.Td>
              <Table.Td>{new Date(m.added_at).toLocaleDateString()}</Table.Td>
              <Table.Td>
                <ActionIcon
                  color="red" variant="subtle" size="sm"
                  onClick={() => removeMember.mutate(m.professional_id)}
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Table.Td>
            </Table.Tr>
          ))}
          {members?.length === 0 && (
            <Table.Tr><Table.Td colSpan={6} style={{ textAlign: 'center' }}>Nenhum membro.</Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={addOpen} onClose={() => setAddOpen(false)} title="Adicionar Membro">
        <Select
          label="Profissional"
          data={availableProfs}
          value={selectedProf}
          onChange={setSelectedProf}
          searchable
          placeholder="Buscar profissional..."
          mb="md"
        />
        <Button fullWidth onClick={handleAdd} loading={addMember.isPending} disabled={!selectedProf}>
          Adicionar
        </Button>
      </Modal>
    </Box>
  )
}
