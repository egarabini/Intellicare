import { Container, Title, Text, Paper, SimpleGrid, ThemeIcon, Stack } from '@mantine/core';
import { IconShieldLock, IconBrain, IconUsers } from '@tabler/icons-react';

const VALUES = [
  {
    icon: IconShieldLock,
    title: 'Privacidade por Design',
    description: 'Nossa arquitetura multi-tenant e IA local garantem que os dados sensíveis nunca saiam do seu controle.',
  },
  {
    icon: IconBrain,
    title: 'IA Ética e Local',
    description: 'Implementamos modelos de IA que rodam na sua infraestrutura, garantindo soberania e segurança dos dados.',
  },
  {
    icon: IconUsers,
    title: 'Cuidado Centrado na Pessoa',
    description: 'A tecnologia é uma ferramenta para potencializar o cuidado humano, focando na jornada e bem-estar do paciente.',
  },
];

export function AboutUs() {
  return (
    <Container size="lg" py={80}>
      <Stack align="center" gap="xs" mb="xl">
        <Title order={2} ta="center">Nossa Missão, Nossos Valores</Title>
        <Text c="dimmed" ta="center" maw={600}>
          A IntelliCare nasceu da convicção de que a tecnologia pode e deve ser uma aliada do cuidado humano, não um substituto.
        </Text>
      </Stack>

      <Paper shadow="xs" p="xl" radius="md" withBorder>
        <Text size="lg" lh={1.7}>
          Nós acreditamos que a informação clínica certa, na hora certa, pode salvar vidas. Por isso, criamos uma plataforma que não apenas otimiza processos, mas que capacita profissionais de saúde a tomarem decisões mais rápidas e seguras. Nossa missão é democratizar o acesso à saúde de alta qualidade, uma instituição por vez.
        </Text>
      </Paper>

      <SimpleGrid cols={{ base: 1, md: 3 }} spacing="xl" mt={60}>
        {VALUES.map((value) => (
          <Stack key={value.title} align="center">
            <ThemeIcon size={64} radius="50%" variant="gradient" gradient={{ from: 'intelliTeal', to: 'intelliBlue', deg: 60 }}>
              <value.icon size={32} />
            </ThemeIcon>
            <Title order={4} mt="md" ta="center">{value.title}</Title>
            <Text ta="center" size="sm" c="dimmed">{value.description}</Text>
          </Stack>
        ))}
      </SimpleGrid>
    </Container>
  );
}
