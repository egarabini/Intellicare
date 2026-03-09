# 🔬 Análise Rápida — Medplum Platform
**Data:** 2026-02-23 | **Objetivo:** Avaliar a visão, arquitetura e oportunidades de absorção para o IntelliCare

---

## 1. O Que É o Medplum

O Medplum é uma **plataforma completa de desenvolvimento em saúde**, com foco em FHIR como linguagem nativa. Não é uma biblioteca — é um produto inteiro construído como monorepo TypeScript (27 packages, Apache 2.0).

### Stack Técnico
| Camada | Medplum | IntelliCare (hoje) |
|---|---|---|
| **Backend** | Express (Node.js) — servidor único | FastAPI (Python) — microserviços modulares |
| **Banco** | PostgreSQL (FHIR nativo em tabelas) | PostgreSQL (schema por tenant) |
| **Cache/Jobs** | Redis + BullMQ | Redis |
| **Auth** | OAuth2/OIDC próprio + SMART-on-FHIR | Keycloak + JWT |
| **Frontend** | React + 118 componentes médicos | Next.js (portal) |
| **Observabilidade** | OpenTelemetry nativo | Prometheus + Grafana |
| **IaC** | AWS CDK + Terraform + Helm | Docker Compose |
| **Integração** | HL7v2 Agent + C-CDA + MCP | FHIR client (httpx) + MCP |

---

## 2. Minha Avaliação — A Visão do Medplum

### ✅ O que é brilhante (e devemos absorver)

#### 2.1 FHIR como Cidadão de Primeira Classe
O Medplum trata FHIR não como um adaptador externo, mas como **a linguagem do banco de dados**. Cada recurso FHIR é armazenado em PostgreSQL com:
- Indexação de **SearchParameters** FHIR nativos
- SQL builder de 37KB que traduz FHIR Search para SQL otimizado
- Suporte a todos os tipos de busca FHIR (token, reference, date, composite, etc.)
- **FHIRPath** como linguagem de expressão para regras e transformações

> **Impacto para IntelliCare:** Hoje, nosso `intellicare-grahame` faz bridge para FHIR, mas os dados vivem em modelos proprietários. Absorver essa visão significa que **cada dado clínico já nasce FHIR**, eliminando a tradução.

#### 2.2 Subscriptions (Event-Driven FHIR)
O Medplum implementa **FHIR Subscriptions R5** completo:
- WebSocket para real-time
- REST hooks para webhooks
- Filtros FHIR nativos (ex: "notifique quando criar um Observation com code=glucose")
- Workers BullMQ processando eventos de forma assíncrona

> **Impacto:** Nossa `intellicare-comunicacao` poderia usar esse modelo para disparar notificações baseadas em mudanças clínicas reais, em vez de triggers manuais.

#### 2.3 Bots (Server-Side Logic)
O conceito de **Bots** é genial: funções TypeScript que executam server-side em resposta a eventos FHIR. Exemplos:
- Bot que roda quando chega um resultado de lab → cria um alerta ao médico
- Bot que roda quando cria um Patient → envia welcome email
- **Executa em VM isolada** com acesso ao `MedplumClient`

> **Impacto:** Isso é exatamente o que nossos módulos Florence e Geralda fazem de forma fixa. Com Bots, essa lógica seria **configurável por tenant** sem precisar redeployar.

#### 2.4 Access Policies (ABAC Granular)
O sistema de **Access Policies** é sofisticado:
- Políticas por recurso FHIR, por campo, por compartment
- Suporte a FHIRPath para regras dinâmicas
- Critérios baseados em Encounter, Patient, Organization
- Políticas por ProjectMembership (equivalente ao nosso tenant/role)

> **Impacto:** Nosso RBAC com Keycloak roles é básico comparado. Absorver Access Policies permite controle granular (ex: "enfermeiro só vê Observations do seu setor").

