import {
  Card, Group, Loader, Stack, Text, ThemeIcon, Title,
} from '@mantine/core'
import { IconPhone, IconMail, IconMapPin, IconClock } from '@tabler/icons-react'
import { useClinicInfo } from '../hooks/usePaciente'

export function ContatoPage() {
  const { data, isLoading } = useClinicInfo()

  if (isLoading) return <Group justify="center" mt="xl"><Loader /></Group>

  const d = data ?? {}

  return (
    <Stack gap="lg">
      <Title order={2}>Contato da Unidade</Title>

      <Card withBorder radius="md" padding="lg">
        <Stack gap="md">
          <Title order={3}>{d.name ?? 'Unidade de Saúde'}</Title>

          <Group gap="sm">
            <ThemeIcon variant="light" color="blue"><IconPhone size={18} /></ThemeIcon>
            <Text>{d.phone ?? 'Não informado'}</Text>
          </Group>

          <Group gap="sm">
            <ThemeIcon variant="light" color="teal"><IconMail size={18} /></ThemeIcon>
            <Text>{d.email ?? 'Não informado'}</Text>
          </Group>

          <Group gap="sm" align="flex-start">
            <ThemeIcon variant="light" color="grape"><IconMapPin size={18} /></ThemeIcon>
            <Text>{d.address ?? 'Não informado'}</Text>
          </Group>

          <Group gap="sm" align="flex-start">
            <ThemeIcon variant="light" color="orange"><IconClock size={18} /></ThemeIcon>
            <Text>{d.hours ?? 'Não informado'}</Text>
          </Group>
        </Stack>
      </Card>
    </Stack>
  )
}

