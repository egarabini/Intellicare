import { useState } from 'react';
import { Container, Title, SimpleGrid, Paper, Text, Group, Select, Stack, Loader, Center } from '@mantine/core';
import { IconStethoscope, IconPrescription, IconNotes, IconAlertTriangle, IconCheck, IconRoute } from '@tabler/icons-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useClinicalKPIs } from '../hooks/useClinicalKPIs';
import { useClinicians } from '../hooks/useGestor';
import dayjs from 'dayjs';

export function IndicadoresPage() {
  const [periodDays, setPeriodDays] = useState('30');
  const [professionalId, setProfessionalId] = useState<string | null>(null);

  const start = dayjs().subtract(parseInt(periodDays), 'day').format('YYYY-MM-DD');
  const end = dayjs().format('YYYY-MM-DD');

  const { data, isLoading, error } = useClinicalKPIs(start, end, professionalId || undefined);
  const { data: clinicians } = useClinicians();

  const clinicianOptions = [
    { value: '', label: 'Todos os Médicos' },
    ...((clinicians ?? [])
      .map((c) => {
        const value = c?.id ?? c?.keycloak_id ?? c?.user_id;
        const label = c?.name ?? c?.full_name ?? c?.email ?? c?.username;
        if (!value || !label) return null;
        return { value: String(value), label: String(label) };
      })
      .filter((option): option is { value: string; label: string } => option !== null))
  ];

  const topProfessionals = Array.isArray(data?.top_professionals)
    ? data.top_professionals
        .map((item) => ({
          name: item?.name || 'Profissional',
          total: Number(item?.total ?? 0),
        }))
    : [];

  const interactionsByDay = Array.isArray(data?.interactions_by_day)
    ? data.interactions_by_day
        .map((item) => ({
          day: item?.day || '',
          total: Number(item?.total ?? 0),
        }))
        .filter((item) => item.day)
    : [];

  function StatCard({ title, value, icon: Icon, color }: any) {
    return (
      <Paper withBorder p="md" radius="md">
        <Group justify="space-between">
          <Text size="xs" c="dimmed" fw={700} tt="uppercase">
            {title}
          </Text>
          <Icon size="1.4rem" stroke={1.5} color={color} />
        </Group>
        <Group align="flex-end" gap="xs" mt={25}>
          <Text size="xl" fw={700}>
            {value}
          </Text>
        </Group>
      </Paper>
    );
  }

  return (
    <Container size="xl">
      <Stack gap="lg">
        <Group justify="space-between" align="center">
          <Title order={2}>Indicadores Clínicos</Title>
          <Group>
            <Select
              label="Período"
              value={periodDays}
              onChange={(v) => setPeriodDays(v || '30')}
              data={[
                { value: '7', label: 'Últimos 7 dias' },
                { value: '30', label: 'Últimos 30 dias' },
                { value: '90', label: 'Últimos 90 dias' },
              ]}
              w={200}
            />
            <Select
              label="Médico"
              value={professionalId || ''}
              onChange={(v) => setProfessionalId(v === '' ? null : v)}
              data={clinicianOptions}
              w={250}
              searchable
            />
          </Group>
        </Group>

        {isLoading && <Center mt="xl"><Loader /></Center>}
        {error && <Text c="red">Erro ao carregar KPIs: {(error as Error).message}</Text>}

        {data && (
          <>
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
              <StatCard
                title="Consultas Fechadas"
                value={data.encounters}
                icon={IconStethoscope}
                color="blue"
              />
              <StatCard
                title="Prescrições Emitidas"
                value={data.prescriptions}
                icon={IconPrescription}
                color="teal"
              />
              <StatCard
                title="Notas Florence"
                value={data.notes}
                icon={IconNotes}
                color="grape"
              />
              <StatCard
                title="Interações Detectadas"
                value={data.interactions_detected}
                icon={IconAlertTriangle}
                color="orange"
              />
              <StatCard
                title="Sugestões IA Aceitas"
                value="N/A"
                icon={IconCheck}
                color="gray"
              />
              <StatCard
                title="Jornadas CarePlanner"
                value={`${data.journeys?.active || 0} A / ${data.journeys?.completed || 0} F / ${data.journeys?.expired || 0} E`}
                icon={IconRoute}
                color="indigo"
              />
            </SimpleGrid>

            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" mt="md">
              <Paper withBorder p="md" radius="md">
                <Title order={4} mb="md">Top Médicos (Prescrições)</Title>
                {topProfessionals.length === 0 ? (
                  <Text c="dimmed">Sem dados de prescrições no período.</Text>
                ) : (
                  <div style={{ height: 300, minWidth: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={topProfessionals} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                        <RechartsTooltip />
                        <Bar dataKey="total" fill="#228be6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </Paper>

              <Paper withBorder p="md" radius="md">
                <Title order={4} mb="md">Interações por Dia</Title>
                {interactionsByDay.length === 0 ? (
                  <Text c="dimmed">Sem interações registradas no período.</Text>
                ) : (
                  <div style={{ height: 300, minWidth: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={interactionsByDay} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="day" tickFormatter={(val: any) => dayjs(val).format('DD/MM')} />
                        <YAxis />
                        <RechartsTooltip labelFormatter={(val: any) => dayjs(val).format('DD/MM/YYYY')} />
                        <Line type="monotone" dataKey="total" stroke="#fd7e14" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </Paper>
            </SimpleGrid>
          </>
        )}
      </Stack>
    </Container>
  );
}
