# ESPECIFICAÇÃO FUNCIONAL - Separação Operacional/Analítico

**Data**: 2026-02-11  
**Status**: 🟢 Especificação Funcional Completa  
**Prioridade**: 🚀 ALTA PRIORIDADE  
**Rastreabilidade**: RESUMO_EXECUTIVO_ANALISE.md → Item 1  

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Problema](#problema)
3. [Definição de Escopo](#definição-de-escopo)
4. [Princípios Funcionais](#princípios-funcionais)
5. [Arquitetura Conceitual](#arquitetura-conceitual)
6. [Atores e Casos de Uso](#atores-e-casos-de-uso)
7. [Requisitos Funcionais](#requisitos-funcionais)
8. [Garantias e Restrições](#garantias-e-restrições)
9. [Estrutura de Dados](#estrutura-de-dados)
10. [Fluxos de Operação](#fluxos-de-operação)

---

## 🎯 Visão Geral

O INTELLICARE precisa garantir que dados operacionais (assistenciais, estado de coordenação) **nunca se contaminem** com dados analíticos (consolidações, agregações, históricos para pesquisa). Esta separação é fundamental para:

- ✅ **Integridade operacional**: Operações não sofrem impacto de análises complexas
- ✅ **Performance**: Consultas analíticas não travam operações críticas
- ✅ **Auditoria**: Rastros separados para causalidade e investigação
- ✅ **Conformidade LGPD**: Dados para análise desassociados de operações
- ✅ **Resiliência**: Falha em análise ≠ Falha em operação

---

## 🚨 Problema

### Contexto Atual

Na arquitetura proposta pela outra equipe (Documentação/Base), existe um princípio crítico:

> **"Separação Operacional/Analítico - Nunca misturar"**

Especificamente:

1. **GC Cuidado** (PostgreSQL) = Repositório Operacional
   - Estado do CarePlanner (coordenação de cuidado)
   - Tarefas, filas, pacientes, eventos da jornada
   - **DEBE**: Sempre consistente, em tempo real, transacional

2. **Data Lakehouse** = Repositório Analítico
   - Consolidação de dados para BI, pesquisa, monitoramento
   - Agregações, projeções, historiadores
   - **PODE**: Ser eventual consistent, atrasado, denormalizado

### O Risco de Contaminação

Sem separação clara:

❌ Queries analíticas pesadas (JOIN 50 tabelas, DISTINCT COUNT) travam operações críticas
❌ Modificações analíticas (agregações temporárias) afetam operação
❌ Dados operacionais se misturam com dados antigos (históricos)
❌ Auditor não consegue separar "qual era o estado real" de "qual era a projeção"
❌ Data Lakehouse fica sujo com lógica operacional

---

## 📐 Definição de Escopo

### Escopo Inclui

1. **Implementação de padrão de separação** em todos os 8 módulos LEGO:
   - intellicare-core (biblioteca base)
   - intellicare-auth (autenticação)
   - intellicare-comunicacao (CPaaS)
   - intellicare-donabedian (métricas)
   - intellicare-florence (gestão clínica)
   - intellicare-geralda (configuração)
   - intellicare-oswaldo (monitoramento)
   - intellicare-portal (interface)
   - intellicare-wanda (orquestração)
   - intellicare-zilda (assistente clínico)

2. **Schemas PostgreSQL separados** por contexto:
   - `{modulo}_operacional` - Dados de operação em tempo real
   - `{modulo}_analitico` - Dados para análise e pesquisa

3. **Pipelines unidirecionais** operacional → analítico:
   - Event-driven (quando dado operacional muda)
   - Ou batch (consolidação periódica)

4. **Monitoramento e alertas** de violação:
   - Detectar escrita em schemas analíticos fora de pipelines
   - Alertar tentativas de leitura de operacional durante consolidação

### Escopo Exclui

❌ Implementação de Full Data Lakehouse (que é infraestrutura central)
❌ Replicação de dados em multi-datacenter
❌ Redesign completo de bancos existentes (evolução incrementa)
❌ Conformidade LGPD total (apenas estrutura para)
❌ Governança institucional formal (setup técnico apenas)

---

## 🔑 Princípios Funcionais

### P1: Unidirecionalidade Rigorosa

```
OPERACIONAL → ANALÍTICO
     (✅ permitido)

ANALÍTICO → OPERACIONAL
     (❌ NUNCA!)
```

**Garantia**: Pipelines de replicação devem ser **write-only** em schemas analíticos.

### P2: Isolamento por Contexto

Cada módulo tem seu próprio espaço:

```
PostgreSQL (intellicare_db)
├── {modulo}_operacional        ← Vivo, transacional
├── {modulo}_analitico          ← Histórico, eventual
└── intellicare_core            ← Compartilhado (usuários, orgs)
```

### P3: Controle de Acesso Granular

```
APP: intellicare-oswaldo (operacional)
  ├── PERMITE leitura em oswaldo_operacional
  ├── PERMITE escrita em oswaldo_operacional
  ├── REJEITA escrita em oswaldo_analitico
  └── PERMITE leitura em oswaldo_analitico (auditoria apenas)

JOB: data-consolidation-job
  ├── REJEITA leitura em oswaldo_analitico? (risco)
  ├── PERMITE leitura em oswaldo_operacional
  └── PERMITE escrita em oswaldo_analitico
```

### P4: Event-Driven Replication

Quando dado operacional muda:

1. Aplicação commit em `{modulo}_operacional`
2. Trigger/Event publica no message broker (Redis Stream, RabbitMQ, etc.)
3. Listener (separado) consome evento
4. Replica em `{modulo}_analitico` (transform conforme necessário)
5. Auditoria registra: "O que", "Quando", "Por que"

### P5: Rastreabilidade Total (Provenance)

```
Tabela operacional: paciente_id=123, status="coordenando"
  ├── created_at: 2026-02-11 10:00:00
  ├── updated_at: 2026-02-11 10:30:00
  ├── provenance: { actor: "florence-module", action: "update_status" }

Tabela analítica: paciente_id=123, status="coordenando", periodo="2026-02"
  ├── replicated_at: 2026-02-11 10:30:05
  ├── source_event_id: "evt-abc123"
  ├── provenance: { source: "oswaldo_operacional", pipeline: "consolidation-v1" }
```

---

## 🏗️ Arquitetura Conceitual

### Camadas

```
┌──────────────────────────────────────────────────────────┐
│           APLICAÇÕES (Módulos LEGO)                      │
│  ┌────────┬──────────┬──────────┬──────────┐             │
│  │Oswaldo │ Florence │Donabedian│ Zilda   │ ...          │
│  └────┬───┴────┬─────┴────┬─────┴────┬────┘             │
├───────┴────────┴──────────┴──────────┴──────────────────┤
│        CAMADA DE ACESSO A DADOS (DAO Layer)              │
│  ├─ OperationalDataAccess (apenas _operacional)          │
│  └─ AnalyticsDataAccess (apenas _analitico, read-only)   │
├──────────────────────────────────────────────────────────┤
│        CAMADA DE EVENTOS (Event Broker)                  │
│  ├─ Redis Streams (operacional → analítico)              │
│  └─ Dead Letter Queue (falhas de replicação)             │
├──────────────────────────────────────────────────────────┤
│        CAMADA DE ORQUESTRAÇÃO (Consolidação)             │
│  ├─ data-consolidation-service                           │
│  ├─ schema-evolution-manager                             │
│  └─ replication-monitor                                  │
├──────────────────────────────────────────────────────────┤
│        BANCO DE DADOS (PostgreSQL)                       │
│  ├─ {modulo}_operacional (transacional)                  │
│  ├─ {modulo}_analitico (eventual, denormalizado)         │
│  └─ intellicare_core (compartilhado - usuarios, orgs)    │
└──────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
OPERAÇÃO NORMAL:
┌─────────────────────────────────────┐
│  Aplicação (oswaldo) escreve        │
│  paciente.status = "coordenando"    │
└────────┬────────────────────────────┘
         │
         ▼ (transação ACID)
┌─────────────────────────────────────┐
│  oswaldo_operacional.pacientes      │
│  (row: id=123, status="...")        │
└────────┬────────────────────────────┘
         │
         ▼ (trigger / app event)
┌─────────────────────────────────────┐
│  Redis Stream                       │
│  paciente:updated:{id}              │
└────────┬────────────────────────────┘
         │
         ▼ [async batch consolidation]
┌─────────────────────────────────────┐
│  osvaldo_analitico.pacientes_hist   │
│  + agregações mensais               │
└─────────────────────────────────────┘

ANÁLISE:
┌─────────────────────────────┐
│ BI Tool / Data Scientist    │
└────────┬────────────────────┘
         │
         ▼ (read-only)
┌─────────────────────────────┐
│ oswaldo_analitico.*         │
│ (nunca toca em _operacional)│
└─────────────────────────────┘
```

---

## 👥 Atores e Casos de Uso

### Atores

1. **Profissional de Saúde** (Médico, Enfermeiro, Coordenador)
   - Interage com app (oswaldo, florence, etc.)
   - Escreve dados operacionais
   - Consulta status em tempo real

2. **Sistema de Orquestração** (Wanda, MCP)
   - Lê estado operacional
   - Publica eventos
   - Muda status de tarefas

3. **Data Consolidation Job**
   - Consome eventos de operacional
   - Transforma e replica em analítico
   - Executa agregações

4. **BI / Pesquisador**
   - Executa queries em schemas analíticos
   - Nunca toca operacional
   - Acesso read-only

5. **Auditor de Conformidade**
   - Verifica provenance de dados
   - Detecta violações de separação
   - Emite relatórios

### Casos de Uso Principais

#### UC1: Criar/Atualizar Paciente (Operacional)

```gherkin
Cenário: Profissional cria paciente
  Dado que ele está no módulo florence
  E Sistema rejeita se tentar escrever em florence_analitico
  Quando ele clica "Criar Paciente"
  Então Sistema:
    - Valida dados no schema florence_operacional
    - Commit em florence_operacional
    - Publica evento "paciente:created" em Redis
    - Retorna id do paciente (imediato)
  E Sistema garante que:
    - florence_analitico é atualizado DEPOIS (eventual)
    - Provenance é registrado
```

#### UC2: Consolidar Dados Analíticos (Batch)

```gherkin
Cenário: Job de consolidação diária
  Dado que é 2:00 AM UTC
  Quando consolidation-service acorda
  Então:
    - Lê eventos desde último checkpoint em Redis
    - Consolida florence_operacional → florence_analitico
    - Agrega por período (dia, semana, mês)
    - Registra estatísticas de replicação
    - Publica métrica: "consolidation:florence:duration=120s"
  E garante que:
    - florence_operacional continua online durante consolidação
    - Falhas são capturadas em DLQ para retry
```

#### UC3: Verificar Histórico de Paciente (Analítico)

```gherkin
Cenário: BI tool consulta histórico
  Dado que BI tool usa role "analytics-read"
  Quando executa:
    SELECT * FROM florence_analitico.pacientes_hist
    WHERE mes = '2026-02'
  Então:
    - Query é executado em segundos (índices otimizadas)
    - Dados podem estar atrasados até 24h (aceitável)
    - System bloqueia se tentar UPDATE/DELETE
    - Provenance mostra "replicated via job-v1"
```

#### UC4: Detectar Violação (Monitoramento)

```gherkin
Cenário: App tenta escrever em schema analítico
  Dado que oswaldo-app tenta:
    INSERT INTO oswaldo_analitico.metricas (...)
  Quando database recebe comando
  Então:
    - Policy de segurança rejeita (coluna-level security)
    - Evento de violação é publicado
    - Alert vai para admin e auditor
    - Requisição falha com 403 Forbidden (app side)
```

---

## ✅ Requisitos Funcionais

### RF1: Segregação de Schemas

- [x] Cada módulo deve ter `{modulo}_operacional` e `{modulo}_analitico`
- [x] Schemas são criados automaticamente via migration
- [x] Permissões são aplicadas via PostgreSQL roles
- [x] Documentação de cada schema disponível

### RF2: Event-Driven Replication

- [x] Quando dado muda em `*_operacional`, evento é publicado
- [x] Evento contém id, tipo, operação, timestamp, ator
- [x] Listener consome evento dentro de X segundos (SLA)
- [x] Dados são replicados respeitando relacionamentos

### RF3: Batch Consolidation

- [x] Job agendável (diário, horário, manual)
- [x] Consolida históricos (denormalizados para performance)
- [x] Calcula agregações (SUM, COUNT, AVG por período)
- [x] Idempotente (rodadas múltiplas = mesmo resultado)

### RF4: Controle de Acesso

- [x] Aplicação operacional pode WRITE em `_operacional`
- [x] Aplicação operacional pode READ `_operacional` (limited)
- [x] Aplicação operacional é REJEITADA em `_analitico`
- [x] Job de consolidação pode READ `_operacional` + WRITE `_analitico`
- [x] BI/Analytics pode READ `_analitico` apenas
- [x] Roles PostgreSQL precisam estar mapeados no Keycloak

### RF5: Auditoria e Provenance

- [x] Tabela `{modulo}_{type}.audit_log` com todas as mudanças
- [x] Provenance no padrão FHIR (ator, ação, timestamp, razão)
- [x] Rastreamento de linhagem: operacional → evento → analítico
- [x] Relatório de conformidade: "Não há contaminação"

### RF6: Monitoramento

- [x] Métrica: tempo de replicação operacional → analítico
- [x] Métrica: eventos em fila vs. consumidos
- [x] Alert: Se replicação ficar > X tempo de atraso
- [x] Alert: Se tentativa de violação de separação
- [x] Dashboard de saúde de consolidação

### RF7: Documentação

- [x] Guia de como adicionar novo módulo
- [x] Schemas gerenciados em version control
- [x] Migration scripts documentados
- [x] Exemplos de queries de troubleshooting

---

## 🔐 Garantias e Restrições

### Garantias

✅ **Garantia 1: Idempotência Operacional**  
Se mesmo comando rodou 2x, estado é idêntico (ou explicado em log).

✅ **Garantia 2: Separação Lógica Rigorosa**  
`oswaldo_analitico` não existe em nível file-system de operacional.

✅ **Garantia 3: Consistência Eventual Analítica**  
Dados em `_analitico` convergem para `_operacional` em ≤ 24h.

✅ **Garantia 4: Rastreabilidade Total**  
Toda mudança em `_operacional` tem provenance em `_analitico`.

✅ **Garantia 5: Rejeição de Contaminação**  
Violação de separação é imediatamente rejeita de forma segura.

### Restrições

🔒 **Restrição 1: Sem Escrita Cruzada**  
Aplicação operacional **nunca** escreve em `_analitico`.

🔒 **Restrição 2: Sem Join Cruzado**  
Queries não podem combinar `_operacional` e `_analitico` diretamente.

🔒 **Restrição 3: Sem Backfill Condicional**  
Se consolidação falhar, sistema não tenta "apagar e refazer"—vai para DLQ.

🔒 **Restrição 4: Sem Cache Compartilhado**  
Cache (Redis) pode ter dados de ambos, mas tags devem separar: `op:{id}` vs `an:{id}`.

🔒 **Restrição 5: Sem Transações Distribuídas**  
Operação sempre em `_operacional` apenas. Analítico é efeito colateral eventual.

---

## 📊 Estrutura de Dados

### Schema Operacional (Exemplo: Oswaldo)

```sql
-- oswaldo_operacional schema
CREATE TABLE pacientes (
  id UUID PRIMARY KEY,
  nome VARCHAR NOT NULL,
  data_nascimento DATE,
  status VARCHAR DEFAULT 'ativo',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES intellicare_core.usuarios(id),
  updated_by UUID REFERENCES intellicare_core.usuarios(id),
  rowversion INT DEFAULT 1  -- para otimistic lock
);

CREATE TABLE audit_log (
  id UUID PRIMARY KEY,
  entity_type VARCHAR NOT NULL,
  entity_id UUID NOT NULL,
  operation VARCHAR NOT NULL,  -- CREATE, UPDATE, DELETE
  old_values JSONB,
  new_values JSONB,
  actor_id UUID REFERENCES intellicare_core.usuarios(id),
  timestamp TIMESTAMP DEFAULT NOW(),
  provenance JSONB -- {"actor": "...", "reason": "..."}
);
```

### Schema Analítico (Exemplo: Oswaldo)

```sql
-- oswaldo_analitico schema (denormalized, indexed for BI)
CREATE TABLE pacientes_hist (
  id UUID,
  nome VARCHAR,
  data_nascimento DATE,
  status VARCHAR,
  period_year INT,
  period_month INT,
  days_in_status INT,
  status_changes INT,
  created_at TIMESTAMP,
  replicated_at TIMESTAMP,
  provenance JSONB,
  PRIMARY KEY (id, period_year, period_month)
);

CREATE TABLE consolidation_meta (
  id UUID PRIMARY KEY,
  schema_name VARCHAR,
  last_consolidated TIMESTAMP,
  event_count INT,
  duration_seconds FLOAT,
  status VARCHAR,  -- 'success', 'warning', 'error'
  next_scheduled TIMESTAMP
);

CREATE TABLE audit_trail (
  id UUID PRIMARY KEY,
  source_schema VARCHAR,  -- 'oswaldo_operacional'
  entity_id UUID,
  operation VARCHAR,
  timestamp TIMESTAMP,
  replicated_at TIMESTAMP,
  actor_id UUID
);
```

---

## 🔄 Fluxos de Operação

### Fluxo 1: Escrita Operacional

```
[Aplicação] 
    ▼ INSERT paciente INTO oswaldo_operacional.pacientes
[PostgreSQL Transação ACID]
    ├─ Validação (constraints, tipos)
    ├─ Execução (INSERT)
    ├─ Trigger (publica evento em Redis)
    └─ Commit/Rollback
    ▼
[Redis Stream: "paciente:created:id123"]
    ├─ event_id: "evt-abc123"
    ├─ entity_id: "id123"
    ├─ operation: "CREATE"
    ├─ timestamp: "2026-02-11T10:00:00Z"
    ├─ actor: "user-xyz"
    └─ data: {...}
    ▼
[Resposta à Aplicação]
    └─ Status 201 Created + id
```

### Fluxo 2: Consolidação Analítica (Batch)

```
[Consolidation Job - 2:00 AM]
    ├─ Conecta ao Redis (checkpoint: "2026-02-11T01:00:00Z")
    ├─ Busca eventos desde então
    ▼
[Processa Eventos]
    ├─ Para cada evento:
    │   ├─ Lê registro em oswaldo_operacional
    │   ├─ Aplica transformação (denormalização)
    │   ├─ Insere/Atualiza em oswaldo_analitico
    │   └─ Registra em audit_trail
    ├─ Calcula agregações (COUNT, SUM, AVG)
    ├─ Registra checkpoint novo
    ▼
[Publicar Métrica]
    ├─ duration: 120 segundos
    ├─ events_processed: 5000
    ├─ status: 'success'
    └─ next_run: 2026-02-12T02:00:00Z
```

### Fluxo 3: Consolidação com Erro

```
[Consolidation Job]
    ├─ Processa 3000 eventos OK
    ├─ Event 3001 falha (foreign key constraint)
    ▼
[Tratamento de Erro]
    ├─ Rollback da transação do evento
    ├─ Publica evento em DLQ (Dead Letter Queue)
    ├─ Registra: "Failed to process event evt-def789"
    ├─ Continua processando restantes
    ▼
[Retry Policy]
    ├─ DLQ consome mensagem em 5 minutos
    ├─ Tenta novamente (máx 3 tentativas)
    ├─ Se falha, gera alerta para DevOps
    └─ Último evento fica em análise manual
```

### Fluxo 4: Verificação de Violação

```
[Aplicação Maliciosa ou Com Bug]
    ▼ INSERT INTO oswaldo_analitico.consolidation_meta
[PostgreSQL Row-Level Security Policy]
    ├─ Verifica role do usuário
    ├─ Vê que role não tem WRITE em _analitico
    ├─ Rejeita operação
    ▼
[Trigger de Auditoria]
    ├─ Registra tentativa violação em audit_log
    ├─ Publica evento "security:violation"
    ▼
[Alert System]
    ├─ Envia para CloudWatch/Prometheus
    ├─ Dispara webhook para Slack/PagerDuty
    ├─ Contato: admin de segurança
    ▼
[Resposta à Aplicação]
    └─ 403 Forbidden + detail
```

---

## 📝 Resumo de Entregas Funcionais

| Requisito | Descrição | Prioridade |
|-----------|-----------|:---:|
| Segregação de Schemas | `*_operacional` e `*_analitico` separados | 🔴 CRÍTICA |
| Event Publishing | Quando operacional muda, evento | 🔴 CRÍTICA |
| Controle de Acesso | RLS policies no PostgreSQL | 🔴 CRÍTICA |
| Batch Consolidation | Job que replica e agrega | 🔴 CRÍTICA |
| Auditoria | Todos os acessos registrados | 🔴 CRÍTICA |
| Monitoramento | Métricas de replicação | 🟡 ALTA |
| Documentação | Guias e troubleshooting | 🟡 ALTA |
| Alertas | Violações de separação | 🟢 MÉDIA |
| Dashboard | Saúde de consolidação | 🟢 MÉDIA |

---

**Próximo Passo**: Leia `ESPECIFICACAO_TECNICA_SEPARACAO_OPERACIONAL_ANALITICO.md` para detalhes de implementação.
