import { Container, Title, Text, SimpleGrid, Card, Image, Badge, Group, Stack } from '@mantine/core';

const AGENTS = [
  {
    name: 'Florence',
    role: 'Protocolos Clínicos',
    description: 'Pipeline RAG completo — ingestão de documentos, busca semântica via pgvector e gestão da base de conhecimento clínico por tenant.',
    color: 'teal',
    image: '/florence.svg',
  },
  {
    name: 'Oswaldo',
    role: 'Análise Clínica + FHIR',
    description: 'Análise clínica com interoperabilidade HL7 FHIR R4. Exportação de dados padronizada para integração com sistemas de saúde.',
    color: 'blue',
    image: '/oswaldo.svg',
  },
  {
    name: 'Cuidado',
    role: 'Assistente IA Clínico',
    description: 'Atendimento ao paciente com IA local — SLM via OLLAMA, respostas em PT-BR, citação de fontes, streaming em tempo real.',
    color: 'violet',
    image: '/cuidado.svg',
  },
  {
    name: 'Gestor',
    role: 'Gestão da Unidade',
    description: 'Indicadores, equipes, programas de saúde e relatórios de uso. Visão completa da unidade sem planilhas manuais.',
    color: 'orange',
    image: '/gestor.svg',
  },
];

export function Agents() {
  return (
    <Container size="lg" py={80}>
      <Stack align="center" gap="xs" mb="xl">
        <Title order={2} ta="center">Nossos Agentes Inteligentes</Title>
        <Text c="dimmed" ta="center" maw={600}>
          Cada agente é um especialista em sua área, trabalhando em conjunto para oferecer a solução de saúde mais completa e integrada do mercado.
        </Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="xl">
        {AGENTS.map((agent) => (
          <Card key={agent.name} shadow="sm" padding="lg" radius="md" withBorder>
            <Card.Section>
              <Image
                src={agent.image}
                height={160}
                alt={agent.name}
              />
            </Card.Section>

            <Stack mt="md" mb="xs">
              <Title order={3}>{agent.name}</Title>
              <Badge color={agent.color} variant="light">
                {agent.role}
              </Badge>
            </Stack>

            <Text size="sm" c="dimmed">
              {agent.description}
            </Text>
          </Card>
        ))}
      </SimpleGrid>
    </Container>
  );
}
