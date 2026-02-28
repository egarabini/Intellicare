# ESPECIFICACAO_FUNCIONAL — Fase 2: Organização Git e Controle de Versão

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Rascunho — aguardando aprovação  
**Referência:** `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`  
**Pré-requisito:** Fase 1 (Estabilização) concluída sem pendências P0

---

## 1. Contexto e Objetivo

O repositório `eduardo/intellicare` está em uso, porém não há estratégia documentada de branches, tags ou releases. Antes do deploy (Fase 3), é essencial estabelecer controle de versão e processo de release para garantir rastreabilidade e governança das alterações.

**Objetivo:** Organizar o repositório Git com estratégia clara de branches, tags e releases, permitindo que qualquer desenvolvedor faça um release de forma controlada e reproduzível.

---

## 2. Escopo

### 2.1 Dentro do escopo

- Definição e documentação da estratégia de branches
- Garantia de `.gitignore` adequado (evitar arquivos sensíveis ou gerados no repositório)
- Criação de `CHANGELOG.md` na raiz do projeto
- Primeira tag semântica (release inicial)
- Documentação do processo de release
- Estratégia de tags e versionamento semântico

### 2.2 Fora do escopo

- Implementação de CI/CD (GitHub Actions, etc.) — Fase posterior
- Deploy automatizado por tag
- Proteção de branches via configuração do repositório remoto (GitHub/GitLab)
- Migração ou alteração do repositório remoto

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-001 | Estratégia de branches deve ser definida e documentada | Obrigatório |
| RF-002 | Branch `main` (ou `master`) deve existir e representar o estado de produção/demo estável | Obrigatório |
| RF-003 | Branch `develop` (ou equivalente) deve existir para integração de features | Obrigatório |
| RF-004 | `.gitignore` deve excluir venv, __pycache__, .env, node_modules, arquivos de IDE e artefatos gerados | Obrigatório |
| RF-005 | `CHANGELOG.md` deve existir na raiz com formato padronizado (ex.: Keep a Changelog) | Obrigatório |
| RF-006 | Primeira tag semântica deve ser criada (ex.: `v0.1.0-demo` ou `v1.0.0-demo`) | Obrigatório |
| RF-007 | Processo de release deve ser documentado passo a passo | Obrigatório |
| RF-008 | Estratégia de tags (quando criar, convenção de nomenclatura) deve ser documentada | Obrigatório |

---

## 4. Requisitos Não Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RNF-001 | Nenhum arquivo sensível (.env com credenciais, chaves, tokens) deve ser versionado | Obrigatório |
| RNF-002 | Nenhum artefato gerado (build, cache, cobertura) deve ser versionado | Obrigatório |
| RNF-003 | Documentação deve ser clara o suficiente para um novo dev executar um release | Obrigatório |
| RNF-004 | Processo de release deve ser reproduzível e não depender de conhecimento tácito | Obrigatório |

---

## 5. Critérios de Aceite

| ID | Critério |
|----|----------|
| CA-001 | Dado o repositório, quando consultar a documentação, então existe `docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md` com branches, tags e fluxo de PR |
| CA-002 | Dado o repositório, quando verificar `.gitignore`, então exclui venv, .venv, __pycache__, .env, node_modules, .idea, .vscode, *.pyc, dist, build, htmlcov, .pytest_cache |
| CA-003 | Dado o repositório, quando verificar a raiz, então existe `CHANGELOG.md` com seções [Unreleased], [Versão] e formato padronizado |
| CA-004 | Dado o repositório, quando listar tags (`git tag`), então existe pelo menos uma tag semântica (ex.: v0.1.0-demo) |
| CA-005 | Dado o repositório, quando consultar a documentação, então existe `docs/PLANNER-CURSOR/PROCESSO_RELEASE.md` com passos para criar um release |
| CA-006 | Dado um desenvolvedor novo, quando seguir PROCESSO_RELEASE.md, então consegue criar uma nova tag e atualizar CHANGELOG sem ambiguidade |

---

## 6. Cenários de Uso

### Cenário 1: Desenvolvedor cria o primeiro release

1. Verifica que Fase 1 está concluída (demo estável)
2. Consulta `ESTRATEGIA_GIT.md` para entender branches e tags
3. Segue `PROCESSO_RELEASE.md`
4. Atualiza `CHANGELOG.md` com as mudanças da release
5. Cria tag `v0.1.0-demo` (ou conforme convenção)
6. Faz push da tag para o remoto
7. Resultado esperado: release documentada e rastreável

### Cenário 2: Desenvolvedor verifica se arquivo sensível está ignorado

1. Verifica `.gitignore` na raiz
2. Confirma que `.env` está listado
3. Executa `git status` e confirma que `.env` não aparece como untracked
4. Resultado esperado: credenciais não são versionadas

### Cenário 3: Novo desenvolvedor entende o fluxo de trabalho

1. Lê `ESTRATEGIA_GIT.md`
2. Entende: `main` = estável, `develop` = integração, `feature/*` = opcional
3. Entende quando e como criar tags
4. Resultado esperado: consegue contribuir sem quebrar o fluxo

---

## 7. Restrições e Premissas

### 7.1 Restrições

- **Repositório:** `eduardo/intellicare` — não alterar URL ou provedor nesta fase
- **Compatibilidade:** Estratégia deve funcionar em Git padrão (sem ferramentas proprietárias obrigatórias)

### 7.2 Premissas

- Fase 1 concluída sem pendências P0 (demo estável)
- Repositório remoto acessível (GitHub, GitLab ou similar)
- Desenvolvedores têm permissão para criar branches e tags
- Convenção semântica: MAJOR.MINOR.PATCH (ex.: 1.0.0) ou variante com sufixo (ex.: v0.1.0-demo)

---

## 8. Entregáveis

| # | Entregável | Descrição |
|---|------------|-----------|
| 1 | ESTRATEGIA_GIT.md | Documento em `docs/PLANNER-CURSOR/` com branches, tags, fluxo de PR, convenções |
| 2 | CHANGELOG.md | Arquivo na raiz do projeto com histórico de mudanças em formato padronizado |
| 3 | PROCESSO_RELEASE.md | Documento em `docs/PLANNER-CURSOR/` com passos para criar um release |
| 4 | .gitignore atualizado | Garantir cobertura de venv, .env, node_modules, artefatos, IDE |
| 5 | Primeira tag criada | Tag semântica (ex.: v0.1.0-demo) apontando para o commit da demo estável |

**Artefatos do fluxo (neste diretório):** O dev deve registrar aqui a ESPECIFICACAO_TECNICA e o PLANO_IMPLEMENTACAO antes da implementação.

---

## 9. Referências

- [Keep a Changelog](https://keepachangelog.com/) — formato sugerido para CHANGELOG
- [Semantic Versioning](https://semver.org/) — convenção de versionamento
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md` — estratégia completa
- `docs/PLANNER-CURSOR/ESTUDO_PROJETO.md` — estrutura do projeto

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Versão inicial |
