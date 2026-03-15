import { Title, Box, Container, Text, Card, Group } from '@mantine/core';
import { IconRobot } from '@tabler/icons-react';
import { SLMAssistant } from '../components/SLMAssistant';

export function AIAssistant() {
  return (
    <Container size="md">
      <Group mb="lg">
        <IconRobot size={32} color="blue" />
        <div>
          <Title order={2}>Assistente Clínico IA</Title>
          <Text c="dimmed">Converse com a base de conhecimento clínico.</Text>
        </div>
      </Group>

      <Card withBorder shadow="sm" radius="md" p="md">
        <SLMAssistant />
      </Card>
    </Container>
  );
}
