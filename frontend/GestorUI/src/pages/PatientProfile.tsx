import { useParams, useNavigate } from 'react-router-dom';
import { Box, Title, Group, Text, Card, Button, Stack, Loader, Center } from '@mantine/core';
import { usePatient } from '../hooks/useGestor';
import { IconArrowLeft } from '@tabler/icons-react';

export function PatientProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: patient, isLoading } = usePatient(id || '');

  if (isLoading) return <Center h="200"><Loader /></Center>;
  if (!patient) return <Text color="red">Paciente não encontrado.</Text>;

  return (
    <Box>
      <Group mb="lg">
        <Button variant="subtle" onClick={() => navigate(-1)} leftSection={<IconArrowLeft size={16} />}>
          Voltar
        </Button>
        <Title order={2}>Perfil do Paciente</Title>
      </Group>

      <Card withBorder padding="lg" radius="md">
        <Stack gap="sm">
          <Group justify="space-between">
            <Title order={3}>{patient.name}</Title>
            <Text fw={700} c={patient.active ? 'green' : 'red'}>{patient.active ? 'Ativo' : 'Inativo'}</Text>
          </Group>
          <Text><b>CPF:</b> {patient.cpf}</Text>
          <Text><b>Data Nascimento:</b> {patient.birth_date}</Text>
          <Text><b>E-mail:</b> {patient.email || 'Não informado'}</Text>
          <Text><b>Telefone:</b> {patient.phone || 'Não informado'}</Text>
          <Text><b>Plano de Saúde:</b> {patient.health_plan || 'Particular'}</Text>
        </Stack>
      </Card>

      <Title order={3} mt="xl" mb="md">Histórico (Em Breve)</Title>
      <Card withBorder>
        <Text c="dimmed">Esta seção exibirá consultas, programas de saúde e prontuários vinculados a este paciente.</Text>
      </Card>
    </Box>
  );
}
