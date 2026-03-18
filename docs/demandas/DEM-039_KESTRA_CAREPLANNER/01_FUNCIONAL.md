---
tipo: especificacao-funcional
demanda: DEM-039
titulo: Kestra Workflow CarePlanner
fase: 1
sprint: "4.1"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-17
depende_de: [DEM-038]
habilita: [DEM-040]
tags: [kestra, careplanner, workflow, orchestration, p0]
---

# DEM-039 — Kestra Workflow CarePlanner

## Objetivo

Completar o ciclo ponta a ponta da jornada conversacional do CarePlanner criando
os **workflows Kestra** que orquestram cada tipo de jornada. A DEM-038 construiu
toda a infraestrutura IntelliCare (tabelas, adapters, services, routes, workers,
métricas), mas não há nenhum flow Kestra definido — sem ele o motor está completo
porém nenhuma jornada real pode ser iniciada.

Esta DEM entrega: dois flows YAML provisionados no Kestra, um script de seed para
publicar os flows via API Kestra, um método `trigger_flow()` no `KestraAdapter`, e
um endpoint `POST /careplanner/journeys/trigger` que permite o GestorUI iniciar
jornadas sem precisar acessar o Kestra diretamente.

---

## Contexto

A DEM-038 construiu o seguinte ciclo esperado:

```
Kestra
  │ POST /careplanner/tasks/open   ← kestra_execution_id = execution.id
  ▼
IntelliCare (CREATED → DISPATCHED → SENT)
  │ dispatcher enfileira RC + aguarda MESSAGE_SENT webhook
  │ (nenhum resume Kestra no SENT — só interno)
  ▼
Paciente responde no Rocket.Chat
  │ webhook inbound → IntelliCare → SENT → REPLIED
  │ kestra.resume_execution(kestra_execution_id, {"content": reply})
  ▼
Kestra retoma → decide próximo passo
```

O lado IntelliCare está implementado e testado. O lado Kestra (o flow YAML) ainda
não existe. Atualmente não existe nenhuma forma de o GestorUI ou ClinicoUI iniciar
uma jornada — o endpoint `/tasks/open` requer um `kestra_execution_id` válido,
que só existe depois que o Kestra cria uma execution.

---

## Escopo

### O que está incluído

| Bloco | O que entrega | Por quê |
|-------|--------------|---------|
| 1 | `infra/kestra/flows/careplanner_jornada_basica.yml` | Flow single-turn: abre task, aguarda resposta do paciente, fecha task |
| 2 | `infra/kestra/flows/careplanner_jornada_video.yml` | Variante com videoconsulta: após resposta, abre sessão Jitsi antes de fechar |
| 3 | `infra/kestra/seed_flows.py` | Script que provisiona os dois flows no Kestra via API (idempotente) |
| 4 | `KestraAdapter.trigger_flow()` | Método que dispara uma nova execution Kestra via API |
| 5 | `POST /careplanner/journeys/trigger` | Endpoint para GestorUI/ClinicoUI iniciar jornadas sem acesso direto ao Kestra |
| 6 | Testes | 3 testes Python + 1 teste de integração local manual |

### O que NÃO está incluído

- Flows multi-turn (loop com mais de uma troca de mensagem) — próxima iteração
- Integração com Programas de Saúde (DEM-014) — depende de DEM-040
- UI no GestorUI para iniciar jornadas — DEM-040
- Autenticação avançada Kestra (básica está desabilitada em dev; produção usa reverse proxy)
- Flows para outros canais além do Rocket.Chat

---

## Critérios de Aceite

1. `python infra/kestra/seed_flows.py` executa sem erro e os dois flows aparecem
   em `GET /api/v1/flows/intellicare` com status `ENABLED`.
2. Chamar `POST /careplanner/journeys/trigger` com payload válido retorna `202` com
   `{ "execution_id": "...", "correlation_id": "...", "status": "CREATED" }`.
3. O flow `careplanner_jornada_basica` avança: task no IntelliCare transita
   CREATED → DISPATCHED → SENT → REPLIED → CLOSED sem intervenção manual.
4. O flow `careplanner_jornada_video` abre sessão Jitsi antes do CLOSED e retorna
   `patient_url` no output final.
5. Se o Pause do Kestra atingir timeout (72h), o flow termina em estado `FAILED`
   no Kestra (o IntelliCare já terá marcado a task como EXPIRED via expiry_worker).
6. `KestraAdapter.trigger_flow()` lança `httpx.HTTPStatusError` com status 4xx/5xx
   e o endpoint retorna `502` com `kestra_unavailable` para o chamador.
7. Todos os testes Python passam; nenhuma regressão nas suítes anteriores.

---

## Resultado Esperado

Ao final desta DEM, o clinician no GestorUI pode iniciar uma jornada conversacional
com um POST simples para o IntelliCare. O Kestra orquestra o ciclo completo de forma
assíncrona, retomando automaticamente quando o paciente responde via Rocket.Chat.
O ciclo end-to-end é testável no ambiente local com os 19 containers rodando.

---

## Notas para o Agente Desenvolvedor

- `kestra_execution_id` precisa ser passado para `open_task` logo no **início** do
  flow Kestra, usando `{{ execution.id }}`. Não existe outro momento para obtê-lo.
- O IntelliCare **não** chama `resume_execution` no evento SENT — apenas no REPLIED.
  O flow Kestra não precisa de um Pause para SENT; vai direto para aguardar REPLIED.
- Autenticação do flow com IntelliCare: usar **Kestra KV Store** com chave
  `intellicare_jwt_{tenant_slug}`. Não embutir tokens no YAML — isso quebraria
  multi-tenancy e vazaria secrets no repositório.
- O namespace Kestra padrão para IntelliCare é `intellicare.careplanner`.
- O `seed_flows.py` deve usar `PUT /api/v1/flows` (idempotente), não POST.
- O endpoint `/careplanner/journeys/trigger` requer role `GESTOR` ou `CLINICO`.
  Não expor para role `PACIENTE`.
