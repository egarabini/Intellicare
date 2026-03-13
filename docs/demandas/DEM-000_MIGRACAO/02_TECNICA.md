---
tipo: especificacao-tecnica
demanda: DEM-000
titulo: Migração IntelliCare V2 → V3
status: aprovado
criado: 2026-03-13
---

# DEM-000 — Especificação Técnica

## Pré-condições verificadas

| Condição | Estado |
|---|---|
| Backup local `C:\DOCSHARE\INTELLICARE_V2` | ✅ Confirmado |
| Repo remoto `github.com/egarabini/Intellicare.git` | ✅ Confirmado |
| Último commit V2: `24c5cae` (DEM-007) | ✅ Confirmado |
| Diretório local `C:\Users\egara\INTELLICARE` | ✅ Existe |

---

## BLOCO 1 — Preservar histórico V2 no GitHub

Executar localmente em `C:\Users\egara\INTELLICARE`:

```powershell
cd C:\Users\egara\INTELLICARE

# 1. Tag marcando o estado final do V2
git tag v2-final -m "IntelliCare V2 - estado final antes da migração V3"
git push origin v2-final

# 2. Branch de arquivo permanente com todo histórico V2
git checkout -b v2-archive
git push origin v2-archive

# 3. Voltar para main
git checkout main
```

**Resultado:** GitHub terá `v2-archive` (histórico completo) e a tag `v2-final`.
Qualquer código V2 pode ser recuperado via `git checkout v2-archive -- <path>`.

---

## BLOCO 2 — Limpar branch main (orphan)

```powershell
cd C:\Users\egara\INTELLICARE

# Criar branch orphan (sem histórico)
git checkout --orphan main-v3

# Remover TODOS os arquivos do staging
git rm -rf .

# Verificar que está limpo
git status
# deve mostrar: "nothing to commit"
```

---

## BLOCO 3 — Criar estrutura V3 local

Criar os diretórios da nova estrutura:

```powershell
$base = "C:\Users\egara\INTELLICARE"

# Estrutura principal
$dirs = @(
    "docs\demandas",
    "docs\decisoes",
    "docs\modulos",
    "docs\_templates",
    "docs\generated",
    "packages\intellicare-core",
    "modules\admin",
    "modules\gestor",
    "modules\cuidado",
    "modules\florence",
    "modules\oswaldo",
    "configs\verticals",
    "configs\plans",
    "configs\overlays",
    "infra",
    "deploy",
    "tests\unit",
    "tests\integration",
    "tests\e2e",
    "tests\architecture",
    "tools\lint-rules",
    "tools\scripts"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path "$base\$dir" | Out-Null
    Write-Host "Criado: $dir"
}
```

---

## BLOCO 4 — Arquivos base do V3

### `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Node
node_modules/
dist/
.next/

# Env
.env
.env.*
!.env.example

# Obsidian (config pessoal)
docs/.obsidian/
docs/.trash/

# IDE
.vscode/settings.json
.idea/
*.swp

# Docker
.docker/

# Logs e temporários
*.log
.tmp/
.worktrees/
```

### `README.md`
```markdown
# IntelliCare V3

Plataforma modular de saúde com arquitetura de módulos carregados dinamicamente.

## Estrutura

- `packages/` — SDK compartilhado (intellicare-core)
- `modules/`  — Módulos de negócio (admin, gestor, cuidado, florence, oswaldo...)
- `configs/`  — Configurações por vertical e plano
- `infra/`    — Docker Compose, Keycloak, migrations
- `deploy/`   — Dockerfile do serviço unificado
- `tests/`    — Testes unitários, integração, e2e, arquitetura
- `tools/`    — Linters, scripts de suporte
- `docs/`     — Vault Obsidian + documentação do projeto

## Início rápido

> Em construção — DEM-002 (infra base) em andamento.

## Documentação

Ver `docs/` para arquitetura, decisões (ADRs), demandas e roadmap.
```

### `AGENTS.md` (índice — ~100 linhas)
Ver arquivo separado — já produzido em AVALIACAO-01.

---

## BLOCO 5 — Placeholders nos módulos

Cada diretório em `modules/` e `packages/` recebe um `_PLACEHOLDER.md`:

```markdown
# [nome-do-módulo] — Placeholder

**Entregue por:** [DEM-NNN]
**Status:** ⏳ Aguardando implementação

## O que vai aqui

[Descrição do módulo]

## Estrutura esperada

```
[nome]/
├── domain/         ← entidades e regras de negócio
├── application/    ← casos de uso
├── infrastructure/ ← banco, cache, APIs externas
└── interfaces/     ← routers FastAPI, schemas Pydantic
```

## Dependências

- intellicare-core
- DEM-NNN deve ser concluída primeiro
```

---

## BLOCO 6 — Primeiro commit V3

```powershell
cd C:\Users\egara\INTELLICARE

git add .
git commit -m "feat: estrutura base IntelliCare V3

- Arquitetura: 1 serviço com módulos carregados dinamicamente
- Tríade: RAG + SLM + pgvector
- Schema autônomo por tenant (sem schema global)
- Docs/ como vault Obsidian + fonte RAG
- Substituição completa da arquitetura V2 (10+ containers)

Histórico V2 preservado em branch v2-archive e tag v2-final."

# Substituir main pelo novo orphan
git branch -D main          # deleta main local (já salva em v2-archive)
git branch -m main-v3 main  # renomeia orphan para main

# Force push (intencional — estamos limpando o histórico do main)
git push origin main --force

# Verificar
git log --oneline
```

> ⚠️ O `--force` aqui é INTENCIONAL e SEGURO porque:
> - O histórico completo está em `v2-archive` e `v2-final` (já pusados)
> - O backup local está em `C:\DOCSHARE\INTELLICARE_V2`
> - Estamos criando um novo capítulo, não apagando o anterior

---

## BLOCO 7 — Staging server

> ⚠️ **Requer acesso SSH ao servidor.** Eduardo fornece dados de conexão.

```bash
# Conectar ao servidor
ssh usuario@IP_SERVIDOR

# Parar todos os containers V2
cd /caminho/do/projeto
docker compose down --remove-orphans
docker compose -f docker-compose.full.yml down --remove-orphans 2>/dev/null || true

# Verificar que parou
docker ps  # deve estar vazio ou sem containers intellicare

# Limpar imagens V2 (opcional — libera espaço)
docker system prune -f

# Limpar diretório do projeto (manter apenas o que for necessário)
# ATENÇÃO: confirmar o caminho exato com Eduardo antes
rm -rf /caminho/do/projeto/*
# ou renomear para backup
mv /caminho/do/projeto /caminho/do/projeto_v2_backup

# Criar diretório limpo para V3
mkdir /caminho/do/projeto
cd /caminho/do/projeto
git clone https://github.com/egarabini/Intellicare.git .
```

---

## BLOCO 8 — Verificação final

```powershell
# Local
cd C:\Users\egara\INTELLICARE
git log --oneline        # deve ter apenas 1 commit
git branch -a            # deve mostrar: main, remotes/origin/main, remotes/origin/v2-archive
git tag                  # deve mostrar: v2-final
Get-ChildItem            # deve mostrar estrutura V3 (sem intellicare-* do V2)
```

```bash
# GitHub (verificar no browser)
# https://github.com/egarabini/Intellicare/branches
# Deve mostrar: main (1 commit), v2-archive (histórico completo)
```

---

## Dependência bloqueante para DEM-001

DEM-001 pode iniciar assim que:
- [ ] `git push --force` do BLOCO 6 for concluído
- [ ] Staging limpo (BLOCO 7) — pode ser paralelo à DEM-001 se necessário
