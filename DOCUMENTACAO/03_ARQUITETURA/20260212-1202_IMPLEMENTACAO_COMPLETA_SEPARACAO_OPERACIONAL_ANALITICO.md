# IMPLEMENTAÇÃO DA SEPARAÇÃO OPERACIONAL/ANALÍTICO - Guia Completo

**Data**: 2026-02-11  
**Status**: 🟢 Completo - Pronto para Execução  
**Prioridade**: 🚀 ALTA  
**Rastreabilidade**: RESUMO_EXECUTIVO_ANALISE.md → Item 1  

---

## 🎯 Visão Geral Executiva

O INTELLICARE precisa implementar uma separação clara entre dados **operacionais** (em tempo real, transacionais) e dados **analíticos** (agregados, históricos). Esta documentação fornece:

✅ **Especificação Funcional** - O que fazer e por quê  
✅ **Especificação Técnica** - Como implementar tecnicamente  
✅ **Plano de Implementação** - Roadmap em fases  
✅ **Steps Executáveis** - Passo-a-passo pronto para executar  

---

## 📚 Documentação de Referência

### 1. **ESPECIFICAÇÃO FUNCIONAL**
📄 Arquivo: `./docs/ESPECIFICACAO_FUNCIONAL_SEPARACAO_OPERACIONAL_ANALITICO.md`

**O quê você vai encontrar:**
- Definição do problema
- Princípios funcionais (unidirecionalidade, isolamento, etc.)
- Casos de uso (criar paciente, consolidar dados, consultar histórico)
- Requisitos funcionais detalhados
- Estrutura de dados conceitual
- Fluxos de operação

**👥 Para quem é:**
- Product managers
- Stakeholders de negócio
- Arquitetos (visão conceitual)

**⏱️ Tempo de leitura:** 20-30 minutos

---

### 2. **ESPECIFICAÇÃO TÉCNICA**
📄 Arquivo: `./docs/ESPECIFICACAO_TECNICA_SEPARACAO_OPERACIONAL_ANALITICO.md`

**O quê você vai encontrar:**
- Arquitetura técnica detalhada
- Stack de tecnologia (Python 3.11+, PostgreSQL 15+, Redis 7+)
- Schema database completo (DDL)
- Padrões de código (DAO genérico, Event Publisher)
- Consolidation Service
- Row-Level Security (RLS) implementação
- Monitoramento (Prometheus, Grafana, alertas)
- Exemplos de código prontos para copiar/colar

**👥 Para quem é:**
- Desenvolvedores senior
- Arquitetos técnicos
- DevOps engineers

**⏱️ Tempo de leitura:** 45-60 minutos + implementação

---

### 3. **PLANO DE IMPLEMENTAÇÃO**
📄 Arquivo: `./docs/PLANO_PASSO_A_PASSO.md`

**O quê você vai encontrar:**
- Timeline completo (6-7 semanas)
- 4 fases de trabalho
- Tasks detalhadas com estimativas de dias
- Checklist de entrega
- Riscos e mitigação
- Métricas de sucesso

**👥 Para quem é:**
- Project managers
- Scrum masters
- Team leads
- Stakeholders de acompanhamento

**⏱️ Tempo de leitura:** 30 minutos (overview) ou 60 minutos (detalhe)

---

### 4. **STEPS EXECUTÁVEIS**
📄 Arquivo: `./steps/STEPS_IMPLEMENTACAO_PASSO_A_PASSO.md`

**O quê você vai encontrar:**
- Commands prontos para copiar/colar
- Scripts bash e python
- Exemplos de código completos
- Testes para cada step
- Procedimentos de validação

**👥 Para quem é:**
- Desenvolvedores implementando
- DevOps fazendo deploy
- QA testando

**⏱️ Tempo de referência:** Consulta conforme executa

---

## 🚀 Como Começar

### Para Entender a Visão (30 min)
1. Leia **ESPECIFICAÇÃO FUNCIONAL** (seção Visão Geral + Problema)
2. Leia **PLANO DE IMPLEMENTAÇÃO** (seção Timeline)
3. Veja **ESPECIFICAÇÃO TÉCNICA** (seção Arquitetura)

