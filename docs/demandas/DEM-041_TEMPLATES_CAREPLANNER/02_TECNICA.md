---
tipo: especificacao-tecnica
demanda: DEM-041
titulo: Templates CarePlanner — CRUD + integração TriggerModal
sprint: "4.2"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
---

# DEM-041 — Especificação Técnica

> Base path: `C:\Users\egara\INTELLICARE\`

---

## PRÉ-CONDIÇÕES

- DEM-038 completa (tabela `care_templates` e métodos `create_template` /
  `list_templates` / `get_template_by_code` já existem no repositório).
- DEM-040 commitada (TriggerJourneyModal a ser modificado existe).

---

## BLOCO 1 — Repositório (`modules/careplanner/repository.py`)

Adicionar dois métodos à classe `CareplannerRepository`, logo após `list_templates`:

```python
async def get_template(
    self, ctx: TenantContext, template_id: UUID
) -> CareTemplateRecord | None:
    async with tenant_session(ctx) as db:
        row = (
            await db.execute(
                text("SELECT * FROM care_templates WHERE id = :id"),
                {"id": str(template_id)},
            )
        ).mappings().first()
    return CareTemplateRecord(**dict(row)) if row else None

async def update_template(
    self,
    ctx: TenantContext,
    template_id: UUID,
    content: str,
    variables: list[str],
    active: bool,
) -> CareTemplateRecord | None:
    async with tenant_session(ctx) as db:
        row = (
            await db.execute(
                text(
                    """
                    UPDATE care_templates
                    SET content   = :content,
                        variables = CAST(:variables AS jsonb),
                        active    = :active,
                        updated_at = NOW()
                    WHERE id = :id AND tenant_slug = :tenant_slug
                    RETURNING *
                    """
                ),
                {
                    "content": content,
                    "variables": json.dumps(variables),
                    "active": active,
                    "id": str(template_id),
                    "tenant_slug": ctx.tenant_id,
                },
            )
        ).mappings().first()
    return CareTemplateRecord(**dict(row)) if row else None
```

Também alterar a assinatura de `list_templates` para aceitar filtro `active`:

```python
async def list_templates(
    self, ctx: TenantContext, active_only: bool = False
) -> list[CareTemplateRecord]:
    async with tenant_session(ctx) as db:
        sql = "SELECT * FROM care_templates"
        if active_only:
            sql += " WHERE active = TRUE"
        sql += " ORDER BY template_code ASC"
        rows = (await db.execute(text(sql))).mappings().all()
    return [CareTemplateRecord(**dict(row)) for row in rows]
```

---

## BLOCO 2 — Service (`modules/careplanner/services.py`)

Adicionar 4 métodos a `CareplannerService` (após `get_dashboard_stats`):

```python
async def list_templates(
    self, ctx: TenantContext, active_only: bool = False
) -> list[dict]:
    records = await self._repo.list_templates(ctx, active_only=active_only)
    return [r.model_dump(mode="json") for r in records]

async def create_template_record(
    self, ctx: TenantContext, payload: CareTemplateCreate
) -> dict:
    from sqlalchemy.exc import IntegrityError
    try:
        record = await self._repo.create_template(ctx, payload)
    except IntegrityError:
        raise api_error(409, "template_already_exists",
                        f"Template '{payload.template_code}' já existe neste canal e tenant")
    return record.model_dump(mode="json")

async def update_template_record(
    self,
    ctx: TenantContext,
    template_id: UUID,
    content: str,
    variables: list[str],
    active: bool,
) -> dict:
    record = await self._repo.update_template(ctx, template_id, content, variables, active)
    if not record:
        raise api_error(404, "template_not_found", "Template não encontrado")
    return record.model_dump(mode="json")

async def toggle_template(self, ctx: TenantContext, template_id: UUID) -> dict:
    record = await self._repo.get_template(ctx, template_id)
    if not record:
        raise api_error(404, "template_not_found", "Template não encontrado")
    updated = await self._repo.update_template(
        ctx, template_id,
        content=record.content,
        variables=record.variables,
        active=not record.active,
    )
    return {"id": str(template_id), "active": updated.active if updated else not record.active}
