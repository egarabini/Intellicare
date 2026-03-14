import { Container, Group, Anchor, Text } from '@mantine/core';

export function Footer() {
  return (
    <footer style={{ borderTop: '1px solid #e9ecef', background: '#f8f9fa' }}>
      <Container size="lg" py="xl">
        <Group justify="space-between">
          <Text c="dimmed" size="sm">
            © {new Date().getFullYear()} IntelliCare. Todos os direitos reservados.
          </Text>
          <Group gap="lg">
            <Anchor href="#" size="sm">Termos de Uso</Anchor>
            <Anchor href="#" size="sm">Política de Privacidade</Anchor>
            <Anchor href="/docs" size="sm">API</Anchor>
          </Group>
        </Group>
      </Container>
    </footer>
  );
}
