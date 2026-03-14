# DEM-020 — Clínico Frontend Completo — Especificação Técnica

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18 + Vite + Mantine UI 7 + @mantine/dates |
| Auth | react-oidc-context — role `CLINICO` |
| HTTP | axios — `baseURL: ''` (paths relativos — já correto) |
| State | @tanstack/react-query (já instalado) |
| Build | `npm run build` → `static/clinico-ui/` |
| Dev | porta `5173`, client_id Keycloak: `clinico-ui` |

---

## 1. Novos Endpoints no Backend (módulo cuidado)

> Arquivo: `packages/intellicare-core/intellicare_core/modules/cuidado/router.py`
> Todos os endpoints requerem role `CLINICO`. O `clinician_id` é lido do JWT (`sub`).

### 1.1 Minha Agenda

```
GET /cuidado/my-agenda?date=2026-03-14
GET /cuidado/my-agenda?from=2026-03-10&to=2026-03-16
```

Retorna agendamentos do clínico autenticado no período:
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "patient_name": "João Silva",
    "scheduled_at": "2026-03-14T09:00:00Z",
    "type": "consulta",
    "status": "agendado",
    "encounter_id": null
  }
]
```

SQL (usa `appointments` criada pelo módulo gestor):
```sql
SET search_path TO tenant_{slug};
SELECT a.id, a.patient_id, p.name AS patient_name,
       a.scheduled_at, a.type, a.status,
       e.id AS encounter_id
FROM appointments a
JOIN patients p ON p.id = a.patient_id
LEFT JOIN encounters e ON e.patient_id = a.patient_id
  AND e.clinician_id = a.clinician_id
  AND e.status = 'open'
WHERE a.clinician_id = :clinician_id
  AND DATE(a.scheduled_at) = :date
ORDER BY a.scheduled_at;
```

### 1.2 Perfil Clínico do Paciente

```
GET  /cuidado/patients/{patient_id}/profile
PATCH /cuidado/patients/{patient_id}/clinical   # alergias, medicações
```

**Response GET /profile:**
```json
{
  "id": "uuid",
  "name": "João Silva",
  "cpf": "12345678901",
  "birth_date": "1980-05-20",
  "email": "joao@email.com",
  "phone": "(11) 98765-4321",
  "health_plan": "Unimed",
  "allergies": "Penicilina",
  "medications": "Metformina 500mg/dia",
  "programs": ["HiperDia", "Obesidade"],
  "last_encounter": "2026-02-10",
  "encounter_count": 12
}
```

**Schema PATCH /clinical:**
```json
{ "allergies": "string", "medications": "string" }
```

Migration SQL para campos clínicos na tabela `patients`:
```sql
ALTER TABLE patients
  ADD COLUMN IF NOT EXISTS allergies TEXT,
  ADD COLUMN IF NOT EXISTS medications TEXT;
```

### 1.3 CID-10 Lookup

```
GET /cuidado/cid10?q=diabetes&limit=10
```

Retorna lista de CIDs filtrados por código ou descrição.
Tabela `cid10` pré-populada no schema `public` (compartilhada entre tenants).

```json
[
  { "code": "E11", "description": "Diabetes mellitus tipo 2" },
  { "code": "E10", "description": "Diabetes mellitus tipo 1" }
]
```

### 1.4 Atualizar Encontro com CID e Prescrição

```
PATCH /cuidado/encounters/{encounter_id}
```

```json
{
  "cid10_code": "E11",
  "prescription": "Metformina 500mg 1x/dia"
}
```

---

## 2. Frontend — Estrutura de Rotas

```
/                          → redirect para /dashboard
/dashboard                 → Dashboard.tsx (Minha Agenda Hoje)
/agenda                    → Agenda.tsx (calendário semanal/mensal)
/patients                  → PatientList.tsx (aprimorada — existente)
/patients/:id              → PatientProfile.tsx (novo)
/patients/:id/encounter    → EncounterView.tsx (existente + melhorias)
/assistant                 → AIAssistant.tsx (SLM standalone)
/profile                   → MyProfile.tsx
/unauthorized              → UnauthorizedPage.tsx
```

---

## 3. AppShell

**Arquivo:** `src/components/AppShell.tsx`

```tsx
import { AppShell, NavLink, Group, Avatar, Text, Badge } from '@mantine/core'
import { IconHome, IconCalendar, IconUsers, IconRobot,
         IconClipboard, IconSettings } from '@tabler/icons-react'
