import {
  Badge, Card, Group, Loader, SimpleGrid, Stack, Text, Title,
} from '@mantine/core'
import { IconHeartbeat } from '@tabler/icons-react'
import { usePrograms } from '../hooks/usePaciente'

const STATUS_COLOR: Record<string, string> = {
  ativo: 'green',
  concluido: 'blue',
  inativo: 'gray',
}

export function ProgramasPage() {
  const { data, isLoading } = usePrograms()

  return (
    <Stack gap="lg">
      <Title order={2}>Programas de Saúde</Title>

      {isLoading ? (
        <Group justify="center" mt="xl"><Loader /></Group>
      ) : !data?.length ? (
        <Card withBorder padding="lg">
          <Text c="dimmed">Você não está inscrito em nenhum programa no momento.</Text>
        </Card>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
          {data.map((p: any) => (
            <Card key={p.id} withBorder radius="md" padding="lg">
              <Group gap="sm" mb="xs">
                <IconHeartbeat size={20} color="var(--mantine-color-teal-6)" />
                <Text fw={600}>{p.name}</Text>
                <Badge color={STATUS_COLOR[p.status] ?? 'gray'} variant="light" ml="auto">
                  {p.status}
                </Badge>
              </Group>
              {p.enrolled_at && (
                <Text size="xs" c="dimmed">
                  Inscrito em {new Date(p.enrolled_at).toLocaleDateString('pt-BR')}
                </Text>
              )}
            </Card>
          ))}
        </SimpleGrid>
      )}
    </Stack>
  )
}

