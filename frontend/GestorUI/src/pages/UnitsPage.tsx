import { useState } from 'react'
import {
  Box, Title, Button, Group, Table, Badge, TextInput, Select, Modal, Stack, Loader, Center, Text,
  ActionIcon, Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconPlus, IconEdit, IconPower, IconSearch } from '@tabler/icons-react'
import { useUnits, useCreateUnit, useUpdateUnit, useToggleUnitStatus, type Unit } from '../hooks/useUnits'
import { useNavigate } from 'react-router-dom'

const TYPE_LABELS: Record<string, string> = {
  ubs: 'UBS',
  hospital: 'Hospital',
  clinic: 'Clínica',
  secretary: 'Secretaria',
  other: 'Outro',
}

const TYPE_OPTIONS = Object.entries(TYPE_LABELS).map(([value, label]) => ({ value, label }))

export function UnitsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Unit | null>(null)

  // form state
  const [name, setName] = useState('')
  const [type, setType] = useState<string>('clinic')
  const [cnes, setCnes] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')

  const { data: units, isLoading } = useUnits(statusFilter ?? undefined)
  const createUnit = useCreateUnit()
  const updateUnit = useUpdateUnit()
  const toggleStatus = useToggleUnitStatus()

  const filtered = (units ?? []).filter(u =>
    !search || u.name.toLowerCase().includes(search.toLowerCase()) || (u.city ?? '').toLowerCase().includes(search.toLowerCase())
  )

  function openCreate() {
    setEditing(null)
    setName(''); setType('clinic'); setCnes(''); setCity(''); setState(''); setPhone(''); setEmail('')
    setModalOpen(true)
  }

  function openEdit(u: Unit) {
    setEditing(u)
    setName(u.name); setType(u.type); setCnes(u.cnes ?? ''); setCity(u.city ?? ''); setState(u.state ?? ''); setPhone(u.phone ?? ''); setEmail(u.email ?? '')
    setModalOpen(true)
  }

  async function handleSubmit() {
    const payload = { name, type: type as Unit['type'], cnes: cnes || undefined, city: city || undefined, state: state || undefined, phone: phone || undefined, email: email || undefined }
    try {
      if (editing) {
        await updateUnit.mutateAsync({ id: editing.id, payload })
        notifications.show({ title: 'Sucesso', message: 'Unidade atualizada', color: 'green' })
      } else {
        await createUnit.mutateAsync(payload)
        notifications.show({ title: 'Sucesso', message: 'Unidade criada', color: 'green' })
      }
      setModalOpen(false)
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar unidade', color: 'red' })
    }
  }

  async function handleToggle(id: number) {
    try {
      await toggleStatus.mutateAsync(id)
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao alterar status', color: 'red' })
    }
  }

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>Unidades de Saúde</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={openCreate}>Adicionar</Button>
      </Group>

      <Group mb="md">
        <TextInput placeholder="Buscar..." leftSection={<IconSearch size={16} />} value={search} onChange={e => setSearch(e.currentTarget.value)} style={{ flex: 1 }} />
        <Select
          placeholder="Status"
          clearable
          data={[{ value: 'active', label: 'Ativa' }, { value: 'inactive', label: 'Inativa' }]}
          value={statusFilter}
          onChange={setStatusFilter}
          w={140}
        />
      </Group>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Cidade</Table.Th>
            <Table.Th>Profissionais</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {filtered.map(u => (
            <Table.Tr key={u.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/units/${u.id}`)}>
              <Table.Td>{u.name}</Table.Td>
              <Table.Td>{TYPE_LABELS[u.type] ?? u.type}</Table.Td>
              <Table.Td>{u.city ?? '—'}{u.state ? ` / ${u.state}` : ''}</Table.Td>
              <Table.Td>{u.professional_count}</Table.Td>
              <Table.Td>
                <Badge color={u.status === 'active' ? 'green' : 'gray'}>{u.status === 'active' ? 'Ativa' : 'Inativa'}</Badge>
              </Table.Td>
              <Table.Td>
                <Group gap="xs" onClick={e => e.stopPropagation()}>
                  <Tooltip label="Editar"><ActionIcon variant="subtle" onClick={() => openEdit(u)}><IconEdit size={16} /></ActionIcon></Tooltip>
                  <Tooltip label={u.status === 'active' ? 'Desativar' : 'Ativar'}>
                    <ActionIcon variant="subtle" color={u.status === 'active' ? 'orange' : 'green'} onClick={() => handleToggle(u.id)}>
                      <IconPower size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
          {filtered.length === 0 && (
            <Table.Tr><Table.Td colSpan={6}><Text c="dimmed" ta="center">Nenhuma unidade encontrada.</Text></Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Editar Unidade' : 'Nova Unidade'} size="md">
        <Stack>
          <TextInput label="Nome" required value={name} onChange={e => setName(e.currentTarget.value)} />
          <Select label="Tipo" required data={TYPE_OPTIONS} value={type} onChange={v => setType(v ?? 'clinic')} />
          <TextInput label="CNES" value={cnes} onChange={e => setCnes(e.currentTarget.value)} />
          <Group grow>
            <TextInput label="Cidade" value={city} onChange={e => setCity(e.currentTarget.value)} />
            <TextInput label="UF" maxLength={2} value={state} onChange={e => setState(e.currentTarget.value)} w={80} />
          </Group>
          <TextInput label="Telefone" value={phone} onChange={e => setPhone(e.currentTarget.value)} />
          <TextInput label="E-mail" value={email} onChange={e => setEmail(e.currentTarget.value)} />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit} loading={createUnit.isPending || updateUnit.isPending}>
              {editing ? 'Salvar' : 'Criar'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  )
}
