# DEM-018 — Admin Completo: Especificação Técnica

## 1. Arquivos a Modificar / Criar

```
modules/admin/router.py          ← adicionar 6 endpoints
modules/admin/service.py         ← adicionar métodos
modules/admin/schemas.py         ← adicionar models
frontend/AdminUI/src/
  ├── hooks/useTenants.ts        ← adicionar hooks
  ├── pages/AuditLog.tsx         ← novo
  ├── pages/TenantUsers.tsx      ← novo (substituir TenantDetail users)
  └── App.tsx                    ← adicionar rotas
infra/docker-compose.yml         ← labels Traefik para subdomínio
```

---

## 2. Backend — Novos Endpoints

### 2.1 Dashboard Stats

```python
# modules/admin/router.py

@router.get("/dashboard/stats")
async def dashboard_stats(
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    return await svc.get_dashboard_stats()
```

```python
# modules/admin/service.py

async def get_dashboard_stats(self) -> dict:
    row = await self._session.execute(text("""
        SELECT
            COUNT(*)                                    AS total_tenants,
            COUNT(*) FILTER (WHERE status = 'active')  AS active_tenants,
            COUNT(*) FILTER (WHERE status = 'suspended') AS suspended_tenants,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS new_last_30d
        FROM public.tenants
    """))
    stats = dict(row.one()._mapping)

    # Receita mensal estimada (soma de faturas do mês corrente)
    rev = await self._session.execute(text("""
        SELECT COALESCE(SUM(i.amount), 0) AS monthly_revenue
        FROM public.invoices i
        WHERE i.status = 'paid'
          AND i.paid_at >= date_trunc('month', NOW())
    """))
    stats["monthly_revenue"] = float(rev.scalar_one())
    return stats
```

---

### 2.2 Convidar Usuário

```python
# schemas.py
class UserInviteRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=3)
    role: Literal["TENANT_GESTOR", "CLINICO", "PACIENTE"]

class UserInviteResponse(BaseModel):
    keycloak_id: str
    email: str
    role: str
    invited: bool  # True=criado, False=já existia
```

```python
# router.py
@router.post("/tenants/{slug}/users/invite",
             response_model=UserInviteResponse,
             status_code=status.HTTP_201_CREATED)
async def invite_user(
    slug: str,
    body: UserInviteRequest,
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    return await svc.invite_user(slug, body)
```

```python
# service.py
async def invite_user(self, slug: str, req: UserInviteRequest) -> dict:
    tenant = await self.get_tenant(slug)
    if not tenant:
        raise HTTPException(404, "Tenant não encontrado")
    group_id = await self._kc.get_tenant_group_id(slug)
    result = await self._kc.invite_user(
        group_id=group_id,
        email=req.email,
        name=req.name,
        role=req.role,
    )
    await self._audit(
        actor=self._actor, action="USER_INVITED",
        target_type="user", target_id=req.email,
        payload={"tenant": slug, "role": req.role},
    )
    return result
```

---

### 2.3 Desativar Usuário

```python
# router.py
@router.patch("/tenants/{slug}/users/{user_id}/deactivate",
              status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    slug: str,
    user_id: str,
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    await svc.deactivate_user(slug, user_id)

# service.py
async def deactivate_user(self, slug: str, user_id: str) -> None:
    await self._kc.deactivate_user(user_id)
    await self._audit(
        actor=self._actor, action="USER_DEACTIVATED",
        target_type="user", target_id=user_id,
        payload={"tenant": slug},
    )
```

---

### 2.4 Audit Log

```python
# schemas.py
class AuditLogEntry(BaseModel):
    id: int
    actor_id: str
    actor_email: Optional[str]
    action: str
    target_type: str
    target_id: Optional[str]
    payload: Optional[dict]
    created_at: datetime

class AuditLogResponse(BaseModel):
    items: List[AuditLogEntry]
    total: int
```

