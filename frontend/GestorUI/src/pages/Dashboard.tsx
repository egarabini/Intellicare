import { Box, SimpleGrid, Card, Group, Text, Title, Stack, ThemeIcon, Loader, Center } from '@mantine/core';
import { IconUsers, IconCalendar, IconFileInvoice, IconDatabase, IconActivity } from '@tabler/icons-react';
import { useDashboardStats } from '../hooks/useGestor';

export function Dashboard() {
  const { data, isLoading, error } = useDashboardStats();

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (error) return <Text color="red">Erro ao carregar dashboard.</Text>;
  if (!data) return null;

  const stats = [
    { title: 'Pacientes Ativos', value: data.patients_active, icon: IconUsers, color: 'blue' },
    { title: 'Consultas Hoje', value: data.appointments_today, icon: IconCalendar, color: 'green' },
    { title: 'Consultas na Semana', value: data.appointments_week, icon: IconCalendar, color: 'teal' },
    { title: 'Consultas no Mês', value: data.appointments_month, icon: IconCalendar, color: 'cyan' },
    { title: 'Faturas (R$)', value: `R$ ${data.invoices_pending_total.toFixed(2)}`, icon: IconFileInvoice, color: 'orange' },
    { title: 'Documentos RAG', value: data.rag_documents_count, icon: IconDatabase, color: 'grape' },
  ];

  return (
    <Box>
      <Title order={2} mb="md">Visão Geral do Tenant</Title>
      
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md" mb="xl">
        {stats.map((stat, i) => (
          <Card key={i} withBorder padding="md" radius="md">
            <Group justify="space-between">
              <div>
                <Text c="dimmed" tt="uppercase" fw={700} fz="xs">
                  {stat.title}
                </Text>
                <Text fw={700} fz="xl">
                  {stat.value}
                </Text>
              </div>
              <ThemeIcon color={stat.color} variant="light" size={38} radius="md">
                <stat.icon size={20} />
              </ThemeIcon>
            </Group>
          </Card>
        ))}
      </SimpleGrid>

      <Title order={3} mb="md">Atividades Recentes</Title>
      <Card withBorder>
        {data.recent_activity.length === 0 ? (
          <Text c="dimmed">Nenhuma atividade recente.</Text>
        ) : (
          <Stack gap="sm">
            {data.recent_activity.map((act, i) => (
              <Group key={i} wrap="nowrap">
                <ThemeIcon variant="light" radius="xl" color="blue"><IconActivity size={16}/></ThemeIcon>
                <div>
                  <Text size="sm" fw={500}>{act.action}</Text>
                  <Text size="xs" c="dimmed">{act.timestamp}</Text>
                </div>
              </Group>
            ))}
          </Stack>
        )}
      </Card>
    </Box>
  );
}
