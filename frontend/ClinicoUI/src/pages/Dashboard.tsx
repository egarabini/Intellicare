import { Box, Title, Group, Badge, Card, Text, Button, Stack, Loader, Center } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import { useMyAgenda } from '../hooks/useMyAgenda';
import { useTeamStats } from '../hooks/useClinicalUsers';

export function Dashboard() {
  const navigate = useNavigate();
  const today = new Date().toISOString().split('T')[0];
  const { data: agenda, isLoading } = useMyAgenda(today);
  const { data: teamStats } = useTeamStats();

  if (isLoading) return <Center h="100%"><Loader /></Center>;

  const pending = agenda?.filter(a => a.encounter_id != null && a.status !== 'realizado').length || 0;

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Minha Agenda — {new Date().toLocaleDateString()}</Title>
        <Group>
          <Badge color="blue" size="lg">{agenda?.length || 0} consultas hoje</Badge>
          {pending > 0 && <Badge color="red" size="lg">{pending} em andamento</Badge>}
        </Group>
      </Group>

      {teamStats && (
        <Card withBorder shadow="sm" radius="md" mb="lg">
          <Group>
            <div>
              <Text size="xs" c="dimmed">Equipe</Text>
              <Text fw={600}>{teamStats.professionals_active} profissionais ativos</Text>
              <Text size="sm" c="dimmed">{teamStats.groups_active} grupos</Text>
            </div>
          </Group>
        </Card>
      )}

      {agenda?.length === 0 ? (
        <Text c="dimmed">Nenhum agendamento para hoje.</Text>
      ) : (
        <Stack gap="sm">
          {agenda?.map(item => (
            <Card key={item.id} withBorder shadow="sm" radius="md">
              <Group justify="space-between">
                <div>
                  <Group gap="xs" mb={4}>
                    <Text fw={500}>{new Date(item.scheduled_at).toLocaleTimeString().slice(0, 5)}</Text>
                    <Badge color="gray" variant="light">{item.type}</Badge>
                    <Badge color={item.status === 'realizado' ? 'green' : 'blue'} variant="dot">{item.status}</Badge>
                  </Group>
                  <Text size="lg" fw={600}>{item.patient_name}</Text>
                </div>
                <Button 
                  onClick={() => navigate(`/patients/${item.patient_id}/encounter`)}
                  variant={item.encounter_id ? "light" : "filled"}
                  color={item.encounter_id ? "orange" : "blue"}
                >
                  {item.encounter_id ? "Retomar" : "Atender"}
                </Button>
              </Group>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  );
}
