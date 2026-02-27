# PADRAO_ENTREGA

Diretório oficial do fluxo de entrega local -> git -> staging.

## Regras base (aprovadas)
1. Desenvolvimento acontece nesta maquina local.
2. Depois de testes e validacoes locais, subir para o git.
3. Atualizacao de staging acontece puxando do git (nunca copiando arquivos da maquina local).
4. Cada modulo deve manter seu `docker-compose` proprio em `docker/` para execucao isolada, sem conflitar com o compose full.

## Especificacoes adicionais (recomendadas)
1. Toda entrega deve ter validacao minima automatizada antes do push.
2. Deploy de staging deve usar `git pull --ff-only` (evita merge acidental no servidor).
3. Toda execucao de deploy deve registrar comando, hora e modulo no diario tecnico.
4. Se smoke test falhar, executar rollback imediato para o commit anterior.

## Estrutura
- `GIT/publish-module.ps1`: script generico para commit/push por modulo.
- `GIT/portal.ps1`: wrapper do modulo portal.
- `GIT/admin.ps1`: wrapper do modulo admin.
- `STAGING/deploy-module.ps1`: script generico de deploy no servidor.
- `STAGING/portal.ps1`: wrapper de deploy portal.
- `STAGING/admin.ps1`: wrapper de deploy admin.
- `PLANO_FECHAMENTO_V1_STAGING.md`: plano oficial de encerramento da V1 e transicao para V2.

## Uso rapido

### 1) Publicar no Git
```powershell
# Portal
.\PADRAO_ENTREGA\GIT\portal.ps1 -CommitMessage "feat(portal): ajuste X"

# Admin
.\PADRAO_ENTREGA\GIT\admin.ps1 -CommitMessage "fix(admin): correcao Y"
```

### 2) Atualizar staging
```powershell
# Portal
.\PADRAO_ENTREGA\STAGING\portal.ps1 -Host 167.86.97.142 -User root

# Admin
.\PADRAO_ENTREGA\STAGING\admin.ps1 -Host 167.86.97.142 -User root
```

## Parametros importantes
- `-Branch`: branch de origem no git (default `main`).
- `-SkipValidation`: pula validacao local (usar apenas em emergencia).
- `-Build`: forca rebuild no `docker compose up` do staging.
- `-RepoPath`: caminho do repo no servidor (default `/opt/intellicare/MODULARIZACAO`).

## Registro oficial
Este diretorio e o ponto oficial de execucao.
Indice geral atualizado em `MODULARIZACAO/DOCUMENTACAO.md`.
