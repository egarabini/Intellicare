/**
 * DEM-065 — TenantConfigPage: editar configurações de um tenant.
 */
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button,
  Center,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconArrowLeft, IconPlus } from '@tabler/icons-react'

import { useTenantConfig, useSetTenantConfig } from '../hooks/useTenants'

export function TenantConfigPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { data, isLoading } = useTenantConfig(slug!)
  const setConfig = useSetTenantConfig(slug!)

  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')

  const handleAdd = async () => {
    if (!newKey.trim() || !newValue.trim()) return
    try {
      await setConfig.mutateAsync({ key: newKey.trim(), value: newValue.trim() })
      notifications.show({ title: 'Salvo', message: `Config '${newKey}' atualizada.`, color: 'green' })
      setNewKey('')
      setNewValue('')
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar configuração.', color: 'red' })
    }
  }

  if (isLoading) return <Center><Loader /></Center>

  return (
    <Stack gap="md">
      <Group>
        <Button variant="subtle" leftSection={<IconArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Voltar
        </Button>
        <Title order={2}>Configurações — {slug}</Title>
      </Group>

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Chave</Table.Th>
            <Table.Th>Valor</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {(data?.configs ?? []).map((cfg) => (
            <Table.Tr key={cfg.key}>
              <Table.Td><Text ff="monospace" size="sm">{cfg.key}</Text></Table.Td>
              <Table.Td>{cfg.value}</Table.Td>
            </Table.Tr>
          ))}
          {(data?.configs ?? []).length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={2}><Text c="dimmed" ta="center">Nenhuma configuração definida.</Text></Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      <Title order={4}>Adicionar / Atualizar</Title>
      <Group>
        <TextInput placeholder="Chave" value={newKey} onChange={(e) => setNewKey(e.currentTarget.value)} />
        <TextInput placeholder="Valor" value={newValue} onChange={(e) => setNewValue(e.currentTarget.value)} style={{ flex: 1 }} />
        <Button leftSection={<IconPlus size={16} />} onClick={handleAdd} loading={setConfig.isPending}>
          Salvar
        </Button>
      </Group>
    </Stack>
  )
}
