# VISÃO GERAL DO SISTEMA — IntelliCare

**Data:** 2026-03-08
**Status:** Canônico — aprovado por Eduardo
**Atualizar este documento a cada decisão arquitetural relevante**

---

## 1. O que é o IntelliCare

IntelliCare é uma plataforma modular de saúde baseada em inteligência artificial.
É um SaaS multi-tenant: múltiplas organizações de saúde (tenants) operam de forma
isolada na mesma plataforma.

A plataforma é composta por:
- Agentes de IA especializados (microserviços Python FastAPI)
- Frontends por perfil de acesso
- Uma orquestradora central (WANDA) que coordena todos os agentes

---

## 2. Arquitetura de frontends

```
PÚBLICO (sem login)
────────────────────────────────────────────────
www.intellicare.ia.br
  React — intellicare-portal (CONGELADO)
  Finalidade: marketing, showcase dos agentes, dashboards públicos de eficiência
  Contém: apresentação do sistema, importância dos agentes, aprovação de clientes
  Login: botão que autentica via Keycloak e redireciona por role (ver abaixo)

ACESSO RESTRITO (requer login)
────────────────────────────────────────────────
admin.intellicare.ia.br
  FastAPI serve HTML próprio — intellicare-admin (porta 8010)
  Acesso: role PLATFORM_ADMIN
  Finalidade: gestão da plataforma (tenants, gestores, planos, billing)
  Painéis extras: DRC, Diabetes, Hipertensão, Câncer (establishments registrados)

gestor.intellicare.ia.br
  FastAPI serve HTML próprio — intellicare-gestor (porta 8011)
  Acesso: role TENANT_GESTOR
  Finalidade: gestão do tenant (unidades, profissionais, alocações)
  Painéis extras: DRC, Diabetes, Hipertensão, Câncer (establishments registrados)

intellicare.ia.br/[tenant]
  React — frontend clínico (módulo NOVO — não é o portal)
  Acesso: PROFISSIONAL e PACIENTE, permissões definidas por plano do tenant
  Finalidade: plataforma de cuidado conectado
  Suporte ao PROFISSIONAL: via WANDA (orquestradora)
  Suporte ao PACIENTE: via GERALDA (que responde à WANDA)
  O que é visível: controlado pelas permissões do cliente
```

---

## 3. Fluxo de login

```
Usuário acessa www.intellicare.ia.br
    ↓
Clica em "Login"
    ↓
Portal envia para Keycloak (realm: intellicare)
    ↓
Usuário autentica (usuário + senha)
    ↓
Keycloak retorna token JWT com role e tenant_id
    ↓
Portal lê a role:
  ├── PLATFORM_ADMIN  → redireciona para admin.intellicare.ia.br
  ├── TENANT_GESTOR   → redireciona para gestor.intellicare.ia.br
  ├── PROFISSIONAL    → redireciona para intellicare.ia.br/[tenant]
  └── PACIENTE        → redireciona para intellicare.ia.br/[tenant]
```

---

## 4. Keycloak — estrutura de realms

```
Keycloak (https://auth.intellicare.ia.br)
├── master          ← realm interno do Keycloak (nunca alterar)
└── intellicare     ← realm único da plataforma IntelliCare
    ├── Clientes registrados
    │   ├── intellicare-portal    (public, SPA)
    │   ├── intellicare-admin     (confidential)
    │   ├── intellicare-gestor    (confidential)
    │   └── intellicare-clinical  (confidential, futuro)
    └── Roles do realm
        ├── PLATFORM_ADMIN    → acessa admin.intellicare.ia.br
        ├── TENANT_GESTOR     → acessa gestor.intellicare.ia.br
        ├── PROFISSIONAL      → acessa intellicare.ia.br/[tenant]
        └── PACIENTE          → acessa intellicare.ia.br/[tenant]
```

**Regra canônica:** existe apenas um realm de aplicação: `intellicare`.
Nenhum módulo deve referenciar outro realm (ex: `bemcuidar`).
O isolamento de tenants é feito via claim `tenant_id` no token, não via realm.

---

## 5. Agentes e orquestração

WANDA é a orquestradora master. Todos os agentes respondem a ela.

```
WANDA (intellicare-wanda — porta 8004)
├── FLORENCE   (8001) — RAG + Protocolos Clínicos
├── OSWALDO    (8002) — Análise Clínica + FHIR
├── DONABEDIAN (8003) — Qualidade + Indicadores
├── GERALDA    (8006) — Atendimento e suporte ao PACIENTE
├── ZILDA      (8007) — CNES + DATASUS
├── MINERVA    (8008) — Extração de Documentos (MCP)
├── PIERRE     (8009) — Busca Científica PubMed + Tavily (MCP)
├── GRAHAME    (8012) — FHIR R4 + CDS Hooks + Terminologia
└── NISE       (8013) — Chatbot + Treinamento (Flowise/Kestra)
```

No frontend clínico (`intellicare.ia.br/[tenant]`):
- O PROFISSIONAL interage com a plataforma → WANDA coordena os agentes necessários
- O PACIENTE interage com GERALDA → GERALDA consulta WANDA quando necessário

---

## 6. Programas de saúde prioritários

Quatro programas implementados e disponíveis para tenants com acesso registrado.
**NÃO aparecem no portal público.**
Aparecem no admin e no gestor para establishments registrados.

| Programa | Status | Onde aparece |
|---|---|---|
| DRC (Doença Renal Crônica) | Em implementação | Admin + Gestor |
| Diabetes | Em implementação | Admin + Gestor |
| Hipertensão | Em implementação | Admin + Gestor |
| Câncer | Em implementação | Admin + Gestor |

---

## 7. Módulos de infraestrutura

| Módulo | Porta | Função |
|---|---|---|
| intellicare-core | — | SDK compartilhado (BaseAgent, contratos, tenant, monitoramento) |
| intellicare-auth | — | Biblioteca de autenticação Keycloak/SMART-on-FHIR |
| intellicare-conhecimento | — | Protocolos FHIR, RAG, terminologia, AI-GED (Knowledge Engine) |
| intellicare-admin | 8010 | Administração da plataforma |
| intellicare-gestor | 8011 | Gestão por tenant |
| PostgreSQL | 5432 | Banco principal (schema por módulo por tenant) |
| Redis | 6379 | Cache + Pub/Sub + Rate Limiting |
| Prometheus | 9090 | Métricas |
| Grafana | 3000 | Dashboards de monitoramento |
| Traefik | 80/443 | Reverse proxy + TLS |

---

## 8. Decisões arquiteturais registradas

| Data | Decisão | Motivo |
|---|---|---|
| 2026-03-08 | Portal React congelado — não receberá mais desenvolvimento | É vitrine externa; features clínicas vão para o frontend clínico |
| 2026-03-08 | Frontend clínico é módulo React separado do portal | Separação de concerns: marketing vs. plataforma clínica |
| 2026-03-08 | Realm Keycloak único: `intellicare` | Simplificação; isolamento via claim tenant_id, não via realm |
| 2026-03-08 | WANDA é orquestradora master — todos os agentes respondem a ela | Arquitetura hub-and-spoke para coordenação de IA |
| 2026-03-08 | 4 programas prioritários (DRC, Diabetes, HAS, Câncer) não são públicos | Benefício exclusivo de establishments registrados |
