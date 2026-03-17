---
tipo: especificacao-funcional
demanda: DEM-038
titulo: CarePlanner Conversacional Multi-tenant
fase: 4
sprint: "4.1"
status: aprovada
planejador: PLANEJADOR
criado: 2026-03-17
revisado: 2026-03-17
depende_de:
  - DEM-003_INTELLICARE_CORE
  - DEM-025_OBSERVABILIDADE
  - DEM-026_NOTIFICACOES_REALTIME
habilita:
  - DEM-039_CAREPLANNER_BACKEND_MVP
tags:
  - fase-4
  - careplanner
  - conversacional
  - integracao
  - multi-tenant
  - lgpd
  - rocketchat
  - kestra
  - jitsi
---

# DEM-038 — CarePlanner Conversacional Multi-tenant

## Objetivo

Implementar, no IntelliCare, um módulo de jornada conversacional para pacientes
com envio e recebimento de mensagens (outbound/inbound) via **Rocket.Chat**,
rastreabilidade ponta a ponta (via **Kestra** como orquestrador de fluxos),
suporte a videoconsulta via **Jitsi**, isolamento por tenant e conformidade com
LGPD.

## Contexto

O IntelliCare V3 consolidou arquitetura modular em um único serviço Python,
com `ModuleLoader`, contratos `BaseModule` e multi-tenancy por schema.

O projeto CarePlanner (referência de estudo) demonstrou os padrões arquiteturais
corretos para fluxos conversacionais — `correlation_id` universal, ACK assíncrono
real, conversation pointer table, propagação de tenant via JWT — mas usava
ferramentas (n8n, Chatwoot) que **não fazem parte do stack IntelliCare**.

Esta DEM adapta esses padrões para o stack definido:

| Componente CarePlanner (referência) | Equivalente IntelliCare |
|-------------------------------------|-------------------------|
| n8n (workflow orchestrator) | **Kestra** |
| Chatwoot (messaging) | **Rocket.Chat** |
| Não havia videoconsulta | **Jitsi** |
| FastAPI backend | FastAPI (mesmo) |
| PostgreSQL | PostgreSQL (mesmo) |

## Stack de Integração

- **Rocket.Chat**: canal de mensagens texto com pacientes. IntelliCare publica
  mensagens via Rocket.Chat REST API e recebe eventos via webhook.
- **Kestra**: orquestrador de workflows de jornada. Kestra aciona IntelliCare
  via webhooks; IntelliCare expõe endpoints que Kestra chama em cada step.
- **Jitsi**: videoconsulta. IntelliCare gera links de sala autenticados e os
  entrega ao paciente via Rocket.Chat.

## Escopo

### Incluído

| Bloco | Entrega | Justificativa |
|-------|---------|---------------|
| 1 | Módulo `careplanner` com contrato `BaseModule` | Padrão arquitetural IntelliCare |
| 2 | API de abertura e consulta de jornada | Kestra inicia via webhook |
| 3 | API de callbacks de entrega (`MESSAGE_SENT`/`FAILED`) | Confirmação assíncrona real |
| 4 | API de webhook inbound (Rocket.Chat → IntelliCare) | Captura de resposta do paciente |
| 5 | Adaptador Rocket.Chat (publicar mensagem, criar sala, desativar) | Canal de mensagens |
| 6 | Adaptador Jitsi (gerar JWT de sala) | Videoconsultas |
| 7 | Persistência por tenant: `care_tasks`, `care_conversations`, `care_events`, `care_templates` | Estado consistente e auditável |
| 8 | Máquina de estados da jornada | Evitar falso positivo de falha |
| 9 | Idempotência por evento | Evitar duplicidade de processamento |
| 10 | Integração com módulos `notifications` e `cuidado` | Valor assistencial imediato |

### Não incluído nesta fase

- push mobile nativo (FCM/APNs);
- bot clínico autônomo para decisões críticas;
- campanha multicanal com AB test e recorrência complexa;
- integração simultânea com múltiplos provedores de mensageria;
- gravação de videoconsulta.

## Atores

| Ator | Papel |
|------|-------|
| `TENANT_GESTOR` | Configura templates, acompanha jornadas, gerencia salas Rocket.Chat do tenant |
| `CLINICO` | Aciona jornadas de cuidado, inicia videoconsultas Jitsi, acompanha respostas |
| Kestra | Orquestrador externo que dispara e retoma steps via webhook IntelliCare |
| Rocket.Chat | Canal de entrega e recepção de mensagens; publica webhook inbound |
| Jitsi | Provedor de sala de videoconsulta; IntelliCare gera JWT de acesso |
| Paciente | Recebe e responde mensagens no Rocket.Chat; entra em sala Jitsi via link |

## Casos de Uso Principais (MVP)

1. **CU-01 — Abrir jornada via Kestra**: Kestra aciona `POST /careplanner/tasks/open`
   com `patient_ref`, tipo de tarefa e template; IntelliCare gera `correlation_id`
   e retorna `202 Accepted`.

2. **CU-02 — Disparar mensagem via Rocket.Chat**: IntelliCare cria sala (se necessário)
   e envia mensagem via Rocket.Chat REST API; canal retorna `200` (aceite técnico);
   status da jornada vai para `DISPATCHED`.