### Para Arquitetar (60 min)
1. Leia **ESPECIFICAÇÃO TÉCNICA** na íntegra
2. Revisite **PLANO DE IMPLEMENTAÇÃO** para faseamento
3. Prepare **STEPS EXECUTÁVEIS** para dev team

### Para Implementar (6-7 semanas)
1. **Semana 1-2**: Siga **PHASE 1** em STEPS
   - Crie intellicare-core
   - Implemente BaseDAO, OperationalDataAccess, EventPublisher
2. **Semana 3-4**: Siga **PHASE 2** em STEPS
   - Migre schemas de todos os módulos
3. **Semana 5-6**: Siga **PHASE 3** em STEPS
   - Implemente consolidation service
4. **Semana 7+**: Siga **PHASE 4** em STEPS
   - Teste, valide, deploy

---

## 🏗️ Arquitetura em 1 Página

```
┌──────────────────────────────────────────────────────────┐
│              APLICAÇÕES (FastAPI/Python)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Oswaldo │ Florence │ Donabedian │ ... (8 módulos) │   │
│  └──────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────┤
│         intellicare-core (Shared Library)                 │
│  ├─ OperationalDataAccess[T] → write ao _operacional    │
│  ├─ AnalyticsDataAccess[T] → read-only do _analitico    │
│  ├─ EventPublisher → Redis Streams                       │
│  ├─ RLSEnforcer → RLS policies                          │
│  └─ ProvenanceTracker → FHIR Provenance                 │
├──────────────────────────────────────────────────────────┤
│              PostgreSQL (um database)                     │
│  ├─ {modulo}_operacional (transacional, write)           │
│  ├─ {modulo}_analitico (eventual, read-only)             │
│  └─ intellicare_core (compartilhado)                     │
├──────────────────────────────────────────────────────────┤
│              Redis (Message Broker)                       │
│  ├─ Streams: {modulo}:events:{entity}                    │
│  └─ DLQ: {modulo}:dlq                                    │
├──────────────────────────────────────────────────────────┤
│       Consolidation Service (Standalone)                  │
│  ├─ Consome eventos de Redis                             │
│  ├─ Replica em {modulo}_analitico                        │
│  └─ Publica métricas                                     │
└──────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
APLICAÇÃO CRIA PACIENTE
      ↓
INSERT INTO oswaldo_operacional.pacientes (...)
      ↓
TRIGGER publica evento em Redis
      ↓
Redis Stream: oswaldo_operacional:events:pacientes
      ↓
Consolidation Job consome evento (2 AM UTC)
      ↓
Replica em oswaldo_analitico.pacientes_hist (denormalizado)
      ↓
BI/Analytics consulta oswaldo_analitico (read-only)
```

### Garantias

✅ **Unidirecionalidade**: operacional → analítico (nunca ao contrário)  
✅ **Isolamento**: Schema separation + RLS policies  
✅ **Rastreabilidade**: Provenance em FHIR standard  
✅ **Performance**: Analítico denormalizado para queries rápidas  
✅ **Resiliência**: Event-driven, idempotência, DLQ para falhas  

---

## 📊 Requisitos Funcionais Chave

| Requisito | Status | Detalhes |
|-----------|--------|----------|
| Segregação de Schemas | ✅ | Cada módulo tem `_operacional` e `_analitico` |
| Event Publishing | ✅ | Redis Streams para mudanças em operacional |
| RLS Policies | ✅ | PostgreSQL row-level security ativo |
| Batch Consolidation | ✅ | Job diário replica e agrega dados |
| Auditoria Completa | ✅ | Provenance FHIR em todas as mudanças |
| Monitoramento | ✅ | Prometheus + Grafana + alertas |
| Documentação | ✅ | Especificação funcional, técnica, steps |

---

## 💻 Stack Tecnológico

