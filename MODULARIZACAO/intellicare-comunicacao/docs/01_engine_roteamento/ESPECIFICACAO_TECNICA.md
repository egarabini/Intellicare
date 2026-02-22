# Domínio 1 — Engine de Roteamento Multi-Canal
## Especificação Técnica

**Base funcional**: `docs/01_engine_roteamento/ESPECIFICACAO_FUNCIONAL.md`
**Escopo**: EF-COM-001, EF-COM-002, EF-COM-003
**Status**: Aprovada com ajustes incorporados (R1-R3)

> ⚠️ **DECISÃO ARQUITETURAL (atualizado em 2026-02-18)**: Matrix/Synapse foi **descontinuado**
> como canal operacional do roteamento. A plataforma interna ativa é **Rocket.Chat**
> (`rocket.gsi.srv.br`).
> `MatrixClientService` permanece apenas para endpoints legados opcionais, controlados por
> `MATRIX_ENABLE_LEGACY_STACK`. `MatrixDispatcher` não integra o `DispatcherManager` ativo.
> Fallback universal para criticidade elevada permanece em **email/push**.

---

## 1. Objetivo técnico

Implementar o núcleo de roteamento assíncrono do módulo `intellicare-comunicacao`, transformando eventos/intenções em entregas multi-canal com:

- seleção de regra por prioridade;
- fallback e escalonamento automático;
- persistência operacional completa;
- rastreabilidade fim a fim (`correlation_id`);
- integração incremental com o estado atual (Rocket.Chat + Redis já operacionais).

---

## 2. Arquitetura técnica (alvo)

### 2.1 Componentes

1. `routing/receiver.py`
- Entrada via API (`POST /api/v1/routing/send`, `send-batch`) e consumidor Redis.
- Validação sintática e idempotência inicial.

2. `routing/engine.py`
- Orquestra pipeline: validar -> resolver destinatário -> consultar LGPD -> aplicar regras -> renderizar -> despachar -> monitorar fallback.

3. `routing/rule_matcher.py`
- Avalia `routing_rules` por `priority` e retorna `RoutingAction`.

4. `routing/recipient_resolver.py`
- Resolve `recipient_id` em contatos e canais possíveis.
- Primeiro ciclo: profissional/paciente com adaptadores; time/broadcast com expansão.

5. `dispatchers/manager.py`
- Interface única `dispatch(channel, payload)` com registro de dispatchers concretos.
- `RocketChatDispatcher` é o canal primário operacional.
- Demais canais (email/sms/whatsapp/push/jitsi) entram por contrato no manager.
- Stack Matrix legado fica isolado dos dispatchers ativos.

6. `templates/renderer.py`
- Jinja2 + validação de parâmetros (`jsonschema`).
- Render por variante de canal.

7. `routing/fallback_monitor.py`
- Monitora timeout de ack/leitura e aciona próximo `ChannelStep` ou escalonamento.

8. `storage/` (novos repositórios)
- `CommunicationIntentRepository`
- `DeliveryResultRepository`
- `RoutingRuleRepository`
- `MessageTemplateRepository`

9. `api/routing_routes.py`, `api/template_routes.py` e `api/channel_routes.py`
- Endpoints funcionais definidos na especificação funcional.

### 2.2 Fluxo de alto nível

1. Receber intent e persistir `status=pending`.
2. Resolver regra e plano de canais.
3. Renderizar conteúdo por canal.
4. Criar `delivery_result` (queued), despachar e atualizar status.
5. Em timeout/falha, avançar cascata.
6. Concluir `intent.status` (`completed`, `partially`, `failed`, `expired`) e publicar eventos.

---

## 3. Modelo de domínio

### 3.1 Entidades principais

1. `CommunicationIntent`
- Identidade, origem, destinatário, classificação, conteúdo, controle de entrega, agendamento, rastreabilidade e status.

2. `DeliveryResult`
- Registro por tentativa/canal com timestamps e erro normalizado.

3. `RoutingRule`
- Condições + ação (steps de canal, timeout, concorrência e escalonamento).

4. `MessageTemplate`
- Versões, schema de parâmetros e variantes por canal.

### 3.2 Estados e transições de intent

- `pending -> processing -> dispatched -> completed`
- `pending/processing -> failed`
- `scheduled -> processing`
- `pending/scheduled -> cancelled`
- `processing -> expired`
- `processing -> partially`

Regras:
- transições inválidas retornam conflito (`409`);
- atualização de status sempre com `updated_at` e trilha de evento.

---

## 4. Contratos técnicos

### 4.1 API de roteamento (primeira entrega)

1. `POST /api/v1/routing/send`
- Entrada: `CommunicationIntentCreate`
- Saída: `202 { intent_id, status }`

2. `POST /api/v1/routing/send-batch`
- Limite: 100 intents/chamada
- Saída: aceitos/rejeitados com IDs

3. `GET /api/v1/routing/intents/{intent_id}`
- Retorna intent + deliveries + timeline

4. `PUT /api/v1/routing/intents/{intent_id}/cancel`
- Cancela apenas `pending|scheduled`

### 4.2 API de templates (primeira entrega)

1. CRUD de templates (`/api/v1/templates`)
2. `POST /api/v1/templates/{id}/preview`
3. `POST /api/v1/templates/{id}/validate`

### 4.3 Contrato interno de dispatcher

```python
class ChannelDispatcher(Protocol):
    channel: str

    async def send(self, message: ChannelMessage) -> DispatchResult:
        ...
    async def is_available(self) -> bool:
        ...
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        ...
    async def get_health(self) -> ChannelHealth:
        ...
    async def supports_read_receipt(self) -> bool:
        ...
    async def supports_rich_content(self) -> bool:
        ...
```

