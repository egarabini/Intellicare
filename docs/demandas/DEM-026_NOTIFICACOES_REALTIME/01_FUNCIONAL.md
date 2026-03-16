---
tipo: especificacao-funcional
demanda: DEM-026
titulo: Notificações em Tempo Real (WebSocket / SSE)
fase: 3
sprint: "3.2"
status: em-execucao
planejador: Claude
criado: 2026-03-16
depende_de: [DEM-019, DEM-025]
habilita: [DEM-029]
tags: [fase-3, notifications, websocket, sse, p2]
---

# DEM-026 — Notificações em Tempo Real (WebSocket / SSE)

## Objetivo

Implementar sistema de notificações em tempo real para a plataforma IntelliCare,
permitindo que eventos clínicos, administrativos e de agendamento sejam comunicados
instantaneamente aos usuários conectados. Utiliza SSE (Server-Sent Events) como
canal principal e WebSocket como alternativa bidirecional, com Redis Pub/Sub para
distribuição entre instâncias.

## Contexto

O IntelliCare V3 já possui módulos de gestão (DEM-019), clínico (DEM-032) e
observabilidade (DEM-025) funcionando. Porém, toda comunicação é request-response.
Eventos como "novo agendamento criado", "resultado de exame disponível" ou
"alerta clínico" dependem de polling manual pelo frontend. Esta DEM preenche essa
lacuna com notificações push server→client.

## Escopo

### O que está incluído

| Bloco | O que entrega | Por quê |
|-------|--------------|---------|
| 1 | Módulo `notifications` com BaseModule | Contrato padrão IntelliCare |
| 2 | Tabelas `notifications` e `notification_preferences` por tenant | Persistência multi-tenant |
| 3 | CRUD REST de notificações (listar, ler, marcar lida, deletar) | API base para frontends |
| 4 | Endpoint SSE `/notifications/stream` | Push real-time server→client |
| 5 | Endpoint WebSocket `/notifications/ws` | Alternativa bidirecional |
| 6 | Redis Pub/Sub para distribuição | Suporte a múltiplas instâncias |
| 7 | Endpoint `POST /notifications/send` | Criação programática de notificações |
| 8 | Testes unitários e de integração | Qualidade |

### O que NÃO está incluído

- Integração frontend (será feita em DEM futura)
- Push notifications mobile (FCM/APNs)
- Email/SMS como canal de notificação
- Templates de notificação configuráveis por tenant
- Fila de retry para notificações falhadas

## Tipos de Notificação

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `appointment` | Agendamentos | "Consulta agendada para 15/03 às 14:00" |
| `clinical` | Alertas clínicos | "Resultado de exame disponível" |
| `system` | Sistema | "Manutenção programada para domingo" |
| `message` | Mensagens | "Nova mensagem do Dr. Silva" |
| `alert` | Urgentes | "Paciente com sinais vitais alterados" |

## Prioridades

| Prioridade | Comportamento |
|-----------|---------------|
| `low` | Entrega normal, sem destaque |
| `normal` | Entrega normal com badge |
| `high` | Entrega imediata com destaque visual |
| `urgent` | Entrega imediata com som/vibração |

## Critérios de Aceite

1. Módulo `notifications` carregado via `ModuleLoader` sem erros
2. `GET /notifications/health` retorna `{"status": "healthy"}`
3. `POST /notifications/send` cria notificação e publica via Redis
4. `GET /notifications/` lista notificações do usuário autenticado (paginado)
5. `PATCH /notifications/{id}/read` marca como lida
6. `GET /notifications/stream` envia SSE com notificações em tempo real
7. `WS /notifications/ws` aceita conexão autenticada e entrega notificações
8. `GET /notifications/unread-count` retorna contagem de não-lidas
9. Multi-tenant: notificações isoladas por schema do tenant
10. Testes passam sem erros

## Resultado Esperado

Sistema de notificações funcional com persistência, entrega em tempo real via
SSE/WebSocket, e API REST completa. Pronto para integração por qualquer frontend
do IntelliCare.

## Notas para o Agente Desenvolvedor

- Redis já está disponível na infra (`localhost:6379`)
- Seguir padrão de camadas: `schemas.py → service.py → router.py`
- Usar `TenantAwareSessionFactory` para queries multi-tenant
- SSE é preferível a WebSocket para notificações unidirecionais (mais simples, funciona com proxies)
- WebSocket requer autenticação via query param `?token=` (não suporta headers custom)
