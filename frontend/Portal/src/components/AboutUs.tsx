import { Container, Title, Text, Paper, Group, Avatar, Stack } from '@mantine/core';

const TEAM = [
  {
    name: 'Dr. Elara Vance',
    role: 'CEO & Co-fundadora',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704d',
    description: 'Médica e entusiasta de tecnologia, apaixonada por revolucionar o atendimento ao paciente com o poder da IA.',
  },
  {
    name: 'Jaxon "Jax" Riley',
    role: 'CTO & Co-fundador',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704e',
    description: 'Arquiteto de software com mais de uma década de experiência na construção de sistemas de saúde escaláveis e seguros.',
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

      <Title order={3} ta="center" mt={60} mb="xl">Conheça os Fundadores</Title>
      <Group justify="center" gap="xl">
        {TEAM.map((member) => (
          <Stack key={member.name} align="center" maw={300}>
            <Avatar src={member.avatar} size={120} radius="50%" />
            <Title order={4} mt="md">{member.name}</Title>
            <Text c="teal" fw={700}>{member.role}</Text>
            <Text ta="center" size="sm" c="dimmed">{member.description}</Text>
          </Stack>
        ))}
      </Group>
    </Container>
  );
}
