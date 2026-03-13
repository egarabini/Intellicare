---
tipo: especificacao-funcional
demanda: DEM-000
titulo: Migração IntelliCare V2 → V3
fase: 0
sprint: "0"
modulo: infra
status: aprovado
dev: planejador
criado: 2026-03-13
depende_de: []
habilita:
  - DEM-001_ESTRUTURA_BASE
tags:
  - fase-0
  - migracao
  - p0
---

# DEM-000 — Migração IntelliCare V2 → V3

## Contexto

O IntelliCare V2 (`C:\Users\egara\INTELLICARE`) chegou ao fim do seu ciclo.
O diagnóstico da ANALISE-01 é claro: arquitetura monolítica (10+ containers
independentes) impossibilita integração com sistemas de saúde existentes,
intellicare-core existe só no papel, e 80% dos módulos são promessa, não produto.

O backup V2 está preservado em `C:\DOCSHARE\INTELLICARE_V2` e no GitHub
como branch `v2-archive` (a ser criado nesta DEM). Ele servirá como fonte
de recuperação de código aproveitável nas fases seguintes.

## Objetivo

Limpar o repositório local e remoto, preservando o histórico V2 de forma
acessível, e criar a estrutura esqueleto do V3 pronta para receber a DEM-001
(estrutura base + vault Obsidian).

## O que esta DEM entrega

1. **Tag `v2-final`** no GitHub marcando o último estado do V2
2. **Branch `v2-archive`** no GitHub preservando todo o histórico V2
3. **Branch `main` limpa** no GitHub — orphan, sem histórico V2
4. **`C:\Users\egara\INTELLICARE`** com estrutura V3 esqueleto commitada
5. **Staging server** com containers V2 parados e diretório limpo

## O que esta DEM NÃO faz

- Não implementa nenhum módulo (isso começa na DEM-002)
- Não configura Docker Compose V3 (DEM-002)
- Não cria o vault Obsidian completo (DEM-001)
- Não configura CI/CD (DEM-002)

## Critérios de aceite

- [ ] `git tag v2-final` existe no GitHub
- [ ] Branch `v2-archive` existe no GitHub com histórico completo
- [ ] Branch `main` no GitHub tem apenas 1 commit ("feat: estrutura base V3")
- [ ] `C:\Users\egara\INTELLICARE` tem a estrutura de pastas V3 (sem código V2)
- [ ] `git log --oneline` no local mostra apenas o commit inicial V3
- [ ] Staging: `docker ps` não mostra containers V2 rodando
- [ ] Staging: diretório do projeto está limpo (sem código V2)
