# V2.0.0 - Keycloak: Autenticação e Autorização IntelliCare

> **Versão:** 2.0.0 | **Data Início:** 2026-03-06 | **Status:** 📋 Referência Técnica
> **Prioridade:** P0 (Crítica) | **Complexidade:** Alta | **Escopo:** Plataforma Completa
> **Rastreabilidade:** Pré-requisito para V2.0.2 (Admin + Gestor)

---

## 🎯 Objetivo

Documentar e implementar a **camada de identidade e acesso** do IntelliCare usando **Keycloak 24.0** como IdP centralizado, cobrindo:

✅ **Realm `bemcuidar`** — Configuração completa de realm, roles, clients e mappers
✅ **intellicare-auth** — Biblioteca Python para integração JWT/PKCE/SMART em todos os módulos
✅ **Portal Frontend** — Fluxo PKCE, refresh automático, multi-tenant token exchange
✅ **SMART-on-FHIR 2.0** — Launch EHR/standalone para integração com GRAHAME
✅ **Multi-tenancy** — JWT claims `tenant_id` + `tenants[]` → schemas isolados por tenant
✅ **Produção** — Traefik + Let's Encrypt + `auth.intellicare.ia.br`

---

## 📁 Documentos desta versão

| Arquivo | Conteúdo | Público-alvo |
|---------|----------|--------------|
| [`01_ESPECIFICACAO_FUNCIONAL.md`](./01_ESPECIFICACAO_FUNCIONAL.md) | Atores, fluxos de autenticação, casos de uso, regras de negócio | PO, arquitetos, designers |
| [`02_ESPECIFICACAO_TECNICA.md`](./02_ESPECIFICACAO_TECNICA.md) | Realm config, 14 clients, JWT structure, intellicare-auth API, PKCE, SMART-on-FHIR | Desenvolvedores, arquitetos |
| [`03_PLANO_IMPLEMENTACAO.md`](./03_PLANO_IMPLEMENTACAO.md) | 5 fases de implementação: infra → realm → módulos Python → portal → produção | Tech lead, DevOps, PMs |

---

## 🗺️ Arquitetura de Autenticação

```
┌─────────────────────────────────────────────────────────────────────┐
│                    auth.intellicare.ia.br:8080                       │
│                    Keycloak 24.0 — Realm: bemcuidar                  │
│                                                                       │
│   Realm Roles              Clients               JWKS Endpoint       │
│   ─────────────────        ─────────────────     ──────────────────  │
│   PLATFORM_ADMIN           intellicare-portal    /realms/bemcuidar/  │
│   PLATFORM_SUPPORT         intellicare-admin     protocol/openid-    │
│   PLATFORM_BILLING         intellicare-api       connect/certs       │
│   TENANT_GESTOR            + 12 módulos                              │
│   CLINICO / MEDICO                                                    │
│   ENFERMEIRO / RECEPCIONISTA                                          │
│   PACIENTE                                                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ JWT RS256 (validação local via JWKS)
           ┌────────────────┼────────────────┐
           │                │                │
           ▼                ▼                ▼
  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐
  │  Portal     │  │  Módulos     │  │  intellicare-   │
  │  React 19   │  │  Python      │  │  admin (8010)   │
  │  (porta 3001)│  │  FastAPI     │  │  intellicare-   │
  │             │  │  (8001-8013) │  │  gestor (8011)  │
  │  authService│  │              │  │                 │
  │  PKCE flow  │  │ intellicare- │  │ require_role    │
  │  TenantCtx  │  │ auth library │  │ (PLATFORM_ADMIN)│
  └─────────────┘  └──────────────┘  └─────────────────┘
```

---

## 🔑 Roles e Destinações