#### 2.5 53 Operações FHIR Implementadas
Medplum implementa operações FHIR padrão:
- `$everything` (Patient), `$summary`, `$export` (Bulk Data)
- `$apply` (PlanDefinition → CarePlan), `$evaluate-measure`
- CodeSystem `$lookup`, `$validate-code`, `$expand`
- ConceptMap `$translate`
- `$extract` (Questionnaire → recursos FHIR), `$graph`
- **AI operations** (`ai.ts` — 9.5KB)
- **C-CDA export/import**

> **Impacto:** Nosso Donabedian poderia usar `$evaluate-measure` nativo. Florence poderia usar `$apply` para gerar CarePlans. Grahame ganharia todas essas operações de graça.

#### 2.6 React Component Library (118 Componentes Médicos)
Uma biblioteca React completa para interfaces médicas:
- `ResourceForm`, `ResourceTable`, `ResourceTimeline`
- `QuestionnaireBuilder`, `QuestionnaireForm`
- `PatientSummary`, `PatientTimeline`, `EncounterTimeline`
- `DiagnosticReportDisplay`, `MeasureReportDisplay`
- `Scheduler`, `SearchControl`, `CcdaDisplay`
- Chat, Assinatura digital, CodeableConceptInput

> **Impacto:** Nosso portal frontend poderia usar esses componentes para construir interfaces clínicas ricas em dias, não semanas.

#### 2.7 MCP Server Nativo
O Medplum tem um **MCP Server** embutido que expõe recursos FHIR para assistentes de IA.

> **Impacto:** Nosso SuperZ/PIERRE faz isso externamente. Ter MCP nativo no CDR é muito mais elegante.

---

### ⚠️ Diferenças Fundamentais de Arquitetura

| Aspecto | Medplum | IntelliCare |
|---|---|---|
| **Modelo de Deploy** | Servidor monolítico | Microserviços separados |
| **Multi-tenancy** | `Project` = tenant (mesmo banco, isolamento por AccessPolicy) | Schema isolation por tenant |
| **Linguagem** | TypeScript/Node.js | Python |
| **Auth** | Auth server próprio embutido | Keycloak externo |
| **AI/ML** | Operação `$ai` com providers | Florence/Geralda como agentes Python |
| **Documentação** | 34 seções, Docusaurus | Docs Markdown no repo |

---

## 3. Desafios da Absorção

### 🔴 Críticos

1. **Diferença de linguagem (TypeScript vs Python)**
   - Medplum é 100% TypeScript. Precisaremos **re-implementar** os conceitos, não copiar código
   - Isso significa entender a **arquitectura** e reproduzir em Python/FastAPI

2. **FHIR Storage nativo requer migração de dados**
   - Nossos modelos atuais são proprietários (ex: CareManager do Geralda, Protocol do Oswaldo)
   - Migrar para FHIR nativo significa redesenhar os schemas
   - Estratégia sugerida: **dual-write** durante transição

3. **Escopo enorme — risco de se perder**
   - 27 packages, 500+ arquivos. Precisamos de disciplina para absorver **por fatia**
   - Não tentar fazer tudo de uma vez

### 🟡 Moderados

4. **Auth: Keycloak vs Auth próprio**
   - Medplum tem auth embutido. Nós usamos Keycloak
   - Decisão: manter Keycloak e adaptar Access Policies FHIR em cima dele
   - Ou: migrar para auth próprio (mais controle, mais trabalho)

5. **Frontend: React puro vs Next.js**
   - Componentes Medplum são React + Mantine UI
   - Nosso portal usa Next.js — a integração é possível mas requer adaptação

6. **Subscriptions requer repensar a Comunicação**
   - Hoje comunicação é channel-based (SMS, email, WhatsApp)
   - Com subscriptions FHIR, o trigger passa a ser data-driven
   - Não substitui — **complementa** o que temos

### 🟢 Baixo Risco

7. **Bots podem ser implementados em Python**
   - O conceito é simples: função que roda em resposta a evento
   - Podemos implementar com Celery/BullMQ + sandbox Python

8. **Operações FHIR são incrementais**
   - Cada operação pode ser implementada individualmente
   - `$everything`, `$summary`, `$evaluate-measure` são grandes quick wins

---

## 4. Benefícios Concretos para IntelliCare

