import { useState, useEffect } from 'react';
import { Button, TextInput, Stack, Paper, Title, ActionIcon, Group, Text, Card, Badge, Box } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconTrash } from '@tabler/icons-react';
import apiClient from '../api/client';
import { CID10Result } from './OswaldoCID10Search';

interface PrescriptionItem {
  drug: string;
  posology: string;
  duration?: string;
  notes?: string;
}

export interface Prescription {
  id: number;
  author_name: string;
  cid10_code: string | null;
  cid10_desc: string | null;
  items: PrescriptionItem[];
  status: string;
  created_at: string;
}

interface OswaldoPrescriptionEditorProps {
  encounterId: string | number;
  patientId: string | number;
  cid10: CID10Result | null;
}

export function OswaldoPrescriptionEditor({ encounterId, patientId, cid10 }: OswaldoPrescriptionEditorProps) {
  const [items, setItems] = useState<PrescriptionItem[]>([]);
  const [drug, setDrug] = useState('');
  const [posology, setPosology] = useState('');
  const [duration, setDuration] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [history, setHistory] = useState<Prescription[]>([]);

  const fetchHistory = async () => {
    try {
      const { data } = await apiClient.get(`/oswaldo/prescriptions/encounter/${encounterId}`);
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (encounterId) fetchHistory();
  }, [encounterId]);

  const handleAddItem = () => {
    if (!drug.trim() || !posology.trim()) {
      notifications.show({ title: 'Atenção', message: 'Preencha medicamento e posologia', color: 'yellow' });
      return;
    }
    setItems([...items, { drug, posology, duration }]);
    setDrug(''); setPosology(''); setDuration('');
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (items.length === 0) {
      notifications.show({ title: 'Atenção', message: 'Adicione pelo menos um item', color: 'yellow' });
      return;
    }
    setLoading(true);
    try {
      const payload = {
        encounter_id: Number(encounterId),
        patient_id: Number(patientId),
        cid10_code: cid10?.code,
        cid10_desc: cid10?.description,
        items
      };
      await apiClient.post('/oswaldo/prescriptions', payload);
      notifications.show({ title: 'Sucesso', message: 'Prescrição salva!', color: 'green' });
      setItems([]);
      fetchHistory();
    } catch (err) {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar a prescrição', color: 'red' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack gap="md">
      <Paper withBorder p="md" radius="md">
        <Title order={5} mb="md">Nova Prescrição</Title>
        <Stack gap="xs" mb="md">
          {items.map((it, idx) => (
            <Group key={idx} justify="space-between" align="center" style={{ borderBottom: '1px solid #eee', paddingBottom: 4 }}>
              <Box>
                <Text fw={500}>{it.drug}</Text>
                <Text size="sm" c="dimmed">{it.posology} {it.duration ? `— ${it.duration}` : ''}</Text>
              </Box>
              <ActionIcon color="red" variant="subtle" onClick={() => handleRemoveItem(idx)}>
                <IconTrash size={16} />
              </ActionIcon>
            </Group>
          ))}
          {items.length === 0 && <Text c="dimmed" size="sm" ta="center">Nenhum item adicionado.</Text>}
        </Stack>

        <Group align="flex-end" mb="md">
          <TextInput label="Medicamento" placeholder="Ex: Dipirona 500mg" value={drug} onChange={e => setDrug(e.currentTarget.value)} style={{ flex: 2 }} />
          <TextInput label="Posologia" placeholder="Ex: 1 comp 6/6h" value={posology} onChange={e => setPosology(e.currentTarget.value)} style={{ flex: 2 }} />
          <TextInput label="Duração" placeholder="Ex: 5 dias" value={duration} onChange={e => setDuration(e.currentTarget.value)} style={{ flex: 1 }} />
          <Button variant="light" onClick={handleAddItem}>+ Adicionar</Button>
        </Group>

        <Button onClick={handleSave} loading={loading} disabled={items.length === 0}>
          Salvar Prescrição
        </Button>
      </Paper>

      <Title order={5} mt="sm">Histórico de Prescrições</Title>
      {history.length === 0 && <Text c="dimmed" fs="italic" size="sm">Nenhuma prescrição registrada neste encontro.</Text>}
      {history.map(rx => (
        <Card key={rx.id} withBorder shadow="sm" radius="md" padding="md">
           <Group justify="space-between" mb="xs">
            <Group gap="xs">
              <Text fw={500}>{rx.author_name}</Text>
              <Text size="xs" c="dimmed">
                {new Date(rx.created_at).toLocaleString('pt-BR')}
              </Text>
            </Group>
            <Badge color={rx.status === 'SIGNED' ? 'green' : 'gray'} variant="light">
              {rx.status}
            </Badge>
          </Group>
          {rx.cid10_code && <Text size="sm" fw={500} c="blue" mb="xs">CID: {rx.cid10_code} - {rx.cid10_desc}</Text>}
          <Stack gap="xs">
            {rx.items.map((it, idx) => (
               <Group key={idx} justify="space-between" align="center" style={{ borderBottom: '1px dotted #ccc' }}>
                 <Text size="sm" fw={500}>• {it.drug}</Text>
                 <Text size="xs" c="dimmed">{it.posology} {it.duration ? `(${it.duration})` : ''}</Text>
               </Group>
            ))}
          </Stack>
        </Card>
      ))}
    </Stack>
  );
}
