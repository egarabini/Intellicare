# Domínio 1 — Engine de Roteamento Multi-Canal
## Plano de Implementação

**Base**: `docs/01_engine_roteamento/ESPECIFICACAO_FUNCIONAL.md` + `ESPECIFICACAO_TECNICA.md`  
**Horizonte**: 2 sprints (S1 + S2)  
**Status**: Em execução avançada (D1 concluído + hardening D2/D6 em 2026-02-18)

---

## 1. Estratégia de execução

Implementar por camadas para liberar valor incremental e manter compatibilidade com o módulo atual:

1. fundação de domínio + persistência;
2. pipeline de roteamento mínimo operacional;
3. fallback/escalonamento;
4. APIs completas + templates;
5. observabilidade, hardening e testes finais.

---

## Status de Execução (2026-02-18)

- Fase 0: concluída
- Fase 1: concluída
- Fase 2: concluída
- Fase 3: concluída
- Fase 4: concluída
- Fase 5: concluída

Evoluções pós-fase:
- integração Rocket.Chat consolidada como canal primário no `DispatcherManager`;
- stack Matrix mantido apenas como legado opcional via `MATRIX_ENABLE_LEGACY_STACK`;
- LGPD/auditoria com endpoints operacionais de listagem e compliance report;
- suíte estável validada com `133 passed, 1 skipped`.

---

## 2. Fases, entregáveis e estimativas

## Fase 0 — Preparação e alinhamento (0,5 dia)

Entregáveis:
- registrar decisões fechadas (Redis delayed worker, LGPD gateway default, fallback email/push);
- checklist de ambientes (DB/Redis/Keycloak).

Saída:
- decisões registradas e premissas congeladas para execução.

## Fase 1 — Estrutura base e migrações (1,5 dia)

Tarefas:
- criar pacotes `routing`, `dispatchers`, `templates` e novos repositórios;
- migration Alembic com tabelas de roteamento;
- modelos Pydantic/SQLAlchemy para intents/delivery/rules/templates.
- completar contrato de dispatcher com 7 métodos (R1);
- aplicar idempotência explícita em persistência e consumer (R7).

Entregáveis:
- migration aplicável;
- entidades e repositórios com testes unitários básicos.

## Fase 2 — Pipeline core de roteamento (2 dias)

Tarefas:
- `RoutingEngine` + `RuleMatcher`;
- `RecipientResolver` com adaptadores plugáveis (R6);
- `DispatcherManager` com `RocketChatDispatcher` como primário e demais canais registrados;
- persistência de `DeliveryResult` por tentativa.
- `LGPDComplianceGateway` + `DefaultLGPDGateway` no ponto de hook do pipeline (R2);
- `TimelineEvent` append-only com retorno no `GET /routing/intents/{id}` (R4).

Entregáveis:
- fluxo `send intent -> dispatch -> status final`;
- testes de fluxo feliz e falha primária.

## Fase 3 — Fallback, timeout e escalonamento (1,5 dia)

Tarefas:
- `FallbackMonitor` e máquina de estados de tentativa;
- escalonamento por `parent_intent_id`;
- controle `max_attempts`/`timeout_seconds`.

Entregáveis:
- fallback automático funcional;
- testes de timeout e escalonamento.

## Fase 4 — Templates e APIs (2 dias)

Tarefas:
- CRUD de templates, preview e validação;
- endpoints de roteamento (`send`, `batch`, `get`, `list`, `cancel`, `rules`);
- endpoints de canais (`GET /channels`, `GET /channels/{channel}/health`, `POST /channels/{channel}/test`) (R3);
- integração de renderização por canal.

Entregáveis:
- APIs completas da primeira entrega;
- 4 templates seed mínimos (clinical alert, medication reminder, teleconsult invite, escalation), cada um com 5 variantes + `params_schema` + `sample_params` (R8).

## Fase 5 — Segurança, observabilidade e finalização (1,5 dia)

Tarefas:
- Keycloak auth middleware e RBAC nos endpoints novos;
- métricas Prometheus e logs estruturados;
- endpoint `GET /api/v1/routing/metrics` para agregados operacionais (R5);
- integração com consumidor Redis no novo pipeline;
- testes de integração e cobertura.

Entregáveis:
- suíte de testes executando com cobertura >= 80%;
- documentação técnica de operação e troubleshooting.

**Estimativa total**: 9 dias úteis (com buffer interno de 1 dia dentro das fases).

---

## 3. Sequenciamento e dependências

Dependências internas:
1. Fase 1 bloqueia Fases 2–5.
2. Fase 2 bloqueia Fase 3.
3. Fase 4 pode iniciar em paralelo parcial com Fase 3 (templates/API).
4. Fase 5 depende de estabilidade de Fases 3 e 4.

Dependências externas:
1. credenciais/ambiente Keycloak.
2. acesso DB com schema `comunicacao_operacional`.
3. Redis disponível para teste do consumer.

---

## 4. Plano de testes por fase

1. Fase 1
- testes de migração e CRUD de repositórios.

2. Fase 2
- testes unitários de regra e dispatch manager;
- integração de envio simples com RocketChat mockado.

3. Fase 3
- cenários de falha primária, fallback secundário, escalonamento final.

4. Fase 4
- contrato de API (status code, payload, erros 4xx/5xx);
- renderização multi-canal com validação de schema.

5. Fase 5
- testes end-to-end de rota via API e via Redis event;
- teste de autorização por role;
- validação de métricas emitidas.

---

## 5. Riscos de implementação e contingência

1. Instabilidade de integrações externas
- contingência: manter stubs e mocks contratuais para não bloquear D1.

2. Regressão no fluxo atual de alerta clínico
- contingência: rodar caminho novo atrás de flag e manter endpoint legado.

3. Crescimento de complexidade no roteamento por regra
- contingência: começar com conjunto mínimo de regras default e expandir iterativamente.

4. Inconsistência de dados de destinatário
- contingência: validação defensiva + status `failed` com erro categorizado.

---

## 6. Critérios de entrada e saída

Critérios para iniciar desenvolvimento:
1. aprovação explícita deste plano;
2. aprovação da especificação técnica;
3. decisões arquiteturais já fechadas e registradas.

Critérios de encerramento da implementação D1:
1. todos critérios de aceite técnicos validados em testes;
2. APIs documentadas e operacionais;
3. migrações estáveis;
4. integração pronta para D2/D4 via contratos de dispatcher.

Status atual:
- critérios de encerramento D1 atendidos;
- execução segue em continuidade para domínios adjacentes (D3/D4/D5/D7).

---

## 7. Checklist de aprovação (pré-código)

1. Escopo EF-COM-001/002/003 está correto.
2. Sequência de fases está aprovada.
3. Estimativas estão aceitáveis.
4. Riscos e contingências estão adequados.
5. Podemos iniciar implementação imediatamente após aprovação.
