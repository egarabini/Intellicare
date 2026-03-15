import { useState } from 'react'
import {
  Card, Group, Loader, Pagination, Stack, Table, Text, Title,
} from '@mantine/core'
import { useHistorico } from '../hooks/usePaciente'

export function HistoricoPage() {
  const [page, setPage] = useState(1)
  const size = 10
  const { data, isLoading } = useHistorico(page, size)

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / size) || 1

  return (
    <Stack gap="lg">
      <Title order={2}>Histórico Clínico</Title>
      <Text size="sm" c="dimmed">
        Consultas encerradas — diagnóstico e prescrição. Notas SOAP são restritas ao clínico.
      </Text>

      {isLoading ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !items.length ? (
        <Card withBorder padding="lg"><Text c="dimmed">Nenhum registro encontrado.</Text></Card>
      ) : (
        <>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Data</Table.Th>
                <Table.Th>Tipo</Table.Th>
                <Table.Th>CID-10</Table.Th>
                <Table.Th>Prescrição</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((r: any) => (
                <Table.Tr key={r.id}>
                  <Table.Td>{r.date ?? '—'}</Table.Td>
                  <Table.Td>{r.type}</Table.Td>
                  <Table.Td>{r.cid10_code ?? '—'}</Table.Td>
                  <Table.Td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.prescription ?? '—'}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
          {totalPages > 1 && (
            <Group justify="center">
              <Pagination total={totalPages} value={page} onChange={setPage} />
            </Group>
          )}
        </>
      )}
    </Stack>
  )
}

