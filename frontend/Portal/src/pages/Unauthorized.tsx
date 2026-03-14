import { Center, Stack, Title, Text, Button, Paper } from '@mantine/core'

interface Props {
  email?: string
  onLogout: () => void
}

export function Unauthorized({ email, onLogout }: Props) {
  return (
    <Center h="100vh" bg="gray.0">
      <Paper withBorder shadow="md" p="xl" radius="md" maw={420} w="100%">
        <Stack align="center" gap="md">
          <Title order={3} ta="center">Acesso não autorizado</Title>
          <Text c="dimmed" ta="center" size="sm">
            O usuário <strong>{email ?? 'desconhecido'}</strong> não possui
            um perfil de acesso configurado nesta plataforma.
          </Text>
          <Text c="dimmed" ta="center" size="xs">
            Entre em contato com o administrador do sistema.
          </Text>
          <Button fullWidth color="red" variant="light" onClick={onLogout}>
            Sair
          </Button>
        </Stack>
      </Paper>
    </Center>
  )
}
