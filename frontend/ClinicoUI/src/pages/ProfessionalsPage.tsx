import { useState } from 'react'
import {
  Box, Title, Group, Button, Table, Badge, Modal, TextInput, Select, Loader, Center,
} from '@mantine/core'
import { IconPlus } from '@tabler/icons-react'
import { useProfessionals, useCreateProfessional, useToggleProfessionalStatus } from '../hooks/useProfessionals'
import { notifications } from '@mantine/notifications'

const COUNCIL_OPTIONS = [
  { value: 'CRM', label: 'CRM' },
  { value: 'COREN', label: 'COREN' },
  { value: 'CRO', label: 'CRO' },
  { value: 'CRP', label: 'CRP' },
  { value: 'CREFITO', label: 'CREFITO' },
  { value: 'other', label: 'Outro' },
]

const emptyForm = { name: '', council_type: 'CRM', council_number: '', specialty: '', phone: '', email: '' }

export function ProfessionalsPage() {
  const { data: professionals, isLoading } = useProfessionals()
  const createProf = useCreateProfessional()
  const [opened, setOpened] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const handleCreate = () => {
    createProf.mutate(
      {
        name: form.name,
        council_type: form.council_type as any,
        council_number: form.council_number,
        specialty: form.specialty,
        phone: form.phone || null,
        email: form.email || null,
      } as any,
      {
        onSuccess: () => {
          setOpened(false)
          setForm(emptyForm)
          notifications.show({ title: 'Sucesso', message: 'Profissional adicionado', color: 'green' })
        },
        onError: () => notifications.show({ title: 'Erro', message: 'Falha ao criar profissional', color: 'red' }),
      },
    )
  }

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Profissionais de Saúde</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setOpened(true)}>
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
            <Table.Th>Unidade</Table.Th>
            <Table.Th>Grupos</Table.Th>
            <Table.Th>Status</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {professionals?.map(p => (
            <Table.Tr key={p.id}>
              <Table.Td>{p.name}</Table.Td>
              <Table.Td>{p.council_type}</Table.Td>
              <Table.Td>{p.council_number}</Table.Td>
              <Table.Td>{p.specialty}</Table.Td>
              <Table.Td>{p.unit_name || '—'}</Table.Td>
              <Table.Td>{p.groups?.length ? p.groups.join(', ') : '—'}</Table.Td>
              <Table.Td>
                <Badge color={p.status === 'active' ? 'green' : 'gray'} variant="dot">
                  {p.status === 'active' ? 'Ativo' : 'Inativo'}
                </Badge>
              </Table.Td>
            </Table.Tr>
          ))}
          {professionals?.length === 0 && (
            <Table.Tr><Table.Td colSpan={7} style={{ textAlign: 'center' }}>Nenhum profissional cadastrado.</Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Adicionar Profissional">
        <TextInput label="Nome" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} mb="sm" />
        <Select label="Conselho" data={COUNCIL_OPTIONS} value={form.council_type} onChange={v => setForm(f => ({ ...f, council_type: v || 'CRM' }))} mb="sm" />
        <TextInput label="Número do Conselho" required value={form.council_number} onChange={e => setForm(f => ({ ...f, council_number: e.target.value }))} mb="sm" />
        <TextInput label="Especialidade" required value={form.specialty} onChange={e => setForm(f => ({ ...f, specialty: e.target.value }))} mb="sm" />
        <TextInput label="Telefone" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} mb="sm" />
        <TextInput label="E-mail" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} mb="sm" />
        <Button fullWidth onClick={handleCreate} loading={createProf.isPending} mt="md">Salvar</Button>
      </Modal>
    </Box>
  )
}
