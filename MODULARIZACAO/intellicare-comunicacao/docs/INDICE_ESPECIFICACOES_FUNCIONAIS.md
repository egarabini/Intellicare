# IntelliCare — Módulo de Comunicação Integrada
## Índice de Especificações Funcionais

**Versão**: 1.0  
**Data**: 15 de Fevereiro de 2026  
**Autor**: Agente Arquiteto de Comunicação  
**Classificação**: Documento Estratégico  
**Aprovação Pendente**: Arquiteto-Chefe (Eduardo Garabini)

---

## Contexto

O módulo `intellicare-comunicacao` é o **sistema nervoso** do IntelliCare — responsável por garantir que a informação clínica certa chegue à pessoa certa, no canal certo, no momento certo, com rastreabilidade completa e conformidade LGPD.

Este documento referencia as 7 Especificações Funcionais detalhadas, organizadas em domínios independentes de desenvolvimento paralelo. Cada domínio pode ser atribuído a um agente DEV diferente.

---

## Domínios Funcionais (Ordem de Prioridade)

| # | Domínio | Pasta | Prioridade | EFs Incluídas | Dependências |
|---|---------|-------|------------|---------------|--------------|
| 1 | **Engine de Roteamento Multi-Canal** | [01_engine_roteamento/](01_engine_roteamento/) | CRÍTICA | EF-COM-001, 002, 003 | Nenhuma (base para tudo) |
| 2 | **Integração Rocket.Chat** | [02_integracao_rocketchat/](02_integracao_rocketchat/) | CRÍTICA | EF-COM-010, 011, 012 | D1 (interface dispatcher) |
| 3 | **Teleconsulta e Vídeo** | [03_teleconsulta_video/](03_teleconsulta_video/) | ALTA | EF-COM-020, 021 | D1, D2 |
| 4 | **Notificações e Canais Externos** | [04_notificacoes_canais_externos/](04_notificacoes_canais_externos/) | ALTA | EF-COM-030, 031, 032, 033 | D1 (interface dispatcher) |
| 5 | **Eventos e Consolidação** | [05_eventos_consolidacao/](05_eventos_consolidacao/) | CRÍTICA | EF-COM-040, 041 | D1 |
| 6 | **Conformidade LGPD e Auditoria** | [06_conformidade_lgpd_auditoria/](06_conformidade_lgpd_auditoria/) | ALTA | EF-COM-050, 051 | D1, D5 |
| 7 | **Dashboard e Monitoramento** | [07_dashboard_monitoramento/](07_dashboard_monitoramento/) | MÉDIA | EF-COM-060, 061 | D5, D6 |

---

## Diagrama de Dependências

```
D1 (Engine Roteamento) ──────────────────────────────────────┐
  │                                                          │
  ├───► D2 (Rocket.Chat) ──► D3 (Teleconsulta)              │
  │                                                          │
  ├───► D4 (Push/WhatsApp/SMS/Email)                         │
  │                                                          │
  ├───► D5 (Eventos/Consolidação) ──► D7 (Dashboard)         │
  │                                                          │
  └───► D6 (LGPD/Auditoria) ───────► D7 (Dashboard)         │
                                                             │
  D1 + D3 (Templates) podem iniciar em PARALELO ◄───────────┘
```

---

## Plano de Sprints (6 semanas)

| Sprint | DEV-1 | DEV-2 | DEV-3 | DEV-4 | DEV-5 | DEV-6 |
|--------|-------|-------|-------|-------|-------|-------|
| **S1** | D1: Router | D1: Templates | — | — | — | D6: LGPD |
| **S2** | D1: Dispatchers | D2: RC API | D3: Teleconsulta | D4: Push | D5: Consumer | D6: Auditoria |
| **S3** | Integração | D2: Sync+Bot | D3: Sala Caso | D4: Email | D5: Consolidação | — |
| **S4** | — | — | — | D4: WhatsApp | D7: Dashboard | — |
| **S5** | — | — | — | D4: SMS | D7: Prometheus | — |
| **S6** | **Integração Final + Testes E2E + Homologação** |

---

## Estado Atual (Baseline)

| Componente | Status | Observação |
|---|---|---|
| Rocket.Chat | ✅ Operacional | v7.13.2, `rocket.gsi.srv.br`, Keycloak SSO ativo |
| Jitsi Meet | ✅ Operacional | `meet.gsi.srv.br`, JWT/Keycloak SSO ativo |
| Keycloak | ✅ Operacional | Realm `bemcuidar`, 9 clients, 7 roles RBAC |
| API FastAPI | ✅ Funcional | 18 endpoints, base para novo router multi-canal |
| Redis Consumer | ✅ Funcional | Consome `alert.created`, base para RoutingEngine |
| Bot @intellicare | 🔵 Planejado | Spec D2 (EF-COM-012) completa, aguarda impl. |
| PostgreSQL Schema | ✅ Parcial | Tabela `patient_room_links` (legado Matrix) |
| ~~Matrix/Synapse~~ | ~~Substituído~~ | Substituído por Rocket.Chat + Jitsi |

---

## Instruções para Agentes DEV

1. **Ler** o documento de especificação do seu domínio **inteiramente**
2. **Gerar** Especificação Técnica com: diagramas, schemas, contratos API, testes planejados
3. **Gerar** Plano de Implementação com: estimativas, ordem de tarefas, riscos
4. **Submeter** para revisão antes de codificar
5. **Desenvolver** seguindo padrões IntelliCare:
   - Dual-schema (operacional/analítico)
   - BaseDAO[T] do intellicare-core
   - EventPublisher para Redis Streams
   - Keycloak auth middleware
   - Testes ≥ 80% cobertura
   - Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic 2.5

---

## Referências

- [Especificação Funcional Completa (consolidada)](../ESPECIFICACOES_FUNCIONAIS_COMUNICACAO.md)
- [Arquitetura Conceitual IntelliCare](../../docs/ANDAMENTO.md)
- [Keycloak Integração](../../KEYCLOAK_INTEGRACAO_FINAL_REPORT.md)
- [CPaaS Documento Técnico](../../docs/)
- [Replicação de Padrões](../../REPLICACAO_KEYCLOAK_COMPLETA.md)
