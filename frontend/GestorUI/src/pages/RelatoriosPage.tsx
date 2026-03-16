import { useState } from 'react'
import { Button, Card, Group, Stack, Text, Title, SimpleGrid } from '@mantine/core'
import { IconFileTypePdf } from '@tabler/icons-react'
import { DatePickerInput } from '@mantine/dates'
import '@mantine/dates/styles.css'
import { useDownloadPdf } from '../hooks/useDownloadPdf'

export function RelatoriosPage() {
  const { downloadPdf, isDownloading } = useDownloadPdf()
  const [startDate, setStartDate] = useState<Date | null>(null)
  const [endDate, setEndDate] = useState<Date | null>(null)

  const handleExportConsultas = () => {
    if (!startDate || !endDate) return
    
    // Format to YYYY-MM-DD
    const start = startDate.toISOString().slice(0, 10)
    const end = endDate.toISOString().slice(0, 10)
    
    void downloadPdf(`/gestor/relatorios/consultas?inicio=${start}&fim=${end}`, `consultas_${start}_${end}.pdf`)
  }

  return (
    <Stack gap="lg">
      <Stack gap={4}>
        <Title order={2}>Relatórios</Title>
        <Text c="dimmed">Exportação de relatórios gerenciais das unidades.</Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Card withBorder radius="lg" p="lg">
          <Stack gap="md">
            <Title order={4}>Consultas por Período</Title>
            <Text size="sm" c="dimmed">
              Exporte a lista completa de atendimentos e consultas do tenant dentro do período selecionado.
            </Text>
            
            <Group grow>
              <DatePickerInput<any>
                label="Data Início"
                placeholder="Selecione..."
                value={startDate}
                onChange={setStartDate as any}
                clearable
              />
              <DatePickerInput<any>
                label="Data Fim"
                placeholder="Selecione..."
                value={endDate}
                onChange={setEndDate as any}
                clearable
              />
            </Group>
            
            <Group justify="flex-end" mt="sm">
              <Button
                leftSection={<IconFileTypePdf size={16} />}
                variant="light"
                color="red"
                disabled={!startDate || !endDate}
                loading={isDownloading}
                onClick={handleExportConsultas}
              >
                Gerar Relatório
              </Button>
            </Group>
          </Stack>
        </Card>
      </SimpleGrid>
    </Stack>
  )
}
