import { useState } from 'react';
import { Container, Title, Text, Button, Group, Stack, Badge, Box, rem, useMantineTheme } from '@mantine/core';
import { EnvironmentSelector } from './EnvironmentSelector';

export function Hero() {
  const [selectorOpened, setSelectorOpened] = useState(false);
  const theme = useMantineTheme();

  return (
    <>
      <Box
        style={{
          background: `linear-gradient(135deg, ${theme.colors.intelliBlue[8]} 0%, ${theme.colors.intelliTeal[7]} 100%)`,
        }}
      >
        <Container size="lg" py={120}>
          <Stack align="center" gap="xl">
            <Badge size="xl" variant="filled" color="intelliTeal">
              IntelliCare v3
            </Badge>
            <Title order={1} ta="center" fz={rem(64)} fw={900} c="white">
              A Revolução da Saúde Inteligente
            </Title>
            <Text size="xl" ta="center" maw={700} c="white">
              Nossa plataforma modular com IA de ponta transforma o cuidado ao paciente, otimiza a gestão e garante a interoperabilidade que sua instituição precisa.
            </Text>
            <Group mt="lg">
              <Button
                size="xl"
                color="intelliTeal"
                onClick={() => setSelectorOpened(true)}
              >
                Explore a Plataforma
              </Button>
              <Button size="xl" variant="outline" component="a" href="/docs" color="white">
                Documentação para Desenvolvedores
              </Button>
            </Group>
          </Stack>
        </Container>
      </Box>

      <EnvironmentSelector
        opened={selectorOpened}
        onClose={() => setSelectorOpened(false)}
      />
    </>
  );
}
