import { useState } from 'react'
import {
  ActionIcon,
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  NativeSelect,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconPlus, IconUserOff } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'

import { useDeactivateUser, useInviteUser, useUsers } from '../hooks/useUsers'

export function UserList() {
  const { data: users, isLoading } = useUsers()
  const invite = useInviteUser()
  const deactivate = useDeactivateUser()
  const [modalOpen, setModalOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<'CLINICO' | 'PACIENTE'>('CLINICO')

  const handleInvite = async () => {
    try {
      await invite.mutateAsync({ email, name, role })
      notifications.show({
        title: 'Usuario convidado',
        message: `${email} adicionado com role ${role}.`,
        color: 'green',
      })
      setModalOpen(false)
      setEmail('')
      setName('')
      setRole('CLINICO')
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Falha ao convidar usuario.',
        color: 'red',
      })
    }
  }

  const handleDeactivate = async (userId: string) => {
    try {
      await deactivate.mutateAsync(userId)
      notifications.show({ title: 'Desativado', message: 'Usuario desativado.', color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao desativar.', color: 'red' })
    }
  }

  if (isLoading) return <Center><Loader /></Center>

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Usuarios</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setModalOpen(true)}>
          Convidar
        </Button>
      </Group>

      <Paper withBorder>
        <Table highlightOnHover striped withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Nome</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Acoes</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {users?.map((u) => (
              <Table.Tr key={u.id}>
                <Table.Td>{u.firstName ?? u.username}</Table.Td>
                <Table.Td>{u.email}</Table.Td>
                <Table.Td>
                  <Badge color={u.enabled ? 'green' : 'gray'} variant="light">
                    {u.enabled ? 'Ativo' : 'Desativado'}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  {u.enabled && (
                    <Tooltip label="Desativar">
                      <ActionIcon
                        color="orange"
                        variant="subtle"
                        onClick={() => handleDeactivate(u.id)}
                        loading={deactivate.isPending}
                      >
                        <IconUserOff size={16} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
            {!users?.length && (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Text ta="center" c="dimmed" py="lg">Nenhum usuario.</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title="Convidar usuario">
        <Stack>
          <TextInput
            label="Nome"
            placeholder="Nome completo"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            required
          />
          <TextInput
            label="Email"
            placeholder="usuario@exemplo.com"
            value={email}
            onChange={(e) => setEmail(e.currentTarget.value)}
            required
          />
          <NativeSelect
            label="Role"
            data={[
              { value: 'CLINICO', label: 'Clinico' },
              { value: 'PACIENTE', label: 'Paciente' },
            ]}
            value={role}
            onChange={(e) => setRole(e.currentTarget.value as 'CLINICO' | 'PACIENTE')}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleInvite} loading={invite.isPending}>Convidar</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
