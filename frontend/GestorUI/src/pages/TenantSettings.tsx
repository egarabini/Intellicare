import { useEffect } from 'react';
import { Box, Title, Group, Button, Stack, TextInput, Text, Center, Loader, Select } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import { IconDeviceFloppy } from '@tabler/icons-react';

export function TenantSettings() {
  const qc = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data } = await api.get('/gestor/profile');
      return data;
    }
  });

  const saveProfile = useMutation({
    mutationFn: async (payload: any) => {
      await api.put('/gestor/profile', payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] });
      alert("Configurações salvas.");
    }
  });

  const form = useForm({
    initialValues: { name: '', email: '', phone: '', address: '', city: '', state: '', unit_type: 'clinic' },
  });

  useEffect(() => {
    if (profile) form.setValues(profile);
  }, [profile]);

  if (isLoading) return <Center h="100%"><Loader /></Center>;

  return (
    <Box maw={600}>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Configurações da Unidade</Title>
      </Group>

      <form onSubmit={form.onSubmit((v: any) => saveProfile.mutate(v))}>
        <Stack gap="sm">
          <TextInput label="Nome da Unidade" required {...form.getInputProps('name')} />
          <TextInput label="E-mail" {...form.getInputProps('email')} />
          <TextInput label="Telefone" {...form.getInputProps('phone')} />
          <TextInput label="Endereço" {...form.getInputProps('address')} />
          <Group grow>
            <TextInput label="Cidade" {...form.getInputProps('city')} />
            <TextInput label="UF" {...form.getInputProps('state')} />
          </Group>
          <Select 
            label="Tipo de Unidade" 
            data={[
              { value: 'ubs', label: 'UBS' },
              { value: 'clinic', label: 'Clínica' },
              { value: 'hospital', label: 'Hospital' },
              { value: 'specialty', label: 'Especializada' }
            ]}
            {...form.getInputProps('unit_type')} 
          />
          <Button type="submit" mt="md" loading={saveProfile.isPending} leftSection={<IconDeviceFloppy size={16}/>}>
            Salvar Configurações
          </Button>
        </Stack>
      </form>
      
      <Box mt="xl" pt="xl" style={{ borderTop: '1px solid #eee' }}>
         <Title order={4} c="red" mb="sm">Zona de Perigo</Title>
         <Text size="sm" mb="md">Ações destrutivas sobre a conta do tenant não podem ser desfeitas.</Text>
         <Button color="red" variant="outline" onClick={() => alert('Contate o suporte para excluir a conta')}>Solicitar Exclusão da Conta</Button>
      </Box>
    </Box>
  );
}
