import { useState } from 'react'
import {
  Button,
  Center,
  Group,
  Loader,
  NativeSelect,
  Paper,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'

import { useProfile, useUpdateProfile, UnitProfileUpdate } from '../hooks/useProfile'

const UNIT_TYPES = [
  { value: 'ubs', label: 'UBS' },
  { value: 'clinic', label: 'Clinica' },
  { value: 'hospital', label: 'Hospital' },
  { value: 'specialty', label: 'Especialidade' },
]

export function ProfilePage() {
  const { data: profile, isLoading, isError } = useProfile()
  const update = useUpdateProfile()
  const [form, setForm] = useState<UnitProfileUpdate | null>(null)

  const current = form ?? profile ?? { name: '', unit_type: 'clinic' as const }

  const handleSave = async () => {
    const payload: UnitProfileUpdate = {
      name: current.name,
      address: current.address ?? null,
      city: current.city ?? null,
      state: current.state ?? null,
      unit_type: current.unit_type ?? 'clinic',
      phone: current.phone ?? null,
      email: current.email ?? null,
    }
    try {
      await update.mutateAsync(payload)
      setForm(null)
      notifications.show({ title: 'Salvo', message: 'Perfil atualizado.', color: 'green' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao salvar perfil.', color: 'red' })
    }
  }

  const set = (field: keyof UnitProfileUpdate, value: string) => {
    setForm({ ...current, [field]: value })
  }

  if (isLoading) return <Center><Loader /></Center>

  return (
    <Stack>
      <Title order={2}>Perfil da Unidade</Title>
      {isError && !profile && (
        <Text c="dimmed" size="sm">Perfil nao configurado. Preencha os dados abaixo.</Text>
      )}
      <Paper withBorder p="lg" radius="md">
        <Stack>
          <TextInput
            label="Nome da unidade"
            value={current.name}
            onChange={(e) => set('name', e.currentTarget.value)}
            required
          />
          <NativeSelect
            label="Tipo"
            data={UNIT_TYPES}
            value={current.unit_type ?? 'clinic'}
            onChange={(e) => set('unit_type', e.currentTarget.value)}
          />
          <TextInput
            label="Endereco"
            value={current.address ?? ''}
            onChange={(e) => set('address', e.currentTarget.value)}
          />
          <Group grow>
            <TextInput
              label="Cidade"
              value={current.city ?? ''}
              onChange={(e) => set('city', e.currentTarget.value)}
            />
            <TextInput
              label="Estado"
              value={current.state ?? ''}
              onChange={(e) => set('state', e.currentTarget.value)}
              maxLength={2}
            />
          </Group>
          <Group grow>
            <TextInput
              label="Telefone"
              value={current.phone ?? ''}
              onChange={(e) => set('phone', e.currentTarget.value)}
            />
            <TextInput
              label="Email"
              value={current.email ?? ''}
              onChange={(e) => set('email', e.currentTarget.value)}
            />
          </Group>
          <Group justify="flex-end">
            <Button onClick={handleSave} loading={update.isPending}>Salvar</Button>
          </Group>
        </Stack>
      </Paper>
    </Stack>
  )
}
