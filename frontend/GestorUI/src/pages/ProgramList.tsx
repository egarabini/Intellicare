import { useState } from 'react';
import { Box, Title, Group, Table, ActionIcon, Button, Modal, Stack, TextInput, Badge } from '@mantine/core';
import { usePrograms } from '../hooks/useGestor';
import { IconHeartRateMonitor, IconEye } from '@tabler/icons-react';

export function ProgramList() {
  const { data: programs, isLoading } = usePrograms();
  const [opened, setOpened] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', eligibility_criteria: '' });

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Programas de Saúde</Title>
        <Button onClick={() => setOpened(true)} leftSection={<IconHeartRateMonitor size={16}/>}>Novo Programa</Button>
      </Group>

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Descrição</Table.Th>
            <Table.Th>Critérios</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr><Table.Td colSpan={5}>Carregando...</Table.Td></Table.Tr>
          ) : programs?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={5}>Nenhum programa cadastrado.</Table.Td></Table.Tr>
          ) : (
            programs?.map(p => (
              <Table.Tr key={p.id}>
                <Table.Td fw={500}>{p.name}</Table.Td>
                <Table.Td>{p.description || '-'}</Table.Td>
                <Table.Td>{p.eligibility_criteria || '-'}</Table.Td>
                <Table.Td><Badge color={p.active ? 'green' : 'gray'}>{p.active ? 'Ativo' : 'Inativo'}</Badge></Table.Td>
                <Table.Td>
                  <ActionIcon variant="light" color="blue"><IconEye size={16}/></ActionIcon>
                </Table.Td>
              </Table.Tr>
            ))
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Novo Programa">
        <Stack gap="sm">
          <TextInput label="Nome do Programa" required value={form.name} onChange={e => setForm({...form, name: e.currentTarget.value})} />
          <TextInput label="Descrição" value={form.description} onChange={e => setForm({...form, description: e.currentTarget.value})} />
          <TextInput label="Critérios de Elegibilidade" value={form.eligibility_criteria} onChange={e => setForm({...form, eligibility_criteria: e.currentTarget.value})} />
          <Button fullWidth onClick={() => alert('Em breve!')}>Salvar</Button>
        </Stack>
      </Modal>
    </Box>
  );
}
