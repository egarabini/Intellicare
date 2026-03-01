# Solução do Problema Git - Acesso HTTPS vs SSH

## Problema Identificado

O servidor **167.86.97.142** não tem chaves SSH configuradas para acessar o GitHub.
Quando o remote está configurado como `git@github.com`, o Git tenta usar autenticação SSH,
que falha com: `Permission denied (publickey)`.

## Solução

Usar **HTTPS** em vez de SSH para o remote do Git.

## Comando para Corrigir no Servidor

Execute no servidor (167.86.97.142):

```bash
cd /opt/intellicare
git remote set-url origin https://github.com/egarabini/Intellicare.git
```

## Verificação

```bash
git remote -v
```

Deve mostrar:
```
origin	https://github.com/egarabini/Intellicare.git (fetch)
origin	https://github.com/egarabini/Intellicare.git (push)
```

## Deploy Completo Corrigido

Após corrigir o remote URL, execute:

```bash
cd /opt/intellicare
git fetch origin
git reset --hard origin/staging
bash scripts/server/setup_env.sh
docker-compose -f docker-compose.full.yml down
docker network rm intellicare_intellicare-network 2>/dev/null || true
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
docker ps
```

## Ou Use o Script Automatizado

```bash
cd /opt/intellicare
bash scripts/server/full_deploy.sh
```

## Por que Isso Aconteceu?

1. O repositório foi movido de `egarabini/intellicare` para `egarabini/Intellicare`
2. Durante o movimento, o remote local foi configurado com SSH
3. O servidor nunca teve chaves SSH configuradas
4. Deployes anteriores funcionavam porque o remote estava com HTTPS

## Prevenção Futura

Sempre usar HTTPS para o remote URL em servidores sem chaves SSH:

```bash
# Correto (HTTPS)
git remote set-url origin https://github.com/egarabini/Intellicare.git

# Errado (SSH) - não funciona sem chaves configuradas
git remote set-url origin git@github.com:egarabini/Intellicare.git
```

## Scripts Criados

Todos os scripts de deploy foram criados para usar HTTPS automaticamente:

- `scripts/server/update_from_git.sh` - Usa HTTPS
- `scripts/server/full_deploy.sh` - Usa HTTPS
- `scripts/server/clone_clean_from_git.sh` - Usa HTTPS
