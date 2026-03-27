# IntelliCare V3 — Plano de Validação Staging

> **Data:** 2026-03-25 | **Executor:** Eduardo (ARQUITETO)
> **Ambiente:** Staging — `https://*.intellicare.ia.br`
> **Profundidade:** Smoke + fluxo principal por área
> **Legenda:** `[ ]` pendente · `[x]` OK · `[!]` falhou / precisa atenção

---

## Credenciais de acesso

| Serviço | URL | Usuário | Senha |
|---------|-----|---------|-------|
| pgAdmin | `http://[VPS]:5050` ou porta mapeada | (ver .env.staging) | — |
| Keycloak Admin | `https://auth.intellicare.ia.br/admin/` | `admin` | (ver KC_ADMIN_PASSWORD) |
| AdminUI | `https://admin.intellicare.ia.br/admin-ui/` | `platform-admin` | `Admin@2025!` |
| GestorUI | `https://api.intellicare.ia.br/gestor-ui/` | `gestor.alfa` | `Demo@1234` |
| ClinicoUI | `https://api.intellicare.ia.br/clinico-ui/` | `dr.silva` | `Demo@1234` |
| PacienteUI | `https://api.intellicare.ia.br/paciente-ui/` | `paciente.alfa` | `Demo@1234` |
| Grafana | `http://[VPS]:3000` | `admin` | (ver GF_ADMIN_PASSWORD) |
| API direta | `https://api.intellicare.ia.br` | — | (token via Keycloak) |

---

## 1. PostgreSQL — Estrutura e Acesso

### 1.1 Acesso via pgAdmin
- [x] pgAdmin carrega sem erro
- [x] Conexão ao servidor `postgres` estabelecida
- [x] Database `intellicare_staging` visível

### 1.2 Schema `public` — tabelas de plataforma
- [x] `public.tenants` — listagem de tenants cadastrados (campo `status`: active/suspended)
- [x] `public.prompt_templates` — 4 seeds ativos; coluna chave: `prompt_key` (não `name`) — DEM-093 ✅

### 1.2b Schema `platform` — identidade centralizada (ADR-004)
- [x] `platform.pessoa` — tabela existe (021 reaplicada após criação manual de schema) — DEM-093 ✅
- [x] `platform.pessoa_fisica` — tabela existe — DEM-093 ✅
- [x] `platform.keycloak_user_mapping` — migration 025 aplicada no VPS em 2026-03-26 (`sub + realm -> pessoa_id`) — rerun formal 1.2b ✅

### 1.3 Schema tenant — tabelas clínicas
Schema `tenant_clinica_alfa` (DEM-093 aplicada em 2026-03-26):
- [x] `professionals` — tabela existe (migration 005) — DEM-093 ✅
- [x] `professionals` — coluna `pessoa_id UUID` presente (migration 024) — DEM-093 ✅
- [x] `patients` — coluna `pessoa_id UUID` presente (migration 022) — DEM-093 ✅
- [x] `clinical_notes` — tabela Florence existe (migration 013)
- [x] `clinical_notes` — coluna `encounter_id` tipo `uuid` — migration 023 aplicada — DEM-093 ✅
- [x] `prescriptions` — coluna `interaction_warnings_count INTEGER DEFAULT 0` — DEM-093 ✅
- [x] `professional_certificates` — tabela existe (migration 019) — DEM-093 ✅
- [x] `push_subscriptions` — tabela notificações PWA (migration 016)

### 1.4 Backup
- [x] Comando de backup executável:
```bash
docker exec intellicare-postgres pg_dump \
  -U intellicare_staging intellicare_staging \
  -Fc -f /tmp/backup_$(date +%Y%m%d).dump
docker cp intellicare-postgres:/tmp/backup_$(date +%Y%m%d).dump ./
```
- [x] Arquivo `.dump` gerado com tamanho > 0

---

## 2. Keycloak — Administração e Roles

### 2.1 Acesso ao Admin Console
- [x] `https://auth.intellicare.ia.br/admin/` → carrega Keycloak Admin Console (302 redirect confirmado — DEM-INF ✅)
- [x] Login com credenciais admin
- [x] Realm `intellicare` selecionado

