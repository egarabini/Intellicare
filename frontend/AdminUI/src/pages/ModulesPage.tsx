import { useMemo, useState } from 'react'
import { Button, Card, Group, Loader, Select, Stack, Switch, Table, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'

import { StatusBadge } from '../components/StatusBadge'
import { useModules, useTenantModules, useUpdateModuleStatus, useUpdateTenantModule } from '../hooks/useModules'
import { useTenants } from '../hooks/useTenants'

const MODULE_STATUS_OPTIONS = [
  { value: 'active', label: 'Ativo' },
  { value: 'inactive', label: 'Inativo' },
  { value: 'dev', label: 'Desenvolvimento' },
]

export function ModulesPage() {
  const modulesQuery = useModules()
  const tenantsQuery = useTenants(1, 100)
  const firstTenant = tenantsQuery.data?.items[0]?.slug ?? ''
  const [tenantSlug, setTenantSlug] = useState('')
  const activeTenant = tenantSlug || firstTenant
  const tenantModulesQuery = useTenantModules(activeTenant)
  const updateModuleStatus = useUpdateModuleStatus()
  const updateTenantModule = useUpdateTenantModule(activeTenant)

  const tenantOptions = useMemo(
    () => (tenantsQuery.data?.items ?? []).map((tenant) => ({ value: tenant.slug, label: tenant.name })),
    [tenantsQuery.data],
  )

  const handleModuleStatus = async (slug: string, status: string) => {
    try {
      await updateModuleStatus.mutateAsync({ slug, status: status as 'active' | 'inactive' | 'dev' })
      notifications.show({ title: 'Modulo atualizado', message: 'Status global atualizado.', color: 'green' })
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao alterar status do modulo.', color: 'red' })
      console.error(error)
    }
  }

  const handleTenantToggle = async (moduleSlug: string, enabled: boolean) => {
    try {
      await updateTenantModule.mutateAsync({ moduleSlug, enabled })
      notifications.show({ title: 'Tenant atualizado', message: 'Habilitacao do modulo salva.', color: 'green' })
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Nao foi possivel atualizar o tenant.', color: 'red' })
      console.error(error)
    }
  }

  if (modulesQuery.isLoading || tenantsQuery.isLoading) {
    return <Loader />
  }

  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={2}>Modulos</Title>
        <Text c="dimmed">Controle global de disponibilidade e habilitacao por tenant.</Text>
      </Stack>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Title order={4}>Catalogo da plataforma</Title>
          <Table withTableBorder striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Modulo</Table.Th>
                <Table.Th>Versao</Table.Th>
                <Table.Th>Tenants ativos</Table.Th>
                <Table.Th>Status global</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(modulesQuery.data ?? []).map((module) => (
                <Table.Tr key={module.slug}>
                  <Table.Td>
                    <Stack gap={0}>
                      <Text fw={600}>{module.name}</Text>
                      <Text size="sm" c="dimmed">{module.description || module.slug}</Text>
                    </Stack>
                  </Table.Td>
                  <Table.Td>{module.version}</Table.Td>
                  <Table.Td>{module.tenant_count}</Table.Td>
                  <Table.Td>
                    <Select
                      data={MODULE_STATUS_OPTIONS}
                      value={module.status}
                      onChange={(value) => value && void handleModuleStatus(module.slug, value)}
                    />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Stack>
      </Card>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Group justify="space-between">
            <Title order={4}>Habilitacao por tenant</Title>
            <Select
              w={320}
              label="Tenant"
              placeholder="Selecione um tenant"
              data={tenantOptions}
              value={activeTenant || null}
              onChange={(value) => setTenantSlug(value ?? '')}
            />
          </Group>

          {tenantModulesQuery.isLoading ? (
            <Loader />
          ) : (
            <Table withTableBorder striped>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Modulo</Table.Th>
                  <Table.Th>Status global</Table.Th>
                  <Table.Th>Habilitado</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {(tenantModulesQuery.data ?? []).map((module) => (
                  <Table.Tr key={module.module_slug}>
                    <Table.Td>
                      <Stack gap={0}>
                        <Text fw={600}>{module.name}</Text>
                        <Text size="sm" c="dimmed">{module.description || module.module_slug}</Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td><StatusBadge status={module.status} /></Table.Td>
                    <Table.Td>
                      <Switch
                        checked={module.enabled}
                        disabled={module.status === 'dev' || updateTenantModule.isPending}
                        onChange={(event) => void handleTenantToggle(module.module_slug, event.currentTarget.checked)}
                      />
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
          <Button variant="light" onClick={() => tenantModulesQuery.refetch()}>
            Atualizar lista
          </Button>
        </Stack>
      </Card>
    </Stack>
  )
}
