import { useParams } from 'react-router-dom'
import { Badge, Loader, Paper, Stack, Switch, Table, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'

import { StatusBadge } from '../components/StatusBadge'
import { useTenant, useTenantUsers } from '../hooks/useTenants'
import { useTenantModules, useUpdateTenantModule } from '../hooks/useModules'

export function TenantDetail() {
  const { slug = '' } = useParams()
  const tenantQuery = useTenant(slug)
  const usersQuery = useTenantUsers(slug)
  const modulesQuery = useTenantModules(slug)
  const updateTenantModule = useUpdateTenantModule(slug)

  if (tenantQuery.isLoading || usersQuery.isLoading || modulesQuery.isLoading) {
    return <Loader />
  }

  const tenant = tenantQuery.data
  const users = usersQuery.data?.users ?? []
  const modules = modulesQuery.data ?? []

  const handleModuleToggle = async (moduleSlug: string, enabled: boolean) => {
    try {
      await updateTenantModule.mutateAsync({ moduleSlug, enabled })
      notifications.show({
        title: 'Modulo atualizado',
        message: 'Configuracao do tenant salva com sucesso.',
        color: 'green',
      })
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Falha ao atualizar modulo do tenant.',
        color: 'red',
      })
    }
  }

  if (!tenant) {
    return (
      <Paper withBorder p="lg">
        <Text>Tenant nao encontrado.</Text>
      </Paper>
    )
  }

  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={2}>{tenant.name}</Title>
        <Text c="dimmed" ff="monospace">
          {tenant.slug}
        </Text>
      </Stack>

      <Paper withBorder p="lg" radius="lg">
        <Stack gap="sm">
          <Text>
            <strong>Status:</strong> <StatusBadge status={tenant.status} />
          </Text>
          <Text>
            <strong>Criado em:</strong> {new Date(tenant.created_at).toLocaleString('pt-BR')}
          </Text>
          <Text>
            <strong>Atualizado em:</strong> {new Date(tenant.updated_at).toLocaleString('pt-BR')}
          </Text>
        </Stack>
      </Paper>

      <Paper withBorder p="lg" radius="lg">
        <Stack gap="md">
          <Title order={3}>Modulos habilitados</Title>
          <Table withTableBorder striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Modulo</Table.Th>
                <Table.Th>Status global</Table.Th>
                <Table.Th>Habilitado</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {modules.map((module) => (
                <Table.Tr key={module.module_slug}>
                  <Table.Td>
                    <Stack gap={0}>
                      <Text fw={600}>{module.name}</Text>
                      <Text size="sm" c="dimmed">{module.description || module.module_slug}</Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <StatusBadge status={module.status} />
                  </Table.Td>
                  <Table.Td>
                    <Switch
                      checked={module.enabled}
                      disabled={module.status === 'dev' || updateTenantModule.isPending}
                      onChange={(event) => void handleModuleToggle(module.module_slug, event.currentTarget.checked)}
                    />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Stack>
      </Paper>

      <Paper withBorder p="lg" radius="lg">
        <Stack gap="md">
          <Title order={3}>Usuarios do tenant</Title>
          <Table withTableBorder striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Username</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Roles</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {users.map((user) => (
                <Table.Tr key={user.keycloak_id}>
                  <Table.Td>{user.username}</Table.Td>
                  <Table.Td>{user.email}</Table.Td>
                  <Table.Td>
                    <Stack gap={4}>
                      {user.roles.map((role) => (
                        <Badge key={role} variant="light" color="blue">
                          {role}
                        </Badge>
                      ))}
                    </Stack>
                  </Table.Td>
                  <Table.Td>{user.enabled ? 'Ativo' : 'Desabilitado'}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Stack>
      </Paper>
    </Stack>
  )
}