| Componente | Versão | Propósito |
|-----------|--------|----------|
| **Python** | 3.11+ | Linguagem base |
| **FastAPI** | 0.100+ | Web framework |
| **SQLAlchemy** | 2.0+ | ORM |
| **PostgreSQL** | 15+ | Database |
| **Redis** | 7+ | Message broker |
| **Prometheus** | 2.45+ | Métricas |
| **Grafana** | 10+ | Visualização |
| **Alembic** | 1.12+ | Migrações |
| **pytest** | 7.0+ | Testes |
| **Docker** | 20+ | Containerização |

---

## ⏱️ Timeline Estimada

| Fase | Duração | Objetivo | Entrega |
|------|---------|----------|---------|
| **1: Fundação** | 2 semanas | intellicare-core + DAOs | Biblioteca compartilhada |
| **2: Core** | 2 semanas | Migrar 8 módulos | Schemas separados |
| **3: Consolidação** | 1.5 semanas | Consolidation Job | Batch processing |
| **4: Deploy** | 1.5 semanas | Validação + deploy | Production-ready |
| **TOTAL** | **6-7 semanas** | Separação completa | ✅ Implementado |

---

## 🎯 Critérios de Sucesso

### Técnicos
- ✅ 85%+ test coverage em todos os módulos
- ✅ Replication lag < 1 minuto (P99)
- ✅ Zero dados perdidos ou duplicados
- ✅ Error rate < 0.1%
- ✅ Query performance BI < 5 segundos

### Operacionais
- ✅ Deploy sem downtime
- ✅ Rollback automatizado < 30 min
- ✅ Alerts ~1 minuto após problema
- ✅ Sem impacto em operações existentes

### Organizacionais
- ✅ Documentação aprovada
- ✅ Equipe confiante e treinada
- ✅ Conformidade LGPD validada
- ✅ Auditoria de segurança ✅

---

## 🔄 Próximos Passos Imediatos

### ✅ Hoje (2026-02-11)
1. Revisar esta documentação
2. Schedule kick-off meeting com equipe
3. Preparar ambiente de desenvolvimento

### 📅 Semana 1 (2026-02-11 a 2026-02-17)
1. Setup initial intellicare-core repository
2. Implement BaseDAO + OperationalDataAccess
3. Implement EventPublisher
4. Setup PostgreSQL schemas + Redis
5. Testes integrados
6. Review + aprovação

### 📅 Semana 2 (2026-02-18 a 2026-02-28)
1. Finalizar Phase 1
2. Iniciar Phase 2 (análise de módulos)
3. Primeiro módulo completo (oswaldo)

---

## 🚨 Pontos de Atenção

### Riscos Alta Probabilidade
- ❌ Equipe usa patterns incorretos → Mitigação: code review rigoroso
- ❌ Performance degrada → Mitigação: load testing antes de deploy
- ❌ RLS bloqueia queries legítimas → Mitigação: whitelist de patterns

### Decisões Críticas
- 🔴 Uma database vs. multi-database? → Decisão: Uma database com schemas
- 🔴 Síncrono vs. async consolidation? → Decisão: Async batch (eventual consistent)
- 🔴 FHIR vs. custom provenance? → Decisão: FHIR standard (Provenance)

---

## 📖 Como Usar Esta Documentação

### Cenário 1: Você é Product Manager
→ Leia: ESPECIFICAÇÃO FUNCIONAL (Visão Geral + Problema)  
→ Depois: PLANO DE IMPLEMENTAÇÃO (Timeline)  
→ Decision: Aprovar ou refinar escopo com equipe

### Cenário 2: Você é Arquiteto Técnico
→ Leia: ESPECIFICAÇÃO FUNCNICA (tudo)  
→ Depois: ESPECIFICAÇÃO TÉCNICA (tudo)  
→ Action: Revisar com dev team, preparar design review

### Cenário 3: Você é Developer
→ Leia: ESPECIFICAÇÃO TÉCNICA (Padrões de Código)  
→ Depois: STEPS EXECUTÁVEIS (seu módulo)  
→ Action: Implementar, testar, fazer code review

### Cenário 4: Você é DevOps
→ Leia: ESPECIFICAÇÃO TÉCNICA (SQL, RLS, Monitoring)  
→ Depois: STEPS EXECUTÁVEIS (Deploy)  
→ Action: Setup infraestrutura, configure alertas, prepare runbook