```

---

## BLOCO 3 — Endpoints (`modules/careplanner/api/routes.py`)

Adicionar Pydantic models e 4 rotas ao final do arquivo:

```python
# ── Pydantic models ────────────────────────────────────────────────────────

class TemplateCreateRequest(BaseModel):
    template_code: str = Field(..., pattern=r"^[a-z0-9_]{2,64}$",
                               description="snake_case, 2-64 chars")
    channel: str = "rocketchat"
    content: str = Field(..., min_length=1, max_length=2000)
    variables: list[str] = Field(default_factory=list)
    active: bool = True


class TemplateUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    variables: list[str] = Field(default_factory=list)
    active: bool = True


# ── Rotas ────────────────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates(
    active: bool | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareplannerService = Depends(get_service),
) -> dict:
    items = await service.list_templates(ctx, active_only=bool(active))
    return {"items": items}


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreateRequest,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    from ..contracts import CareTemplateCreate, Channel
    payload = CareTemplateCreate(
        template_code=body.template_code,
        channel=Channel(body.channel),
        content=body.content,
        variables=body.variables,
        active=body.active,
    )
    return await service.create_template_record(ctx, payload)


@router.put("/templates/{template_id}")
async def update_template(
    template_id: UUID,
    body: TemplateUpdateRequest,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.update_template_record(
        ctx, template_id, body.content, body.variables, body.active
    )


@router.patch("/templates/{template_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_template(
    template_id: UUID,
    ctx: TenantContext = Depends(require_role("GESTOR")),
    service: CareplannerService = Depends(get_service),
) -> dict:
    return await service.toggle_template(ctx, template_id)
```

---

## BLOCO 4 — Seed de Templates (`modules/careplanner/services.py`)

Adicionar método `seed_default_templates` chamado no `startup` do `main.py`
(após as migrações, antes de iniciar os workers):

```python
async def seed_default_templates(self, ctx: TenantContext) -> None:
    """Cria templates padrão se ainda não existirem no tenant."""
    from ..contracts import CareTemplateCreate, Channel
    defaults = [
        CareTemplateCreate(
            template_code="boas_vindas",
            content="Olá! Sou o assistente do IntelliCare. "
                    "Estamos iniciando seu acompanhamento. "
                    "Você confirma que está disponível para conversar?",
            variables=[],
        ),
        CareTemplateCreate(
            template_code="check_in",
            content="Olá! Como você está se sentindo hoje? "
                    "Está conseguindo seguir o plano de cuidados?",
            variables=[],
        ),
        CareTemplateCreate(
            template_code="lembrete_medicacao",
            content="Lembrete: é hora de tomar seu medicamento. "
                    "Você já tomou hoje?",
            variables=[],
        ),
        CareTemplateCreate(
            template_code="teleconsulta_confirmacao",
            content="Sua teleconsulta está confirmada. "
                    "Em breve você receberá o link para a videochamada. "
                    "Responda SIM para confirmar sua presença.",
            variables=[],
        ),
    ]
    for template in defaults:
        try:
            await self._repo.create_template(ctx, template)
        except Exception:
            pass  # ON CONFLICT DO NOTHING equivalente
```

Em `main.py`, dentro de `startup()`, após as migrações e antes de `create_task`:

```python
# Seed de templates padrão por tenant
from .services import build_careplanner_service
from intellicare_core.contracts.base import TenantContext
from sqlalchemy import text

async with get_engine().begin() as conn:
    tenant_slugs = (
        await conn.execute(text("SELECT slug FROM public.tenants"))
    ).scalars().all()

svc = build_careplanner_service()
for slug in tenant_slugs:
    ctx = TenantContext.from_slug(slug=slug, user_id="startup-seed")
    await svc.seed_default_templates(ctx)
```

---

## BLOCO 5 — Hooks (`frontend/GestorUI/src/hooks/useGestor.ts`)

Adicionar ao final do arquivo:

```typescript
// ── Template types ────────────────────────────────────────────────────────

export interface CareTemplate {
  id: string;
  template_code: string;
  channel: string;
  content: string;
  variables: string[];
  active: boolean;
  tenant_slug: string;
  created_at: string;
  updated_at: string;
}

export interface TemplateCreatePayload {
  template_code: string;
  channel?: string;
  content: string;
  variables?: string[];
  active?: boolean;
}

export interface TemplateUpdatePayload {
  content: string;
  variables: string[];
  active: boolean;
}

// ── Hooks ─────────────────────────────────────────────────────────────────

export function useCareplannerTemplates(activeOnly = false) {
  return useQuery<{ items: CareTemplate[] }>({
    queryKey: ['careplanner_templates', activeOnly],
    queryFn: async () => {
      const url = activeOnly
        ? '/careplanner/templates?active=true'
        : '/careplanner/templates';
      const { data } = await api.get(url);
      return data;
    },
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation<CareTemplate, Error, TemplateCreatePayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/careplanner/templates', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_templates'] });
    },
  });
}

