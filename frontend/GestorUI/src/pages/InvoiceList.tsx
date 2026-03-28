import { useState } from 'react';
import { Box, Title, Group, Table, Badge, Button, Select, Text } from '@mantine/core';
import { useInvoices, useMarkInvoicePaid } from '../hooks/useGestor';
import { IconDownload, IconCheck } from '@tabler/icons-react';
import api from '../api/client';

export function InvoiceList() {
  const [status, setStatus] = useState<string | null>(null);
  const { data: invoices, isLoading } = useInvoices(1, 50, status || undefined);
  const markInvoicePaid = useMarkInvoicePaid();

  const handleExportCSV = async () => {
    try {
      const response = await api.get('/gestor/invoices/export-csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'faturas.csv');
      document.body.appendChild(link);
      link.click();
    } catch (e) {
      alert("Erro ao exportar faturas.");
    }
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Faturas</Title>
        <Button leftSection={<IconDownload size={16}/>} variant="light" onClick={handleExportCSV}>
          Exportar CSV
        </Button>
      </Group>

      <Select
        label="Filtrar por Status"
        placeholder="Todos"
        value={status}
        onChange={setStatus}
        data={[
          { value: 'pending', label: 'Pendente' },
          { value: 'paid', label: 'Pago' },
          { value: 'overdue', label: 'Atrasado' }
        ]}
        clearable
        mb="md"
        w={300}
      />

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>ID</Table.Th>
            <Table.Th>Data de Criação</Table.Th>
            <Table.Th>Valor (R$)</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Data Pgto</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr><Table.Td colSpan={6}>Carregando...</Table.Td></Table.Tr>
          ) : invoices?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={6}>Nenhuma fatura encontrada.</Table.Td></Table.Tr>
          ) : (
            invoices?.map(inv => (
              <Table.Tr key={inv.id}>
                <Table.Td><Text size="xs" c="dimmed">{inv.id}</Text></Table.Td>
                <Table.Td>{new Date(inv.created_at).toLocaleDateString()}</Table.Td>
                <Table.Td>{Number(inv.amount ?? 0).toFixed(2)}</Table.Td>
                <Table.Td>
                  <Badge color={inv.status === 'paid' ? 'green' : inv.status === 'overdue' ? 'red' : 'orange'}>
                    {inv.status}
                  </Badge>
                </Table.Td>
                <Table.Td>{inv.paid_at ? new Date(inv.paid_at).toLocaleDateString() : '-'}</Table.Td>
                <Table.Td>
                  {inv.status !== 'paid' && (
                    <Button 
                      size="xs" variant="light" color="green"
                      leftSection={<IconCheck size={14}/>}
                      onClick={() => markInvoicePaid.mutate(inv.id)}
                      loading={markInvoicePaid.isPending}
                    >
                      Pagar
                    </Button>
                  )}
                </Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>
    </Box>
  );
}
