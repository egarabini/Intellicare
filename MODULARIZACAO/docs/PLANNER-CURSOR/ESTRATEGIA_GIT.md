# Estratégia Git — IntelliCare MODULARIZACAO

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovado  
**Repositório:** `eduardo/intellicare`

---

## 1. Visão Geral

Este documento define a estratégia de controle de versão para o projeto IntelliCare MODULARIZACAO, incluindo:
- Estratégia de branches
- Convenção de tags e versionamento
- Fluxo de trabalho (workflow)
- Regras de merge e Pull Requests
- Convenção de mensagens de commit

---

## 2. Estratégia de Branches

### 2.1 Diagrama de Branches

```
main (produção/demo estável)
  ↑
  merge via PR (recomendado)
  ↑
develop (integração contínua)
  ↑
  merge via PR (recomendado)
  ↑
feature/* | bugfix/* | hotfix/* (desenvolvimento)
```

### 2.2 Branches Principais

#### `main`
- **Propósito:** Representa o estado de produção/demo estável
- **Proteção:** Sempre deve estar funcional e testado
- **Merges:** Apenas via Pull Request (recomendado)
- **Tags:** Todas as releases são tagueadas a partir de `main`
- **Regra:** Nunca fazer commit direto em `main`

#### `develop`
- **Propósito:** Branch de integração contínua
- **Uso:** Integrar features antes de ir para `main`
- **Merges:** Recebe merges de `feature/*`, `bugfix/*`
- **Regra:** Deve estar sempre em estado "quase pronto para release"

### 2.3 Branches de Desenvolvimento

#### `feature/*`
- **Propósito:** Desenvolvimento de novas funcionalidades
- **Nomenclatura:** `feature/<nome-descritivo>`
- **Exemplos:**
  - `feature/auth-keycloak`
  - `feature/dashboard-grafana`
  - `feature/api-exames`
- **Origem:** Criada a partir de `develop`
- **Destino:** Merge para `develop` via PR
- **Ciclo de vida:** Deletada após merge

#### `bugfix/*`
- **Propósito:** Correção de bugs não críticos
- **Nomenclatura:** `bugfix/<nome-descritivo>`
- **Exemplos:**
  - `bugfix/health-endpoint-timeout`
  - `bugfix/validation-error`
- **Origem:** Criada a partir de `develop`
- **Destino:** Merge para `develop` via PR

#### `hotfix/*`
- **Propósito:** Correção urgente em produção
- **Nomenclatura:** `hotfix/<nome-descritivo>`
- **Exemplos:**
  - `hotfix/critical-security-patch`
  - `hotfix/database-connection-leak`
- **Origem:** Criada a partir de `main`
- **Destino:** Merge para `main` E `develop` via PR
- **Urgência:** Deve ser tratado com prioridade máxima

---

## 3. Convenção de Tags e Versionamento

### 3.1 Versionamento Semântico (SemVer)

