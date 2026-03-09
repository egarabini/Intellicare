# 📋 W1-B — Especificação Funcional: FHIR Subscriptions Engine

## 1. Objetivo

Implementar um **engine de Subscriptions FHIR** que permite que sistemas e usuários recebam notificações automáticas quando recursos clínicos são criados, atualizados ou deletados. Isso transforma o IntelliCare de um sistema pull-only para **event-driven**.

---

## 2. Conceito de Subscription FHIR

Uma Subscription FHIR define:
- **Critério:** "Observation?code=glucose&value-quantity=gt200" (quando glicose > 200)
- **Canal:** Como notificar (webhook, WebSocket, bot)
- **Status:** active, off, error

Quando um recurso FHIR é criado/atualizado/deletado e **bate com o critério**, o sistema dispara uma notificação pelo canal configurado.

---

## 3. Funcionalidades

### 3.1 Criação e Gestão de Subscriptions
- CRUD de recursos `Subscription` via API FHIR padrão
- Suporte a status: `requested` → `active` → `off` | `error`
- Validação de critério (deve ser um FHIR Search válido)
- Subscription por tenant (isolamento multi-tenant)

### 3.2 Canais de Notificação

#### 3.2.1 REST-Hook (Webhook)
- Envia `POST` HTTP com o recurso FHIR no body
- Headers configuráveis (ex: `Authorization: Bearer xxx`)
- Assinatura HMAC-SHA256 para verificar autenticidade (`X-Signature`)
- Retry com backoff exponencial (1s, 2s, 4s, 8s — até 4 tentativas)
- Timeout de 120s por request
- AuditEvent para cada tentativa (sucesso/falha)

#### 3.2.2 WebSocket (Real-time)
- Conexão WebSocket persistente para notificações real-time
- Filtragem por critério FHIR no momento da conexão
- Publish via Redis Pub/Sub
- Ideal para dashboards e monitoramento em tempo real

#### 3.2.3 Bot (Automação)
- Canal `endpoint: "Bot/{id}"` — executa um bot/automação ao invés de HTTP
- Integração com o Bots Engine (Onda 2 — pode ficar como stub na Onda 1)
- Permite lógica personalizada por tenant

### 3.3 Avaliação de Critério
- Quando um recurso FHIR é criado/atualizado/deletado:
  1. Buscar todas as Subscriptions ativas no tenant
  2. Para cada, avaliar se o recurso bate com o critério
  3. Se sim, enfileirar job de notificação
- Critérios suportados:
  - ResourceType simples: `Observation`
  - Com filtros: `Observation?code=glucose`
  - Com operadores: `Observation?value-quantity=gt200`
  - Interactions: create, update, delete (via extension)

### 3.4 Processamento Assíncrono
- Jobs enfileirados em **Celery** (nosso equivalente ao BullMQ do Medplum)
- Workers independentes processam a fila
- Retry automático com backoff exponencial
- Dead letter queue para jobs que falharam todas as tentativas
- Métricas de tempo na fila, tempo de execução, taxa de sucesso

### 3.5 AuditEvent
- Cada tentativa de notificação gera um `AuditEvent` FHIR
- Registra: sucesso/falha, status HTTP, mensagem de erro, duração
- Permite rastreamento completo do lifecycle de uma notificação

---

## 4. Casos de Uso

| Cenário | Critério | Canal | Resultado |
|---|---|---|---|
| Alerta de glicose alta | `Observation?code=glucose&value-quantity=gt200` | REST-hook → Alerta Florence | Florence recebe e cria tarefa de enfermagem |
| Dashboard de admissões | `Encounter?status=arrived` | WebSocket → Dashboard | Dashboard atualiza em tempo real |
| Relatório de prescrição | `MedicationRequest?status=active` | REST-hook → Wanda | Wanda processa nova prescrição |
| Notificação ao médico | `DiagnosticReport?status=final` | REST-hook → Comunicação | Comunicação envia push notification |
| Auditoria de cancelamento | `Encounter?status=cancelled` | REST-hook → Admin | Admin registra log de auditoria |

---

## 5. Regras de Negócio

1. **Isolamento:** Subscriptions de um tenant não acessam dados de outro
2. **Rate limiting:** Máximo de 100 subscriptions ativas por tenant
3. **Timeout:** REST-hooks que não respondem em 120s são considerados falha
4. **Max retries:** Padrão 4, configurável por subscription (max 19)
5. **Desativação automática:** Subscription com 4+ falhas consecutivas muda para status `error`
6. **AuditEvent obrigatório:** Toda execução gera auditoria (sucesso e falha)
7. **Exclusão de AuditEvent:** Subscriptions nunca são disparadas para mudanças em AuditEvents (evitar loops)

---

## 6. Sinergia com WAHA (WhatsApp HTTP API)

> A integração WAHA em andamento (EF-COM-034, `intellicare-comunicacao/channels/whatsapp/waha_client.py`) é **complementar e sinérgica** com Subscriptions:

- **Subscriptions → REST-hook → Comunicação → WAHA**: Um Subscription pode notificar o módulo Comunicação via REST-hook, que por sua vez envia a notificação ao paciente via WhatsApp (Meta ou WAHA)
- **Teste sem custo**: Em dev/homologação, usar `WHATSAPP_BACKEND=waha` permite testar fluxos de Subscription→Notificação completos sem custo por mensagem da Meta API
- **Nenhuma interferência**: WAHA é um canal de mensageria (downstream), Subscriptions é um sistema de notificação event-driven (upstream). Operam em camadas diferentes

---

## 7. Referência Medplum

| Componente | Arquivo | Tamanho |
|---|---|---|
| Subscription Worker | `workers/subscription.ts` | 782 linhas |
| WebSocket Handler | `subscriptions/websockets.ts` | 18KB |
| Criteria Matching | `core/src/search/match.ts` | ~500 linhas |
| AuditEvent Helper | `util/auditevent.ts` | ~200 linhas |
