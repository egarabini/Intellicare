import { Container, Group, Anchor, Text, Stack, Image } from '@mantine/core';

const links = [
    { link: '/docs', label: 'Documentação API' },
    { link: '#', label: 'Staging' },
    { link: '#', label: 'Política de Privacidade' },
  ];

export function Footer() {
    const items = links.map((link) => (
        <Anchor
          c="dimmed"
          key={link.label}
          href={link.link}
          onClick={(event) => event.preventDefault()}
          size="sm"
        >
          {link.label}
        </Anchor>
      ));

  return (
    <footer style={{ borderTop: '1px solid var(--mantine-color-gray-2)', background: 'var(--mantine-color-gray-0)' }}>
      <Container size="lg" py="xl">
        <Group justify="space-between">
            <Stack>
                <Image src="/logo/logo_completo_intellicare.png" w={150} alt="IntelliCare logo" />
                <Text c="dimmed" size="sm">
                    © {new Date().getFullYear()} IntelliCare. Todos os direitos reservados.
                </Text>
            </Stack>
            <Group>{items}</Group>
        </Group>
      </Container>
    </footer>
  );
}
