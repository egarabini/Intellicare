# DEM-092 — Plano de Execução

> ⚠️ **Processo obrigatório**: criar `04_DIARIO.md` durante a execução e `05_FINALIZACAO.md` ao entregar.

## Pré-requisitos

- [ ] DNS `pgadmin.intellicare.ia.br` apontando para o IP do VPS (igual aos outros subdomínios)
- [ ] Acesso SSH ao VPS
- [ ] Acesso ao repositório local para edição do `docker-compose.yml`

## Passo 1 — Adicionar variáveis ao `.env.staging`

No VPS ou no arquivo local antes de push:

```bash
# Adicionar ao infra/.env.staging
PGADMIN_EMAIL=admin@intellicare.ia.br
PGADMIN_PASSWORD=<senha-forte-aqui>
```

> `.env.staging` não entra no git (está no `.gitignore`). Editar diretamente no VPS e também no arquivo local.

## Passo 2 — Editar `infra/docker-compose.yml`

Adicionar o bloco do serviço `pgadmin` e o volume `pgadmin_data` conforme `02_TECNICA.md`.

Dois pontos de edição no arquivo:
- Na seção `services:` — adicionar o bloco completo do `pgadmin`
- Na seção `volumes:` — adicionar `pgadmin_data:`

## Passo 3 — Commit e push

```bash
git add infra/docker-compose.yml
git commit -m "feat(infra): adicionar pgAdmin ao stack staging (DEM-092)"
git push origin main
```

## Passo 4 — Deploy no VPS

```bash
cd /opt/intellicare
git pull origin main

# Subir apenas o pgAdmin
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d --no-deps pgadmin

# Verificar
docker ps | grep pgadmin
# esperado: intellicare-pgadmin Up X seconds
```

## Passo 5 — Aguardar certificado SSL

Let's Encrypt pode levar até 2 minutos para emitir o certificado para o novo subdomínio. Testar:

```bash
curl -I https://pgadmin.intellicare.ia.br/
# esperado: HTTP/2 200
```

## Passo 6 — Login e conexão ao PostgreSQL

1. Acessar `https://pgadmin.intellicare.ia.br`
2. Login com `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`
3. Add New Server:
   - Name: `intellicare-staging`
   - Host: `postgres`
   - Port: `5432`
   - Database: `intellicare_staging`
   - Username / Password: valores do `.env.staging`
4. Confirmar que o database e schemas aparecem

## Passo 7 — Keycloak Admin (sem código — só validação)

1. Abrir `https://auth.intellicare.ia.br/admin/`
2. Obter credenciais: `docker exec intellicare-keycloak env | grep KEYCLOAK_ADMIN`
3. Fazer login
4. Confirmar: realm `intellicare`, usuários, roles, clients

## Gotchas

- pgAdmin na mesma rede Docker (`intellicare-net`) → pode usar `postgres` como hostname interno
- Se o certificado não emitir: verificar que o DNS `pgadmin.intellicare.ia.br` já propagou (`nslookup pgadmin.intellicare.ia.br`)
- Se pgAdmin não conectar ao postgres: verificar que `PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"` está no compose (permite salvar senhas sem master password adicional)
- Keycloak `start-dev` mode: o console de admin é totalmente funcional mesmo em dev mode — não é uma limitação

## Fase 2 — Dev Local

- [x] Expor `pgadmin` em `localhost:5050`
- [x] Padronizar `PGADMIN_EMAIL` e `PGADMIN_PASSWORD` no ambiente local
- [x] Pré-cadastrar `IntelliCare Local PostgreSQL` via `servers.local.json`
- [x] Tornar o cadastro declarativo com reload no startup do container
