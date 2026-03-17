# DEM-037 — AdminUI Fixes — Especificação Técnica

## Visão geral de arquivos alterados

| Arquivo | Tipo | Item |
|---------|------|------|
| `db/platform_migrations/005_gestor_email.sql` | Novo | #3 |
| `modules/admin/schemas.py` | Alterar | #2, #3, #5 |
| `modules/admin/service.py` | Alterar | #3, #5 |
| `modules/admin/router.py` | Alterar | #2 |
| `frontend/AdminUI/src/pages/DashboardPage.tsx` | Alterar | #1 |
| `frontend/AdminUI/src/pages/TenantList.tsx` | Alterar | #2, #3 |
| `frontend/AdminUI/src/pages/TenantDetail.tsx` | Alterar | #3 |
| `frontend/AdminUI/src/pages/TenantForm.tsx` | Alterar | #2, #3 |
| `frontend/AdminUI/src/pages/TenantUsers.tsx` | Alterar | #4 |
| `frontend/AdminUI/src/pages/AdminUsersPage.tsx` | Alterar | #5, #6 |
| `frontend/AdminUI/src/hooks/useTenants.ts` | Alterar | #2, #3 |
| `frontend/AdminUI/src/hooks/useAdminUsers.ts` | Alterar | #5 |
| `frontend/AdminUI/src/App.tsx` | Alterar | #2 (nova rota) |

---

## 1. Backend

### 1.1 Nova migration — `db/platform_migrations/005_gestor_email.sql`

```sql
-- DEM-037: adicionar gestor_email à tabela de tenants
ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS gestor_email TEXT;
```

---

### 1.2 `modules/admin/schemas.py`

**`TenantResponse`** — adicionar `gestor_email`:

```python
class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    status: str
    gestor_email: str | None = None   # ← NOVO
    created_at: datetime
    updated_at: datetime
```

**`TenantUpdate`** — novo schema para PATCH/PUT:

```python
class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    gestor_email: str | None = None
```

**`AdminUserOut`** — adicionar `temporary_password`:

```python
class AdminUserOut(BaseModel):
    id: int
    keycloak_id: str | None = None
    email: EmailStr
    name: str
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    temporary_password: str | None = None   # ← NOVO — só preenchido na criação
```

---

### 1.3 `modules/admin/service.py`

**`provision_tenant`** — salvar `gestor_email` no banco:

Localizar o INSERT INTO `public.tenants` dentro de `provision_tenant` e adicionar `gestor_email` aos campos:

```python
# Antes (trecho):
await conn.execute(
    text("""
        INSERT INTO public.tenants (slug, name, status)
        VALUES (:slug, :name, 'active')
    """),
    {"slug": req.slug, "name": req.name},
)

# Depois:
await conn.execute(
    text("""
        INSERT INTO public.tenants (slug, name, status, gestor_email)
        VALUES (:slug, :name, 'active', :gestor_email)
    """),
    {"slug": req.slug, "name": req.name, "gestor_email": req.gestor_email},
)
```

**Novo método `update_tenant`:**

```python
async def update_tenant(self, slug: str, payload: TenantUpdate, actor: TenantContext) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.gestor_email is not None:
        updates["gestor_email"] = payload.gestor_email
    if not updates:
        # Nada a atualizar — buscar e retornar o atual
        async with get_engine().connect() as conn:
            row = (await conn.execute(
                text("SELECT * FROM public.tenants WHERE slug = :slug"),
                {"slug": slug},
            )).mappings().first()
        return dict(row) if row else {}

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["slug"] = slug
    updates["updated_at"] = "now()"

    async with get_engine().begin() as conn:
        row = (await conn.execute(
            text(f"""
                UPDATE public.tenants
                SET {set_clause}, updated_at = now()
                WHERE slug = :slug
                RETURNING *
            """),
            updates,
        )).mappings().first()
        await self._audit(conn, actor, "TENANT_UPDATED", "tenant", slug, payload.model_dump(exclude_none=True))
    return dict(row) if row else {}
```

**`create_admin_user`** — retornar `temporary_password`:

```python
async def create_admin_user(self, payload: AdminUserCreate, actor: TenantContext) -> dict[str, Any]:
    kc_result = await self._kc.create_admin_user(payload.email, payload.name, enabled=payload.status == "active")
    async with get_engine().begin() as conn:
        row = (await conn.execute(...)).mappings().first()
        await self._audit(...)
    result = dict(row) if row else {}
    result["temporary_password"] = kc_result["temporary_password"]  # ← NOVO
    return result
```

---

### 1.4 `modules/admin/router.py`

**Novo endpoint `PUT /tenants/{slug}`:**

Adicionar após o endpoint de criação de tenant:

