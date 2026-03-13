import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ActionIcon,
  Button,
  Center,
  Group,
  Loader,
  Pagination,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconEye, IconPlayerPause, IconPlayerPlay, IconPlus, IconSearch } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'

import { StatusBadge } from '../components/StatusBadge'
import { useTenants, useUpdateTenantStatus } from '../hooks/useTenants'

export function TenantList({ embedded = false }: { embedded?: boolean }) {
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const { data, isLoading } = useTenants(page)
  const updateStatus = useUpdateTenantStatus()
  const navigate = useNavigate()

  const tenants = (data?.items ?? []).filter((tenant) => {
    const probe = `${tenant.name} ${tenant.slug}`.toLowerCase()
    return probe.includes(query.toLowerCase())
  })

  const handleToggle = async (slug: string, current: string) => {
    const next = current === 'active' ? 'suspended' : 'active'
    try {
      await updateStatus.mutateAsync({ slug, status: next })
      notifications.show({
        title: 'Status atualizado',
        message: `Tenant ${next === 'active' ? 'reativado' : 'suspenso'} com sucesso.`,
        color: next === 'active' ? 'green' : 'orange',
      })
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Falha ao atualizar status do tenant.',
        color: 'red',
      })
    }
  }

  if (isLoading) {
    return (
      <Center>
        <Loader />
      </Center>
    )
  }

  const totalPages = data ? Math.max(Math.ceil(data.total / data.size), 1) : 1

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={embedded ? 3 : 2}>{embedded ? 'Tenants recentes' : 'Tenants'}</Title>
        {!embedded && (
          <Button leftSection={<IconPlus size={16} />} onClick={() => navigate('/tenants/new')}>
            Novo Tenant
          </Button>
        )}
      </Group>

      <TextInput
        placeholder="Buscar por nome ou slug"
        value={query}
        onChange={(event) => setQuery(event.currentTarget.value)}
        leftSection={<IconSearch size={16} />}
      />

      <Table highlightOnHover striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Slug</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Criado em</Table.Th>
            <Table.Th>Acoes</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {tenants.map((tenant) => (
            <Table.Tr key={tenant.id}>
              <Table.Td>{tenant.name}</Table.Td>
              <Table.Td>
                <Text size="sm" c="dimmed" ff="monospace">
                  {tenant.slug}
                </Text>
              </Table.Td>
              <Table.Td>
                <StatusBadge status={tenant.status} />
              </Table.Td>
              <Table.Td>{new Date(tenant.created_at).toLocaleDateString('pt-BR')}</Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <Tooltip label="Ver detalhe">
                    <ActionIcon variant="subtle" onClick={() => navigate(`/tenants/${tenant.slug}`)}>
                      <IconEye size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label={tenant.status === 'active' ? 'Suspender' : 'Reativar'}>
                    <ActionIcon
                      variant="subtle"
                      color={tenant.status === 'active' ? 'orange' : 'green'}
                      onClick={() => handleToggle(tenant.slug, tenant.status)}
                      loading={updateStatus.isPending}
                    >
                      {tenant.status === 'active' ? <IconPlayerPause size={16} /> : <IconPlayerPlay size={16} />}
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {totalPages > 1 && <Pagination total={totalPages} value={page} onChange={setPage} />}
    </Stack>
  )
}
