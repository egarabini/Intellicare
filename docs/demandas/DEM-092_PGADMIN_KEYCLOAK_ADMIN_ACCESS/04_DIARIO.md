# DEM-092 — Diário de Execução

> Dev: DEV-1 | Data: 2026-03-25

## Execução

### pgAdmin

1. `PGADMIN_EMAIL` e `PGADMIN_PASSWORD` adicionados ao `infra/.env.staging` do VPS
2. `git pull origin main` — docker-compose.yml com serviço `pgadmin` recebido
3. `docker compose --env-file infra/.env.staging -f infra/docker-compose.yml up -d --no-deps pgadmin`
4. Container `intellicare-pgadmin` UP, porta 80/tcp ativa
5. Traefik: `http://pgadmin.intellicare.ia.br` → redirect 307 para HTTPS
6. `https://pgadmin.intellicare.ia.br/login` → 200 OK ✅

### Keycloak Admin Console

Sem alteração de código. Documentação de acesso registrada em `02_TECNICA.md`.
URL correta: `https://auth.intellicare.ia.br/admin/`
Credenciais: via `docker exec intellicare-keycloak env | grep KEYCLOAK_ADMIN`

## Credenciais pgAdmin (staging)

- Email: `admin@intellicare.ia.br`
- Password: `IC_PgAdmin#2026!Stg` *(registrado em `.env.staging` do VPS — não entra no git)*
