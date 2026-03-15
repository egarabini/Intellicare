import { useState } from 'react';
import { Box, Title, Group, Badge, Card, Text, Button, Stack, Loader, Center, Grid, Select } from '@mantine/core';
import { DatePicker } from '@mantine/dates';
import { useNavigate } from 'react-router-dom';
import { useMyAgenda } from '../hooks/useMyAgenda';

import '@mantine/dates/styles.css';

export function Agenda() {
  const [date, setDate] = useState<Date | null>(new Date());
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  
  const dateStr = date ? date.toISOString().split('T')[0] : undefined;
  const { data: agenda, isLoading } = useMyAgenda(dateStr);
  const navigate = useNavigate();

  const filteredAgenda = agenda?.filter(a => !typeFilter || a.type === typeFilter);

  return (
    <Box>
      <Title order={2} mb="lg">Agenda Clínica</Title>

      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder shadow="sm" radius="md" p="md">
            <DatePicker 
              value={date} 
              onChange={(v: any) => setDate(v)} 
              size="md" 
              w="100%"
            />
          </Card>
          
          <Select
            mt="md"
            label="Filtrar por tipo"
            placeholder="Todos os tipos"
            value={typeFilter}
            onChange={setTypeFilter}
            data={[
              { value: 'consulta', label: 'Consulta' },
              { value: 'retorno', label: 'Retorno' },
              { value: 'exame', label: 'Exame' }
            ]}
            clearable
          />
        </Grid.Col>
        
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Title order={4} mb="md">
            Consultas em {date ? date.toLocaleDateString() : 'Nenhuma data'}
          </Title>
          
          {isLoading ? (
            <Center mt="xl"><Loader /></Center>
          ) : !filteredAgenda || filteredAgenda.length === 0 ? (
            <Text c="dimmed">Agenda livre para este dia.</Text>
          ) : (
            <Stack gap="sm">
              {filteredAgenda.map(item => (
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
        </Grid.Col>
      </Grid>
    </Box>
  );
}
