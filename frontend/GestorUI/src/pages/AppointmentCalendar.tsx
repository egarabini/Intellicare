import { useState } from 'react';
import { Box, Title, Group, Table, ActionIcon, Button, Modal, Stack, Select, Text, TextInput, Badge } from '@mantine/core';
import { useAppointments, useCreateAppointment, useCancelAppointment, usePatients, useClinicians } from '../hooks/useGestor';
import { IconTrash, IconCalendarPlus } from '@tabler/icons-react';

export function AppointmentCalendar() {
  const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [clinicianId, setClinicianId] = useState<string | null>(null);
  const [opened, setOpened] = useState(false);

  const { data: appointments, isLoading } = useAppointments(date, clinicianId || undefined);
  const { data: patients } = usePatients(1, 100);
  const { data: clinicians } = useClinicians();
  
  const createAppointment = useCreateAppointment();
  const cancelAppointment = useCancelAppointment();

  const [form, setForm] = useState<{ patient_id: string; clinician_id: string; scheduled_at: string; type: 'consulta' | 'retorno' | 'exame'; notes: string }>({ patient_id: '', clinician_id: '', scheduled_at: '', type: 'consulta', notes: '' });

  const onSubmit = async () => {
    try {
      await createAppointment.mutateAsync(form);
      setOpened(false);
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Erro ao criar agendamento');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'agendado': return 'blue';
      case 'confirmado': return 'green';
      case 'realizado': return 'gray';
      case 'cancelado': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Title order={2}>Agendamentos</Title>
        <Button onClick={() => setOpened(true)} leftSection={<IconCalendarPlus size={16}/>}>Novo Agendamento</Button>
      </Group>

      <Group mb="md">
        <TextInput type="date" label="Data" value={date} onChange={(e) => setDate(e.currentTarget.value)} />
        <Select 
          label="Clínico (Filtro)" 
          placeholder="Todos"
          value={clinicianId} 
          onChange={setClinicianId}
          data={clinicians?.map(c => ({ value: c.id, label: c.firstName + ' ' + c.lastName })) || []}
          clearable
        />
      </Group>

      <Table highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Data/Hora</Table.Th>
            <Table.Th>Paciente</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {isLoading ? (
            <Table.Tr><Table.Td colSpan={5}>Carregando...</Table.Td></Table.Tr>
          ) : appointments?.length === 0 ? (
            <Table.Tr><Table.Td colSpan={5}>Nenhum agendamento para esta data.</Table.Td></Table.Tr>
          ) : (
            appointments?.map(a => {
              const p = patients?.find(pat => pat.id === a.patient_id);
              return (
                <Table.Tr key={a.id}>
                  <Table.Td>{new Date(a.scheduled_at).toLocaleString()}</Table.Td>
                  <Table.Td>{p?.name || a.patient_id}</Table.Td>
                  <Table.Td>{a.type}</Table.Td>
                  <Table.Td><Badge color={getStatusColor(a.status)}>{a.status}</Badge></Table.Td>
                  <Table.Td>
                    {a.status !== 'cancelado' && (
                      <ActionIcon color="red" variant="subtle" onClick={() => cancelAppointment.mutate(a.id)}>
                        <IconTrash size={16} />
                      </ActionIcon>
                    )}
                  </Table.Td>
                </Table.Tr>
              );
            })
          )}
        </Table.Tbody>
      </Table>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Novo Agendamento">
        <Stack gap="sm">
          <Select 
            label="Paciente" required 
            data={patients?.map(p => ({ value: p.id, label: p.name })) || []}
            onChange={v => setForm({...form, patient_id: v || ''})} 
          />
          <Select 
            label="Clínico" required 
            data={clinicians?.map(c => ({ value: c.id, label: c.email })) || []}
            onChange={v => setForm({...form, clinician_id: v || ''})} 
          />
          <TextInput 
            type="datetime-local" label="Data e Hora" required 
            onChange={e => setForm({...form, scheduled_at: new Date(e.currentTarget.value).toISOString()})} 
          />
          <Select 
            label="Tipo" required 
            data={['consulta', 'retorno', 'exame']} 
            value={form.type} onChange={v => setForm({...form, type: (v as any) || 'consulta'})}
          />
          <TextInput label="Notas" onChange={e => setForm({...form, notes: e.currentTarget.value})} />
          <Button fullWidth onClick={onSubmit} loading={createAppointment.isPending}>Agendar</Button>
        </Stack>
      </Modal>
    </Box>
  );
}