export function useUpdateTemplate(templateId: string) {
  const queryClient = useQueryClient();
  return useMutation<CareTemplate, Error, TemplateUpdatePayload>({
    mutationFn: async (payload) => {
      const { data } = await api.put(`/careplanner/templates/${templateId}`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_templates'] });
    },
  });
}

export function useToggleTemplate() {
  const queryClient = useQueryClient();
  return useMutation<{ id: string; active: boolean }, Error, string>({
    mutationFn: async (templateId) => {
      const { data } = await api.patch(`/careplanner/templates/${templateId}/toggle`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['careplanner_templates'] });
    },
  });
}
```

---

## BLOCO 6 — `pages/CareplannerTemplates.tsx` (novo)

```tsx
import {
  ActionIcon, Badge, Box, Button, Card, Center, Divider, Group,
  Loader, Modal, Stack, Table, Text, Textarea, TextInput, Title, Tooltip,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { IconEdit, IconPlus, IconToggleLeft, IconToggleRight } from '@tabler/icons-react';
import {
  useCareplannerTemplates, useCreateTemplate, useUpdateTemplate,
  useToggleTemplate, type CareTemplate, type TemplateCreatePayload,
} from '../hooks/useGestor';

// ── Form de criação/edição ─────────────────────────────────────────────────

interface TemplateFormValues {
  template_code: string;
  content: string;
  variables_raw: string; // vírgula-separado, convertido para list[str] no submit
}

function TemplateModal({
  opened, onClose, editing,
}: {
  opened: boolean;
  onClose: () => void;
  editing: CareTemplate | null;
}) {
  const create = useCreateTemplate();
  const update = useUpdateTemplate(editing?.id ?? '');
  const [conflictError, setConflictError] = useState('');

  const form = useForm<TemplateFormValues>({
    initialValues: {
      template_code: editing?.template_code ?? '',
      content: editing?.content ?? '',
      variables_raw: editing?.variables.join(', ') ?? '',
    },
    validate: {
      template_code: (v) =>
        !editing && !/^[a-z0-9_]{2,64}$/.test(v)
          ? 'snake_case, 2–64 caracteres minúsculos'
          : null,
      content: (v) => (!v.trim() ? 'Conteúdo obrigatório' : null),
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    setConflictError('');
    const variables = values.variables_raw
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean);

    try {
      if (editing) {
        await update.mutateAsync({ content: values.content, variables, active: editing.active });
      } else {
        await create.mutateAsync({
          template_code: values.template_code,
          content: values.content,
          variables,
        } as TemplateCreatePayload);
      }
      notifications.show({
        title: editing ? 'Template atualizado' : 'Template criado',
        color: 'teal',
        message: '',
      });
      form.reset();
      onClose();
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setConflictError('Já existe um template com este código neste canal.');
      } else {
        notifications.show({ title: 'Erro', message: 'Tente novamente.', color: 'red' });
      }
    }
  });

  const isLoading = create.isPending || update.isPending;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={editing ? 'Editar Template' : 'Novo Template'}
      size="lg"
    >
      <form onSubmit={handleSubmit}>
        <Stack>
          <TextInput
            label="Código do Template"
            placeholder="ex. boas_vindas"
            required
            disabled={!!editing}
            description="snake_case, apenas letras minúsculas, números e _"
            data-testid="input-template-code"
            {...form.getInputProps('template_code')}
          />
          {conflictError && (
            <Text size="sm" c="red">{conflictError}</Text>
          )}
          <Textarea
            label="Conteúdo da Mensagem"
            placeholder="Olá! Estamos iniciando seu acompanhamento..."
            required
            autosize
            minRows={4}
            maxRows={10}
            data-testid="input-template-content"
            {...form.getInputProps('content')}
          />
          <TextInput
            label="Variáveis (opcional)"
            placeholder="nome_paciente, data_consulta"
            description="Nomes das variáveis separados por vírgula"
            {...form.getInputProps('variables_raw')}
          />
          <Group justify="flex-end" mt="sm">
            <Button variant="subtle" onClick={onClose} disabled={isLoading}>
              Cancelar
            </Button>
            <Button type="submit" loading={isLoading} data-testid="btn-salvar-template">
              {editing ? 'Salvar' : 'Criar Template'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

// ── Página principal ───────────────────────────────────────────────────────

export function CareplannerTemplates() {
  const { data, isLoading } = useCareplannerTemplates();
  const toggle = useToggleTemplate();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<CareTemplate | null>(null);

  const openCreate = () => { setEditing(null); setModalOpen(true); };
  const openEdit = (t: CareTemplate) => { setEditing(t); setModalOpen(true); };
  const closeModal = () => { setEditing(null); setModalOpen(false); };

  if (isLoading) return <Center h="100%"><Loader /></Center>;

  const templates = data?.items ?? [];

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>Templates de Mensagem</Title>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={openCreate}
          data-testid="btn-novo-template"
        >
          Novo Template
        </Button>
      </Group>

      <Card withBorder>
        {templates.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">
            Nenhum template cadastrado. Clique em "Novo Template" para começar.
          </Text>
        ) : (
          <Table highlightOnHover data-testid="table-templates">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Código</Table.Th>
                <Table.Th>Canal</Table.Th>
                <Table.Th>Conteúdo</Table.Th>
                <Table.Th>Variáveis</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Ações</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {templates.map((t) => (
                <Table.Tr key={t.id} data-testid={`row-template-${t.template_code}`}>
                  <Table.Td>
                    <Text ff="monospace" size="sm">{t.template_code}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge variant="light" color="blue" size="sm">
                      {t.channel}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" lineClamp={1} maw={300}>
                      {t.content}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {t.variables.length > 0 ? t.variables.join(', ') : '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={t.active ? 'teal' : 'gray'} variant="light">
                      {t.active ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Editar">
                        <ActionIcon
                          variant="subtle"
                          onClick={() => openEdit(t)}
                          data-testid={`btn-edit-${t.template_code}`}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label={t.active ? 'Desativar' : 'Ativar'}>
                        <ActionIcon
                          variant="subtle"
                          color={t.active ? 'orange' : 'teal'}
                          loading={toggle.isPending}
                          onClick={() => toggle.mutate(t.id)}
                          data-testid={`btn-toggle-${t.template_code}`}
                        >
                          {t.active
                            ? <IconToggleRight size={16} />
                            : <IconToggleLeft size={16} />
                          }
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      <TemplateModal opened={modalOpen} onClose={closeModal} editing={editing} />
    </Box>
  );
}
```

---

## BLOCO 7 — Integração no `TriggerJourneyModal.tsx` (DEM-040)

Substituir o `TextInput` de `template_code` por um `Select` dinâmico:

```tsx
// Adicionar import do hook
import { useCareplannerTemplates } from '../hooks/useGestor';

// Dentro do componente TriggerJourneyModal, antes do return:
const { data: templatesData } = useCareplannerTemplates(true); // activeOnly=true
const templateOptions = (templatesData?.items ?? []).map((t) => ({
  value: t.template_code,
  label: `${t.template_code} — ${t.content.slice(0, 40)}${t.content.length > 40 ? '…' : ''}`,
}));

// Substituir o TextInput de template_code por:
<Select
  label="Template de Mensagem"
  placeholder="Selecione um template (opcional)"
  data={templateOptions}
  clearable
  searchable
  data-testid="select-template-code"
  {...form.getInputProps('template_code')}
/>
```

---

## BLOCO 8 — Navegação e Rota (`App.tsx`)

```tsx
// Importar a nova página
import { CareplannerTemplates } from './pages/CareplannerTemplates'

// Dentro de <Routes>:
<Route path="/careplanner/templates" element={<CareplannerTemplates />} />

// No NavLinks, adicionar sub-item após "CarePlanner":
<MantineNavLink
  component={NavLink}
  to="/careplanner"
  label="CarePlanner"
  leftSection={<IconMessage size="1rem"/>}
>
  <MantineNavLink component={NavLink} to="/careplanner" label="Dashboard" pl="md" />
  <MantineNavLink component={NavLink} to="/careplanner/templates" label="Templates" pl="md"
    data-testid="nav-templates" />
</MantineNavLink>
```

---

## BLOCO 9 — Testes Python (`test_careplanner_phase_f.py`)

```
test_list_templates_vazio           — list_templates retorna [] num tenant novo
test_create_template_sucesso        — cria template, retorna record completo
test_create_template_duplicate_409  — mesmo code+channel → api_error 409
test_update_template                — atualiza content e active via service
test_toggle_template                — toggle inverte active
```

5 testes. Fixture: mesmo padrão dos arquivos anteriores (`setup_careplanner_phase_f_schema`).

## BLOCO 10 — Testes Playwright (`e2e/careplanner.spec.ts`)

```typescript
test('DEM041-01: página de templates lista seed defaults', async ({ page }) => {
  await page.route('**/careplanner/templates*', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'tpl-uuid-1', template_code: 'boas_vindas',
            channel: 'rocketchat', content: 'Olá! Sou o assistente...',
            variables: [], active: true,
            tenant_slug: 'alfa', created_at: '2026-03-18T00:00:00Z',
            updated_at: '2026-03-18T00:00:00Z',
          },
        ],
      }),
    });
  });
  await page.goto('/careplanner/templates');
  await expect(page.getByTestId('table-templates')).toBeVisible();
  await expect(page.getByTestId('row-template-boas_vindas')).toBeVisible();
});

