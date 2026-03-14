import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TextInput, Table, Text, Stack, Title, Loader, Center } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { usePatients } from '../hooks/usePatients'

export function PatientList() {
  const [search, setSearch] = useState('')
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
        <Table highlightOnHover striped withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Nome</Table.Th>
              <Table.Th>Data Nasc.</Table.Th>
              <Table.Th>CPF</Table.Th>
              <Table.Th>Telefone</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data.map(p => (
              <Table.Tr
                key={p.id}
                onClick={() => navigate(`/encounter/${p.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <Table.Td>{p.full_name}</Table.Td>
                <Table.Td>{new Date(p.birth_date).toLocaleDateString('pt-BR')}</Table.Td>
                <Table.Td>{p.cpf}</Table.Td>
                <Table.Td>{p.phone ?? '—'}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  )
}
