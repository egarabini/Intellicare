# ESPECIFICACAO_TECNICA — Fase 2: Organização Git e Controle de Versão

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovada para execução  
**Base funcional:** `ESPECIFICACAO_FUNCIONAL_FASE2_GIT_v1.0.md`

---

## 1. Objetivo Técnico

Estabelecer controle de versão robusto no repositório `eduardo/intellicare` através de:
- Estratégia documentada de branches (main, develop, feature/*)
- Versionamento semântico com tags
- Processo reproduzível de release
- Proteção contra versionamento de arquivos sensíveis ou gerados

---

## 2. Arquitetura de Controle de Versão

### 2.1 Estratégia de Branches

```
main (produção/demo estável)
  ↑
  merge via PR
  ↑
develop (integração)
  ↑
  merge via PR
  ↑
feature/* (desenvolvimento)
```

**Regras:**
- `main`: Sempre estável, representa estado de produção/demo
- `develop`: Integração contínua de features
- `feature/*`: Branches de desenvolvimento (ex.: `feature/auth-keycloak`, `feature/fix-health-endpoint`)
- Merges para `main` e `develop` devem ser via Pull Request (recomendado)

### 2.2 Estratégia de Tags

**Convenção:** Versionamento Semântico (SemVer) com prefixo `v`

```
v<MAJOR>.<MINOR>.<PATCH>[-<SUFIXO>]

Exemplos:
- v0.1.0-demo    (primeira release da demo)
- v0.2.0-demo    (segunda release com novas features)
- v1.0.0         (primeira release de produção)
- v1.0.1         (patch/bugfix)
- v1.1.0         (nova feature)
- v2.0.0         (breaking change)
```

**Quando criar tags:**
- Após merge para `main` de uma release
- Quando a demo está estável e testada
- Antes de deploy em ambiente de produção

---

## 3. Estrutura de Arquivos

### 3.1 .gitignore

**Localização:** Raiz do projeto (`./.gitignore`)

**Conteúdo obrigatório:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
.venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Environment variables (CRÍTICO - SEGURANÇA)
.env
.env.local
.env.*.local
*.env

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Node.js (para intellicare-portal)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Build artifacts
*.log
*.pid
*.seed
*.pid.lock

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
*.bak
*.swp
```

### 3.2 CHANGELOG.md

**Localização:** Raiz do projeto (`./CHANGELOG.md`)

**Formato:** [Keep a Changelog](https://keepachangelog.com/)

**Estrutura:**

```markdown
# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- (mudanças ainda não lançadas)

### Changed
- (mudanças ainda não lançadas)

### Fixed
- (mudanças ainda não lançadas)

## [0.1.0-demo] - 2026-02-20

### Added
- Estrutura modular com 15 módulos (core, wanda, florence, oswaldo, etc.)
- Integração Keycloak SSO em 9 módulos
- Engine de roteamento D1 (comunicacao)
- Canais externos D4 (Push, WhatsApp, SMS, Email)
- Dashboard Grafana e métricas Prometheus
- Demo local funcional com 6 backends + portal

### Changed
- Migração de Matrix/Synapse para Rocket.Chat + Jitsi (V5)

### Fixed
- Estabilização da demo local (Fase 1)
```

---

## 4. Documentação Técnica

### 4.1 ESTRATEGIA_GIT.md

**Localização:** `docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md`

**Conteúdo:**
1. Estratégia de branches (main, develop, feature/*)
2. Fluxo de trabalho (feature → develop → main)
3. Convenção de tags (SemVer)
4. Regras de merge (PR obrigatório para main/develop)
5. Convenção de mensagens de commit (opcional: Conventional Commits)
6. Proteção de branches (recomendações)

### 4.2 PROCESSO_RELEASE.md

**Localização:** `docs/PLANNER-CURSOR/PROCESSO_RELEASE.md`

**Conteúdo:**
1. Pré-requisitos (demo estável, testes passando)
2. Passos para criar release:
   - Atualizar CHANGELOG.md
   - Merge develop → main
   - Criar tag
   - Push tag para remoto
3. Verificação pós-release
4. Rollback (se necessário)

---

## 5. Implementação Técnica

### 5.1 Verificação do Estado Atual

```bash
# Verificar branch atual
git branch

# Verificar tags existentes
git tag

# Verificar arquivos não rastreados
git status

# Verificar .gitignore
cat .gitignore
```

### 5.2 Criação de Branches

```bash
# Criar branch develop (se não existir)
git checkout -b develop

# Push develop para remoto
git push -u origin develop

# Voltar para main
git checkout main
```

### 5.3 Criação da Primeira Tag

```bash
# Garantir que está em main
git checkout main

# Criar tag anotada
git tag -a v0.1.0-demo -m "Release inicial da demo - Fase 1 concluída"

# Push tag para remoto
git push origin v0.1.0-demo

# Verificar tag criada
git tag
git show v0.1.0-demo
```

---

## 6. Validação Técnica

### 6.1 Checklist de Validação

```bash
# 1. Verificar .gitignore
grep -E "(venv|\.env|__pycache__|node_modules)" .gitignore

# 2. Verificar que .env não está versionado
git ls-files | grep "\.env$"  # Deve retornar vazio

# 3. Verificar CHANGELOG.md existe
test -f CHANGELOG.md && echo "OK" || echo "FALTA"

# 4. Verificar tags
git tag | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+"

# 5. Verificar documentação
test -f docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md && echo "OK" || echo "FALTA"
test -f docs/PLANNER-CURSOR/PROCESSO_RELEASE.md && echo "OK" || echo "FALTA"
```

### 6.2 Critérios de Sucesso

- [ ] `.gitignore` cobre todos os padrões obrigatórios
- [ ] Nenhum arquivo `.env` versionado
- [ ] `CHANGELOG.md` existe e segue formato Keep a Changelog
- [ ] Tag `v0.1.0-demo` (ou similar) criada
- [ ] `ESTRATEGIA_GIT.md` documentado
- [ ] `PROCESSO_RELEASE.md` documentado
- [ ] Branches `main` e `develop` existem

---

## 7. Segurança

### 7.1 Proteção de Credenciais

**CRÍTICO:** Garantir que nenhum arquivo com credenciais seja versionado.

**Arquivos a proteger:**
- `.env` (todas as variantes)
- Arquivos de configuração com tokens/senhas
- Chaves SSH/API
- Certificados privados

**Verificação:**
```bash
# Buscar possíveis credenciais versionadas
git log --all --full-history -- "*.env"
git log --all --full-history -- "*credentials*"
git log --all --full-history -- "*secret*"
```

**Se encontrar credenciais versionadas:**
1. Remover do histórico (git filter-branch ou BFG Repo-Cleaner)
2. Revogar credenciais comprometidas
3. Gerar novas credenciais

---

## 8. Próximos Passos (Pós-Fase 2)

- **Fase 3:** Deploy mínimo (CI/CD, ambientes)
- **Fase 4:** Monitoramento (alertas, dashboards)
- **Fase 5:** Produção ready (auth, LGPD, hardening)

---

## 9. Referências Técnicas

- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

