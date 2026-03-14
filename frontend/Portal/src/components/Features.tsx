import { Container, Title, Text, SimpleGrid, Card, ThemeIcon, Stack } from '@mantine/core';
import { IconLock, IconRobot, IconHeart, IconBuilding } from '@tabler/icons-react';

const FEATURES = [
  {
    icon: IconLock,
    title: 'Segurança e Privacidade',
    description: 'LGPD by design com multi-tenancy nativo, garantindo que os dados do paciente estejam sempre seguros e isolados.',
  },
  {
    icon: IconRobot,
    title: 'Inteligência Artificial Local',
    description: 'Modelos de linguagem (SLMs) e RAG rodam localmente, garantindo que os dados sensíveis nunca saiam da sua instituição.',
  },
  {
    icon: IconHeart,
    title: 'Interoperabilidade Padrão Ouro',
    description: 'Comunicação via HL7 FHIR R4, o padrão global para troca de informações de saúde. Integração perfeita com seus sistemas existentes.',
  },
  {
    icon: IconBuilding,
    title: 'Arquitetura Modular e Escalável',
    description: 'De uma complexa teia de microserviços para um único container inteligente. Reduza custos e complexidade de TI.',
  },
];

export function Features() {
  return (
    <Container size="lg" py={80}>
      <Stack align="center" gap="xs" mb="xl">
        <Title order={2} ta="center">Por que IntelliCare é a Escolha Certa?</Title>
        <Text c="dimmed" ta="center" maw={600}>
          Nossa plataforma foi construída sobre pilares sólidos que garantem a eficiência, segurança e inovação que a sua instituição de saúde merece.
        </Text>
      </Stack>
      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xl">
        {FEATURES.map((feature) => (
          <Card key={feature.title} shadow="sm" padding="lg" radius="md" withBorder>
            <ThemeIcon size={48} radius="md" variant="gradient" gradient={{ from: 'teal', to: 'blue', deg: 60 }}>
              <feature.icon size={24} />
            </ThemeIcon>
            <Title order={3} mt="md">{feature.title}</Title>
            <Text mt="sm" c="dimmed">{feature.description}</Text>
          </Card>
        ))}
      </SimpleGrid>
    </Container>
  );
}
