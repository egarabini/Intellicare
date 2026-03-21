/**
 * DEM-065 — TenantsManager: gestão avançada de tenants.
 * Provision, suspend, reactivate, soft-delete, config.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ActionIcon,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  Pagination,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import {
  IconEye,
  IconPencil,
  IconPlayerPause,
  IconPlayerPlay,
  IconPlus,
  IconRocket,
  IconSearch,
  IconSettings,
  IconTrash,
} from '@tabler/icons-react'

import { StatusBadge } from '../components/StatusBadge'
import {
  useDeleteTenant,
  useProvisionTenant,
  useReactivateTenant,
  useSuspendTenant,
  useTenants,
} from '../hooks/useTenants'

export function TenantsManager() {
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const { data, isLoading } = useTenants(page)
  const suspendTenant = useSuspendTenant()
  const reactivateTenant = useReactivateTenant()
  const deleteTenant = useDeleteTenant()
  const provisionTenant = useProvisionTenant()
  const navigate = useNavigate()

  // Modal provision
  const [provisionOpened, provisionHandlers] = useDisclosure(false)
  const [provSlug, setProvSlug] = useState('')
  const [provName, setProvName] = useState('')
  const [provEmail, setProvEmail] = useState('')

  // Modal delete
  const [deleteOpened, deleteHandlers] = useDisclosure(false)
  const [deleteSlug, setDeleteSlug] = useState('')

  const tenants = (data?.items ?? []).filter((tenant) => {
    const probe = `${tenant.name} ${tenant.slug}`.toLowerCase()
    return probe.includes(query.toLowerCase())
  })

  const handleSuspend = async (slug: string) => {
    try {
      await suspendTenant.mutateAsync(slug)
      notifications.show({ title: 'Suspenso', message: `Tenant ${slug} suspenso.`, color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao suspender tenant.', color: 'red' })
    }
  }

  const handleReactivate = async (slug: string) => {
    try {
      await reactivateTenant.mutateAsync(slug)
      notifications.show({ title: 'Reativado', message: `Tenant ${slug} reativado.`, color: 'green' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao reativar tenant.', color: 'red' })
    }
  }

  const handleDelete = async () => {
    try {
      await deleteTenant.mutateAsync(deleteSlug)
      notifications.show({ title: 'Removido', message: `Tenant ${deleteSlug} removido (soft-delete).`, color: 'red' })
      deleteHandlers.close()
      setDeleteSlug('')
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao remover tenant.', color: 'red' })
    }
  }

  const handleProvision = async () => {
    if (!provSlug || !provName || !provEmail) return
    try {
      await provisionTenant.mutateAsync({ slug: provSlug, name: provName, gestor_email: provEmail })
      notifications.show({ title: 'Provisionado', message: `Tenant ${provSlug} criado com sucesso.`, color: 'green' })
      provisionHandlers.close()
      setProvSlug('')
      setProvName('')
      setProvEmail('')
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao provisionar tenant.', color: 'red' })
    }
  }

  if (isLoading) return <Center><Loader /></Center>

  const totalPages = data ? Math.max(Math.ceil(data.total / data.size), 1) : 1

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Gestão de Tenants</Title>
        <Group>
          <Button leftSection={<IconPlus size={16} />} onClick={() => navigate('/tenants/new')}>
            Novo Tenant
          </Button>
          <Button leftSection={<IconRocket size={16} />} color="teal" onClick={provisionHandlers.open}>
            Provisionar Tenant
          </Button>
        </Group>
      </Group>

      <TextInput
        placeholder="Buscar por nome ou slug"
        value={query}
        onChange={(e) => setQuery(e.currentTarget.value)}
        leftSection={<IconSearch size={16} />}
      />

      <Table highlightOnHover striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Slug</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Gestor</Table.Th>
            <Table.Th>Criado em</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {tenants.map((tenant) => (
            <Table.Tr key={tenant.id}>
              <Table.Td>{tenant.name}</Table.Td>
              <Table.Td>
                <Text size="sm" c="dimmed" ff="monospace">{tenant.slug}</Text>
              </Table.Td>
              <Table.Td>
                <StatusBadge status={tenant.status} />
              </Table.Td>
              <Table.Td>
                <Text size="sm" c="dimmed">{tenant.gestor_email ?? '—'}</Text>
              </Table.Td>
              <Table.Td>{new Date(tenant.created_at).toLocaleDateString('pt-BR')}</Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <Tooltip label="Ver detalhe">
                    <ActionIcon variant="subtle" onClick={() => navigate(`/tenants/${tenant.slug}`)}>
                      <IconEye size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label="Editar">
                    <ActionIcon variant="subtle" color="blue" onClick={() => navigate(`/tenants/${tenant.slug}/edit`)}>
                      <IconPencil size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label="Configurações">
                    <ActionIcon variant="subtle" color="grape" onClick={() => navigate(`/tenants/${tenant.slug}/config`)}>
                      <IconSettings size={16} />
                    </ActionIcon>
                  </Tooltip>
                  {tenant.status === 'active' ? (
                    <Tooltip label="Suspender">
                      <ActionIcon
                        variant="subtle"
                        color="orange"
                        onClick={() => handleSuspend(tenant.slug)}
                        loading={suspendTenant.isPending}
                      >
                        <IconPlayerPause size={16} />
                      </ActionIcon>
                    </Tooltip>
                  ) : tenant.status === 'suspended' ? (
                    <Tooltip label="Reativar">
                      <ActionIcon
                        variant="subtle"
                        color="green"
                        onClick={() => handleReactivate(tenant.slug)}
                        loading={reactivateTenant.isPending}
                      >
                        <IconPlayerPlay size={16} />
                      </ActionIcon>
                    </Tooltip>
                  ) : null}
                  <Tooltip label="Remover (soft-delete)">
                    <ActionIcon
                      variant="subtle"
                      color="red"
                      onClick={() => { setDeleteSlug(tenant.slug); deleteHandlers.open() }}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {totalPages > 1 && <Pagination total={totalPages} value={page} onChange={setPage} />}

      {/* Modal — Provisionar Tenant */}
      <Modal opened={provisionOpened} onClose={provisionHandlers.close} title="Provisionar Novo Tenant">
        <Stack gap="sm">
          <TextInput label="Slug" placeholder="clinica_abc" value={provSlug} onChange={(e) => setProvSlug(e.currentTarget.value)} />
          <TextInput label="Nome" placeholder="Clínica ABC" value={provName} onChange={(e) => setProvName(e.currentTarget.value)} />
          <TextInput label="E-mail do Gestor" placeholder="gestor@clinica.com" value={provEmail} onChange={(e) => setProvEmail(e.currentTarget.value)} />
          <Button onClick={handleProvision} loading={provisionTenant.isPending} color="teal">
            Provisionar
          </Button>
        </Stack>
      </Modal>

      {/* Modal — Confirmação de Delete */}
      <Modal opened={deleteOpened} onClose={deleteHandlers.close} title="Confirmar Remoção">
        <Stack gap="sm">
          <Text>
            Tem certeza que deseja remover o tenant <Badge variant="light">{deleteSlug}</Badge>?
          </Text>
          <Text size="sm" c="dimmed">
            Esta ação é um soft-delete — o schema não será removido, mas o tenant ficará inacessível.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={deleteHandlers.close}>Cancelar</Button>
            <Button color="red" onClick={handleDelete} loading={deleteTenant.isPending}>Remover</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
