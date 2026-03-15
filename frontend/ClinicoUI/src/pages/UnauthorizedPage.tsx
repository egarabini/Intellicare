import { Stack, Paper, Title, Text, Group, Button } from '@mantine/core';
import { useAuth } from 'react-oidc-context';

export function UnauthorizedPage() {
  const auth = useAuth();
  
  return (
    <Stack align="center" justify="center" h="100%">
      <Paper withBorder radius="lg" p="xl" maw={460}>
        <Stack gap="md">
          <Title order={2}>Acesso negado</Title>
          <Text c="dimmed">
            Esta interface e exclusiva para profissionais com role <code>CLINICO</code>.
          </Text>
          <Group justify="flex-end">
            <Button variant="light" onClick={() => void auth.signoutRedirect()}>Sair</Button>
          </Group>
        </Stack>
      </Paper>
    </Stack>
  );
}
