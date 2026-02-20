# PLANO_IMPLEMENTACAO — Fase 2: Organização Git e Controle de Versão

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovado para execução  
**Base funcional:** `ESPECIFICACAO_FUNCIONAL_FASE2_GIT_v1.0.md`  
**Base técnica:** `ESPECIFICACAO_TECNICA_FASE2_GIT_v1.0.md`

---

## 1. Visão Geral

**Objetivo:** Implementar controle de versão robusto no repositório `eduardo/intellicare` em ~4 horas.

**Pré-requisitos:**
- Fase 1 (Estabilização) concluída
- Acesso ao repositório remoto
- Git instalado e configurado

**Estimativa total:** ~4 horas

---

## 2. Fases de Implementação

### Fase 2.1 — Atualizar .gitignore (30 min)

**Objetivo:** Garantir que arquivos sensíveis e gerados não sejam versionados.

**Tarefas:**
1. Verificar `.gitignore` existente na raiz do projeto
2. Adicionar padrões obrigatórios (venv, .env, __pycache__, node_modules, IDE)
3. Verificar que nenhum arquivo sensível está versionado
4. Commit das alterações

**Comandos:**
```bash
# Verificar .gitignore atual
cat .gitignore

# Editar .gitignore (adicionar padrões da ESPECIFICACAO_TECNICA)
# Verificar arquivos não rastreados
git status

# Verificar que .env não está versionado
git ls-files | grep "\.env$"  # Deve retornar vazio

# Commit
git add .gitignore
git commit -m "chore: atualizar .gitignore para Fase 2 (venv, .env, IDE, artefatos)"
```

**Critério de sucesso:**
- [ ] `.gitignore` cobre todos os padrões obrigatórios
- [ ] Nenhum arquivo `.env` versionado
- [ ] `git status` não mostra arquivos sensíveis como untracked

**Responsável:** Dev/Agente  
**Estimativa:** 30 min

---

### Fase 2.2 — Criar CHANGELOG.md (30 min)

**Objetivo:** Criar histórico de mudanças versionado.

**Tarefas:**
1. Criar `CHANGELOG.md` na raiz do projeto
2. Seguir formato Keep a Changelog
3. Documentar release inicial (v0.1.0-demo)
4. Commit das alterações

**Comandos:**
```bash
# Criar CHANGELOG.md (usar template da ESPECIFICACAO_TECNICA)
# Editar arquivo com histórico da Fase 1

# Commit
git add CHANGELOG.md
git commit -m "docs: adicionar CHANGELOG.md com release inicial"
```

**Critério de sucesso:**
- [ ] `CHANGELOG.md` existe na raiz
- [ ] Segue formato Keep a Changelog
- [ ] Contém seção [Unreleased] e [0.1.0-demo]

**Responsável:** Dev/Agente  
**Estimativa:** 30 min

---

### Fase 2.3 — Criar ESTRATEGIA_GIT.md (1 hora)

**Objetivo:** Documentar estratégia de branches, tags e fluxo de trabalho.

