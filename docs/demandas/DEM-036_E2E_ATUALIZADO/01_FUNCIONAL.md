# DEM-036 — E2E Atualizado — Cobertura DEM-029, DEM-026, DEM-027, DEM-028, DEM-030, DEM-032, DEM-035

## Objetivo

Ampliar a suíte de testes E2E para cobrir as funcionalidades entregues nas DEMs 026–035 que ficaram sem cobertura automatizada. Ao final desta DEM, todas as funcionalidades críticas do produto devem ter pelo menos um teste automatizado que prove que estão funcionando de ponta a ponta.

---

## Contexto

A DEM-024 estabeleceu a base E2E com 13 testes (4+3+3+3 por módulo). Desde então foram entregues 9 DEMs que adicionaram endpoints, páginas e comportamentos sem cobertura E2E correspondente. Esta DEM fecha essa lacuna antes de produção.

---

## O que está sem cobertura hoje

| DEM | Funcionalidade | Tipo de teste a criar |
|-----|---------------|----------------------|
| DEM-026 | Módulo notificações — CRUD + SSE | Pytest (API) |
| DEM-027 | Endpoints PDF — retornam application/pdf | Pytest (API) |
| DEM-028 | Grafana alerting — 9 regras ativas | Pytest (API externa) |
| DEM-029 | Confirm/cancel agendamento — 404 para paciente errado | Pytest (API) |
| DEM-030 | Servidores, Módulos, Financeiro admin — páginas novas | Playwright (AdminUI) |
| DEM-032 | Grupos, Profissionais, Equipe Clínica — páginas novas | Playwright (ClinicoUI) |
| DEM-035 | Sino de notificações — badge visível no header | Playwright (4 módulos) |

---

## Comportamentos esperados

### Testes Pytest (API)

**DEM-026 — Notificações:**
- `POST /notifications/` com token válido cria notificação e retorna 201 com `id`
- `GET /notifications/` retorna lista (pode estar vazia mas responde 200)
- `PATCH /notifications/{id}/read` retorna 200 e `is_read: true`
- `DELETE /notifications/{id}` retorna 204
- `GET /notifications/stream` com token válido retorna `Content-Type: text/event-stream`

**DEM-027 — Relatórios PDF:**
- `GET /reports/admin/tenants` com admin token retorna 200 e `Content-Type: application/pdf`
- `GET /reports/gestor/appointments` com gestor token retorna 200 e `Content-Type: application/pdf`
- `GET /reports/clinico/patients` com clinico token retorna 200 e `Content-Type: application/pdf`
- Acesso sem token retorna 401; acesso com role errado retorna 403

**DEM-028 — Grafana alertas:**
- `GET http://localhost:3000/api/v1/provisioning/alert-rules` retorna 200 e lista com pelo menos 9 regras

**DEM-029 — Agendamento:**
- `PATCH /cuidado/appointments/{id_inexistente}/confirm` com token de paciente retorna 404
- `PATCH /cuidado/appointments/{id_inexistente}/cancel` com token de paciente retorna 404

### Testes Playwright

**AdminUI (DEM-030):**
- Navegar para Servidores → URL contém `/servers`
- Navegar para Módulos → URL contém `/modules`
- Navegar para Financeiro → URL contém `/financeiro`
- Navegar para Usuários Admin → URL contém `/users`

**ClinicoUI (DEM-032):**
- Navegar para Grupos → URL contém `/groups`
- Navegar para Profissionais → URL contém `/professionals`
- Navegar para Equipe → URL contém `/clinical-users`

**GestorUI (DEM-027):**
- Navegar para Relatórios → URL contém `/relatorios` → página carrega sem erro

**NotificationBell (DEM-035) — verificação de presença:**
- AdminUI: após login, `[aria-label="Notificações"]` está visível no header
- GestorUI: após login, `[aria-label="Notificações"]` está visível no header
- ClinicoUI: após login, `[aria-label="Notificações"]` está visível no header
- PacienteUI: após login, `[aria-label="Notificações"]` está visível no header

---

## Critérios de aceitação

1. `pytest tests/e2e/ -m e2e -q` → todos os novos testes passam
2. `npx playwright test` → todos os novos testes passam (incluindo os 13 existentes)
3. Total de testes pytest E2E: ≥ 18 (eram 8 + 5 novos para DEM-026/027/028/029)
4. Total de testes Playwright: ≥ 24 (eram 13 + 11 novos)
5. Tempo total de execução Playwright não ultrapassa 3 minutos com 4 workers

---

## O que NÃO está no escopo

- Testes de carga ou performance
- Testes de acessibilidade
- Testes de SSE em tempo real via Playwright (complexidade alta, ROI baixo para agora)
- Cobertura de todos os endpoints (apenas os críticos de cada DEM)