```python
# router.py
@router.get("/audit", response_model=AuditLogResponse)
async def audit_log(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    from_date: Optional[datetime] = None,
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    return await svc.get_audit_log(page, size, action, from_date)

# service.py
async def get_audit_log(
    self, page: int, size: int,
    action: Optional[str], from_date: Optional[datetime]
) -> dict:
    where = ["1=1"]
    params: dict = {"limit": size, "offset": (page - 1) * size}
    if action:
        where.append("action = :action")
        params["action"] = action
    if from_date:
        where.append("created_at >= :from_date")
        params["from_date"] = from_date

    where_clause = " AND ".join(where)
    rows = await self._session.execute(
        text(f"""
            SELECT id, actor_id, actor_email, action, target_type,
                   target_id, payload, created_at
            FROM public.platform_audit_log
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), params
    )
    count = await self._session.execute(
        text(f"SELECT COUNT(*) FROM public.platform_audit_log WHERE {where_clause}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    return {
        "items": [dict(r._mapping) for r in rows],
        "total": count.scalar_one(),
    }
```

---

### 2.5 Editar Tenant

```python
# schemas.py
class TenantUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3)

# router.py
@router.patch("/tenants/{slug}", response_model=TenantResponse)
async def update_tenant(
    slug: str,
    body: TenantUpdateRequest,
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    return await svc.update_tenant(slug, body)

# service.py
async def update_tenant(self, slug: str, req: TenantUpdateRequest) -> dict:
    await self._session.execute(
        text("UPDATE public.tenants SET name=:name, updated_at=NOW() WHERE slug=:slug"),
        {"name": req.name, "slug": slug},
    )
    await self._session.commit()
    return await self.get_tenant(slug)
```

---

### 2.6 Deletar Tenant

```python
# router.py
@router.delete("/tenants/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    slug: str,
    _=Depends(require_role(["PLATFORM_ADMIN"])),
    svc: TenantService = Depends(_get_service),
):
    await svc.delete_tenant(slug)

# service.py
async def delete_tenant(self, slug: str) -> None:
    schema = f"tenant_{slug.replace('-', '_')}"
    # 1. Drop schema com todos os dados
    await self._session.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    # 2. Soft delete na tabela de tenants
    await self._session.execute(
        text("UPDATE public.tenants SET status='terminated', updated_at=NOW() WHERE slug=:slug"),
        {"slug": slug},
    )
    await self._session.commit()
    # 3. Remover grupo do Keycloak
    group_id = await self._kc.get_tenant_group_id(slug)
    if group_id:
        await self._kc.delete_group(group_id)
    await self._audit(
        actor=self._actor, action="TENANT_DELETED",
        target_type="tenant", target_id=slug, payload={},
    )
```

> ⚠️ Adicionar método `delete_group(group_id)` no `KeycloakAdminClient`.

---

## 3. Frontend — Novos Hooks

```typescript
// src/hooks/useTenants.ts — adicionar:

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/admin/dashboard/stats').then(r => r.data),
    refetchInterval: 30_000,
  })
}

export function useInviteUser(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; name: string; role: string }) =>
      apiClient.post(`/admin/tenants/${slug}/users/invite`, body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users', slug] }),
  })
}

export function useDeactivateUser(slug: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.patch(`/admin/tenants/${slug}/users/${userId}/deactivate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-users', slug] }),
  })
}

