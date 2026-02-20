# Processo de Release — IntelliCare MODULARIZACAO

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovado  
**Repositório:** `eduardo/intellicare`

---

## 1. Visão Geral

Este documento define o processo passo a passo para criar releases no projeto IntelliCare MODULARIZACAO. Qualquer desenvolvedor deve conseguir executar um release seguindo este guia sem ambiguidade.

---

## 2. Pré-requisitos

Antes de iniciar um release, verificar:

### 2.1 Checklist de Pré-requisitos

- [ ] **Demo estável:** Todos os serviços sobem sem erros
- [ ] **Testes passando:** Executar `check_demo_health.ps1` com sucesso
- [ ] **Branch develop atualizado:** `git pull origin develop`
- [ ] **Sem commits pendentes:** `git status` limpo
- [ ] **CHANGELOG.md atualizado:** Seção [Unreleased] preenchida
- [ ] **Documentação atualizada:** README, guias, etc.
- [ ] **Aprovação:** ARQUITETO ou PLANEJADOR aprovou a release

### 2.2 Ferramentas Necessárias

- Git instalado e configurado
- Acesso ao repositório remoto (`eduardo/intellicare`)
- Permissão para criar tags e fazer push

---

## 3. Processo de Release (Passo a Passo)

### Passo 1: Preparar Branch Develop

```bash
# 1.1. Ir para branch develop
git checkout develop

# 1.2. Atualizar develop
git pull origin develop

# 1.3. Verificar status
git status
# Deve retornar: "nothing to commit, working tree clean"
```

**Validação:** Branch develop está limpo e atualizado.

---

### Passo 2: Atualizar CHANGELOG.md

```bash
# 2.1. Editar CHANGELOG.md
# Mover itens de [Unreleased] para nova seção [X.Y.Z]

# Exemplo de estrutura:
## [Unreleased]
(vazio ou novos itens)

## [0.2.0-demo] - 2026-02-25

### Added
- Nova funcionalidade X
- Nova funcionalidade Y

### Changed
- Mudança Z

### Fixed
- Correção W

# 2.2. Commitar CHANGELOG
git add CHANGELOG.md
git commit -m "docs: atualizar CHANGELOG para release v0.2.0-demo"
git push origin develop
```

**Validação:** CHANGELOG.md contém seção da nova release com data.

---

### Passo 3: Criar Pull Request (develop → main)

```bash
# 3.1. Via interface do GitHub/GitLab, criar PR:
# - Base: main
# - Compare: develop
# - Título: "Release v0.2.0-demo"
# - Descrição: Copiar seção do CHANGELOG da release

# 3.2. Aguardar aprovação e merge
# (ARQUITETO ou PLANEJADOR deve aprovar)

# 3.3. Após merge, atualizar main local
git checkout main
git pull origin main
```

**Validação:** Branch main contém todas as mudanças de develop.

---

### Passo 4: Criar Tag Semântica

```bash
# 4.1. Garantir que está em main
git checkout main
git pull origin main

# 4.2. Criar tag anotada
git tag -a v0.2.0-demo -m "Release 0.2.0-demo - Descrição breve"

# Exemplo completo:
git tag -a v0.2.0-demo -m "Release 0.2.0-demo - Adiciona features X, Y e corrige bug Z"

# 4.3. Verificar tag criada
git tag
git show v0.2.0-demo

# 4.4. Push tag para remoto
git push origin v0.2.0-demo
```

**Validação:** Tag existe localmente e no remoto.

---

### Passo 5: Verificação Pós-Release

```bash
# 5.1. Verificar tag no remoto
git ls-remote --tags origin

# 5.2. Verificar que main está atualizado
git log --oneline -5

# 5.3. Testar demo localmente
.\start-infrastructure.ps1
.\start_demo.bat
.\check_demo_health.ps1

# 5.4. Verificar CHANGELOG no GitHub/GitLab
# (acessar repositório e confirmar que tag aparece)
```

**Validação:** Release está visível no repositório remoto.

---

### Passo 6: Comunicar Release

