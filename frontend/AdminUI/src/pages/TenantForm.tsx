import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Group, Loader, Paper, Stack, TextInput, Title } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'

import { useCreateTenant, useTenant, useUpdateTenant } from '../hooks/useTenants'

type TenantFormValues = {
  name: string
  slug: string
  gestor_email: string
}

function buildSlug(name: string) {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 30)
}

export function TenantForm() {
  const navigate = useNavigate()
  const createTenant = useCreateTenant()

  const form = useForm<TenantFormValues>({
    initialValues: {
      name: '',
      slug: '',
      gestor_email: '',
    },
    validate: {
      name: (value) => (value.trim().length < 3 ? 'Nome deve ter ao menos 3 caracteres' : null),
      slug: (value) =>
        /^[a-z0-9_]{3,30}$/.test(value)
          ? null
          : 'Slug: 3-30 chars, apenas minusculas, numeros e underscore',
      gestor_email: (value) => (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? null : 'Email invalido'),
    },
  })

  const handleNameChange = (name: string) => {
    form.setFieldValue('name', name)
    form.setFieldValue('slug', buildSlug(name))
  }

  const handleSubmit = async (values: TenantFormValues) => {
    try {
      await createTenant.mutateAsync(values)
      notifications.show({
        title: 'Tenant criado',
        message: `${values.name} criado com sucesso.`,
        color: 'green',
      })
      navigate('/tenants')
    } catch (error: unknown) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Erro ao criar tenant.'
      notifications.show({
        title: 'Erro',
        message,
        color: 'red',
      })
    }
  }

  return (
    <Stack maw={560}>
      <Title order={2}>Novo Tenant</Title>
      <Paper withBorder p="lg" radius="lg">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput
              label="Nome"
              placeholder="Clinica Sao Lucas"
              required
              {...form.getInputProps('name')}
              onChange={(event) => handleNameChange(event.currentTarget.value)}
            />
            <TextInput
              label="Slug"
              placeholder="clinica_sao_lucas"
              description="Gerado automaticamente. Identificador unico e imutavel."
              required
              {...form.getInputProps('slug')}
            />
            <TextInput
              label="Email do gestor"
              placeholder="gestor@cliente.com"
              required
              {...form.getInputProps('gestor_email')}
            />
            <Group justify="flex-end">
              <Button variant="subtle" onClick={() => navigate('/tenants')}>
                Cancelar
              </Button>
              <Button type="submit" loading={createTenant.isPending}>
                Criar Tenant
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </Stack>
  )
}

export function TenantEditForm() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { data: tenant, isLoading } = useTenant(slug!)
  const updateTenant = useUpdateTenant()

  const form = useForm({
    initialValues: { name: tenant?.name ?? '', gestor_email: tenant?.gestor_email ?? '' },
  })

  useEffect(() => {
    if (tenant) {
      form.setValues({ name: tenant.name, gestor_email: tenant.gestor_email ?? '' })
    }
  }, [tenant]) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) return <Loader />

  const handleSubmit = async (values: { name: string; gestor_email: string }) => {
    try {
      await updateTenant.mutateAsync({ slug: slug!, body: values })
      notifications.show({ title: 'Tenant atualizado', message: values.name, color: 'green' })
      navigate(`/tenants/${slug}`)
    } catch (error: unknown) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Erro ao atualizar tenant.'
      notifications.show({ title: 'Erro', message, color: 'red' })
    }
  }

  return (
    <Stack maw={560}>
      <Title order={2}>Editar Tenant — {slug}</Title>
      <Paper withBorder p="lg" radius="lg">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput label="Slug" value={slug} disabled description="Imutável após criação." />
            <TextInput label="Nome" required {...form.getInputProps('name')} />
            <TextInput label="Email do gestor" {...form.getInputProps('gestor_email')} />
            <Group justify="flex-end">
              <Button variant="subtle" onClick={() => navigate(`/tenants/${slug}`)}>Cancelar</Button>
              <Button type="submit" loading={updateTenant.isPending}>Salvar</Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </Stack>
  )
}