export function useDeleteTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => apiClient.delete(`/admin/tenants/${slug}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  })
}

export function useAuditLog(page = 1, action?: string) {
  return useQuery({
    queryKey: ['audit-log', page, action],
    queryFn: () => apiClient.get('/admin/audit', {
      params: { page, size: 50, action }
    }).then(r => r.data),
  })
}
```

---

## 4. Frontend — Dashboard Melhorado

```tsx
// src/pages/DashboardPage.tsx — substituir stats hardcoded por dados reais

import { useDashboardStats } from '../hooks/useTenants'
import { SimpleGrid, Card, Text, Title, Loader, RingProgress, Group } from '@mantine/core'

export function DashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()

  if (isLoading) return <Loader />

  return (
    <Stack>
      <Title order={2}>Dashboard</Title>
      <SimpleGrid cols={4}>
        <Card withBorder>
          <Text size="xs" c="dimmed">Total Tenants</Text>
          <Title order={2}>{stats?.total_tenants ?? 0}</Title>
        </Card>
        <Card withBorder>
          <Text size="xs" c="dimmed" color="green">Ativos</Text>
          <Title order={2} c="green">{stats?.active_tenants ?? 0}</Title>
        </Card>
        <Card withBorder>
          <Text size="xs" c="dimmed" color="orange">Suspensos</Text>
          <Title order={2} c="orange">{stats?.suspended_tenants ?? 0}</Title>
        </Card>
        <Card withBorder>
          <Text size="xs" c="dimmed">Receita Mensal</Text>
          <Title order={2}>
            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
              .format(stats?.monthly_revenue ?? 0)}
          </Title>
        </Card>
      </SimpleGrid>
      {/* TenantList abaixo */}
    </Stack>
  )
}
```

---

## 5. Frontend — Página de Usuários com Convite

```tsx
// src/pages/TenantUsers.tsx

import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Title, Stack, Table, Badge, Button, Group,
  Modal, TextInput, Select, ActionIcon, Tooltip,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { IconUserPlus, IconUserOff } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { useTenantUsers, useInviteUser, useDeactivateUser } from '../hooks/useTenants'

export function TenantUsers() {
  const { slug } = useParams<{ slug: string }>()
  const [inviteOpen, setInviteOpen] = useState(false)
  const { data: users } = useTenantUsers(slug!)
  const invite    = useInviteUser(slug!)
  const deactivate = useDeactivateUser(slug!)

  const form = useForm({
    initialValues: { email: '', name: '', role: 'CLINICO' },
    validate: {
      email: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Email inválido',
      name:  v => v.length >= 3 ? null : 'Mínimo 3 caracteres',
    },
  })

  const handleInvite = async (values: typeof form.values) => {
    try {
      await invite.mutateAsync(values)
      notifications.show({ title: 'Usuário convidado', message: values.email, color: 'green' })
      setInviteOpen(false)
      form.reset()
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao convidar usuário', color: 'red' })
    }
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={3}>Usuários — {slug}</Title>
        <Button leftSection={<IconUserPlus size={16} />} onClick={() => setInviteOpen(true)}>
          Convidar Usuário
        </Button>
      </Group>

      <Table withTableBorder highlightOnHover>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Email</Table.Th>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Role</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {users?.map((u: any) => (
            <Table.Tr key={u.keycloak_id}>
              <Table.Td>{u.email}</Table.Td>
              <Table.Td>{u.username}</Table.Td>
              <Table.Td><Badge variant="light">{u.roles?.[0]}</Badge></Table.Td>
              <Table.Td>
                <Badge color={u.enabled ? 'green' : 'red'} variant="light">
                  {u.enabled ? 'Ativo' : 'Inativo'}
                </Badge>
              </Table.Td>
              <Table.Td>
                {u.enabled && (
                  <Tooltip label="Desativar usuário">
                    <ActionIcon
                      color="red" variant="subtle"
                      onClick={() => deactivate.mutate(u.keycloak_id)}
                    >
                      <IconUserOff size={16} />
                    </ActionIcon>
                  </Tooltip>
                )}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <Modal opened={inviteOpen} onClose={() => setInviteOpen(false)} title="Convidar Usuário">
        <form onSubmit={form.onSubmit(handleInvite)}>
          <Stack>
            <TextInput label="Email" required {...form.getInputProps('email')} />
            <TextInput label="Nome completo" required {...form.getInputProps('name')} />
            <Select
              label="Perfil"
              data={[
                { value: 'TENANT_GESTOR', label: 'Gestor' },
                { value: 'CLINICO',       label: 'Clínico' },
                { value: 'PACIENTE',      label: 'Paciente' },
              ]}
              {...form.getInputProps('role')}
            />
            <Button type="submit" loading={invite.isPending}>Enviar Convite</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
```

---

## 6. Frontend — Audit Log

```tsx
// src/pages/AuditLog.tsx

import { useState } from 'react'
import { Title, Stack, Table, Text, Select, Group, Badge, Pagination } from '@mantine/core'
import { useAuditLog } from '../hooks/useTenants'

const ACTION_COLORS: Record<string, string> = {
  TENANT_CREATED:    'green',
  TENANT_SUSPENDED:  'orange',
  TENANT_ACTIVATED:  'blue',
  TENANT_DELETED:    'red',
  USER_INVITED:      'teal',
  USER_DEACTIVATED:  'red',
}

export function AuditLog() {
  const [page, setPage] = useState(1)
  const [filterAction, setFilterAction] = useState<string | null>(null)
  const { data } = useAuditLog(page, filterAction ?? undefined)

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Audit Log</Title>
        <Select
          placeholder="Filtrar por ação"
          clearable
          data={Object.keys(ACTION_COLORS)}
          value={filterAction}
          onChange={setFilterAction}
          w={220}
        />
      </Group>

      <Table withTableBorder striped>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Data/Hora</Table.Th>
            <Table.Th>Ator</Table.Th>
            <Table.Th>Ação</Table.Th>
            <Table.Th>Alvo</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {data?.items.map((entry: any) => (
            <Table.Tr key={entry.id}>
              <Table.Td>
                <Text size="sm">{new Date(entry.created_at).toLocaleString('pt-BR')}</Text>
              </Table.Td>
              <Table.Td>
                <Text size="sm" ff="monospace">{entry.actor_email ?? entry.actor_id}</Text>
              </Table.Td>
              <Table.Td>
                <Badge color={ACTION_COLORS[entry.action] ?? 'gray'} variant="light">
                  {entry.action}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Text size="sm">{entry.target_id ?? '—'}</Text>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      <Pagination
        total={Math.ceil((data?.total ?? 0) / 50)}
        value={page}
        onChange={setPage}
      />
    </Stack>
  )
}
```

---

## 7. Traefik — Subdomínio `admin.intellicare.ia.br`

Adicionar ao serviço `intellicare-service` em `infra/docker-compose.yml`:

```yaml
labels:
  - "traefik.enable=true"
  # Rota por subdomínio (produção)
  - "traefik.http.routers.intellicare-admin.rule=Host(`admin.intellicare.ia.br`)"
  - "traefik.http.routers.intellicare-admin.entrypoints=websecure"
  - "traefik.http.routers.intellicare-admin.tls.certresolver=letsencrypt"
  - "traefik.http.services.intellicare-admin.loadbalancer.server.port=8000"
  # Redirect HTTP → HTTPS
  - "traefik.http.routers.intellicare-admin-http.rule=Host(`admin.intellicare.ia.br`)"
  - "traefik.http.routers.intellicare-admin-http.entrypoints=web"
  - "traefik.http.routers.intellicare-admin-http.middlewares=redirect-to-https"
  - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
```

Adicionar ao serviço `traefik` em `infra/docker-compose.yml`:

```yaml
command:
  - "--entrypoints.web.address=:80"
  - "--entrypoints.websecure.address=:443"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
  - "--certificatesresolvers.letsencrypt.acme.email=egarabini@gmail.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
volumes:
  - ./letsencrypt:/letsencrypt
ports:
  - "80:80"
  - "443:443"
  - "8090:8080"  # dashboard
```

> **Pré-requisito DNS:** Entrada A em `admin.intellicare.ia.br` apontando para o IP do servidor antes de subir o Traefik com ACME. Sem DNS válido o Let's Encrypt não emite o certificado.

---

## 8. Rotas App.tsx — Adicionar

```tsx
// src/App.tsx
import { TenantUsers } from './pages/TenantUsers'
import { AuditLog }    from './pages/AuditLog'

// dentro de <Routes>:
<Route path="/tenants/:slug/users" element={<TenantUsers />} />
<Route path="/audit"               element={<AuditLog />} />
```

Adicionar no NavBar/AppShell:
```tsx
<NavLink component={Link} to="/audit" label="Audit Log" leftSection={<IconShield size={16} />} />
```

---

## 9. Checklist de Aceite Técnico

- [ ] `GET /admin/dashboard/stats` retorna dados reais
- [ ] `POST /admin/tenants/{slug}/users/invite` cria usuário no Keycloak
- [ ] `PATCH /admin/tenants/{slug}/users/{id}/deactivate` desativa usuário
- [ ] `GET /admin/audit` retorna log paginado com filtros
- [ ] `DELETE /admin/tenants/{slug}` remove schema + grupo Keycloak
- [ ] Dashboard mostra KPIs reais (não hardcoded)
- [ ] TenantUsers permite convidar e desativar
- [ ] AuditLog filtrável por ação
- [ ] Traefik roteia `admin.intellicare.ia.br` com SSL válido
- [ ] `http://` redireciona para `https://`
- [ ] DNS configurado antes de subir Let's Encrypt