**Tarefas:**
1. Criar `docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md`
2. Documentar estratégia de branches (main, develop, feature/*)
3. Documentar convenção de tags (SemVer)
4. Documentar fluxo de trabalho (feature → develop → main)
5. Documentar regras de merge (PR recomendado)
6. Commit das alterações

**Conteúdo obrigatório:**
- Diagrama de branches
- Convenção de nomenclatura (feature/*, bugfix/*, hotfix/*)
- Quando criar tags
- Fluxo de Pull Request
- Convenção de mensagens de commit (opcional: Conventional Commits)

**Comandos:**
```bash
# Criar arquivo
# Editar com conteúdo da ESPECIFICACAO_TECNICA

# Commit
git add docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md
git commit -m "docs: adicionar estratégia Git (branches, tags, fluxo)"
```

**Critério de sucesso:**
- [ ] `ESTRATEGIA_GIT.md` existe
- [ ] Documenta branches (main, develop, feature/*)
- [ ] Documenta convenção de tags (SemVer)
- [ ] Documenta fluxo de trabalho

**Responsável:** Dev/Agente  
**Estimativa:** 1 hora

---

### Fase 2.4 — Criar PROCESSO_RELEASE.md (1 hora)

**Objetivo:** Documentar processo passo a passo para criar releases.

**Tarefas:**
1. Criar `docs/PLANNER-CURSOR/PROCESSO_RELEASE.md`
2. Documentar pré-requisitos (demo estável, testes passando)
3. Documentar passos para criar release
4. Documentar verificação pós-release
5. Documentar rollback (se necessário)
6. Commit das alterações

**Conteúdo obrigatório:**
- Checklist de pré-requisitos
- Passos detalhados (atualizar CHANGELOG, merge, tag, push)
- Comandos Git exatos
- Verificação pós-release
- Procedimento de rollback

**Comandos:**
```bash
# Criar arquivo
# Editar com processo detalhado

# Commit
git add docs/PLANNER-CURSOR/PROCESSO_RELEASE.md
git commit -m "docs: adicionar processo de release passo a passo"
```

**Critério de sucesso:**
- [ ] `PROCESSO_RELEASE.md` existe
- [ ] Contém checklist de pré-requisitos
- [ ] Contém passos detalhados com comandos Git
- [ ] Novo dev consegue seguir sem ambiguidade

**Responsável:** Dev/Agente  
**Estimativa:** 1 hora

---

### Fase 2.5 — Criar branch develop (15 min)

**Objetivo:** Criar branch de integração.

**Tarefas:**
1. Verificar se branch `develop` já existe
2. Criar branch `develop` a partir de `main`
3. Push para remoto
4. Verificar criação

**Comandos:**
```bash
# Verificar branches existentes
git branch -a

# Criar develop (se não existir)
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop

# Verificar
git branch -a
```

**Critério de sucesso:**
- [ ] Branch `develop` existe localmente
- [ ] Branch `develop` existe no remoto
- [ ] Branch `develop` está sincronizado com `main`

**Responsável:** Dev/Agente  
**Estimativa:** 15 min

---

### Fase 2.6 — Criar primeira tag (15 min)

**Objetivo:** Criar tag semântica para release inicial.

**Tarefas:**
1. Garantir que está em `main`
2. Criar tag anotada `v0.1.0-demo`
3. Push tag para remoto
4. Verificar tag criada

**Comandos:**
```bash
# Garantir que está em main
git checkout main
git pull origin main

# Criar tag anotada
git tag -a v0.1.0-demo -m "Release inicial da demo - Fase 1 concluída"

# Push tag para remoto
git push origin v0.1.0-demo

# Verificar tag criada
git tag
git show v0.1.0-demo
```

**Critério de sucesso:**
- [ ] Tag `v0.1.0-demo` criada localmente
- [ ] Tag `v0.1.0-demo` existe no remoto
- [ ] Tag aponta para commit correto (HEAD de main)

**Responsável:** Dev/Agente  
**Estimativa:** 15 min

---

### Fase 2.7 — Validação final (30 min)

**Objetivo:** Validar que todos os requisitos foram atendidos.

**Tarefas:**
1. Executar checklist de validação técnica
2. Verificar todos os critérios de aceite
3. Testar processo de release (simulação)
4. Documentar resultado em relatório

**Checklist de validação:**
```bash
# 1. Verificar .gitignore
grep -E "(venv|\.env|__pycache__|node_modules)" .gitignore

# 2. Verificar que .env não está versionado
git ls-files | grep "\.env$"  # Deve retornar vazio

# 3. Verificar CHANGELOG.md
test -f CHANGELOG.md && echo "OK" || echo "FALTA"

# 4. Verificar tags
git tag | grep -E "^v[0-9]+\.[0-9]+\.[0-9]+"

# 5. Verificar documentação
test -f docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md && echo "OK" || echo "FALTA"
test -f docs/PLANNER-CURSOR/PROCESSO_RELEASE.md && echo "OK" || echo "FALTA"

# 6. Verificar branches
git branch -a | grep -E "(main|develop)"
```

**Critérios de aceite (da ESPECIFICACAO_FUNCIONAL):**
- [ ] CA-001: `ESTRATEGIA_GIT.md` existe e documenta branches/tags/PR
- [ ] CA-002: `.gitignore` exclui venv, .env, __pycache__, node_modules, IDE
- [ ] CA-003: `CHANGELOG.md` existe com formato Keep a Changelog
- [ ] CA-004: Tag semântica `v0.1.0-demo` existe
- [ ] CA-005: `PROCESSO_RELEASE.md` existe com passos detalhados
- [ ] CA-006: Novo dev consegue seguir PROCESSO_RELEASE.md sem ambiguidade

**Responsável:** Dev/Agente  
**Estimativa:** 30 min

---

## 3. Cronograma

| Fase | Duração | Dependências | Início | Fim |
|------|---------|--------------|--------|-----|
| 2.1 - .gitignore | 30 min | Nenhuma | T+0h | T+0.5h |
| 2.2 - CHANGELOG.md | 30 min | 2.1 | T+0.5h | T+1h |
| 2.3 - ESTRATEGIA_GIT.md | 1 hora | 2.2 | T+1h | T+2h |
| 2.4 - PROCESSO_RELEASE.md | 1 hora | 2.3 | T+2h | T+3h |
| 2.5 - Branch develop | 15 min | 2.4 | T+3h | T+3.25h |
| 2.6 - Primeira tag | 15 min | 2.5 | T+3.25h | T+3.5h |
| 2.7 - Validação final | 30 min | 2.6 | T+3.5h | T+4h |

**Total:** ~4 horas

---

## 4. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Credenciais versionadas no histórico | Média | Alto | Executar git log para buscar .env; usar BFG se necessário |
| Conflitos em .gitignore | Baixa | Baixo | Revisar antes de commit |
| Tag já existe | Baixa | Médio | Verificar tags existentes antes de criar |
| Branch develop já existe | Média | Baixo | Verificar branches antes de criar |

---

## 5. Entregáveis

| # | Entregável | Localização | Status |
|---|------------|-------------|--------|
| 1 | .gitignore atualizado | `MODULARIZACAO/.gitignore` | Pendente |
| 2 | CHANGELOG.md | `MODULARIZACAO/CHANGELOG.md` | Pendente |
| 3 | ESTRATEGIA_GIT.md | `docs/PLANNER-CURSOR/ESTRATEGIA_GIT.md` | Pendente |
| 4 | PROCESSO_RELEASE.md | `docs/PLANNER-CURSOR/PROCESSO_RELEASE.md` | Pendente |
| 5 | Branch develop | Remoto: `origin/develop` | Pendente |
| 6 | Tag v0.1.0-demo | Remoto: `origin/v0.1.0-demo` | Pendente |

---

## 6. Próximos Passos (Pós-Fase 2)

1. **Fase 3 — Deploy Mínimo:** CI/CD, ambientes (dev/hml/prod)
2. **Fase 4 — Monitoramento:** Alertas, dashboards Grafana
3. **Fase 5 — Produção Ready:** Auth, LGPD, hardening

---

## 7. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

