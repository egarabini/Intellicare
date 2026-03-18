# IntelliCare V3

[![CI](https://github.com/egarabini/Intellicare/actions/workflows/ci.yml/badge.svg)](https://github.com/egarabini/Intellicare/actions/workflows/ci.yml)

> Plataforma modular de saúde — 1 serviço, módulos dinâmicos, RAG/SLM/pgvector.

## Arquitetura

```
packages/intellicare-core/   → SDK compartilhado (contratos, FHIR, tenant, monitoring)
modules/admin/               → Administração do sistema
modules/gestor/              → Gestão clínica
modules/cuidado/             → Cuidado ao paciente (RAG + SLM)
modules/florence/            → Protocolos clínicos (RAG)
modules/oswaldo/             → Análise clínica + FHIR
configs/                     → Configurações por vertical/plano/overlay
infra/                       → Docker, PostgreSQL, Redis, Prometheus
deploy/                      → Scripts de deploy e CI/CD
tests/                       → Testes unitários, integração, e2e, arquitetura
tools/                       → Linters customizados, scripts utilitários
docs/                        → Documentação viva (Obsidian vault)
```

## Início Rápido

```bash
# Infraestrutura mínima
docker compose up -d

# Módulo admin (desenvolvimento)
cd modules/admin
pip install -e ".[dev]"
uvicorn admin.api.app:app --reload --port 8010
```

## Documentação

- `AGENTS.md` — Guia para agentes de IA (índice, regras, arquitetura)
- `docs/` — Vault Obsidian com design docs, demandas, referências

## Histórico

| Versão | Status | Descrição |
|--------|--------|-----------|
| V1 | Arquivado | Protótipo inicial |
| V2 | Arquivado (branch `v2-archive`) | Monolítico, 10+ containers |
| V3 | **Ativo** | 1 serviço, módulos dinâmicos, RAG/SLM/pgvector |

---

*IntelliCare — Cuidando de quem cuida.*
