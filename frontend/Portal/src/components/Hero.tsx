import { Container, Title, Text, Button, Group, Stack, Badge, Box } from '@mantine/core';

export function Hero() {
  return (
    <Box style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #0f766e 100%)', color: 'white' }}>
      <Container size="lg" py={120}>
        <Stack align="center" gap="xl">
          <Badge size="xl" variant="filled" color="teal">
            IntelliCare v3
          </Badge>
          <Title order={1} ta="center" style={{ fontSize: '4rem', fontWeight: 900 }}>
            A Revolução da Saúde Inteligente
          </Title>
          <Text size="xl" ta="center" maw={700}>
            Nossa plataforma modular com IA de ponta transforma o cuidado ao paciente, otimiza a gestão e garante a interoperabilidade que sua instituição precisa.
          </Text>
          <Group mt="lg">
            <Button size="xl" component="a" href="/admin-ui/" color="teal">
              Explore a Plataforma
            </Button>
            <Button size="xl" variant="outline" component="a" href="/docs" color="white">
              Documentação para Desenvolvedores
            </Button>
          </Group>
        </Stack>
      </Container>
    </Box>
  );
}