Seguimos o [Semantic Versioning 2.0.0](https://semver.org/):

```
v<MAJOR>.<MINOR>.<PATCH>[-<SUFIXO>]
```

**Componentes:**
- **MAJOR:** Mudanças incompatíveis na API (breaking changes)
- **MINOR:** Novas funcionalidades compatíveis com versões anteriores
- **PATCH:** Correções de bugs compatíveis com versões anteriores
- **SUFIXO:** Opcional (ex.: `-demo`, `-alpha`, `-beta`, `-rc1`)

**Exemplos:**
- `v0.1.0-demo` — Primeira release da demo
- `v0.2.0-demo` — Segunda release com novas features
- `v1.0.0` — Primeira release de produção
- `v1.0.1` — Patch/bugfix
- `v1.1.0` — Nova feature
- `v2.0.0` — Breaking change

### 3.2 Quando Criar Tags

- ✅ Após merge para `main` de uma release
- ✅ Quando a demo está estável e testada
- ✅ Antes de deploy em ambiente de produção
- ✅ Ao final de cada sprint/fase (opcional)
- ❌ Nunca criar tags em branches de desenvolvimento

### 3.3 Tipos de Tags

#### Tags Anotadas (Recomendado)
```bash
git tag -a v0.1.0-demo -m "Release inicial da demo - Fase 1 concluída"
```

#### Tags Leves (Não recomendado para releases)
```bash
git tag v0.1.0-demo
```

**Regra:** Sempre usar tags anotadas para releases oficiais.

---

## 4. Fluxo de Trabalho (Workflow)

### 4.1 Fluxo de Feature

```bash
# 1. Criar branch de feature a partir de develop
git checkout develop
git pull origin develop
git checkout -b feature/nova-funcionalidade

# 2. Desenvolver e commitar
git add .
git commit -m "feat: adicionar nova funcionalidade"

# 3. Push para remoto
git push -u origin feature/nova-funcionalidade

# 4. Criar Pull Request (develop ← feature/nova-funcionalidade)
# (via interface do GitHub/GitLab)

# 5. Após aprovação e merge, deletar branch local
git checkout develop
git pull origin develop
git branch -d feature/nova-funcionalidade
```

### 4.2 Fluxo de Release

```bash
# 1. Garantir que develop está estável
git checkout develop
git pull origin develop

# 2. Criar Pull Request (main ← develop)
# (via interface do GitHub/GitLab)

# 3. Após merge, criar tag em main
git checkout main
git pull origin main
git tag -a v0.2.0-demo -m "Release 0.2.0 - Novas features X, Y, Z"
git push origin v0.2.0-demo

# 4. Atualizar CHANGELOG.md
# (editar arquivo e commitar)
```

### 4.3 Fluxo de Hotfix

```bash
# 1. Criar branch de hotfix a partir de main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 2. Corrigir bug e commitar
git add .
git commit -m "fix: corrigir bug crítico X"

# 3. Criar PR para main
git push -u origin hotfix/critical-bug
# (criar PR: main ← hotfix/critical-bug)

# 4. Após merge em main, criar tag
git checkout main
git pull origin main
git tag -a v0.1.1-demo -m "Hotfix: correção crítica"
git push origin v0.1.1-demo

# 5. Fazer merge também em develop
git checkout develop
git merge main
git push origin develop

# 6. Deletar branch de hotfix
git branch -d hotfix/critical-bug
```

---

## 5. Regras de Merge e Pull Requests

### 5.1 Pull Requests Obrigatórios

**Recomendado para:**
- Merges para `main` (obrigatório)
- Merges para `develop` (recomendado)

**Benefícios:**
- Code review
- Discussão de mudanças
- Histórico de decisões
- Integração contínua (CI) automática

### 5.2 Checklist de Pull Request

Antes de criar um PR, verificar:
- [ ] Código está funcionando localmente
- [ ] Testes estão passando
- [ ] Documentação atualizada (se aplicável)
- [ ] CHANGELOG.md atualizado (para releases)
- [ ] Sem conflitos com branch de destino
- [ ] Mensagens de commit seguem convenção

### 5.3 Aprovação de Pull Requests

**Para merges em `main`:**
- Mínimo 1 aprovação (recomendado: ARQUITETO ou PLANEJADOR)
- Todos os checks de CI passando
- Sem conflitos

**Para merges em `develop`:**
- Mínimo 1 aprovação (recomendado)
- Testes passando

---

## 6. Convenção de Mensagens de Commit

### 6.1 Formato (Conventional Commits)

```
<tipo>(<escopo>): <descrição curta>

<corpo opcional>

<rodapé opcional>
```

### 6.2 Tipos de Commit

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `feat` | Nova funcionalidade | `feat(auth): adicionar login com Keycloak` |
| `fix` | Correção de bug | `fix(api): corrigir timeout em health check` |
| `docs` | Documentação | `docs: atualizar README com instruções` |
| `style` | Formatação (sem mudança de lógica) | `style: formatar código com black` |
| `refactor` | Refatoração | `refactor(db): otimizar query de exames` |
| `test` | Testes | `test(florence): adicionar testes unitários` |
| `chore` | Tarefas de manutenção | `chore: atualizar dependências` |
| `perf` | Performance | `perf(api): otimizar endpoint de alertas` |
| `ci` | CI/CD | `ci: adicionar GitHub Actions` |

### 6.3 Exemplos de Boas Mensagens

```bash
feat(comunicacao): adicionar dispatcher de WhatsApp

Implementa integração com Meta Graph API v18.0 para envio
de mensagens WhatsApp via templates pré-aprovados.

Refs: #123
```

```bash
fix(health): corrigir timeout em check de Redis

O health check estava falhando devido a timeout muito curto.
Aumentado de 1s para 5s.

Closes: #456
```

```bash
docs(fase2): adicionar estratégia Git

Documenta branches, tags, fluxo de trabalho e convenções
de commit para o projeto.
```

---

## 7. Proteção de Branches (Recomendações)

### 7.1 Configurações Recomendadas para `main`

- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators (opcional)
- ❌ Allow force pushes (NUNCA)
- ❌ Allow deletions (NUNCA)

### 7.2 Configurações Recomendadas para `develop`

- ✅ Require pull request reviews before merging (opcional)
- ✅ Require status checks to pass before merging
- ❌ Allow force pushes (evitar)

---

## 8. Boas Práticas

### 8.1 Commits

- ✅ Commits pequenos e atômicos
- ✅ Mensagens descritivas
- ✅ Um commit = uma mudança lógica
- ❌ Commits gigantes com múltiplas mudanças
- ❌ Mensagens vagas ("fix", "update", "wip")

### 8.2 Branches

- ✅ Nomes descritivos
- ✅ Deletar após merge
- ✅ Manter branches curtas (< 1 semana)
- ❌ Branches de longa duração (exceto main/develop)
- ❌ Branches órfãs sem uso

### 8.3 Pull Requests

- ✅ Descrição clara do que foi feito
- ✅ Referenciar issues relacionadas
- ✅ Screenshots (se aplicável)
- ✅ Checklist de validação
- ❌ PRs gigantes (> 500 linhas)

---

## 9. Referências

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