`DispatchResult` mínimo:
- `success: bool`
- `channel_message_id: str | None`
- `channel_room_id: str | None`
- `error_code: str | None`
- `error_message: str | None`
- `timestamp: datetime`
- `metadata: dict[str, Any]`

Modelos complementares obrigatórios no contrato:
- `ResolvedRecipient`
- `RenderedContent`
- `ChannelHealth`
- `ChannelMessage`

### 4.4 API de canais

1. `GET /api/v1/channels`
- Lista canais registrados no `DispatcherManager`.

2. `GET /api/v1/channels/{channel}/health`
- Retorna saúde detalhada de um canal via `get_health()`.

3. `POST /api/v1/channels/{channel}/test`
- Dispara mensagem de teste operacional (admin).

---

## 5. Persistência e migrações

### 5.1 Schema

- `comunicacao_operacional` para dados transacionais de roteamento.
- (Opcional futuro) `comunicacao_analitico` para agregações.

### 5.2 Tabelas iniciais

1. `communication_intents`
2. `delivery_results`
3. `routing_rules`
4. `message_templates`

A migration seguirá estrutura da funcional, com índices por:
- status/severity/recipient/correlation/date (intents)
- intent_id/status/channel (delivery_results)
- priority active (routing_rules)

Mecanismo de idempotência explícito:
- `UNIQUE(source_module, source_event_id)` em `communication_intents` (quando `source_event_id` não nulo);
- deduplicação no consumer Redis por `event_id` com TTL de 24h.

---

## 6. Integração com código existente

1. Usar `RocketChatDispatcher` como implementação concreta primária do canal interno.
2. Evoluir `RedisAlertConsumer` para produzir `CommunicationIntent` (em vez de envio direto).
3. Manter endpoints legados Matrix em paralelo por compatibilidade, com feature flag.
4. Preservar `patient_room_links` e usá-lo no `recipient_resolver` como rota de apoio quando necessário.

---

## 7. Observabilidade, segurança e conformidade

### 7.1 Observabilidade

- Métricas Prometheus:
- `comm_intent_received_total`
- `comm_intent_completed_total`
- `comm_intent_failed_total`
- `comm_delivery_attempt_total{channel,status}`
- `comm_routing_latency_ms`
- logs estruturados com `correlation_id`, `intent_id`, `channel`, `attempt`.

### 7.2 Segurança

- Middleware JWT Keycloak em todos endpoints de roteamento/templates.
- RBAC por endpoint conforme funcional.
- Sanitização de payload e validação estrita via Pydantic.

### 7.3 LGPD

- Gateway explícito no pipeline (`LGPDComplianceGateway`) entre resolução de destinatário e seleção de regra.
- Aplicar exclusão de canais (`excluded_channels`) e preferências.
- Regra de exceção para criticidade (quiet hours) conforme especificação funcional.
- Auditoria de decisão de rota gravada em timeline.

Contrato:

```python
class LGPDComplianceGateway(Protocol):
    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str,
    ) -> LGPDDecision:
        ...
```

Implementação D1:
- `DefaultLGPDGateway` (provisório) com override para `CRITICAL` e `HIGH` clínico;
- D6 substituirá por implementação real (injeção de dependência, sem refatorar pipeline).

---

## 8. Estratégia de testes

1. Unitários
- `rule_matcher`, `renderer`, `fallback_monitor`, `recipient_resolver`.

2. Integração
- API de roteamento com banco + dispatcher mock.
- Redis consumer -> intent pipeline.

3. Contrato
- dispatchers stubs com testes de interface comum.
- testes dos endpoints de canais (`/api/v1/channels*`).

4. Não-funcionais
- benchmark básico para metas:
- critical < 500ms (sem tempo de canal externo),
- medium < 2s.

Meta: cobertura global >= 80%.

---

## 9. Riscos técnicos e mitigação

1. Dependência de integrações externas (Rocket.Chat/WhatsApp/SMS)
- Mitigação: stubs e contrato estável já no D1.

2. Complexidade de fallback concorrente
- Mitigação: modelo explícito de estado e testes de timeout com relógio controlado.

3. Duplicidade de eventos
- Mitigação: idempotência por `intent_id`/`source_event_id` + `correlation_id`.

4. Migração sem regressão do fluxo legado Matrix
- Mitigação: manutenção de endpoints legados atrás de `MATRIX_ENABLE_LEGACY_STACK`.

---

## 10. Critérios de pronto técnico (Definition of Done D1)

1. APIs de roteamento e templates publicadas e testadas.
2. Migrações aplicáveis em ambiente local.
3. Pipeline completo intent -> regra -> render -> dispatch -> delivery_result.
4. Fallback e escalonamento cobertos por testes automatizados.
5. Métricas e logs com `correlation_id` disponíveis.
6. Stubs de canais externos entregues para integração dos domínios dependentes.

---

## 11. Decisões de arquitetura fechadas

1. Scheduler/timeouts:
- `Redis delayed worker` com `ZADD` + polling de intents vencidos.

2. Preferências LGPD no ciclo inicial:
- `DefaultLGPDGateway` no D1; fonte definitiva via tabela local `communication_preferences` quando D6 entrar.

3. Degradação Rocket.Chat:
- fallback universal por canais externos (`email`/`push`) para `CRITICAL` e `HIGH`.

4. Timeline:
- Implementação append-only via `intent_timeline` em JSONB (tabela dedicada na evolução D1).