### 2.2 Roles definidas
- [x] Role `PLATFORM_ADMIN` existe em Realm Roles
- [x] Role `TENANT_GESTOR` existe
- [x] Role `CLINICO` existe
- [x] Role `PACIENTE` existe

### 2.3 Usuários e atribuições
- [x] `platform-admin` → role `PLATFORM_ADMIN` atribuída
- [x] `gestor.alfa` → role `TENANT_GESTOR` atribuída
- [x] `dr.silva` → role `CLINICO` atribuída
- [x] `paciente.alfa` → role `PACIENTE` atribuída

### 2.4 Clients registrados
- [x] `admin-cli` (Keycloak admin CLI)
- [x] `admin-ui` (frontend AdminUI)
- [x] `clinico-ui` (frontend ClinicoUI)
- [x] `gestor-ui` (frontend GestorUI)
- [x] `paciente-ui` (frontend PacienteUI)
- [x] `intellicare-frontend` (frontend genérico)
- [x] `intellicare-service` (backend service account)
- [x] `portal` (Portal público)

### 2.5 JWT Issuer
- [x] `GET https://auth.intellicare.ia.br/realms/intellicare/.well-known/openid-configuration` → 200
- [x] Campo `issuer`: `https://auth.intellicare.ia.br/realms/intellicare` — DEM-INF ✅ (`1fa8b8d`)

---

## 3. AdminUI — Administração da Plataforma

> URL: `https://admin.intellicare.ia.br/admin-ui/` | Login: `platform-admin`

### 3.1 Acesso
- [x] Login bem-sucedido → **fix aplicado** (`c4ceaee`) — `.env.production` criado, rebuild via Docker Compose no VPS
  - Bundle confirmado: `authority:"https://auth.intellicare.ia.br/realms/intellicare"` ✅
- [x] Menu lateral visível: Tenants, Modules, Users, Prompts, Identity

### 3.2 Tenants
- [x] Lista de tenants carrega (GET /admin/tenants → 200)
- [x] Tenant `alfa` aparece com status `active`
- [x] Ação **Suspender** tenant → status muda para `suspended`
- [x] Ação **Reativar** tenant → status volta para `active`

### 3.3 Módulos
- [x] Página de módulos carrega
- [x] Toggle de módulo funciona (enable/disable)

### 3.4 Usuários Admin
- [x] Lista de usuários admin carrega
- [x] Campo de senha admin editável

### 3.5 Prompt Templates
- [!] Lista de templates carrega (migration 017)
- [!] Versão atual visível
- [!] Rollback para versão anterior disponível

### 3.6 Identidade Centralizada (DEM-089)
- [x] Página `/admin-ui/identity` carrega
- [x] Cards de totais: total pessoas, vínculos por tenant
- [!] Tabela por tenant com pacientes e profissionais vinculados
- [!] Botão "Reconciliar identidades" presente
- [!] Clicar reconciliar → retorna JSON `{"processed": N, "linked": N, "skipped": 0, "errors": []}`

---

## 4. GestorUI — Gestão do Estabelecimento

> URL: `https://gestor.intellicare.ia.br/gestor-ui/` | Login: `gestor.alfa`

### 4.1 Acesso
- [!] Login bem-sucedido → dashboard carrega
- [ ] Menu lateral: Dashboard, Unidades, Usuários, CarePlanner, Indicadores, Relatórios

### 4.2 Dashboard principal
- [ ] KPIs clínicos carregam (DEM-081): encontros, notas, prescrições, interações, jornadas

### 4.3 Unidades / Estabelecimentos
- [ ] Lista de unidades carrega (`GET /admin/units`)
- [ ] Detalhe de unidade abre
- [ ] Lista de usuários do tenant visível

### 4.4 CarePlanner (Gestor)
- [ ] Lista de jornadas carrega
- [ ] Criar nova jornada → modal abre, canal selecionável (WA/Email/SMS)
- [ ] Jornada criada aparece na lista com status DISPATCHED ou SENT

### 4.5 Indicadores (DEM-081)
- [ ] Página `/indicadores` carrega
- [ ] Filtro por período funciona
- [ ] Gráfico de interações por dia renderiza

### 4.6 Relatório PDF de jornada (DEM-052)
- [ ] Abrir jornada existente → botão PDF visível
- [ ] Clicar → PDF abre em nova aba com dados preenchidos