```bash
# 6.1. Notificar equipe
# - Enviar email/mensagem com link da release
# - Incluir CHANGELOG da versão
# - Destacar breaking changes (se houver)

# 6.2. Atualizar documentação externa (se aplicável)
# - Wiki do projeto
# - Documentação de usuário
# - Notas de release públicas
```

**Validação:** Equipe está ciente da nova release.

---

## 4. Convenção de Versionamento

### 4.1 Quando Incrementar Cada Número

| Tipo de Mudança | Incremento | Exemplo |
|-----------------|------------|---------|
| Breaking change (incompatível) | MAJOR | v1.0.0 → v2.0.0 |
| Nova funcionalidade (compatível) | MINOR | v1.0.0 → v1.1.0 |
| Correção de bug (compatível) | PATCH | v1.0.0 → v1.0.1 |
| Release de demo | MINOR + sufixo | v0.1.0-demo → v0.2.0-demo |

### 4.2 Exemplos de Versionamento

```
v0.1.0-demo  → Primeira release da demo
v0.2.0-demo  → Segunda release com novas features
v0.3.0-demo  → Terceira release
v1.0.0       → Primeira release de produção (sem sufixo)
v1.0.1       → Patch/bugfix
v1.1.0       → Nova feature
v2.0.0       → Breaking change
```

---

## 5. Rollback (Se Necessário)

### 5.1 Quando Fazer Rollback

- Bug crítico descoberto após release
- Falha em produção
- Incompatibilidade não detectada

### 5.2 Processo de Rollback

```bash
# 5.2.1. Reverter main para tag anterior
git checkout main
git reset --hard v0.1.0-demo  # Tag anterior estável
git push origin main --force  # ⚠️ CUIDADO: force push

# 5.2.2. Deletar tag problemática (local e remoto)
git tag -d v0.2.0-demo
git push origin :refs/tags/v0.2.0-demo

# 5.2.3. Criar hotfix para corrigir problema
git checkout -b hotfix/critical-bug
# (corrigir bug)
git add .
git commit -m "fix: corrigir bug crítico"
git push -u origin hotfix/critical-bug

# 5.2.4. Criar PR e nova release
# (seguir processo normal de release)
```

**⚠️ ATENÇÃO:** Rollback com force push deve ser usado apenas em emergências.

---

## 6. Checklist Final de Release

### Antes de Criar Tag

- [ ] Todos os testes passando
- [ ] Demo funcional localmente
- [ ] CHANGELOG.md atualizado
- [ ] Documentação atualizada
- [ ] PR aprovado e merged (develop → main)
- [ ] Main atualizado localmente

### Após Criar Tag

- [ ] Tag existe no remoto (`git ls-remote --tags origin`)
- [ ] Tag aponta para commit correto (`git show v0.X.Y-demo`)
- [ ] CHANGELOG reflete a release
- [ ] Equipe notificada
- [ ] Documentação externa atualizada (se aplicável)

---

## 7. Troubleshooting

### Problema: Tag já existe

```bash
# Erro: "tag 'v0.2.0-demo' already exists"

# Solução 1: Deletar tag local e remota
git tag -d v0.2.0-demo
git push origin :refs/tags/v0.2.0-demo

# Solução 2: Usar versão diferente
git tag -a v0.2.1-demo -m "..."
```

### Problema: Esqueci de atualizar CHANGELOG

```bash
# Solução: Criar commit adicional em main
git checkout main
# (editar CHANGELOG.md)
git add CHANGELOG.md
git commit -m "docs: atualizar CHANGELOG para v0.2.0-demo"
git push origin main

# Não é necessário recriar tag
```

### Problema: Merge conflict em PR

```bash
# Solução: Atualizar develop com main
git checkout develop
git merge main
# (resolver conflitos)
git add .
git commit -m "merge: resolver conflitos com main"
git push origin develop

# Recriar PR
```

---

## 8. Referências

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [ESTRATEGIA_GIT.md](ESTRATEGIA_GIT.md) - Estratégia de branches e tags
- [Git Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

---

## 9. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