test('DEM041-02: criar template com código duplicado exibe erro inline', async ({ page }) => {
  await page.route('**/careplanner/templates', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({ status: 409, contentType: 'application/json',
        body: JSON.stringify({ detail: { code: 'template_already_exists' } }) });
    } else {
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: [] }) });
    }
  });
  await page.goto('/careplanner/templates');
  await page.getByTestId('btn-novo-template').click();
  await page.getByTestId('input-template-code').fill('boas_vindas');
  await page.getByTestId('input-template-content').fill('Conteúdo de teste');
  await page.getByTestId('btn-salvar-template').click();
  await expect(page.getByText('Já existe um template com este código')).toBeVisible();
});
```

---

## Estrutura de Arquivos — Resumo

```
modules/careplanner/
  repository.py          ← get_template, update_template, list_templates(active_only)
  services.py            ← list_templates, create_template_record, update_template_record,
                            toggle_template, seed_default_templates
  api/routes.py          ← GET/POST /templates, PUT/PATCH /templates/:id/toggle
  main.py                ← chamar seed_default_templates no startup

frontend/GestorUI/src/
  hooks/useGestor.ts                   ← 4 hooks + 3 interfaces
  pages/CareplannerTemplates.tsx       ← NOVO
  components/TriggerJourneyModal.tsx   ← substituir TextInput por Select
  App.tsx                              ← rota + sub-nav CarePlanner

packages/intellicare-core/tests/
  test_careplanner_phase_f.py          ← NOVO, 5 testes
```

---

## Comandos de Validação

```bash
pytest packages/intellicare-core/tests/test_careplanner_phase_f.py -v
pytest packages/intellicare-core/tests/ -q          # garantir não-regressão total
cd frontend/GestorUI && npm run build
npm run test:e2e                                     # 9 total: 7 DEM-040 + 2 novos
```