---

## 5. ClinicoUI — Módulo Clínico

> URL: `https://api.intellicare.ia.br/clinico-ui/` | Login: `dr.silva`

### 5.1 Acesso
- [ ] Login bem-sucedido → dashboard carrega
- [ ] Menu: Dashboard, Agenda, Pacientes, CarePlanner

### 5.2 Lista de pacientes
- [ ] Lista carrega com pacientes cadastrados
- [ ] Busca por nome funciona

### 5.3 Perfil do paciente
- [ ] Abrir paciente → perfil carrega (PessoaFísica, diagnósticos, histórico)
- [ ] Linha do Tempo (DEM-071) carrega: encounters + notes + prescriptions + journeys em UNION

### 5.4 Encontro clínico
- [ ] Criar novo encontro → modal/página abre
- [ ] **Florence — Notas SOAP** (DEM-055/057):
  - [ ] Aba "Notas Florence" presente em EncounterView
  - [ ] Campo SOAP editável
  - [ ] Botão "Sugestão IA" → retorna sugestão (rule-based ou LLM)
- [ ] Salvar nota → persiste e aparece na timeline

### 5.5 Receituário Oswaldo (DEM-058/061)
- [ ] Aba Oswaldo presente
- [ ] Busca CID-10 funciona
- [ ] Adicionar medicamento → campo de posologia editável
- [ ] **Alerta de interação** (DEM-077): adicionar 2 medicamentos com interação → banner colorido aparece
- [ ] Botão "Sugestão IA" Oswaldo → retorna sugestão
- [ ] Gerar PDF receituário → PDF abre com dados do médico + template CFM/ANVISA

### 5.6 Assinatura digital (DEM-080)
- [ ] Seção "Certificado Digital" no perfil → upload `.pfx` disponível
- [ ] (Smoke apenas — não é necessário ter certificado real)

### 5.7 PDF clínico do encontro (DEM-062)
- [ ] Botão PDF no EncounterView → PDF com Florence + Oswaldo gerado

### 5.8 CarePlanner ClinicoUI (DEM-045)
- [ ] Página CarePlanner carrega com filtro "Minhas jornadas"
- [ ] Badge de jornadas REPLIED no sino de notificações

---

## 6. PacienteUI / Portal — Módulo Paciente

> URL: `https://api.intellicare.ia.br/paciente-ui/` | Login: `paciente.alfa`

### 6.1 Acesso
- [ ] Login bem-sucedido → home carrega

### 6.2 Meu Histórico (DEM-076)
- [ ] Página carrega com encontros passados
- [ ] Notas Florence visíveis (sem partes internas SOAP-A)
- [ ] Prescrições listadas

### 6.3 Baixar receituário (DEM-076)
- [ ] Clicar "Baixar Receituário" em uma prescrição → PDF abre

### 6.4 Minhas Jornadas (DEM-059)
- [ ] Lista de jornadas CarePlanner do paciente carrega
- [ ] Status de cada jornada visível

### 6.5 Notificações PWA (DEM-066)
- [ ] Sino de notificações visível
- [ ] Toggle push notification disponível (subscribe/unsubscribe)

---

## 7. APIs críticas — Validação direta

> Executar via curl ou Postman com token Bearer de `platform-admin`

### 7.1 Health e serviço
```bash
curl https://api.intellicare.ia.br/health
```
- [ ] Retorna `{"status": "ok"}` ou similar

### 7.2 Health adapters (DEM-051)
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.intellicare.ia.br/health/adapters
```
- [ ] Retorna status de RC, Evolution, Listmonk, Jasmin

### 7.3 Identity endpoints (DEM-083/084/088/089)
```bash
# Criar/encontrar pessoa por CPF
curl -X POST https://api.intellicare.ia.br/identity/pessoas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cpf":"123.456.789-09","nome_completo":"Teste Validacao","data_nascimento":"1990-01-01"}'
```
- [ ] Retorna 201 (criado) ou 200 (já existia — idempotente)

```bash
# Stats de identidade
curl -H "Authorization: Bearer $TOKEN" \
  https://api.intellicare.ia.br/identity/admin/stats
