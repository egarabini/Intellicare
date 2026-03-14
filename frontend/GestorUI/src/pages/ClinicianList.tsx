import { useState } from 'react';
import { Box, Title, Group, Table, ActionIcon, Button, Modal, Stack, TextInput, Select, Badge } from '@mantine/core';
import { useClinicians, useInviteClinician, useDeactivateClinician } from '../hooks/useGestor';
import { IconUserPlus, IconTrash } from '@tabler/icons-react';

export function ClinicianList() {
  const { data: clinicians, isLoading } = useClinicians();
  const inviteUser = useInviteClinician();
  const deactivateUser = useDeactivateClinician();

  const [opened, setOpened] = useState(false);
  const [form, setForm] = useState({ name: '', email: '' });

  const handleInvite = async () => {
    try {
      await inviteUser.mutateAsync(form);
      setOpened(false);
      setForm({ name: '', email: '' });
    } catch (e: any) {
      alert("Erro ao convidar: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Equipe Clínica</Title>
        <Button onClick={() => setOpened(true)} leftSection={<IconUserPlus size={16}/>}>Convidar Clínico</Button>
      </Group>

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Email</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr><Table.Td colSpan={4}>Carregando...</Table.Td></Table.Tr>
          ) : clinicians?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={4}>Nenhum clínico cadastrado nesta unidade.</Table.Td></Table.Tr>
          ) : (
            clinicians?.map(c => (
              <Table.Tr key={c.id}>
                <Table.Td>{c.firstName} {c.lastName}</Table.Td>
                <Table.Td>{c.email}</Table.Td>
                <Table.Td><Badge color={c.enabled ? 'green' : 'red'}>{c.enabled ? 'Ativo' : 'Inativo'}</Badge></Table.Td>
                <Table.Td>
                  {c.enabled && (
                    <ActionIcon onClick={() => deactivateUser.mutate(c.id)} color="red" variant="subtle">
                      <IconTrash size={16} />
                    </ActionIcon>
                  )}
                </Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Convidar Clínico">
        <Stack gap="sm">
          <TextInput label="Nome" required value={form.name} onChange={e => setForm({...form, name: e.currentTarget.value})} />
          <TextInput label="Email Institucional" type="email" required value={form.email} onChange={e => setForm({...form, email: e.currentTarget.value})} />
          <Button fullWidth onClick={handleInvite} loading={inviteUser.isPending}>Enviar Convite</Button>
        </Stack>
      </Modal>
    </Box>
  );
}
