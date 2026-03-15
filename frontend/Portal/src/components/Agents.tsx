import { Badge, Card, Container, Image, SimpleGrid, Stack, Text, Title } from '@mantine/core';

const AGENTS = [
  {
    name: 'Florence',
    role: 'Protocolos Clinicos',
    description: 'Curadoria de conhecimento clinico, fluxos assistenciais e apoio a decisoes baseadas em evidencia.',
    color: 'teal',
    image: '/agents/agente_florence_ia.png',
  },
  {
    name: 'Oswaldo',
    role: 'Interoperabilidade e FHIR',
    description: 'Leitura, estruturacao e intercambio de dados clinicos com padroes de interoperabilidade em saude.',
    color: 'blue',
    image: '/agents/agente_oswaldo_ia.png',
  },
  {
    name: 'Grahame',
    role: 'Documentos e OCR',
    description: 'Captura de conteudo documental, extracao estruturada e preparo de insumos para automacao e RAG.',
    color: 'cyan',
    image: '/agents/agente_grahame_ai.png',
  },
  {
    name: 'Pierre',
    role: 'Operacao e Faturamento',
    description: 'Apoio a rotinas operacionais, indicadores financeiros e governanca de execucao da plataforma.',
    color: 'orange',
    image: '/agents/agente_pierre_ia.png',
  },
  {
    name: 'Minerva',
    role: 'Analise e Inteligencia',
    description: 'Sintese de sinais, leitura de contexto e suporte analitico para gestao e acompanhamento clinico.',
    color: 'grape',
    image: '/agents/agente_minerva_ia.png',
  },
  {
    name: 'Nise',
    role: 'Cuidado Humanizado',
    description: 'Visao ampliada do cuidado, comunicacao empatica e apoio a jornadas centradas na pessoa.',
    color: 'pink',
    image: '/agents/agente_nise_ia.png',
  },
  {
    name: 'Wanda',
    role: 'Enfermagem e Jornada',
    description: 'Organizacao de rotinas assistenciais, continuidade do cuidado e suporte a equipes multiprofissionais.',
    color: 'violet',
    image: '/agents/agente_wanda_ia.png',
  },
  {
    name: 'Zilda Arns',
    role: 'Prevencao e Territorio',
    description: 'Acompanhamento de populacoes, foco em prevencao e cuidado longitudinal com alcance comunitario.',
    color: 'lime',
    image: '/agents/agente_zilda_arns_ia.png',
  },
  {
    name: 'Donabedian',
    role: 'Qualidade Assistencial',
    description: 'Leitura de estrutura, processo e resultado para elevar seguranca, qualidade e maturidade operacional.',
    color: 'indigo',
    image: '/agents/agente_donabedian_ia.png',
  },
  {
    name: 'Hipocrates',
    role: 'Raciocinio Clinico',
    description: 'Apoio ao julgamento clinico, organizacao de hipoteses e reforco da tomada de decisao segura.',
    color: 'red',
    image: '/agents/agente_hipocrates_ia.png',
  },
  {
    name: 'Geralda',
    role: 'APS e Coordenacao',
    description: 'Suporte a atencao primaria, estratificacao de demanda e articulacao entre linhas de cuidado.',
    color: 'green',
    image: '/agents/agente_geralda_ia.png',
  },
];

export function Agents() {
  return (
    <Container size="lg" py={80}>
      <Stack align="center" gap="xs" mb="xl">
        <Title order={2} ta="center">Ecossistema de Agentes IntelliCare</Title>
        <Text c="dimmed" ta="center" maw={760}>
          O Portal agora usa as ilustracoes oficiais dos agentes da plataforma. Cada personagem representa uma frente especializada do ecossistema IntelliCare.
        </Text>
      </Stack>

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="xl">
        {AGENTS.map((agent) => (
          <Card key={agent.name} shadow="sm" padding="lg" radius="lg" withBorder>
            <Card.Section
              style={{
                background: 'linear-gradient(180deg, rgba(15,118,110,0.08) 0%, rgba(30,58,95,0.02) 100%)',
              }}
            >
              <Image
                src={agent.image}
                height={240}
                fit="contain"
                alt={agent.name}
                p="md"
              />
            </Card.Section>

            <Stack mt="md" gap="xs">
              <Badge color={agent.color} variant="light" w="fit-content">
                {agent.role}
              </Badge>
              <Title order={3}>{agent.name}</Title>
              <Text size="sm" c="dimmed">
                {agent.description}
              </Text>
            </Stack>
          </Card>
        ))}
      </SimpleGrid>
    </Container>
  );
}