import { useAuth } from 'react-oidc-context'
import { useNavigate, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/dashboard',  icon: IconHome,      label: 'Início' },
  { path: '/agenda',     icon: IconCalendar,  label: 'Agenda' },
  { path: '/patients',   icon: IconUsers,     label: 'Pacientes' },
  { path: '/assistant',  icon: IconRobot,     label: 'Assistente IA' },
  { path: '/profile',    icon: IconSettings,  label: 'Meu Perfil' },
]

export function ClinicoShell({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const name = auth.user?.profile?.name ?? 'Clínico'
  const tenant = auth.user?.profile?.['tenant_slug'] ?? ''

  return (
    <AppShell navbar={{ width: 220, breakpoint: 'sm' }} padding="md">
      <AppShell.Navbar p="xs">
        <Group mb="md" px="xs">
          <Avatar radius="xl" color="blue">{name[0]}</Avatar>
          <div>
            <Text size="sm" fw={500}>{name}</Text>
            <Badge size="xs" color="gray">{tenant}</Badge>
          </div>
        </Group>
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            label={item.label}
            leftSection={<item.icon size={18} />}
            active={location.pathname.startsWith(item.path)}
            onClick={() => navigate(item.path)}
            mb={4}
          />
        ))}
        <NavLink
          label="Sair"
          mt="auto"
          onClick={() => auth.signoutRedirect()}
          color="red"
        />
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
```

---

## 4. Role Guard

**Arquivo:** `src/auth/RoleGuard.tsx`

```tsx
import { useAuth } from 'react-oidc-context'
import { Navigate } from 'react-router-dom'

export function RoleGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  if (auth.isLoading) return <div>Verificando permissões...</div>
  if (!auth.isAuthenticated) {
    auth.signinRedirect()
    return null
  }
  const roles: string[] = auth.user?.profile?.realm_access?.roles ?? []
  if (!roles.includes('CLINICO') && !roles.includes('PLATFORM_ADMIN')) {
    return <Navigate to="/unauthorized" replace />
  }
  return <>{children}</>
}
```

**Aplicar em `App.tsx`:**
```tsx
<RoleGuard>
  <ClinicoShell>
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
      {/* ... demais rotas ... */}
    </Routes>
  </ClinicoShell>