### Curto Prazo (1-2 sprints)
| O quê | Impacto | Esforço |
|---|---|---|
| Absorver modelo de **Access Policies FHIR** | Controle granular por recurso/campo/tenant | Médio |
| Implementar **FHIR Subscriptions** no Grahame | Notificações event-driven nativas | Médio |
| Portar **3 operações FHIR** ($everything, $summary, $evaluate-measure) | CDR mais completo | Baixo |

### Médio Prazo (3-5 sprints)
| O quê | Impacto | Esforço |
|---|---|---|
| **Bots/Automations engine** (Python) | Lógica configurável por tenant sem redeploy | Alto |
| **FHIR-native storage** para novos recursos | Dados já nascem FHIR, sem tradução | Alto |
| Absorver **React components** para portal clínico | UI clínica rica em menos tempo | Médio |
| **QuestionnaireBuilder** para formulários dinâmicos | Tenants criam forms sem código | Médio |

### Longo Prazo (6+ sprints)
| O quê | Impacto | Esforço |
|---|---|---|
| Migrar dados existentes para **FHIR storage nativo** | Elimina camada de tradução | Muito Alto |
| **SMART-on-FHIR launch** para apps de terceiros | Ecossistema de apps | Alto |
| **CDS Hooks** para decisão clínica em tempo real | Diferencial competitivo enorme | Alto |
| **Certify ONC** (se mirar mercado US) | Compliance regulatório | Muito Alto |

---

## 5. Minha Recomendação

### A Visão Certa: **"FHIR-First, Python-Native"**

Não copiar o Medplum — **absorver sua filosofia** e implementar com nossos pontos fortes:

1. **Manter Python/FastAPI** — nossa equipe é excelente nisso, e IA/ML é superior em Python
2. **Manter microserviços** — mais resiliente que monolito para multi-tenant
3. **Adotar FHIR como linguagem de dados** — o conceito mais valioso do Medplum
4. **Implementar Bots em Python** — mais poderoso que TypeScript para ML/NLP
5. **Absorver Access Policies** — nosso RBAC precisa evoluir
6. **Usar React components seletivamente** — para o portal clínico

### Próximo Passo Sugerido

Criar um **roadmap de absorção** organizado em ondas:

```
Onda 1: FHIR Operations + Subscriptions  (Grahame + Comunicação)
Onda 2: Bots Engine + Access Policies     (Core + Auth)
Onda 3: FHIR-Native Storage              (Core + todos os módulos)
Onda 4: React Components + SMART Launch   (Portal)
```

**Quer que eu detalhe o planejamento de alguma dessas ondas?**

---

## Referência: Mapa do Código Medplum

```
medplum-main/packages/
├── core/           → SDK client (159KB client.ts) — FHIRPath, Search, Types
├── server/         → API Express
│   ├── auth/       → 21 módulos (login, MFA, Google SSO, scopes)
│   ├── fhir/       → CDR + Repo (107KB) + SQL (37KB) + Search (69KB)
│   │   ├── operations/  → 53 operações FHIR ($everything, $apply, etc.)
│   │   ├── accesspolicy.ts → ABAC granular
│   │   └── sharding.ts    → Database sharding
│   ├── oauth/      → OAuth2/OIDC + SMART-on-FHIR
│   ├── bots/       → Server-side function execution
│   ├── mcp/        → MCP Server para AI
│   ├── workers/    → BullMQ (subscriptions, cron, reindex)
│   └── subscriptions/ → WebSocket + REST hook
├── react/          → 118 componentes médicos React
├── fhir-router/    → URL router FHIR padrão
├── fhirtypes/      → TypeScript types de todos recursos FHIR
├── definitions/    → SearchParams, ValueSets, StructureDefinitions
├── ccda/           → C-CDA import/export
├── hl7/            → HL7v2 client/server
├── agent/          → On-premise agent (bridge HL7v2/FHIR)
├── cli/            → CLI para deploy e gestão
├── cdk/            → AWS CDK (infra as code)
├── app/            → Frontend web app
├── docs/           → Documentação (34 seções)
└── mock/           → Mock server para testes
```
