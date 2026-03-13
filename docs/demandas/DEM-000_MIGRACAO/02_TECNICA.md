# DEM-000 — Migração V2 → V3: Especificação Técnica (REVISADA)

> **⚠️ REVISÃO CRÍTICA — 2026-03-13**
> O plano original (orphan branch + force push) foi **descartado** porque os commits
> de planejamento DEM-004 a DEM-015 já estão no `main`. A abordagem agora é mais
> simples e segura: preservar V2 em branch/tag e remover as pastas legadas com
> `git rm`. Nenhum force push. Nenhum commit perdido.

---

## Estado atual do repositório (antes desta DEM)

| Item | Estado |
|---|---|
| Branch `main` | Tem V2 (`intellicare-*`) + planejamento V3 (`docs/demandas/`) |
| Commits de planejamento | `48ae2c9` … `eaa5c04` — **PRESERVAR** |
| Backup local V2 | ✅ Confirmado por Eduardo |
| Pastas V2 a remover | 16 pastas `intellicare-*` listadas abaixo |
| Pastas V3 a manter | `docs/`, `modules/`, `packages/`, `tests/`, `tools/`, `configs/`, `deploy/`, `infra/` |

### Pastas V2 a remover (lista completa)

```
intellicare-admin
intellicare-auth
intellicare-comunicacao
intellicare-conhecimento
intellicare-core
intellicare-donabedian
intellicare-florence
intellicare-geralda
intellicare-gestor
intellicare-grahame
intellicare-minerva
intellicare-nise
intellicare-oswaldo
intellicare-pierre
intellicare-wanda
intellicare-zilda
```

---

## BLOCO 1 — Preservar V2 no GitHub

```cmd
cd C:\Users\egara\INTELLICARE

:: Tag marcando o último estado que ainda contém o código V2
git tag v2-final -m "IntelliCare V2 - estado final com código legado"
git push origin v2-final

:: Branch de arquivo permanente (snapshot completo: V2 + docs planejamento)
git checkout -b v2-archive
git push origin v2-archive

:: Voltar para main
git checkout main
```

**Resultado:** GitHub terá:
- `v2-final` (tag) — aponta para o commit atual, que tem V2 + planejamento V3
- `v2-archive` (branch) — acesso permanente a qualquer arquivo V2 via `git checkout v2-archive -- <path>`

---

## BLOCO 2 — Remover pastas V2 do main

```cmd
cd C:\Users\egara\INTELLICARE

git rm -r ^
  intellicare-admin ^
  intellicare-auth ^
  intellicare-comunicacao ^
  intellicare-conhecimento ^
  intellicare-core ^
  intellicare-donabedian ^
  intellicare-florence ^
  intellicare-geralda ^
  intellicare-gestor ^
  intellicare-grahame ^
  intellicare-minerva ^
  intellicare-nise ^
  intellicare-oswaldo ^
  intellicare-pierre ^
  intellicare-wanda ^
  intellicare-zilda
```

> **Nota:** O `^` é continuação de linha no cmd do Windows.
> Se preferir PowerShell, substituir `^` por `` ` `` (backtick).

Verificar o que vai ser removido antes de commitar:

```cmd
git status
:: Deve listar apenas "deleted: intellicare-*/..." — nenhum arquivo de docs/ ou modules/
```

---

## BLOCO 3 — Commit e push

```cmd
cd C:\Users\egara\INTELLICARE

echo chore: remove modulos V2 legados - migracao para V3 > _msg.txt
echo. >> _msg.txt
echo Historico V2 preservado em: >> _msg.txt
echo   - tag v2-final >> _msg.txt
echo   - branch v2-archive >> _msg.txt
echo. >> _msg.txt
echo Backup local em: C:\DOCSHARE\INTELLICARE_V2 >> _msg.txt
echo. >> _msg.txt
echo Pastas removidas: intellicare-admin, intellicare-auth, >> _msg.txt
echo intellicare-comunicacao, intellicare-conhecimento, intellicare-core, >> _msg.txt
echo intellicare-donabedian, intellicare-florence, intellicare-geralda, >> _msg.txt
echo intellicare-gestor, intellicare-grahame, intellicare-minerva, >> _msg.txt
echo intellicare-nise, intellicare-oswaldo, intellicare-pierre, >> _msg.txt
echo intellicare-wanda, intellicare-zilda >> _msg.txt

git commit -F _msg.txt
del _msg.txt

git push origin main
```

---

## BLOCO 4 — Verificação local pós-limpeza

```cmd
cd C:\Users\egara\INTELLICARE

:: Deve mostrar apenas pastas V3
dir /b /ad

:: Esperado:
:: .git
:: .worktrees
:: configs
:: deploy
:: docs
:: infra
:: modules
:: packages
:: tests
:: tools
```

```cmd
:: Histórico deve ter commits de planejamento intactos
git log --oneline -10

:: Esperado (do mais recente para o mais antigo):
:: <novo hash>  chore: remove modulos V2 legados
:: eaa5c04      docs: atualiza dashboard - DEMs 010-015 aprovados
:: 6ec3592      DEM-010 a DEM-015: planejamento completo Fase 2 e 3
:: 5ff6139      docs: DEM-009 pgvector RAG pipeline ...
:: ...

:: Branches e tags
git branch -a
:: main, remotes/origin/main, remotes/origin/v2-archive

git tag
:: v2-final
```

---

## BLOCO 5 — Staging server

> ⚠️ Requer acesso SSH. Eduardo fornece dados de conexão antes do dev executar.

```bash
# Conectar ao servidor
ssh usuario@IP_SERVIDOR

# Parar containers V2
docker compose down --remove-orphans 2>/dev/null || true

# Verificar que parou
docker ps  # deve estar vazio ou sem containers intellicare-*

# Limpar imagens V2 (libera espaço em disco)
docker system prune -f

# Atualizar repositório no servidor para o main limpo
cd /caminho/do/projeto
git fetch origin
git reset --hard origin/main

# Confirmar estado
ls -la
git log --oneline -3
```

---

## O que NÃO fazer

| Ação | Motivo |
|---|---|
| `git push --force` no main | Destruiria os commits de planejamento (DEM-004 a DEM-015) |
| `git checkout --orphan` | Desnecessário — o main já está limpo de histórico problemático |
| Remover `docs/demandas/` | Esta pasta é o planejamento completo V3 — nunca tocar |
| Remover `modules/`, `packages/` | Esqueleto V3 já criado pelo planejador — preservar |
| `git rm -rf .` | NUNCA — apagaria tudo incluindo docs/ |

---

## Checklist de aceite

- [ ] `git tag v2-final` existe no GitHub
- [ ] Branch `v2-archive` existe no GitHub com histórico completo
- [ ] `git log --oneline` no main mostra commits de planejamento intactos (DEM-004 … eaa5c04)
- [ ] Nenhuma pasta `intellicare-*` existe localmente ou no main remoto
- [ ] `docs/demandas/` com todos os DEM-000 a DEM-015 intactos
- [ ] `modules/`, `packages/`, `tests/`, `tools/` presentes e intactos
- [ ] Staging: `docker ps` sem containers V2
- [ ] Staging: `git log --oneline -3` mostra commit de remoção V2 como mais recente

---

## Dependência bloqueante para DEM-002

DEM-002 (infra Docker) pode iniciar assim que:
- [ ] BLOCO 3 (commit + push) for concluído
- [ ] BLOCO 5 (staging) pode rodar em paralelo com DEM-002 se necessário