```python
from .schemas import TenantUpdate  # adicionar ao import existente

@router.put("/tenants/{slug}", response_model=TenantResponse)
async def update_tenant(
    slug: str,
    body: TenantUpdate,
    actor: AdminRequired,
) -> TenantResponse:
    result = await _service.update_tenant(slug, body, actor)
    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(**result)
```

---

## 2. Frontend

### 2.1 `frontend/AdminUI/src/hooks/useTenants.ts`

Adicionar `gestor_email` à interface `Tenant` e criar `useUpdateTenant`:

```typescript
export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended' | 'trial'
  gestor_email?: string   // ← NOVO
  created_at: string
  updated_at: string
}

export function useUpdateTenant() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ slug, body }: { slug: string; body: { name?: string; gestor_email?: string } }) =>
      apiClient.put(`/admin/tenants/${slug}`, body).then((r) => r.data),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['tenants'] })
      void queryClient.invalidateQueries({ queryKey: ['tenant', variables.slug] })
    },
  })
}
```

---

### 2.2 `frontend/AdminUI/src/hooks/useAdminUsers.ts`

Adicionar `temporary_password` ao `AdminUser`:

```typescript
export interface AdminUser {
  id: number
  keycloak_id: string | null
  email: string
  name: string
  role: 'admin' | 'financ' | 'coordenador'
  status: 'active' | 'inactive'
  last_login_at: string | null
  created_at: string
  temporary_password?: string   // ← NOVO — só presente na resposta de criação
}
```

---

### 2.3 `frontend/AdminUI/src/App.tsx`

Adicionar rota `/tenants/:slug/edit`:

```tsx
import { TenantEditForm } from './pages/TenantForm'  // ou reutilizar TenantForm com prop

// Dentro do <Routes>:
<Route path="/tenants/:slug/edit" element={<TenantEditForm />} />
```

---

### 2.4 `frontend/AdminUI/src/pages/TenantForm.tsx`

Adaptar para suportar modo edição. Criar um segundo export `TenantEditForm` (ou usar `mode` prop):

```tsx
// TenantEditForm — carrega dados existentes e faz PUT
export function TenantEditForm() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { data: tenant, isLoading } = useTenant(slug!)
  const updateTenant = useUpdateTenant()

  const form = useForm({
    initialValues: { name: tenant?.name ?? '', gestor_email: tenant?.gestor_email ?? '' },
  })

  // Sincronizar valores quando tenant carrega
  useEffect(() => {
    if (tenant) {
      form.setValues({ name: tenant.name, gestor_email: tenant.gestor_email ?? '' })
    }
  }, [tenant])  // eslint-disable-line

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
            <TextInput label="Slug" value={slug} disabled
              description="Imutável após criação." />
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
```

---

### 2.5 `frontend/AdminUI/src/pages/TenantList.tsx`

Duas alterações:

**a) Adicionar botão editar:**
```tsx
import { IconEye, IconPencil, IconPlayerPause, IconPlayerPlay, IconPlus, IconSearch } from '@tabler/icons-react'

// Dentro do Group de ações de cada linha:
<Tooltip label="Editar">
  <ActionIcon variant="subtle" color="blue" onClick={() => navigate(`/tenants/${tenant.slug}/edit`)}>
    <IconPencil size={16} />
  </ActionIcon>
</Tooltip>
```

**b) Adicionar coluna Gestor:**
```tsx
// No Table.Thead, adicionar após <Table.Th>Status</Table.Th>:
<Table.Th>Gestor</Table.Th>

// No Table.Tbody, adicionar após a célula de Status:
<Table.Td>
  <Text size="sm" c="dimmed">{tenant.gestor_email ?? '—'}</Text>
</Table.Td>
```

---

### 2.6 `frontend/AdminUI/src/pages/TenantDetail.tsx`

Adicionar `gestor_email` ao bloco de dados:

```tsx
// Dentro do Paper de dados do tenant, após a linha "Atualizado em":
<Text>
  <strong>Gestor:</strong>{' '}
  <Text component="span" c="dimmed">{tenant.gestor_email ?? 'Não informado'}</Text>
</Text>
```

---

### 2.7 `frontend/AdminUI/src/pages/TenantUsers.tsx`

Fix badge de role vazio:

```tsx
// Antes:
<Badge variant="light">{u.roles?.[0]}</Badge>

// Depois:
<Badge variant="light" color={u.roles?.[0] ? 'blue' : 'gray'}>
  {u.roles?.[0] ?? 'Sem role'}
</Badge>
```

---

### 2.8 `frontend/AdminUI/src/pages/DashboardPage.tsx`

Adicionar estado vazio:

