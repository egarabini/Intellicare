import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TextInput, Table, Text, Stack, Title, Loader, Center, Pagination, Badge } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { usePatients } from '../hooks/usePatients'

export function PatientList() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [debounced] = useDebouncedValue(search, 400)
  const { data, isLoading, isFetching } = usePatients(debounced)
  const navigate = useNavigate()

  return (
    <Stack>
      <Title order={2}>Pacientes</Title>
      <TextInput
        placeholder="Buscar por nome (mín. 3 caracteres)..."
        value={search}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.currentTarget.value)}
        rightSection={isFetching ? <Loader size="xs" /> : null}
      />

      {isLoading && (
        <Center><Loader /></Center>
      )}

      {data && data.length === 0 && (
        <Text c="dimmed">Nenhum paciente encontrado.</Text>
      )}

      {data && data.length > 0 && (
        <>
          <Table highlightOnHover striped withTableBorder>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Idade</Table.Th>
                <Table.Th>CPF</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.slice((page - 1) * 15, page * 15).map(p => {
                const age = new Date().getFullYear() - new Date(p.birth_date).getFullYear();
                return (
                  <Table.Tr
                    key={p.id}
                    onClick={() => navigate(`/patients/${p.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Table.Td fw={500}>{p.full_name}</Table.Td>
                    <Table.Td>{age} anos</Table.Td>
                    <Table.Td>{p.cpf}</Table.Td>
                    <Table.Td>
                      <Badge color={p.active ? 'green' : 'red'} variant="light">
                        {p.active ? 'Ativo' : 'Inativo'}
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
          
          {data.length > 15 && (
            <Center mt="md">
              <Pagination 
                value={page} 
                onChange={setPage} 
                total={Math.ceil(data.length / 15)} 
              />
            </Center>
          )}
        </>
      )}
    </Stack>
  )
}
