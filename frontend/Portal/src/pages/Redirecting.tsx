import { Center, Stack, Loader, Text } from '@mantine/core'

interface Props {
  message?: string
}

export function Redirecting({ message = 'Redirecionando...' }: Props) {
  return (
    <Center h="100vh">
      <Stack align="center" gap="sm">
        <Loader size="lg" />
        <Text c="dimmed">{message}</Text>
      </Stack>
    </Center>
  )
}
