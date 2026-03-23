# IntelliCare V3 — Documentação de Arquitetura

> Mantida pelo ARQUITETO. Atualizada ao encerrar cada sprint.
> Última atualização: 2026-03-21 | Sprint 2026-04-18

---

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `01_VISAO_SISTEMA.md` | C4 Context + C4 Container, stack tecnológica |
| `02_MODULOS_E_DEPENDENCIAS.md` | Grafo de dependências, Executor Matrix, padrão multi-tenant |
| `03_FLUXOS_CLINICOS.md` | Atendimento clínico end-to-end, CarePlanner com fallback, estados de jornada, notificações |
| `04_INFRAESTRUTURA_E_DEPLOY.md` | Docker services, CI/CD pipeline, schema-per-tenant, migrations, gotchas históricos |
| `05_CAMADA_IA.md` | Arquitetura LLM atual, padrão Hybrid, roadmap IA (Marie, MinIO) |

## Decisões Arquiteturais (ADRs)

Os ADRs vivem em `docs/adr/` na raiz do projeto:

| ADR | Título | Status |
|-----|--------|--------|
| ADR-001 | Executor Matrix — classificação Worker/Agent/Hybrid/Human | ✅ Implementado |
| ADR-002 | Módulo Marie — Dify como orquestrador IA avançado | 🔬 Proposto — aguarda gatilho |
| ADR-003 | MinIO — object storage médico S3-compatible | 🔬 Proposto — aguarda gatilho |

## Como ler os diagramas

Os diagramas usam **Mermaid** — renderizados nativamente no GitHub, Obsidian e VS Code (extensão Mermaid Preview).

- `C4Context` / `C4Container` — visão sistêmica (requer plugin C4 no Obsidian)
- `graph TD/LR` — dependências e fluxos
- `sequenceDiagram` — interações temporais
- `stateDiagram-v2` — máquinas de estado
- `flowchart` — decisões e ramificações
- `timeline` — roadmap temporal