---

## 🤝 Contato e Suporte

### Questões sobre Especificação
→ Contato: Arquiteto de Solução  
→ Local: ESPECIFICACAO_FUNCIONAL/TECNICA.md

### Questões sobre Implementação
→ Contato: Tech Lead  
→ Local: STEPS_IMPLEMENTACAO_PASSO_A_PASSO.md

### Questões sobre Project Management
→ Contato: Project Manager  
→ Local: PLANO_PASSO_A_PASSO.md

---

## 📋 Índice de Arquivos

```
./docs/
├── ESPECIFICACAO_FUNCIONAL_SEPARACAO_OPERACIONAL_ANALITICO.md
│   └── O que, por que, casos de uso, requisitos
├── ESPECIFICACAO_TECNICA_SEPARACAO_OPERACIONAL_ANALITICO.md
│   └── Como implementar, código, arquitetura técnica
├── PLANO_PASSO_A_PASSO.md
│   └── Timeline, roadmap, checklist, riscos
└── IMPLEMENTACAO_COMPLETA_GUIA.md (este arquivo)
    └── Índice e consolidação

./steps/
└── STEPS_IMPLEMENTACAO_PASSO_A_PASSO.md
    └── Commands prontos para executar, scripts

DOCUMENTACAO/consolidacao/
└── RESUMO_EXECUTIVO_ANALISE.md
    └── Análise dos 8 documentos que motivou isso
```

---

## ✨ Checklist de Leitura

Dependendo do seu role, marque essa lista:

**[ ] Product Manager / Stakeholder**
- [ ] Cenário 1 (acima)
- [ ] Problema (Especificação Funcional)
- [ ] Arquitetura Conceitual
- [ ] Timeline
- [ ] Métricas de Sucesso

**[ ] Arquiteto / Tech Lead**
- [ ] Especificação Funcional (completa)
- [ ] Especificação Técnica (completa)
- [ ] Plano (completa)
- [ ] Arquitetura em 1 página (acima)

**[ ] Developer / DevOps**
- [ ] Especificação Técnica (seu stack)
- [ ] Steps Executáveis (seus steps)
- [ ] Padrões de Código (seu module)
- [ ] Testes (como validar)

---

## 🎓 Lições Aprendidas & Melhores Práticas

Documentadas nesta implementação:

✅ **Don't mix operational and analytical data** - Violação causa downtime  
✅ **Use event-driven architecture** - Desacopla sistemas  
✅ **Make replication idempotent** - Múltiplas execuções = mesmo resultado  
✅ **Implement RLS policies** - Segurança em camada de BD  
✅ **Monitor replication lag** - Problem early warning  
✅ **Document everything** - Este arquivo prova  

---

## 📈 Métricas de Sucesso (Resumo)

Após implementação, você conseguirá:

📊 **Operacional**
- Criar/atualizar paciente em < 100ms
- Sem qualquer degradação durante consolidação de dados

📊 **Analítico**
- Consultas BI em < 5 segundos
- Dados com até 24h de atraso aceitável
- Não precisa se preocupar com performance do operacional

📊 **Conformidade**
- 100% rastreabilidade via Provenance
- Zero contaminação entre camadas
- Audit trail completo para descoberta

---

## 🏁 Conclusão

Esta documentação fornece **tudo que você precisa** para implementar separação operacional/analítico no INTELLICARE:

✅ **Entender a visão** (Funcional)  
✅ **Conhecer a arquitetura técnica** (Técnica)  
✅ **Planejar a execução** (Plano)  
✅ **Executar passo-a-passo** (Steps)  

**Tempo total de implementação**: 6-7 semanas  
**Equipe recomendada**: 2-3 desenvolvedores  
**Data de início recomendada**: 2026-02-11  
**Data de conclusão estimada**: 2026-04-18  

---

**📌 IMPORTANTE**: Esta documentação é um VIVO DOCUMENT. À medida que implementar, registre aprendizados, atualize riscos, e refine o plano. 

**Comece com STEP 1.1 em ./steps/STEPS_IMPLEMENTACAO_PASSO_A_PASSO.md** 🚀
