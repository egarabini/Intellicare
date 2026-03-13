---
tipo: especificacao-funcional
demanda: DEM-001
titulo: Vault Obsidian + Documentação Base
fase: 0
sprint: "0.1"
status: aprovado
planejador: Claude
criado: 2026-03-13
depende_de:
  - DEM-000_MIGRACAO
habilita:
  - DEM-002_INFRA_DOCKER
tags:
  - fase-0
  - docs
  - vault
  - p0
---

# DEM-001 — Vault Obsidian + Documentação Base

## Objetivo

Transformar o diretório `docs/` do repositório IntelliCare V3 em um **vault Obsidian
funcional** — com templates, ADRs, notas de módulos e dashboard de demandas.

Sem isso, os agentes desenvolvedores não têm:
- Contexto estruturado para ler antes de codificar
- Templates para criar novos documentos de demanda com consistência
- Decisões arquiteturais registradas e rastreáveis
- Dashboard para ver o estado de todas as DEMs em andamento

---

## Contexto

A DEM-000 criou a estrutura esqueleto do repositório. O `docs/` tem apenas placeholders.

O Obsidian já é o documentador oficial do projeto (Meu Cofre). A decisão é que
`docs/` **É** o vault — os mesmos arquivos `.md` servem simultaneamente:

- GitHub (render markdown + frontmatter)
- Obsidian (knowledge base navegável com graph, templates, Dataview)
- Agentes (frontmatter YAML parseável como contexto)
- RAG/pgvector (ingerível via `tools/scripts/ingest_docs.py` — DEM-002)

---

## Escopo

### O que está incluído

| Bloco | O que cria | Por quê |
|-------|-----------|---------|
| 1 | `docs/.gitignore` | Excluir `.obsidian/` e `.trash/` do git |
| 2 | `docs/_templates/` (6 templates) | Padronizar criação de DEMs |
| 3 | `docs/index.md` (MOC) | Ponto de entrada do vault |
| 4 | `docs/decisoes/` (3 ADRs) | Registrar decisões arquiteturais críticas |
| 5 | `docs/modulos/` (5 notas) | Uma nota por módulo: contexto para agentes |
| 6 | `docs/demandas/_dashboard.md` | Dashboard Dataview de todas as DEMs |
| 7 | `docs/design-docs/` (6 docs) | Princípios, produto, qualidade, segurança, planos |
| 8 | `docs/demandas/DEM-001_VAULT_OBSIDIAN/` | Autopublicação desta demanda |

### O que NÃO está incluído

- Nenhum código Python ou infraestrutura
- O pipeline de ingestão RAG (`ingest_docs.py`) é DEM-002 — depende do PostgreSQL+pgvector rodando
- Configuração do Obsidian (plugins, hotkeys) — é config pessoal, fica fora do git

---

## Critérios de Aceite

1. `docs/` abre como vault Obsidian válido (adicionar pasta no Obsidian sem erros)
2. Todos os templates existem e têm frontmatter YAML correto
3. ADR-001, ADR-002 e ADR-003 documentam as decisões aprovadas na ANALISE-01
4. Cada módulo (admin, gestor, cuidado, florence, oswaldo) tem nota própria em `docs/modulos/`
5. `docs/demandas/_dashboard.md` tem queries Dataview corretas (mesmo que sem dados ainda)
6. `docs/design-docs/PLANS.md` contém o roadmap de fases e DEMs do projeto
7. Arquivos commitados e pusheados para `origin main`
8. `docs/.gitignore` impede que `.obsidian/` entre no git

---

## Resultado Esperado

Após DEM-001, qualquer agente que clonar o repositório e ler `AGENTS.md` → `docs/index.md`
terá compreensão completa de:

- As decisões arquiteturais que não mudam (ADRs)
- O estado de cada módulo (notas de módulo)
- O roadmap do projeto (PLANS.md)
- Como criar uma nova demanda (templates)
- Quais DEMs estão em andamento (dashboard)

---

## Notas para o Agente Desenvolvedor

Esta é uma DEM de **criação de conteúdo markdown**, não de código. Todos os blocos
são criação de arquivos `.md` com conteúdo específico.

Leia `02_TECNICA.md` — ele contém o conteúdo exato de cada arquivo a ser criado.
Não improvise o conteúdo dos ADRs ou das notas de módulo. Use exatamente o que
está especificado na TECNICA.