```tsx
import { Alert } from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'

// Adicionar import do hook useNavigate
import { useNavigate } from 'react-router-dom'

// Dentro de DashboardPage(), antes do return:
const navigate = useNavigate()

// No JSX, após o <Group justify="space-between"> do título e antes dos cards:
{stats?.total_tenants === 0 && (
  <Alert
    icon={<IconInfoCircle size={18} />}
    title="Nenhum tenant cadastrado"
    color="blue"
    variant="light"
  >
    A plataforma ainda não tem tenants. Crie o primeiro para começar.{' '}
    <Button
      size="xs"
      variant="subtle"
      onClick={() => navigate('/tenants/new')}
      px={4}
    >
      Criar tenant
    </Button>
  </Alert>
)}
```

---

### 2.9 `frontend/AdminUI/src/pages/AdminUsersPage.tsx`

**a) Mostrar modal com senha temporária:**

```tsx
import { Modal, CopyButton, Code } from '@mantine/core'
import { IconCheck, IconCopy } from '@tabler/icons-react'

// Adicionar estado:
const [tempPassword, setTempPassword] = useState<string | null>(null)

// No save(), após mutateAsync com sucesso (criação):
const result = await createUser.mutateAsync(form)
if (result.temporary_password) {
  setTempPassword(result.temporary_password)
}
// (não mostrar notifications.show de sucesso — o modal já serve como feedback)

// Modal de senha temporária:
<Modal
  opened={!!tempPassword}
  onClose={() => setTempPassword(null)}
  title="Usuário criado com sucesso"
  centered
>
  <Stack gap="md">
    <Text size="sm">Senha temporária de primeiro acesso:</Text>
    <Group gap="xs">
      <Code fz="lg" style={{ flex: 1 }}>{tempPassword}</Code>
      <CopyButton value={tempPassword ?? ''} timeout={2000}>
        {({ copied, copy }) => (
          <Button
            size="xs"
            color={copied ? 'teal' : 'blue'}
            leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
            onClick={copy}
          >
            {copied ? 'Copiado' : 'Copiar'}
          </Button>
        )}
      </CopyButton>
    </Group>
    <Alert color="orange" variant="light" icon={<IconInfoCircle size={16} />}>
      Esta senha não será exibida novamente. Anote antes de fechar.
    </Alert>
    <Group justify="flex-end">
      <Button onClick={() => setTempPassword(null)}>Fechar</Button>
    </Group>
  </Stack>
</Modal>
```

**b) Melhorar handler de erro:**

```tsx
// Antes:
} catch (error) {
  notifications.show({ title: 'Erro', message: 'Falha ao salvar usuario admin.', color: 'red' })
  console.error(error)
}

// Depois:
} catch (error) {
  const message =
    (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    'Falha ao salvar usuario admin.'
  notifications.show({ title: 'Erro', message, color: 'red' })
  console.error(error)
}
```

---

## 3. Checklist de entrega

- [ ] `db/platform_migrations/005_gestor_email.sql` criado
- [ ] `modules/admin/schemas.py`: `TenantResponse` com `gestor_email`, `TenantUpdate` criado, `AdminUserOut` com `temporary_password`
- [ ] `modules/admin/service.py`: `provision_tenant` salva `gestor_email`, `update_tenant` criado, `create_admin_user` retorna `temporary_password`
- [ ] `modules/admin/router.py`: `PUT /tenants/{slug}` adicionado
- [ ] `frontend/AdminUI/src/hooks/useTenants.ts`: `Tenant.gestor_email`, `useUpdateTenant`
- [ ] `frontend/AdminUI/src/hooks/useAdminUsers.ts`: `AdminUser.temporary_password`
- [ ] `frontend/AdminUI/src/App.tsx`: rota `/tenants/:slug/edit`
- [ ] `frontend/AdminUI/src/pages/TenantForm.tsx`: `TenantEditForm` exportado
- [ ] `frontend/AdminUI/src/pages/TenantList.tsx`: botão editar + coluna Gestor
- [ ] `frontend/AdminUI/src/pages/TenantDetail.tsx`: campo `gestor_email` exibido
- [ ] `frontend/AdminUI/src/pages/TenantUsers.tsx`: badge "Sem role" em cinza
- [ ] `frontend/AdminUI/src/pages/DashboardPage.tsx`: Alert estado vazio
- [ ] `frontend/AdminUI/src/pages/AdminUsersPage.tsx`: modal senha + erro com detalhe
- [ ] Build AdminUI: ok (sem erros TypeScript)
- [ ] Testar: criar tenant → gestor_email aparece na lista
- [ ] Testar: editar tenant → nome atualiza
- [ ] Testar: criar admin user → modal com senha aparece → copiar funciona
- [ ] Testar: criar admin user com email duplicado → mensagem real do backend aparece
- [ ] Aplicar migration `005_gestor_email.sql` no staging antes do deploy
