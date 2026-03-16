import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, Title, Card, Group, Text, Badge, Tabs, Table, Button, Loader, Center, Stack,
  Modal, TextInput, NumberInput, ActionIcon, Tooltip,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconArrowLeft, IconPlus, IconTrash, IconFileTypePdf } from '@tabler/icons-react'
import { useUnit, useUnitProfessionals, useAllocateProfessional, useRemoveProfessional } from '../hooks/useUnits'
import { useDownloadPdf } from '../hooks/useDownloadPdf'

const TYPE_LABELS: Record<string, string> = {
  ubs: 'UBS', hospital: 'Hospital', clinic: 'Clínica', secretary: 'Secretaria', other: 'Outro',
}

export function UnitDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const unitId = Number(id)

  const { data: unit, isLoading: loadingUnit } = useUnit(unitId)
  const { data: professionals, isLoading: loadingProfs } = useUnitProfessionals(unitId)
  const allocate = useAllocateProfessional()
  const remove = useRemoveProfessional()
  const { downloadPdf, isDownloading } = useDownloadPdf()

  const [allocModalOpen, setAllocModalOpen] = useState(false)
  const [profId, setProfId] = useState<number | ''>('')
  const [roleInUnit, setRoleInUnit] = useState('')
  const [workloadHours, setWorkloadHours] = useState<number | ''>('')

  async function handleAllocate() {
    if (!profId) return
    try {
      await allocate.mutateAsync({
        unitId,
        payload: {
          professional_id: Number(profId),
          role_in_unit: roleInUnit || undefined,
          workload_hours: workloadHours ? Number(workloadHours) : undefined,
        },
      })
      notifications.show({ title: 'Sucesso', message: 'Profissional alocado', color: 'green' })
      setAllocModalOpen(false)
      setProfId(''); setRoleInUnit(''); setWorkloadHours('')
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao alocar profissional', color: 'red' })
    }
  }

  async function handleRemove(professionaId: number) {
    try {
      await remove.mutateAsync({ unitId, profId: professionaId })
      notifications.show({ title: 'Removido', message: 'Profissional removido da unidade', color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao remover', color: 'red' })
    }
  }

  if (loadingUnit) return <Center h="100%"><Loader /></Center>
  if (!unit) return <Text c="red">Unidade não encontrada.</Text>

  return (
    <Box>
      <Group mb="md" justify="space-between">
        <Group>
          <ActionIcon variant="subtle" onClick={() => navigate('/units')}><IconArrowLeft size={20} /></ActionIcon>
          <Title order={2}>{unit.name}</Title>
          <Badge color={unit.status === 'active' ? 'green' : 'gray'} size="lg">
            {unit.status === 'active' ? 'Ativa' : 'Inativa'}
          </Badge>
        </Group>
        <Button
          leftSection={<IconFileTypePdf size={16} />}
          variant="light"
          color="red"
          loading={isDownloading}
          onClick={() => void downloadPdf(`/gestor/relatorios/profissionais/${unitId}`, `profissionais-unidade-${unitId}.pdf`)}
        >
          Exportar Profissionais
        </Button>
      </Group>

      <Card withBorder mb="lg" p="md">
        <Stack gap="xs">
          <Group><Text fw={600} w={120}>Tipo:</Text><Text>{TYPE_LABELS[unit.type] ?? unit.type}</Text></Group>
          {unit.cnes && <Group><Text fw={600} w={120}>CNES:</Text><Text>{unit.cnes}</Text></Group>}
          {unit.address && <Group><Text fw={600} w={120}>Endereço:</Text><Text>{unit.address}</Text></Group>}
          <Group><Text fw={600} w={120}>Cidade/UF:</Text><Text>{unit.city ?? '—'}{unit.state ? ` / ${unit.state}` : ''}</Text></Group>
          {unit.phone && <Group><Text fw={600} w={120}>Telefone:</Text><Text>{unit.phone}</Text></Group>}
          {unit.email && <Group><Text fw={600} w={120}>E-mail:</Text><Text>{unit.email}</Text></Group>}
        </Stack>
      </Card>

      <Tabs defaultValue="equipe">
        <Tabs.List>
          <Tabs.Tab value="equipe">Equipe ({professionals?.length ?? 0})</Tabs.Tab>
          <Tabs.Tab value="pacientes">Pacientes ({unit.patient_count})</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="equipe" pt="md">
          <Group justify="flex-end" mb="sm">
            <Button size="xs" leftSection={<IconPlus size={14} />} onClick={() => setAllocModalOpen(true)}>
              Alocar Profissional
            </Button>
          </Group>
          {loadingProfs ? <Loader size="sm" /> : (
            <Table striped>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Nome</Table.Th>
                  <Table.Th>Especialidade</Table.Th>
                  <Table.Th>Função</Table.Th>
                  <Table.Th>Horas/sem</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {(professionals ?? []).map(p => (
                  <Table.Tr key={p.professional_id}>
                    <Table.Td>{p.name}</Table.Td>
                    <Table.Td>{p.specialty ?? '—'}</Table.Td>
                    <Table.Td>{p.role_in_unit ?? '—'}</Table.Td>
                    <Table.Td>{p.workload_hours ?? '—'}</Table.Td>
                    <Table.Td>
                      <Tooltip label="Remover">
                        <ActionIcon variant="subtle" color="red" onClick={() => handleRemove(p.professional_id)}>
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Table.Td>
                  </Table.Tr>
                ))}
                {(professionals ?? []).length === 0 && (
                  <Table.Tr><Table.Td colSpan={5}><Text c="dimmed" ta="center">Nenhum profissional alocado.</Text></Table.Td></Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="pacientes" pt="md">
          <Text c="dimmed">Contagem de pacientes vinculados: {unit.patient_count}</Text>
        </Tabs.Panel>
      </Tabs>

      <Modal opened={allocModalOpen} onClose={() => setAllocModalOpen(false)} title="Alocar Profissional">
        <Stack>
          <NumberInput label="ID do Profissional" required value={profId} onChange={v => setProfId(v as number)} min={1} />
          <TextInput label="Função na Unidade" value={roleInUnit} onChange={e => setRoleInUnit(e.currentTarget.value)} />
          <NumberInput label="Carga Horária Semanal" value={workloadHours} onChange={v => setWorkloadHours(v as number)} min={1} max={168} />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setAllocModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleAllocate} loading={allocate.isPending}>Alocar</Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  )
}
