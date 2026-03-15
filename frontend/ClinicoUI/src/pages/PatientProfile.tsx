import { useState } from 'react';
import { Title, Tabs, Box, Group, Text, Card, Stack, Badge, Button, Loader, Center, TextInput, Textarea, Avatar, Timeline, Grid } from '@mantine/core';
import { useParams, useNavigate } from 'react-router-dom';
import { usePatientProfile, usePatientHistory, useUpdatePatientClinical } from '../hooks/usePatients';
import { IconUser, IconHistory, IconHeartRateMonitor, IconStethoscope, IconEdit, IconCheck } from '@tabler/icons-react';
import { useForm } from '@mantine/form';

export function PatientProfile() { 
  const { id } = useParams() as { id: string };
  const navigate = useNavigate();
  const { data: profile, isLoading } = usePatientProfile(id);
  const { data: history } = usePatientHistory(id);
  const updateClinical = useUpdatePatientClinical();
  
  const [editingClinical, setEditingClinical] = useState(false);
  
  const form = useForm({
    initialValues: {
      allergies: '',
      medications: ''
    }
  });

  if (isLoading) return <Center h="100%"><Loader /></Center>;
  if (!profile) return <Text c="red">Paciente não encontrado.</Text>;

  const age = new Date().getFullYear() - new Date(profile.birth_date).getFullYear();

  const handleEditClinical = () => {
    form.setValues({
      allergies: profile.allergies || '',
      medications: profile.medications || ''
    });
    setEditingClinical(true);
  };

  const handleSaveClinical = (values: typeof form.values) => {
    updateClinical.mutate({ id, data: values }, {
      onSuccess: () => setEditingClinical(false)
    });
  };

  return (
    <Box>
      <Group justify="space-between" mb="xl">
        <Group>
          <Avatar size="lg" color="blue" radius="xl">{profile.full_name[0]}</Avatar>
          <div>
            <Title order={2}>{profile.full_name}</Title>
            <Text c="dimmed">{age} anos • {profile.cpf} • {profile.phone || 'Sem telefone'}</Text>
          </div>
        </Group>
        <Button 
          leftSection={<IconStethoscope size={20} />} 
          size="md" 
          onClick={() => navigate(`/patients/${id}/encounter`)}
        >
          Novo Atendimento
        </Button>
      </Group>

      <Tabs defaultValue="perfil">
        <Tabs.List>
          <Tabs.Tab value="perfil" leftSection={<IconUser size={16} />}>Perfil Clínico</Tabs.Tab>
          <Tabs.Tab value="historico" leftSection={<IconHistory size={16} />}>Histórico ({profile.encounter_count})</Tabs.Tab>
          <Tabs.Tab value="programas" leftSection={<IconHeartRateMonitor size={16} />}>Programas</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="perfil" pt="xl">
          <Grid gutter="md">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder shadow="sm" radius="md">
                <Title order={4} mb="md">Dados Demográficos</Title>
                <Stack gap="sm">
                  <Group justify="space-between"><Text fw={500}>Nascimento:</Text><Text>{new Date(profile.birth_date).toLocaleDateString()}</Text></Group>
                  <Group justify="space-between"><Text fw={500}>Sexo:</Text><Text>{profile.sex === 'M' ? 'Masculino' : profile.sex === 'F' ? 'Feminino' : 'Outro'}</Text></Group>
                  <Group justify="space-between"><Text fw={500}>Email:</Text><Text>{profile.email || '—'}</Text></Group>
                  <Group justify="space-between"><Text fw={500}>Plano de Saúde:</Text><Text>{profile.health_plan || 'Particular/SUS'}</Text></Group>
                  <Group justify="space-between"><Text fw={500}>Status:</Text>
                    <Badge color={profile.active ? 'green' : 'red'}>{profile.active ? 'Ativo' : 'Inativo'}</Badge>
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
            
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card withBorder shadow="sm" radius="md">
                <Group justify="space-between" mb="md">
                  <Title order={4}>Informações Clínicas</Title>
                  {!editingClinical ? (
                    <Button variant="subtle" size="xs" onClick={handleEditClinical} leftSection={<IconEdit size={14}/>}>Editar</Button>
                  ) : (
                    <Button variant="light" size="xs" color="green" onClick={() => form.onSubmit(handleSaveClinical)()} loading={updateClinical.isPending} leftSection={<IconCheck size={14}/>}>Salvar</Button>
                  )}
                </Group>
                
                {editingClinical ? (
                  <form>
                    <Stack gap="md">
                      <Textarea label="Alergias Relevantes" {...form.getInputProps('allergies')} />
                      <Textarea label="Medicamentos em Uso" {...form.getInputProps('medications')} />
                    </Stack>
                  </form>
                ) : (
                  <Stack gap="md">
                    <Box>
                      <Text fw={500} size="sm" c="dimmed">Alergias Relevantes</Text>
                      <Text>{profile.allergies || 'Nenhuma alergia registrada.'}</Text>
                    </Box>
                    <Box>
                      <Text fw={500} size="sm" c="dimmed">Medicamentos em Uso</Text>
                      <Text>{profile.medications || 'Nenhum medicamento registrado.'}</Text>
                    </Box>
                  </Stack>
                )}
              </Card>
            </Grid.Col>
          </Grid>
        </Tabs.Panel>

        <Tabs.Panel value="historico" pt="xl">
          {!history || history.length === 0 ? (
            <Text c="dimmed">Nenhum atendimento registrado para este paciente.</Text>
          ) : (
            <Timeline active={0} bulletSize={24} lineWidth={2}>
              {history.map((enc) => (
                <Timeline.Item 
                  key={enc.id} 
                  title={`${enc.type ? enc.type.toUpperCase() : 'CONSULTA'} - ${new Date(enc.opened_at).toLocaleDateString()}`}
                  bullet={<IconStethoscope size={16} />}
                >
                  <Text c="dimmed" size="sm" mb={4}>
                    Motivo: {enc.chief_complaint || 'Não informado'}
                  </Text>
                  {enc.cid10_code && (
                    <Badge size="sm" color="cyan" mb={4}>CID: {enc.cid10_code}</Badge>
                  )}
                  <Text size="xs" mt={4}>
                    Status: {enc.status} | Aberto em: {new Date(enc.opened_at).toLocaleTimeString()}
                  </Text>
                </Timeline.Item>
              ))}
            </Timeline>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="programas" pt="xl">
          {!profile.programs || profile.programs.length === 0 ? (
            <Text c="dimmed">Paciente não inscrito em nenhum programa de saúde.</Text>
          ) : (
            <Stack gap="sm">
              {profile.programs.map((prog, i) => (
                <Card key={i} withBorder shadow="sm" radius="md">
                  <Text fw={500}>{prog}</Text>
                </Card>
              ))}
            </Stack>
          )}
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
}
