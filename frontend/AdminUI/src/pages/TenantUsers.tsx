import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Title, Stack, Table, Badge, Button, Group,
  Modal, TextInput, Select, ActionIcon, Tooltip,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { IconUserPlus, IconUserOff } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { useTenantUsers, useInviteUser, useDeactivateUser } from '../hooks/useTenants'

export function TenantUsers() {
  const { slug } = useParams<{ slug: string }>()
  const [inviteOpen, setInviteOpen] = useState(false)
  const { data: users } = useTenantUsers(slug!)
  const invite    = useInviteUser(slug!)
  const deactivate = useDeactivateUser(slug!)

  const form = useForm({
    initialValues: { email: '', name: '', role: 'CLINICO' },
    validate: {
      email: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Email inválido',
      name:  v => v.length >= 3 ? null : 'Mínimo 3 caracteres',
    },
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleInvite = async (values: any) => {
    try {
      await invite.mutateAsync(values)
      notifications.show({ title: 'Usuário convidado', message: values.email, color: 'green' })
      setInviteOpen(false)
      form.reset()
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao convidar usuário', color: 'red' })
    }
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Usuários — {slug}</Title>
        <Button leftSection={<IconUserPlus size={16} />} onClick={() => setInviteOpen(true)}>
          Convidar Usuário
        </Button>
      </Group>

      <Table withTableBorder highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Email</Table.Th>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Role</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {users?.users?.map((u: any) => (
            <Table.Tr key={u.keycloak_id}>
              <Table.Td>{u.email}</Table.Td>
              <Table.Td>{u.username}</Table.Td>
              <Table.Td>
                <Badge variant="light" color={u.roles?.[0] ? 'blue' : 'gray'}>
                  {u.roles?.[0] ?? 'Sem role'}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Badge color={u.enabled ? 'green' : 'red'} variant="light">
                  {u.enabled ? 'Ativo' : 'Inativo'}
                </Badge>
              </Table.Td>
              <Table.Td>
                {u.enabled && (
                  <Tooltip label="Desativar usuário">
                    <ActionIcon
                      color="red" variant="subtle"
                      onClick={() => deactivate.mutate(u.keycloak_id)}
                    >
                      <IconUserOff size={16} />
                    </ActionIcon>
                  </Tooltip>
                )}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <Modal opened={inviteOpen} onClose={() => setInviteOpen(false)} title="Convidar Usuário">
        <form onSubmit={form.onSubmit(handleInvite)}>
          <Stack>
            <TextInput label="Email" required {...form.getInputProps('email')} />
            <TextInput label="Nome completo" required {...form.getInputProps('name')} />
            <Select
              label="Perfil"
              data={[
                { value: 'TENANT_GESTOR', label: 'Gestor' },
                { value: 'CLINICO',       label: 'Clínico' },
                { value: 'PACIENTE',      label: 'Paciente' },
              ]}
              {...form.getInputProps('role')}
            />
            <Button type="submit" loading={invite.isPending}>Enviar Convite</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
