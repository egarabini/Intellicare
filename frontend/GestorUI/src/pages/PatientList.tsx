import { useState } from 'react';
import { Box, Title, Group, Button, Table, ActionIcon, TextInput, Modal, Stack, Pagination } from '@mantine/core';
import { useForm } from '@mantine/form';
import { usePatients, useCreatePatient, useDeactivatePatient } from '../hooks/useGestor';
import { IconSearch, IconEye, IconTrash, IconUserPlus } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useDebouncedValue } from '@mantine/hooks';

export function PatientList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebouncedValue(search, 300);
  const [opened, setOpened] = useState(false);
  const navigate = useNavigate();

  const { data: patients, isLoading } = usePatients(page, 20, debouncedSearch);
  const createPatient = useCreatePatient();
  const deactivatePatient = useDeactivatePatient();

  const form = useForm({
    initialValues: { name: '', cpf: '', birth_date: '', email: '', phone: '', health_plan: '' },
    validate: {
      name: (val) => (val.length < 3 ? 'Nome muito curto' : null),
      cpf: (val) => (val.length !== 11 ? 'CPF deve ter 11 dígitos' : null),
    },
  });

  const onSubmit = async (vals: any) => {
    await createPatient.mutateAsync(vals);
    setOpened(false);
    form.reset();
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Lista de Pacientes</Title>
        <Button leftSection={<IconUserPlus size={16} />} onClick={() => setOpened(true)}>Novo Paciente</Button>
      </Group>

      <TextInput
        placeholder="Buscar por nome ou CPF..."
        leftSection={<IconSearch size={16} />}
        value={search}
        onChange={(e) => setSearch(e.currentTarget.value)}
        mb="md"
      />

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>CPF</Table.Th>
            <Table.Th>Data Nasc.</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr><Table.Td colSpan={5} align="center">Carregando...</Table.Td></Table.Tr>
          ) : patients?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={5} align="center">Nenhum paciente encontrado</Table.Td></Table.Tr>
          ) : (
            patients?.map((p) => (
              <Table.Tr key={p.id}>
                <Table.Td>{p.name}</Table.Td>
                <Table.Td>{p.cpf}</Table.Td>
                <Table.Td>{p.birth_date}</Table.Td>
                <Table.Td>{p.active ? 'Ativo' : 'Inativo'}</Table.Td>
                <Table.Td>
                  <Group gap={4}>
                    <ActionIcon onClick={() => navigate(`/patients/${p.id}`)} variant="light" color="blue"><IconEye size={16}/></ActionIcon>
                    {p.active && (
                      <ActionIcon onClick={() => deactivatePatient.mutate(p.id)} variant="light" color="red"><IconTrash size={16}/></ActionIcon>
                    )}
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>
      
      <Group justify="center" mt="md">
         <Pagination value={page} onChange={setPage} total={10} />
      </Group>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Novo Paciente" size="lg">
        <form onSubmit={form.onSubmit(onSubmit)}>
          <Stack gap="sm">
            <TextInput label="Nome" required {...form.getInputProps('name')} />
            <TextInput label="CPF (Apenas números)" required {...form.getInputProps('cpf')} />
            <TextInput label="Data de Nasc. (YYYY-MM-DD)" required {...form.getInputProps('birth_date')} />
            <TextInput label="E-mail" {...form.getInputProps('email')} />
            <TextInput label="Telefone" {...form.getInputProps('phone')} />
            <TextInput label="Plano de Saúde" {...form.getInputProps('health_plan')} />
            <Button type="submit" loading={createPatient.isPending} fullWidth mt="md">Cadastrar</Button>
          </Stack>
        </form>
      </Modal>
    </Box>
  );
}
