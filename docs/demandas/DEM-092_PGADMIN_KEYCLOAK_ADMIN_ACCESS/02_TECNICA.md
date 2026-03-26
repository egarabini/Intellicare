# DEM-092 — Spec Técnica

## 1. pgAdmin — Novo serviço no docker-compose.yml

### Serviço a adicionar

```yaml
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: intellicare-pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: "True"
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - intellicare-net
    depends_on:
      postgres:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.pgadmin.rule=Host(`pgadmin.intellicare.ia.br`)"
      - "traefik.http.routers.pgadmin.entrypoints=websecure"
      - "traefik.http.routers.pgadmin.tls.certresolver=letsencrypt"
      - "traefik.http.services.pgadmin.loadbalancer.server.port=80"
      - "traefik.http.routers.pgadmin-http.rule=Host(`pgadmin.intellicare.ia.br`)"
      - "traefik.http.routers.pgadmin-http.entrypoints=web"
      - "traefik.http.routers.pgadmin-http.middlewares=redirect-to-https"
      - "traefik.http.routers.pgadmin-http.service=pgadmin"
```

### Volume a adicionar (seção `volumes:`)

```yaml
  pgadmin_data:
```

### Variáveis a adicionar no `.env.staging`

```env
PGADMIN_EMAIL=admin@intellicare.ia.br
PGADMIN_PASSWORD=<senha-forte>
```

### DNS a criar

```
A  pgadmin.intellicare.ia.br  → IP do VPS
```

### Conexão ao servidor no pgAdmin (pós-login)

Após login, criar servidor manualmente ou usar o "servers.json" pré-configurado:

- **Host:** `postgres` (nome interno Docker — funciona porque estão na mesma rede)
- **Port:** `5432`
- **Database:** `intellicare_staging`
- **Username:** valor de `POSTGRES_USER` do `.env.staging`
- **Password:** valor de `POSTGRES_PASSWORD` do `.env.staging`

> Alternativa: pre-seed via arquivo `servers.json` montado como volume para que a conexão apareça automaticamente pós-login.

---

## 2. Keycloak Admin Console — Diagnóstico e Acesso

### Por que falhou

O console está acessível mas a URL correta não estava documentada. O Traefik roteia `auth.intellicare.ia.br → keycloak:8080` sem restrição de path, portanto todos os caminhos funcionam — mas o console está em `/admin/`, não na raiz.

### URL correta

```
https://auth.intellicare.ia.br/admin/
```

Ou diretamente no realm:
```
https://auth.intellicare.ia.br/admin/master/console/
```

### Credenciais

Estão no `.env.staging`:
```bash
grep KEYCLOAK_ADMIN infra/.env.staging
# KEYCLOAK_ADMIN=admin
# KEYCLOAK_ADMIN_PASSWORD=<valor>
```

Ou no VPS:
```bash
docker exec intellicare-keycloak env | grep KEYCLOAK_ADMIN
```

### Verificação de saúde do Keycloak

```bash
curl https://auth.intellicare.ia.br/health/ready
# esperado: {"status":"UP","checks":[...]}
```

### Atualizar validação no plano

O item `2.1 Acesso ao Admin Console` do plano de validação deve usar a URL `/admin/` e buscar as credenciais no `.env.staging` antes de tentar o login.

---

## Ordem de execução

1. Adicionar variáveis `PGADMIN_EMAIL` e `PGADMIN_PASSWORD` ao `infra/.env.staging`
2. Adicionar serviço `pgadmin` e volume `pgadmin_data` ao `infra/docker-compose.yml`
3. Commitar e fazer push
4. No VPS: `git pull origin main`
5. Subir pgAdmin: `docker compose --env-file infra/.env.staging -f infra/docker-compose.yml up -d --no-deps pgadmin`
6. Aguardar Let's Encrypt emitir certificado para `pgadmin.intellicare.ia.br`
7. Acessar `https://pgadmin.intellicare.ia.br` e criar conexão ao servidor
8. Testar Keycloak admin: `https://auth.intellicare.ia.br/admin/`
