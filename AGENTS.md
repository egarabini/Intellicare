# AGENTS.md — IntelliCare V3
# Guia para Agentes de IA

> Leia este arquivo primeiro. Ele é um índice — não uma enciclopédia.
> Para detalhes, siga os links para `docs/`.

---

## O que é o IntelliCare

Plataforma modular de saúde. **1 serviço Python** (`intellicare-service`) que carrega
módulos dinamicamente. Comunicação via REST + HL7 FHIR R4. RAG + SLM + pgvector como
triad central de IA clínica.

---

## Mapa de Módulos

| Módulo | Diretório | Porto | Papel |
|--------|-----------|-------|-------|
| admin | `modules/admin/` | 8010 | Administração do sistema |
| gestor | `modules/gestor/` | 8011 | Gestão clínica |
| cuidado | `modules/cuidado/` | 8004 | Cuidado ao paciente + RAG/SLM |
| florence | `modules/florence/` | 8001 | Protocolos clínicos RAG |
| oswaldo | `modules/oswaldo/` | 8002 | Análise clínica + FHIR |

SDK compartilhado: `packages/intellicare-core/`

---

## 5 Regras que Nunca Quebram

1. **Contrato obrigatório** — Todo módulo implementa `BaseAgent` e expõe
   `GET /health`, `GET /info`, `POST /analyze`.

2. **Dependências apenas para baixo** — `contracts → config → repository → services → api`.
   Nunca importe `services` dentro de `contracts`.

3. **Multi-tenancy via schema PostgreSQL** — Cada tenant é `tenant_{slug}`.
   Nunca use tabelas globais entre tenants. Use `TenantAwareSessionFactory`.

4. **Segredos nunca no código** — Use `.env` (local) ou variáveis de ambiente (produção).
   O arquivo `keycloak_client_secrets.json` está no `.gitignore`.

5. **Obsidian vault = docs/** — Toda documentação vive em `docs/`.
   Os mesmos arquivos servem GitHub, agentes e pipeline RAG.

---

## Estrutura de Camadas (por módulo)

```
modules/<nome>/
├── <nome>/
│   ├── contracts.py      # Schemas Pydantic — sem imports de camadas superiores
│   ├── config.py         # Settings (pydantic-settings)
│   ├── repository.py     # Acesso a dados (SQLAlchemy async)
│   ├── services.py       # Lógica de negócio
│   └── api/
│       ├── app.py        # FastAPI app + lifespan
│       └── routes.py     # Endpoints
├── tests/
├── pyproject.toml
└── Dockerfile
```

---

## Onde Encontrar Mais

| Tópico | Arquivo |
|--------|---------|
| Design e princípios | `docs/design-docs/core-beliefs.md` |
| Demandas ativas | `docs/demandas/` |
| Referências FHIR | `docs/references/fhir-r4-recursos-usados.md` |
| Roadmap | `docs/design-docs/PLANS.md` |

---

## Workflow de Demandas (DEM-NNN)

Cada demanda tem 5 documentos em `docs/demandas/DEM-NNN_NOME/`:

| Doc | Autor | Conteúdo |
|-----|-------|---------|
| `01_FUNCIONAL.md` | PLANEJADOR | O quê e por quê |
| `02_TECNICA.md` | PLANEJADOR | Como implementar (comandos exatos) |
| `03_PLANO.md` | DESENVOLVEDOR | Plano de execução |
| `04_DIARIO.md` | DESENVOLVEDOR | Log de execução |
| `05_FINALIZACAO.md` | DESENVOLVEDOR | Resultado + lições |

Agente desenvolvedor: leia `01_FUNCIONAL.md` e `02_TECNICA.md` antes de qualquer ação.
