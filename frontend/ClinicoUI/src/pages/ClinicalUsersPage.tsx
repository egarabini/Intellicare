import { Box, Title, Table, Badge, Loader, Center } from '@mantine/core'
import { useClinicalUsers } from '../hooks/useClinicalUsers'

export function ClinicalUsersPage() {
  const { data: users, isLoading } = useClinicalUsers()

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Title order={2} mb="lg">Equipe — Usuários Clínicos</Title>

      <Table striped highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>E-mail</Table.Th>
            <Table.Th>Papel</Table.Th>
            <Table.Th>Status</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {users?.map(u => (
            <Table.Tr key={u.id}>
              <Table.Td>{u.name}</Table.Td>
              <Table.Td>{u.email || '—'}</Table.Td>
              <Table.Td><Badge variant="light">{u.role}</Badge></Table.Td>
              <Table.Td>
                <Badge color={u.status === 'active' ? 'green' : 'gray'} variant="dot">
                  {u.status === 'active' ? 'Ativo' : 'Inativo'}
                </Badge>
              </Table.Td>
            </Table.Tr>
          ))}
          {users?.length === 0 && (
            <Table.Tr><Table.Td colSpan={4} style={{ textAlign: 'center' }}>Nenhum usuário encontrado.</Table.Td></Table.Tr>
          )}
        </Table.Tbody>
      </Table>
    </Box>
  )
}