3. **CU-03 — Confirmar entrega real**: Rocket.Chat ou worker interno dispara
   callback `MESSAGE_SENT`; IntelliCare grava `channel_conversation_id` (BIGINT)
   e avança para `SENT`.

4. **CU-04 — Receber resposta do paciente**: Rocket.Chat dispara webhook inbound;
   IntelliCare correlaciona pela sala/conversation_id; jornada avança para `REPLIED`;
   Kestra é notificado via webhook para retomar o fluxo.

5. **CU-05 — Agendar videoconsulta Jitsi**: CLINICO aciona `POST /careplanner/consultations/video`;
   IntelliCare gera JWT de sala Jitsi e envia o link ao paciente via Rocket.Chat.

6. **CU-06 — Fechar jornada**: CLINICO ou Kestra chama `POST /careplanner/tasks/{id}/close`;
   status vai para `CLOSED`; sala Rocket.Chat pode ser arquivada.

7. **CU-07 — Tratar inbound órfão**: Mensagem inbound sem correlação válida registra
   `ORPHAN_INBOUND`; notificação interna alerta operador.

## Regras de Negócio

### RN-01 — Correlação obrigatória

Toda jornada possui `correlation_id` (UUID v4) gerado pelo IntelliCare no momento
da abertura. Este campo viaja em todos os webhooks Kestra ↔ IntelliCare e é a
chave de rastreabilidade entre tarefa, conversa e eventos.

### RN-02 — Semântica assíncrona correta

`HTTP 2xx` do Rocket.Chat no dispatch indica aceite de processamento, **não**
envio confirmado. A jornada só avança para `SENT` após evento assíncrono
`MESSAGE_SENT`. Jamais marcar `FAILED` por ausência imediata de confirmação.

### RN-03 — Confirmação real de envio

O vínculo de conversa (`channel_conversation_id` BIGINT) deve ser persistido
**apenas** no evento assíncrono de entrega real (`MESSAGE_SENT`).

### RN-04 — Multi-tenancy estrito

`tenant_slug` é extraído do JWT Keycloak (claim `tenant_slug`) em **todos** os
boundaries. Nenhuma operação aceita `tenant_slug` por parâmetro de corpo sem
validação cruzada com o JWT. Não é permitido fallback para tenant genérico.

### RN-05 — Idempotência de evento

Cada callback deve possuir `event_id` único. Reenvios idênticos (mesmo `event_id`)
devem retornar `202` sem efeito colateral.

### RN-06 — Inbound órfão

Mensagem inbound sem correlação válida: (a) registra `ORPHAN_INBOUND` com payload
completo; (b) retorna `202` para evitar retry em loop do Rocket.Chat; (c) gera
notificação interna para operador do tenant.

### RN-07 — Jitsi JWT por sala

Links de videoconsulta são gerados com JWT assinado pelo IntelliCare (segredo
compartilhado com Jitsi) com validade máxima de 2 horas. O link **nunca** é
reutilizável após expirar.

### RN-08 — Isolamento de salas Rocket.Chat por tenant

Salas são nomeadas com o padrão `ic_{tenant_slug}_{patient_keycloak_id}` para
garantir separação entre tenants no mesmo servidor Rocket.Chat.

## Fluxo Funcional de Alto Nível

```
Kestra
  │ POST /careplanner/tasks/open (correlation_id gerado)
  ▼
IntelliCare
  │ Adapter Rocket.Chat → cria sala + envia mensagem
  │ status → DISPATCHED
  ▼
Rocket.Chat
  │ webhook callback MESSAGE_SENT
  ▼
IntelliCare
  │ grava channel_conversation_id
  │ status → SENT
  │ notifica Kestra (webhook resume)
  ▼
Paciente responde no Rocket.Chat
  │ webhook inbound → IntelliCare
  ▼
IntelliCare
  │ correlaciona por sala → jornada REPLIED
  │ notifica Kestra (webhook resume)
  │ opcional: gera link Jitsi + envia via Rocket.Chat
  ▼
Kestra retoma fluxo → decide próximo step
```

## Critérios de Aceite Funcionais

1. Criação de jornada retorna `correlation_id` e status `CREATED` com `202`.
2. Dispatch com `202` do Rocket.Chat mantém tarefa em `DISPATCHED`, sem falso `FAILED`.
3. Callback `MESSAGE_SENT` avança para `SENT` e grava `channel_conversation_id`.
4. Inbound correlacionado avança jornada para `REPLIED` e notifica Kestra.
5. Evento duplicado (mesmo `event_id`) não duplica efeito (idempotência).
6. Eventos de tenants diferentes nunca se misturam (isolamento por JWT).
7. Inbound sem ponteiro registra `ORPHAN_INBOUND` e retorna `202`.
8. Link Jitsi gerado com JWT válido, sala nomeada por `{tenant}_{correlation_id}`.
9. Sala Rocket.Chat segue padrão `ic_{tenant_slug}_{patient_keycloak_id}`.

## Resultado Esperado

Ao final desta DEM, o IntelliCare terá a especificação completa para implementar
o CarePlanner conversacional de forma nativa, usando Kestra como orquestrador,
Rocket.Chat como canal de mensagens e Jitsi para videoconsultas — com isolamento
multi-tenant estrito, rastreabilidade via `correlation_id` e conformidade LGPD.
