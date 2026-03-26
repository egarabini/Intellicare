# DEM-092 — pgAdmin + Keycloak Admin Access

## Objetivo

Corrigir dois pontos de falha encontrados na validação de staging (2026-03-25):

1. **pgAdmin:** não existe no stack — adicionar o serviço ao `docker-compose.yml` para acesso visual ao PostgreSQL
2. **Keycloak Admin:** console acessível mas URL e credenciais não documentadas — padronizar acesso e confirmar funcionamento

## Critério de aceite

### pgAdmin
- `https://pgadmin.intellicare.ia.br` carrega a interface de login
- Login com credenciais do `.env.staging` funciona
- Conexão ao servidor `intellicare-postgres` estabelecida
- Database `intellicare_staging` navegável (schemas, tabelas, dados)

### Keycloak Admin Console
- `https://auth.intellicare.ia.br/admin/` carrega o console
- Login com `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD` funciona
- Realm `intellicare` visível com usuários e roles configurados

## Fora de escopo

- Alterações de schema ou dados no PostgreSQL
- Alterações de configuração do Keycloak
- Criação de novos usuários ou roles
