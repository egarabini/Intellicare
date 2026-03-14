# DEM-022 — Portal do Paciente — Especificação Técnica

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 18 + Vite + Mantine UI 7 |
| Auth | react-oidc-context — role `PACIENTE` |
| HTTP | axios — `baseURL: ''` (paths relativos) |
| Token | tokenRef.ts (padrão do projeto — copiar de AdminUI) |
| Build | `npm run build` → `static/paciente-ui/` |
| Dev | porta `5177`, client_id Keycloak: `paciente-ui` |

---

## 1. Criar o projeto frontend

```bash
cd frontend/
npm create vite@latest PacienteUI -- --template react-ts
cd PacienteUI
npm install @mantine/core @mantine/hooks @mantine/notifications \
  @tanstack/react-query axios react-router-dom react-oidc-context \
  oidc-client-ts @tabler/icons-react
```

`vite.config.ts` — configurar base e outDir:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/paciente-ui/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/paciente-ui',
    emptyOutDir: true,
  },
})
```

---

## 2. Novos Endpoints Backend (módulo cuidado)

> Arquivo: `packages/intellicare-core/intellicare_core/modules/cuidado/router.py`
> Todos requerem role `PACIENTE`. O `patient_id` é lido do atributo `patient_id` do JWT
> (ou buscado via `user_id` no Keycloak — usar `sub` como chave).

### 2.1 Painel do paciente

```
GET /cuidado/paciente/painel
```

```json
{
  "patient_name": "João Silva",
  "next_appointment": {
    "scheduled_at": "2026-03-20T09:00:00Z",
    "clinician_name": "Dr. Carlos Silva",
    "type": "retorno"
  },
  "clinic_notice": "Lembre-se de trazer seus exames na próxima consulta.",
  "upcoming_count": 2,
  "past_count": 12
}
```

### 2.2 Agendamentos do paciente

```
GET  /cuidado/paciente/appointments?status=upcoming|past
PATCH /cuidado/paciente/appointments/{appt_id}/confirm
DELETE /cuidado/paciente/appointments/{appt_id}   # cancela
```

### 2.3 Histórico clínico (resumo — sem notas SOAP)

```
GET /cuidado/paciente/history?page=1&size=10
```

```json
{
  "items": [
    {
      "id": "uuid",
      "date": "2026-02-10",
      "clinician_name": "Dr. Carlos Silva",
      "type": "consulta",
      "cid10_code": "E11",
      "cid10_description": "Diabetes mellitus tipo 2",
      "prescription": "Metformina 500mg 1x/dia"
    }
  ],
  "total": 12, "page": 1, "size": 10
}
```

> **Não retornar** o campo `notes` (conteúdo SOAP) — privacidade clínica.

### 2.4 Meus programas

```
GET /cuidado/paciente/programs
```

### 2.5 Meus dados (atualizar e-mail/telefone)

```
GET   /cuidado/paciente/me
PATCH /cuidado/paciente/me
```

PATCH aceita apenas: `{ "email": "string", "phone": "string" }`.
CPF, nome e data de nascimento são read-only.

### 2.6 Dados da clínica

```
GET /cuidado/paciente/clinic-info
```

Retorna dados públicos do tenant: nome, telefone, endereço, e-mail, horário.

---

## 3. Keycloak — Client `paciente-ui`

Executar `setup_keycloak.py` com adição do novo client. Ou criar manualmente:

```python
ensure_client(kc, "paciente-ui", {
    "clientId": "paciente-ui",
    "name": "Paciente UI",
    "enabled": True,
    "publicClient": True,
    "standardFlowEnabled": True,
    "redirectUris": [
        "http://localhost:5177/*",
        "http://localhost:9000/paciente-ui/*",
        "http://127.0.0.1:9000/paciente-ui/*"
    ],
    "webOrigins": ["http://localhost:5177", "http://localhost:9000", "http://127.0.0.1:9000"],
    "protocolMappers": [realm_roles_mapper_payload(), tenant_id_mapper_payload()],
})
```

---

## 4. Estrutura de Arquivos

```
frontend/PacienteUI/src/
  auth/
    AuthProvider.tsx     # OIDC config, client_id: paciente-ui
    tokenRef.ts          # copiar de AdminUI
  api/
    client.ts            # axios, baseURL: '', usa getToken()
  hooks/
    usePaciente.ts       # todos os hooks de dados do paciente
  pages/
    PainelPage.tsx       # F01 — painel inicial
    AgendaPage.tsx       # F02 — meus agendamentos
    HistoricoPage.tsx    # F03 — histórico clínico
    ProgramasPage.tsx    # F04 — meus programas
    CadastroPage.tsx     # F05 — meus dados
    ContatoPage.tsx      # F06 — dados da clínica
  App.tsx                # rotas + AppShell + role guard PACIENTE
  main.tsx
```

---

## 5. App.tsx — estrutura principal

```tsx
// Role guard: verifica roles.includes('PACIENTE')
// AppShell com navbar lateral simples:
//   🏠 Meu Painel       → /
//   📅 Minha Agenda     → /agenda
//   📋 Meu Histórico    → /historico
//   💊 Meus Programas   → /programas
//   👤 Meu Cadastro     → /cadastro
//   🏥 Contato          → /contato

// Token síncrono no corpo do componente:
//   setToken(auth.user?.access_token ?? null)
```

---

## 6. Registrar no main.py

Em `packages/intellicare-core/intellicare_core/main.py`, adicionar servição do static:

```python
app.mount(
    "/paciente-ui",
    StaticFiles(directory=str(STATIC_DIR / "paciente-ui"), html=True),
    name="paciente-ui",
)
```

---

## 7. Checklist de Entrega

- [ ] `npm create vite` + dependências instaladas
- [ ] `vite.config.ts` com base `/paciente-ui/` e outDir correto
- [ ] Client `paciente-ui` criado no Keycloak
- [ ] 6 endpoints backend implementados (prefixo `/cuidado/paciente/`)
- [ ] 6 páginas React implementadas
- [ ] Role guard: bloqueia sem role `PACIENTE`
- [ ] Token síncrono (tokenRef.ts)
- [ ] Build sem erros: `npm run build`
- [ ] `app.mount` no `main.py`
- [ ] Acessível em `http://127.0.0.1:9000/paciente-ui/`
- [ ] Login com `paciente.alfa` / `Demo@1234` funciona
- [ ] Commit: `feat(DEM-022): paciente portal completo`
