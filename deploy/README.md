# IntelliCare V3 — Deploy Staging

## Objetivo

Atualizar o ambiente de staging com impacto minimo, usando restart seletivo do
servico principal e seed de flows do Kestra.

## Pre-requisitos no VPS

- Docker com plugin Compose instalado.
- Git com acesso ao repositorio.
- Arquivo de segredos real em `infra/.env.staging` (nao versionado).

## Setup inicial (uma vez)

1. Copiar o template:

```bash
cp infra/.env.staging.example infra/.env.staging
```

2. Preencher todas as variaveis do `infra/.env.staging` com segredos reais.

3. Subir infraestrutura:

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml up -d
```

## Atualizacao de staging

Executar na raiz do repositorio:

```bash
STAGING_ENV_FILE=infra/.env.staging bash deploy/staging_update.sh
```

## O que o script faz

1. valida pre-requisitos (git limpo, docker, compose, env file);
2. atualiza codigo (`git pull --ff-only origin main`);
3. faz build do `intellicare-service`;
4. reinicia somente `intellicare-service` (`--no-deps`);
5. executa seed de flows Kestra;
6. mostra status final dos servicos.

## Verificacoes pos-deploy

- API: `https://api.intellicare.ia.br/health`
- Gestor UI: `https://gestor.intellicare.ia.br/gestor-ui/`
- Kestra UI: `https://kestra.intellicare.ia.br`

## Seguranca

- Nunca commitar `infra/.env.staging`.
- Rotacionar segredos periodicamente.
- Manter backups antes de atualizacoes maiores.
