import { Box, Title, Text, Card, Group, Stack, Avatar } from '@mantine/core';
import { useAuth } from 'react-oidc-context';

export function MyProfile() {
  const auth = useAuth()
  const p = auth.user?.profile;
  const name = p?.name ?? 'Clínico';
  const email = p?.email ?? '';
  const tenant = p?.['tenant_slug'] ?? '';

  return (
    <Box>
      <Title order={2} mb="lg">Meu Perfil</Title>
      
      <Card withBorder shadow="sm" radius="md" maw={600}>
        <Group>
          <Avatar size="xl" color="blue" radius="xl">{name[0]}</Avatar>
          <Stack gap={0}>
            <Title order={3}>{name as string}</Title>
            <Text c="dimmed">{email as string}</Text>
          </Stack>
        </Group>
        
        <Stack mt="xl" gap="xs">
          <Group justify="space-between">
            <Text fw={500}>Cargo / Role:</Text>
            <Text>{((p?.realm_access as any)?.roles as string[])?.includes('CLINICO') ? 'Clínico (CLINICO)' : 'Administrador'}</Text>
          </Group>
          <Group justify="space-between">
            <Text fw={500}>Tenant Principal:</Text>
            <Text>{tenant as string}</Text>
          </Group>
        </Stack>
      </Card>
    </Box>
  );
}
