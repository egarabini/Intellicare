import { useState } from 'react';
import { Box, Title, Group, Badge, Card, Text, Button, Stack, Loader, Center, Grid, Select, SimpleGrid } from '@mantine/core';
import { DatePicker } from '@mantine/dates';
import { useNavigate } from 'react-router-dom';
import { useMyAgenda } from '../hooks/useMyAgenda';
import { useDownloadPdf } from '../hooks/useDownloadPdf';
import { IconFileTypePdf } from '@tabler/icons-react';

import '@mantine/dates/styles.css';

const STATUS_META: Record<string, { color: string; label: string }> = {
  agendado: { color: 'blue', label: 'Agendado' },
  confirmado: { color: 'green', label: 'Confirmado pelo paciente' },
  realizado: { color: 'gray', label: 'Realizado' },
  cancelado: { color: 'red', label: 'Cancelado' },
};

function toLocalDateParam(value: Date) {
  const year = value.getFullYear();
  const month = `${value.getMonth() + 1}`.padStart(2, '0');
  const day = `${value.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function Agenda() {
  const [date, setDate] = useState<Date | null>(new Date());
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  
  const dateStr = date ? toLocalDateParam(date) : undefined;
  const { data: agenda, isLoading } = useMyAgenda(dateStr);
  const { downloadPdf, isDownloading } = useDownloadPdf();
  const navigate = useNavigate();

  const filteredAgenda = agenda?.filter((item) => {
    const matchesType = !typeFilter || item.type === typeFilter;
    const matchesStatus = !statusFilter || item.status === statusFilter;
    return matchesType && matchesStatus;
  }) ?? [];

  const summary = filteredAgenda.reduce((acc, item) => {
    acc.total += 1;
    if (item.status === 'confirmado') acc.confirmed += 1;
    if (item.status === 'cancelado') acc.cancelled += 1;
    if (item.encounter_id) acc.inProgress += 1;
    return acc;
  }, { total: 0, confirmed: 0, cancelled: 0, inProgress: 0 });

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Agenda Clínica</Title>
        <Button
          leftSection={<IconFileTypePdf size={16} />}
          variant="light"
          color="red"
          disabled={!dateStr}
          loading={isDownloading}
          onClick={() => {
            if (dateStr) {
              void downloadPdf(`/cuidado/relatorios/agenda?data=${dateStr}`, `agenda_${dateStr}.pdf`)
            }
          }}
        >
          Exportar Agenda Diária
        </Button>
      </Group>

      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder shadow="sm" radius="md" p="md">
            <DatePicker 
              value={date} 
              onChange={(v: any) => setDate(v)} 
              size="md" 
              w="100%"
            />
          </Card>
          
          <Select
            mt="md"
            label="Filtrar por tipo"
            placeholder="Todos os tipos"
            value={typeFilter}
            onChange={setTypeFilter}
            data={[
              { value: 'consulta', label: 'Consulta' },
              { value: 'retorno', label: 'Retorno' },
              { value: 'exame', label: 'Exame' }
            ]}
            clearable
          />

          <Select
            mt="md"
            label="Filtrar por status"
            placeholder="Todos os status"
            value={statusFilter}
            onChange={setStatusFilter}
            data={[
              { value: 'agendado', label: 'Agendado' },
              { value: 'confirmado', label: 'Confirmado' },
              { value: 'realizado', label: 'Realizado' },
              { value: 'cancelado', label: 'Cancelado' }
            ]}
            clearable
          />
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Title order={4} mb="md">
            Consultas em {date ? date.toLocaleDateString() : 'Nenhuma data'}
          </Title>

          <SimpleGrid cols={{ base: 2, sm: 4 }} mb="md">
            <Card withBorder radius="md" p="sm">
              <Text size="xs" c="dimmed">Total</Text>
              <Text fw={700} size="xl">{summary.total}</Text>
            </Card>
            <Card withBorder radius="md" p="sm">
              <Text size="xs" c="dimmed">Confirmados</Text>
              <Text fw={700} size="xl" c="green">{summary.confirmed}</Text>
            </Card>
            <Card withBorder radius="md" p="sm">
              <Text size="xs" c="dimmed">Cancelados</Text>
              <Text fw={700} size="xl" c="red">{summary.cancelled}</Text>
            </Card>
            <Card withBorder radius="md" p="sm">
              <Text size="xs" c="dimmed">Em atendimento</Text>
              <Text fw={700} size="xl" c="orange">{summary.inProgress}</Text>
            </Card>
          </SimpleGrid>
          
          {isLoading ? (
            <Center mt="xl"><Loader /></Center>
          ) : filteredAgenda.length === 0 ? (
            <Text c="dimmed">Agenda livre para este dia.</Text>
          ) : (
            <Stack gap="sm">
              {filteredAgenda.map(item => (
                <Card key={item.id} withBorder shadow="sm" radius="md">
                  <Group justify="space-between" align="flex-start">
                    <div>
                      <Group gap="xs" mb={4}>
                        <Text fw={500}>{new Date(item.scheduled_at).toLocaleTimeString().slice(0, 5)}</Text>
                        <Badge color="gray" variant="light">{item.type}</Badge>
                        <Badge color={STATUS_META[item.status]?.color ?? 'gray'} variant="dot">
                          {STATUS_META[item.status]?.label ?? item.status}
                        </Badge>
                      </Group>
                      <Text size="lg" fw={600}>{item.patient_name}</Text>
                      <Text size="sm" c="dimmed">
                        {item.encounter_id ? 'Atendimento já iniciado.' : 'Pronto para iniciar atendimento.'}
                      </Text>
                    </div>
                    <Button 
                      onClick={() => navigate(`/patients/${item.patient_id}/encounter`)}
                      variant={item.encounter_id ? "light" : "filled"}
                      color={item.status === 'cancelado' ? 'gray' : item.encounter_id ? "orange" : "blue"}
                      disabled={item.status === 'cancelado'}
                    >
                      {item.status === 'cancelado' ? 'Cancelado' : item.encounter_id ? "Retomar" : "Atender"}
                    </Button>
                  </Group>
                </Card>
              ))}
            </Stack>
          )}
        </Grid.Col>
      </Grid>
    </Box>
  );
}
