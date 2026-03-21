---
tipo: especificacao-funcional
demanda: DEM-066
titulo: Notificações Push PWA
sprint: 2026-04-18
status: em-execucao
dev: DEV-2
criado: 2026-03-21
depende_de: [DEM-026, DEM-035]
habilita: [DEM-068]
tags: [pwa, push, service-worker, vapid, notificacoes, frontend, backend]
---

# DEM-066 — Notificações Push PWA

## Objetivo

O IntelliCare já tem notificações em tempo real via SSE + Redis Pub/Sub (DEM-026) e sino `NotificationBell` nos 4 módulos (DEM-035). O problema: **essas notificações só chegam com o app aberto**. Push nativo PWA entrega alertas mesmo com o browser fechado ou app em background — crítico para clínicos que precisam ser alertados de mensagens urgentes fora do horário em que estão com a janela aberta.

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-066 |
|---------|------|--------------|
| Notificação com app fechado | Impossível | Push nativo via Service Worker |
| Opt-in de notificação | Não existe | Toggle "Ativar notificações" no NotificationBell |
| Subscriptions | Não existe | Tabela `push_subscriptions` por usuário/device |
| Subscriptions mortas | N/A | Auto-removidas ao receber 410 GONE |
| Instalação como app | Não suportado | `manifest.json` + SW habilita "Adicionar à tela inicial" |

---

## Personas e fluxos

**Dr. Silva (Clínico) — opt-in:**
1. Abre ClinicoUI → clica no sino
2. Vê toggle "Receber notificações mesmo com app fechado"
3. Browser solicita permissão → Dr. Silva aceita
4. Subscription salva no banco vinculada à sua conta Keycloak

**Dr. Silva — recebe push fora do app:**
1. Paciente manda mensagem no WhatsApp CarePlanner às 19h
2. Dr. Silva está com o browser fechado
3. Notificação nativa aparece no celular/desktop
4. Ao clicar, abre diretamente a jornada no ClinicoUI

**Subscription expirada:**
1. Browser desinstala app ou usuário revoga permissão
2. Próximo push recebe 410 GONE do serviço de push
3. Sistema remove a subscription automaticamente — sem acumular entradas mortas

---

## Critérios de aceite

1. ClinicoUI registra Service Worker sem erros no Console do browser
2. Toggle no `NotificationBell` solicita permissão e salva subscription via `POST /notifications/push/subscribe`
3. Com browser fechado, ao receber mensagem RC/WA no CarePlanner, push chega no dispositivo registrado
4. Subscription com resposta 410 é removida automaticamente do banco
5. `GET /notifications/push/vapid-public-key` retorna 200 sem autenticação (necessário para o SW)
6. Testes automatizados: 4/5 passando (push real mockado em CI)

---

## Fora de escopo

- Push para PacienteUI (segunda fase)
- Push em dispositivos iOS Safari < 16.4 (não suporta Push API)
- Agrupamento / categorização de notificações por tipo
