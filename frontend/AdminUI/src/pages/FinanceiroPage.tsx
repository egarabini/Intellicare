import { useState } from 'react'
import {
  ActionIcon,
  Button,
  Card,
  Group,
  Loader,
  NumberInput,
  Pagination,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { IconCash, IconDeviceFloppy, IconTrash, IconFileTypePdf } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { MonthPickerInput } from '@mantine/dates'
import '@mantine/dates/styles.css'

import { StatusBadge } from '../components/StatusBadge'
import {
  ExpensePayload,
  useCreateExpense,
  useDeleteExpense,
  useExpenses,
  useFinanceiroDashboard,
  useInvoices,
  useUpdateInvoiceStatus,
} from '../hooks/useFinanceiro'
import { useDownloadPdf } from '../hooks/useDownloadPdf'

const INVOICE_STATUS_OPTIONS = [
  { value: 'pending', label: 'Pendente' },
  { value: 'paid', label: 'Pago' },
  { value: 'overdue', label: 'Atrasado' },
  { value: 'cancelled', label: 'Cancelado' },
]

const EXPENSE_CATEGORY_OPTIONS = [
  { value: 'infrastructure', label: 'Infraestrutura' },
  { value: 'license', label: 'Licenca' },
  { value: 'personnel', label: 'Pessoal' },
  { value: 'other', label: 'Outros' },
]

function currency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function emptyExpense(): ExpensePayload {
  return {
    category: 'infrastructure',
    description: '',
    amount_brl: 0,
    expense_date: new Date().toISOString().slice(0, 10),
    tenant_slug: '',
  }
}

export function FinanceiroPage() {
  const [invoicePage, setInvoicePage] = useState(1)
  const [expensePage, setExpensePage] = useState(1)
  const [expenseForm, setExpenseForm] = useState<ExpensePayload>(emptyExpense())
  const dashboardQuery = useFinanceiroDashboard()
  const invoicesQuery = useInvoices(invoicePage, 10)
  const expensesQuery = useExpenses(expensePage, 10)
  const updateInvoiceStatus = useUpdateInvoiceStatus()
  const createExpense = useCreateExpense()
  const deleteExpense = useDeleteExpense()
  const { downloadPdf, isDownloading } = useDownloadPdf()
  const [reportMonth, setReportMonth] = useState<Date | null>(new Date())

  const saveExpense = async () => {
    try {
      await createExpense.mutateAsync({
        ...expenseForm,
        tenant_slug: expenseForm.tenant_slug || null,
      })
      notifications.show({ title: 'Despesa registrada', message: 'Lancamento salvo com sucesso.', color: 'green' })
      setExpenseForm(emptyExpense())
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao registrar despesa.', color: 'red' })
      console.error(error)
    }
  }

  const removeExpense = async (id: number) => {
    try {
      await deleteExpense.mutateAsync(id)
      notifications.show({ title: 'Despesa removida', message: 'Lancamento excluido.', color: 'green' })
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao excluir despesa.', color: 'red' })
      console.error(error)
    }
  }

  const changeInvoiceStatus = async (id: string, status: string) => {
    try {
      await updateInvoiceStatus.mutateAsync({ id, status: status as 'paid' | 'overdue' | 'cancelled' | 'pending' })
      notifications.show({ title: 'Fatura atualizada', message: 'Status financeiro atualizado.', color: 'green' })
    } catch (error) {
      notifications.show({ title: 'Erro', message: 'Falha ao atualizar fatura.', color: 'red' })
      console.error(error)
    }
  }

  if (dashboardQuery.isLoading || invoicesQuery.isLoading || expensesQuery.isLoading) {
    return <Loader />
  }

  const dashboard = dashboardQuery.data
  const invoices = invoicesQuery.data
  const expenses = expensesQuery.data

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-start">
        <Stack gap={4}>
          <Title order={2}>Financeiro</Title>
          <Text c="dimmed">Receita, despesas de plataforma e acompanhamento de faturas.</Text>
        </Stack>
        <Group>
          <MonthPickerInput
            placeholder="Mês do relatório"
            value={reportMonth}
            onChange={setReportMonth}
            w={160}
          />
          <Button
            leftSection={<IconFileTypePdf size={16} />}
            variant="light"
            color="red"
            disabled={!reportMonth}
            loading={isDownloading}
            onClick={() => {
              if (!reportMonth) return;
              const mesStr = reportMonth.toISOString().slice(0, 7);
              void downloadPdf(`/admin/relatorios/receita?mes=${mesStr}`, `receita-${mesStr}.pdf`);
            }}
          >
            Exportar Receita
          </Button>
        </Group>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 4 }}>
        <Card withBorder radius="lg" p="lg"><Stack gap={4}><Text c="dimmed">Receita do mes</Text><Title order={3}>{currency(dashboard?.receita_mes ?? 0)}</Title></Stack></Card>
        <Card withBorder radius="lg" p="lg"><Stack gap={4}><Text c="dimmed">Despesa do mes</Text><Title order={3}>{currency(dashboard?.despesa_mes ?? 0)}</Title></Stack></Card>
        <Card withBorder radius="lg" p="lg"><Stack gap={4}><Text c="dimmed">Resultado do mes</Text><Title order={3}>{currency(dashboard?.resultado_mes ?? 0)}</Title></Stack></Card>
        <Card withBorder radius="lg" p="lg"><Stack gap={4}><Text c="dimmed">Inadimplencia</Text><Title order={3}>{currency(dashboard?.inadimplencia ?? 0)}</Title></Stack></Card>
      </SimpleGrid>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Title order={4}>Faturas</Title>
          <Table withTableBorder striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Tenant</Table.Th>
                <Table.Th>Periodo</Table.Th>
                <Table.Th>Vencimento</Table.Th>
                <Table.Th>Valor</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(invoices?.items ?? []).map((invoice) => (
                <Table.Tr key={invoice.id}>
                  <Table.Td>{invoice.tenant_slug}</Table.Td>
                  <Table.Td>{invoice.period_start} a {invoice.period_end}</Table.Td>
                  <Table.Td>{invoice.due_date}</Table.Td>
                  <Table.Td>{currency(invoice.amount_brl_display)}</Table.Td>
                  <Table.Td>
                    <Select
                      data={INVOICE_STATUS_OPTIONS}
                      value={invoice.status}
                      onChange={(value) => value && void changeInvoiceStatus(invoice.id, value)}
                    />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
          <Pagination total={Math.max(Math.ceil((invoices?.total ?? 0) / 10), 1)} value={invoicePage} onChange={setInvoicePage} />
        </Stack>
      </Card>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Title order={4}>Nova despesa</Title>
          <SimpleGrid cols={{ base: 1, md: 4 }}>
            <Select label="Categoria" data={EXPENSE_CATEGORY_OPTIONS} value={expenseForm.category} onChange={(value) => value && setExpenseForm({ ...expenseForm, category: value as ExpensePayload['category'] })} />
            <TextInput label="Descricao" value={expenseForm.description} onChange={(e) => setExpenseForm({ ...expenseForm, description: e.currentTarget.value })} />
            <NumberInput label="Valor (centavos)" min={0} value={expenseForm.amount_brl} onChange={(value) => setExpenseForm({ ...expenseForm, amount_brl: Number(value) || 0 })} />
            <TextInput label="Data" type="date" value={expenseForm.expense_date} onChange={(e) => setExpenseForm({ ...expenseForm, expense_date: e.currentTarget.value })} />
          </SimpleGrid>
          <Group justify="space-between">
            <TextInput w={280} label="Tenant relacionado (opcional)" value={expenseForm.tenant_slug ?? ''} onChange={(e) => setExpenseForm({ ...expenseForm, tenant_slug: e.currentTarget.value })} />
            <Button leftSection={<IconCash size={16} />} onClick={() => void saveExpense()} loading={createExpense.isPending}>
              Registrar despesa
            </Button>
          </Group>
        </Stack>
      </Card>

      <Card withBorder radius="lg" p="lg">
        <Stack gap="md">
          <Title order={4}>Despesas recentes</Title>
          <Table withTableBorder striped>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Data</Table.Th>
                <Table.Th>Categoria</Table.Th>
                <Table.Th>Descricao</Table.Th>
                <Table.Th>Tenant</Table.Th>
                <Table.Th>Valor</Table.Th>
                <Table.Th>Acoes</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(expenses?.items ?? []).map((expense) => (
                <Table.Tr key={expense.id}>
                  <Table.Td>{expense.expense_date}</Table.Td>
                  <Table.Td><StatusBadge status={expense.category} /></Table.Td>
                  <Table.Td>{expense.description}</Table.Td>
                  <Table.Td>{expense.tenant_slug || 'Plataforma'}</Table.Td>
                  <Table.Td>{currency(expense.amount_brl_display)}</Table.Td>
                  <Table.Td>
                    <ActionIcon variant="subtle" color="red" onClick={() => void removeExpense(expense.id)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
          <Pagination total={Math.max(Math.ceil((expenses?.total ?? 0) / 10), 1)} value={expensePage} onChange={setExpensePage} />
        </Stack>
      </Card>
    </Stack>
  )
}
