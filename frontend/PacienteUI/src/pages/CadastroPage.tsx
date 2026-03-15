import {
  Button, Card, Group, Loader, Stack, Text, TextInput, Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useMe, useUpdateMe } from '../hooks/usePaciente'
import { useState, useEffect } from 'react'

export function CadastroPage() {
  const { data, isLoading } = useMe()
  const update = useUpdateMe()

  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')

  useEffect(() => {
    if (data) {
      setEmail(data.email ?? '')
      setPhone(data.phone ?? '')
    }
  }, [data])

  if (isLoading) return <Group justify="center" mt="xl"><Loader /></Group>

  const d = data ?? {}

  return (
    <Stack gap="lg">
      <Title order={2}>Meus Dados</Title>

      <Card withBorder radius="md" padding="lg">
        <Stack gap="sm">
          <Group>
            <Text fw={500} w={120}>Nome:</Text>
            <Text>{d.full_name ?? '—'}</Text>
          </Group>
          <Group>
            <Text fw={500} w={120}>CPF:</Text>
            <Text>{d.cpf ?? '—'}</Text>
          </Group>
          <Group>
            <Text fw={500} w={120}>Nascimento:</Text>
            <Text>{d.birth_date ? new Date(d.birth_date).toLocaleDateString('pt-BR') : '—'}</Text>
          </Group>
          <Group>
            <Text fw={500} w={120}>Plano:</Text>
            <Text>{d.health_plan ?? '—'}</Text>
          </Group>
        </Stack>
      </Card>

      <Card withBorder radius="md" padding="lg">
        <Title order={4} mb="md">Atualizar contato</Title>
        <Stack gap="sm">
          <TextInput
            label="E-mail"
            value={email}
            onChange={(e) => setEmail(e.currentTarget.value)}
          />
          <TextInput
            label="Telefone"
            value={phone}
            onChange={(e) => setPhone(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              loading={update.isPending}
              onClick={() => update.mutate({ email, phone }, {
                onSuccess: () => notifications.show({ message: 'Dados atualizados!', color: 'green' }),
                onError: () => notifications.show({ message: 'Erro ao atualizar', color: 'red' }),
              })}
            >
              Salvar
            </Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  )
}