```
- [ ] Retorna totais de pessoas, vínculos, cobertura por tenant

### 7.4 Reconciliação (DEM-089)
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://api.intellicare.ia.br/identity/admin/reconcile?scope=all"
```
- [ ] Retorna `{"processed": N, "linked": N, "skipped": 0, "errors": []}`

---

## 8. Dashboards — Grafana e Observabilidade

> Grafana: `http://[VPS]:3000` (ou porta configurada)

### 8.1 Acesso
- [ ] Login Grafana → home carrega
- [ ] 5 targets UP no Prometheus (ver `http://[VPS]:9090/targets`)

### 8.2 Dashboards existentes
- [ ] **IntelliCare Overview** — panels: requests/s, latência, erros
- [ ] **CarePlanner Overview** (DEM-043):
  - [ ] Disparos por canal (WA/Email/SMS)
  - [ ] REPLIED/h
  - [ ] Videoconsultas ativas
  - [ ] p95 DISPATCHED→SENT
- [ ] **KPIs Clínicos** — prescrições, interações, notas Florence
- [ ] **Alertas configurados** (DEM-028) — regras visíveis em Alerting → Rules

### 8.3 Métricas CarePlanner (DEM-043)
```bash
# Verificar métrica diretamente no Prometheus
curl http://[VPS]:9090/api/v1/query?query=careplanner_dispatch_total
```
- [ ] Retorna séries com label `channel`

---

## 9. Históricos, Logs e Infraestrutura

### 9.1 Logs do serviço principal
```bash
docker logs intellicare-service --tail 50 2>&1 | grep -E "ERROR|WARNING|startup"
```
- [ ] Nenhum ERROR crítico no startup
- [ ] Log mostra módulos carregados (identity, cuidado, admin, etc.)

### 9.2 Containers em execução
```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml ps
```
- [ ] `intellicare-service` → Up (healthy)
- [ ] `keycloak` → Up (healthy)
- [ ] `postgres` → Up (healthy)
- [ ] `redis` → Up
- [ ] `traefik` → Up

### 9.3 Kestra — Flows ativos (DEM-039/067)
- [ ] Acessar Kestra UI (porta configurada)
- [ ] Flows presentes: `jornada_basica`, `jornada_video`, `fallback_canal`, `retry_backoff`
- [ ] Último trigger de flow sem erro

### 9.4 Evolution API — WhatsApp (DEM-047/053)
```bash
curl http://localhost:8082/instance/fetchInstances \
  -H "apikey: $EVOLUTION_KEY"
```
- [ ] Instância `intellicare` com `state: open`

### 9.5 Certificado SSL / Traefik
- [ ] `https://admin.intellicare.ia.br` → cadeado verde (Let's Encrypt válido)
- [ ] `https://api.intellicare.ia.br` → cadeado verde
- [ ] `https://auth.intellicare.ia.br` → cadeado verde

---

## Resumo de resultados

> Preencher ao final de cada seção

| Área | Total itens | ✅ OK | ❌ Falhou | ⚠️ Parcial | Observação |
|------|-------------|-------|-----------|-----------|------------|
| 1. PostgreSQL | 14 | | | | |
| 2. Keycloak | 15 | | | | |
| 3. AdminUI | 16 | | | | |
| 4. GestorUI | 11 | | | | |
| 5. ClinicoUI | 18 | | | | |
| 6. PacienteUI | 7 | | | | |
| 7. APIs críticas | 8 | | | | |
| 8. Dashboards | 10 | | | | |
| 9. Infraestrutura | 11 | | | | |
| **Total** | **110** | | | | |

---

## Issues encontrados

> Registrar aqui qualquer item que falhou ou precisa de atenção

| # | Área | Item | Sintoma | Ação |
|---|------|------|---------|------|
| 1 | 3. AdminUI | 3.1 Login loop | `GET /admin-ui/undefined/realms/...` 404 — VITE_KEYCLOAK_URL undefined no bundle | ✅ Fix `c4ceaee` — `.env.production` + rebuild Docker |
| 2 | 3. AdminUI | 3.2 API Tenants falha  | `list_tenants` falhava com 500 silencioso devido a falta de `deleted_at` na API  | ✅ Fix: Migration 026 aplicada p/ ADD COLUMN `deleted_at` em `public.tenants` |

---

*Gerado pelo ARQUITETO — IntelliCare V3 — 2026-03-25*
