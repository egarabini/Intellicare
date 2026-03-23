# IntelliCare V3 — Visão Geral do Sistema

> Documentação técnica de arquitetura. Mantida pelo ARQUITETO.
> Última atualização: 2026-03-21 | Sprint 2026-04-18

---

## Contexto C4 — Nível 1: Sistema no Mundo

```mermaid
C4Context
    title IntelliCare V3 — Contexto do Sistema

    Person(admin, "Administrador", "Gerencia tenants, planos e infraestrutura da plataforma")
    Person(gestor, "Gestor de Tenant", "Opera unidade clínica, agenda, CarePlanner e relatórios")
    Person(clinico, "Clínico", "Realiza atendimentos, registra notas Florence e prescrições Oswaldo")
    Person(paciente, "Paciente", "Acompanha jornadas, agenda e histórico clínico")

    System(intellicare, "IntelliCare V3", "Plataforma assistencial multimodal com IA clínica integrada")

    System_Ext(keycloak, "Keycloak", "Autenticação e autorização OAuth2/OIDC")
    System_Ext(evolution, "Evolution API", "Gateway WhatsApp Business via Baileys")
    System_Ext(kestra, "Kestra", "Orquestrador de workflows de jornadas clínicas")
    System_Ext(ollama, "Ollama / OpenAI", "Modelos LLM para sugestão clínica (local ou cloud)")
    System_Ext(grafana, "Prometheus + Grafana", "Observabilidade e alertas operacionais")

    Rel(admin, intellicare, "Administra via", "HTTPS / AdminUI")
    Rel(gestor, intellicare, "Opera via", "HTTPS / GestorUI")
    Rel(clinico, intellicare, "Atende via", "HTTPS / ClinicoUI")
    Rel(paciente, intellicare, "Acompanha via", "HTTPS / PacienteUI")
    Rel(intellicare, keycloak, "Autentica usuários via", "OAuth2 / OIDC")
    Rel(intellicare, evolution, "Envia/recebe WhatsApp via", "REST API")
    Rel(intellicare, kestra, "Dispara e monitora jornadas via", "REST API")
    Rel(intellicare, ollama, "Consulta LLM para sugestões clínicas via", "OpenAI-compatible API")
    Rel(grafana, intellicare, "Coleta métricas de", "Prometheus scrape")
```

---

## Containers C4 — Nível 2: Componentes Principais

```mermaid
C4Container
    title IntelliCare V3 — Containers

    Person(clinico, "Clínico / Gestor / Admin / Paciente")

    Container(adminui, "AdminUI", "React 18 + Mantine UI 7", "SPA para administração da plataforma")
    Container(gestorui, "GestorUI", "React 18 + Mantine UI 7", "SPA para gestão do tenant")
    Container(clinicoui, "ClinicoUI", "React 18 + Mantine UI 7", "SPA para atendimento clínico")
    Container(pacienteui, "PacienteUI", "React 18 + Mantine UI 7", "SPA para acompanhamento do paciente")

    Container(api, "intellicare-service", "FastAPI + Python 3.12", "API principal — módulos admin, gestor, cuidado, florence, oswaldo, careplanner, notificações")

    ContainerDb(postgres, "PostgreSQL 16", "SQL", "Schema-per-tenant. Schema 'platform' para metadados globais")
    ContainerDb(redis, "Redis 7", "Cache / Pub-Sub", "Pub/Sub para notificações SSE, cache de sessão")

    Container_Ext(keycloak, "Keycloak 24", "OAuth2 / OIDC", "IAM — realms por tenant")
    Container_Ext(evolution, "Evolution API v2.3.7", "WhatsApp Gateway", "Instância 'intellicare' conectada via QR")
    Container_Ext(kestra, "Kestra 0.20", "Workflow Engine", "Flows de jornada condicional")
    Container_Ext(traefik, "Traefik v2.11", "Reverse Proxy", "TLS termination, roteamento por path")

    Rel(clinico, traefik, "HTTPS")
    Rel(traefik, adminui, "/ admin-ui/")
    Rel(traefik, gestorui, "/gestor-ui/")
    Rel(traefik, clinicoui, "/clinico-ui/")
    Rel(traefik, pacienteui, "/paciente-ui/")
    Rel(traefik, api, "/admin, /gestor, /cuidado, /florence, /oswaldo, /careplanner, /auth, /notifications")
    Rel(api, postgres, "asyncpg / SQLAlchemy")
    Rel(api, redis, "aioredis")
    Rel(api, keycloak, "JWT validation / Admin API")
    Rel(api, evolution, "REST — dispatch WhatsApp")
    Rel(api, kestra, "REST — trigger flows")
```

---

## Stack tecnológica

| Camada | Tecnologia | Versão | Papel |
|--------|-----------|--------|-------|
| Frontend | React + Mantine UI | 18 / 7 | 4 SPAs (Admin, Gestor, Clínico, Paciente) |
| Build Frontend | Vite | 5 | Bundler com `optimizeDeps` para Docker |
| Backend | FastAPI | 0.111 | API assíncrona — módulos por domínio |
| Runtime | Python | 3.12 | Async-first com `asyncpg` |
| ORM | SQLAlchemy | 2.x async | Schema-per-tenant via `search_path` |
| Migrations | Alembic | 1.13 | Programático para provisionamento automático |
| Banco | PostgreSQL | 16 | Schema-per-tenant + schema `platform` global |
| Cache/PubSub | Redis | 7 | SSE notifications + push subscriptions |
| Auth | Keycloak | 24 | OAuth2/OIDC, realms por tenant |
| Proxy | Traefik | v2.11 | TLS Let's Encrypt, routing por path |
| WhatsApp | Evolution API | v2.3.7 | Baileys v7 — único compatível com QR estável |
| Workflows | Kestra | 0.20 | Flows condicionais com Switch nativo |
| LLM | Ollama / OpenAI | — | `shared/llm.py` wrapper com fallback rule-based |
| PDF | WeasyPrint + Jinja2 | — | Relatórios clínicos e de jornada |
| Observabilidade | Prometheus + Grafana | v2.51 / v10.4 | 9 alert rules, 13+ panels |
| Containerização | Docker + Compose | — | Multi-stage builds, profiles por ambiente |
| CI/CD | GitHub Actions | — | pytest + build dos 3 frontends |