| Role | Nível | Destino Portal | Descrição |
|------|-------|----------------|-----------|
| `PLATFORM_ADMIN` | Realm | `/admin` | Superadmin IntelliCare — gerencia toda a plataforma |
| `PLATFORM_SUPPORT` | Realm | `/admin` (read-only) | Suporte técnico — visualização |
| `PLATFORM_BILLING` | Realm | `/admin/billing` | Faturamento da plataforma |
| `TENANT_GESTOR` | Realm | `/gestor` | Admin local — gerencia seu tenant |
| `CLINICO` | Realm | `/dashboard` | Profissional de saúde geral |
| `MEDICO` | Realm | `/dashboard` | Médico |
| `ENFERMEIRO` | Realm | `/dashboard` | Enfermeiro |
| `RECEPCIONISTA` | Realm | `/dashboard` | Recepcionista |
| `PACIENTE` | Realm | `/paciente` | Área do paciente (escopo futuro) |

---

## 🏗️ Clients Keycloak

| Client ID | Tipo | Usado por | Porta |
|-----------|------|-----------|-------|
| `intellicare-portal` | Public (PKCE) | Portal React (frontend) | 3001 |
| `intellicare-admin` | Public | Admin React (V2.0.2) | 8010 |
| `intellicare-api` | Bearer-only | Validação de tokens | — |
| `intellicare-wanda` | Confidential | WANDA orquestrador | 8004 |
| `intellicare-florence` | Confidential | FLORENCE RAG | 8001 |
| `intellicare-oswaldo` | Confidential | OSWALDO análise clínica | 8002 |
| `intellicare-donabedian` | Confidential | DONABEDIAN qualidade | 8003 |
| `intellicare-comunicacao` | Confidential | Comunicação WhatsApp | 8005 |
| `intellicare-geralda` | Confidential | GERALDA gestão | 8006 |
| `intellicare-zilda` | Confidential | ZILDA CNES/DATASUS | 8007 |
| `intellicare-minerva` | Confidential | MINERVA documentos | 8008 |
| `intellicare-pierre` | Confidential | PIERRE PubMed | 8009 |
| `intellicare-grahame` | Confidential | GRAHAME FHIR R4 | 8012 |
| `intellicare-gestor` | Confidential | GESTOR módulos | 8011 |
| `intellicare-nise` | Confidential | NISE chatbot | 8013 |

---

## 📊 Status de Implementação

| Fase | Entregável | Status |
|------|------------|--------|
| 0 | Infraestrutura: Docker, PostgreSQL Keycloak, Traefik | ✅ Concluído |
| 1 | Realm `bemcuidar`: roles, clients, mappers, realm.json | ✅ Concluído |
| 2 | intellicare-auth: biblioteca Python JWT/PKCE/SMART | ✅ Concluído |
| 3 | Portal Frontend: authService.ts PKCE + TenantContext | 🔄 Em Progresso |
| 4 | SMART-on-FHIR 2.0: GRAHAME + EHR launch | ⬜ Pendente |
| 5 | Produção: Traefik HTTPS + monitoramento + alertas | ⬜ Pendente |

---

## 🌐 Endpoints Principais

```
Base URL:   https://auth.intellicare.ia.br
Realm URL:  https://auth.intellicare.ia.br/realms/bemcuidar

Auth:       /realms/bemcuidar/protocol/openid-connect/auth
Token:      /realms/bemcuidar/protocol/openid-connect/token
UserInfo:   /realms/bemcuidar/protocol/openid-connect/userinfo
JWKS:       /realms/bemcuidar/protocol/openid-connect/certs
Logout:     /realms/bemcuidar/protocol/openid-connect/logout
SMART:      /realms/bemcuidar/.well-known/smart-configuration
Admin API:  /admin/realms/bemcuidar/
Health:     /health/ready
```

---

## 🔗 Relacionamentos

- **Pré-requisito de:** V2.0.2 (Admin + Gestor), todos os módulos clínicos
- **Integra com:** `intellicare-core` (tenant resolver), `intellicare-wanda` (token exchange), `intellicare-grahame` (SMART-on-FHIR)
- **Deploy:** `docker-compose.keycloak.yml` + Traefik + PostgreSQL dedicado

---

*Gerado em: 2026-03-06 | Responsável: Eduardo Garabini*