</RoleGuard>
```

---

## 5. Componentes por Página

### Dashboard.tsx

```tsx
// Hooks:
//   useMyAgenda(today) → GET /cuidado/my-agenda?date=2026-03-14
//
// Layout:
//   <Title>Minha Agenda — {formatDate(today)}</Title>
//   <Badge color="blue">{agenda.length} consultas hoje</Badge>
//   <Badge color="red">{pendentes} sem nota fechada</Badge>
//
// Lista de agendamentos:
//   <Card> por item:
//     horário + nome paciente + tipo (badge) + status (badge)
//     Botão "Atender" → navigate(`/patients/${patient_id}/encounter`)
//
// Sem agendamentos: <Text>Nenhum agendamento para hoje.</Text>
```

### Agenda.tsx

```tsx
// @mantine/dates <Calendar> (mensal) + lista lateral por dia selecionado
// Hook: useMyAgenda({ from, to }) → intervalo do mês visível
// Click em dia → seleciona → lista eventos na lateral
// Click em evento → navigate para encounter ou patient profile
// Filtro: Select de tipo (todos / consulta / retorno / exame)
```

### PatientList.tsx (aprimorada)

```tsx
// MANTER código atual (busca + tabela)
// ADICIONAR colunas: última consulta, programas (badges)
// ADICIONAR paginação: <Pagination> Mantine com page/size
// MUDAR onClick → navigate(`/patients/${p.id}`) (antes era /encounter/:id)
// Hook atualizado: usePatients(search, page) → /cuidado/patients?q=...&page=...&size=20
```

### PatientProfile.tsx (novo)

```tsx
// Tabs Mantine: Resumo | Atendimentos | Documentos
//
// Aba Resumo:
//   Grid 2 colunas:
//     Esquerda: dados cadastrais (read-only)
//     Direita: Alergias (Textarea editável) + Medicações (Textarea editável)
//              Botão Salvar → PATCH /cuidado/patients/:id/clinical
//   Programas inscritos: badges coloridos
//
// Aba Atendimentos:
//   Timeline de encontros passados
//   Botão "Novo Atendimento" → navigate(`/patients/${id}/encounter`)
//
// Aba Documentos:
//   Lista de docs RAG do paciente (read-only)
```

### EncounterView.tsx (melhorias sobre o existente)

```tsx
// MANTER: SOAP Textarea + addNote + closeEncounter + SLMAssistant
//
// ADICIONAR:
//   1. Breadcrumb: <Breadcrumbs> Pacientes > {nome} > Atendimento
//   2. CID-10 Autocomplete:
//        <Autocomplete
//          label="CID-10"
//          data={cids.map(c => ({ value: c.code, label: `${c.code} — ${c.description}` }))}
//          onChange={setCid10}
//        />
//        Hook: useCid10Search(query) → GET /cuidado/cid10?q=...
//   3. Campo Prescrição: <Textarea label="Prescrição" />
//   4. Salvar CID + prescrição: PATCH /cuidado/encounters/:id
//   5. Confirmação ao fechar: <Modal> com resumo (CID, prescrição, notas)
```

### AIAssistant.tsx (página standalone)

```tsx
// Página dedicada — SLMAssistant sem contexto de encontro
// Chat interface:
//   - Histórico de mensagens em memória (useState, sem localStorage)
//   - Input com botão enviar + Enter
//   - Chips de sugestão rápida:
//       "Diagnóstico diferencial" | "Protocolo de tratamento"
//       "Resumo clínico" | "Interação medicamentosa"
//   - Indicador do modelo: badge "llama3.2:1b" (lido de GET /slm/models)
//   - SSE streaming: mesma lógica do SLMAssistant.tsx existente
```

---

## 6. Hooks a criar/atualizar

```
src/hooks/
  useMyAgenda.ts       → GET /cuidado/my-agenda
  usePatientProfile.ts → GET /cuidado/patients/:id/profile
                         PATCH /cuidado/patients/:id/clinical
  useCid10Search.ts    → GET /cuidado/cid10?q=...
  useAIAssistant.ts    → SSE POST /slm/chat (sem contexto de encontro)
```

Atualizar `usePatients.ts` para suportar paginação (`page`, `size`).
Atualizar `useEncounters.ts` para incluir PATCH (CID + prescrição).

---

## 7. Checklist de Entrega

- [ ] `AppShell` com sidebar em todas as páginas
- [ ] `RoleGuard` — bloqueia sem role `CLINICO`
- [ ] `Dashboard` — lista agenda do dia com botão "Atender"
- [ ] `Agenda` — calendário mensal + lista lateral
- [ ] `PatientList` — paginada + cols adicionais
- [ ] `PatientProfile` — 3 abas (Resumo / Atendimentos / Documentos)
- [ ] `EncounterView` — CID-10 autocomplete + prescrição + confirmação de fechamento
- [ ] `AIAssistant` — página standalone com histórico em memória
- [ ] `MyProfile` — nome, especialidade, preferências
- [ ] Novos endpoints backend: `/my-agenda`, `/profile`, `/clinical`, `/cid10`
- [ ] Migration: `ALTER TABLE patients ADD allergies, medications`
- [ ] Build sem erros TypeScript: `npm run build`
- [ ] Build copiado para `static/clinico-ui/`
- [ ] Commit: `feat(DEM-020): clinico frontend completo`

---

## 8. Ordem de implementação sugerida

1. AppShell + RoleGuard + rotas (habilita navegação entre todas as páginas)
2. Dashboard + useMyAgenda (endpoint /my-agenda no backend)
3. PatientProfile + campos clínicos (allergies/medications)
4. EncounterView melhorias (CID-10, prescrição)
5. Agenda (calendário)
6. AIAssistant standalone
7. MyProfile
8. Build + testes
