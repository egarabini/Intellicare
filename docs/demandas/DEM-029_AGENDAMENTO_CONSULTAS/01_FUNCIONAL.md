# DEM-029 — Agendamento de Consultas (Integração ClinicoUI + PacienteUI)

## Objetivo

Fechar o ciclo de agendamento entre o profissional de saúde (ClinicoUI) e o paciente (PacienteUI), garantindo que as ações de confirmação/cancelamento de consulta sejam visíveis e consistentes nos dois módulos em tempo real.

---

## Contexto

O backend de agendamento (`/cuidado/appointments`) já existia. O gap era na integração: o portal do paciente não resolvia corretamente o usuário logado em tenants com schema legado, não exibia o nome do profissional responsável, e os dois frontends tinham estado dessincronizado após confirmações/cancelamentos.

---

## Comportamento esperado

### Portal do Paciente (PacienteUI)

| Funcionalidade | Comportamento |
|----------------|---------------|
| Listar consultas | Exibe todas as consultas do paciente com nome do profissional responsável |
| Confirmar consulta | Atualiza status para `confirmed` e reflete imediatamente no painel |
| Cancelar consulta | Atualiza status para `cancelled` e remove do painel de próximas consultas |
| Erro em confirm/cancel | Exibe mensagem clara quando consulta não existe ou não pertence ao paciente (404) |
| Atualização automática | Agenda e painel atualizam periodicamente sem recarregar a página |

### Agenda Clínica (ClinicoUI)

| Funcionalidade | Comportamento |
|----------------|---------------|
| Listar agenda | Exibe consultas do dia com status atualizado (incluindo confirmações do paciente) |
| Filtro por status | Filtra por `scheduled`, `confirmed`, `cancelled`, `in_progress` |
| Resumo de status | Exibe totais: confirmados / cancelados / em atendimento |
| Data sem desvio | Datas exibidas em horário local (sem desvio de toISOString UTC) |
| Atualização automática | Agenda reflete confirmações/cancelamentos feitos pelo paciente |

---

## Correções de integridade no backend

| Problema | Correção |
|----------|----------|
| Schema legado com `patients.name` em vez de `patients.full_name` | Fallback automático: tenta `full_name`, cai em `name` |
| `user_id` sem registro em `patients` | Fallback por e-mail do token Keycloak |
| Confirm/cancel retornavam 500 para consultas inexistentes | Agora retornam 404 com mensagem clara |
| Nome do clínico não disponível no portal | Resolvido via `tenant_users` pelo `professional_id` |

---

## Critérios de aceitação

1. Paciente logado vê suas consultas com nome do profissional
2. Confirmar/cancelar consulta atualiza o painel imediatamente
3. Clínico vê confirmações/cancelamentos do paciente sem recarregar
4. Consultas inexistentes retornam 404 (não 500)
5. Datas exibidas em horário local correto
6. `pytest tests/test_cuidado_portal.py` → 3 passed
7. Build do ClinicoUI e PacienteUI sem erros
