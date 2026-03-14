# DEM-023 — Deploy Produção

## Objetivo

Colocar o IntelliCare V3 em produção num servidor VPS com:
- HTTPS em todos os endpoints (Let's Encrypt via Traefik)
- Subdomínios por módulo
- Variáveis de ambiente seguras (sem senhas de dev)
- Backup automático do banco de dados

---

## 1. Pré-requisitos (Eduardo — ação manual)

Antes de executar este DEM, Eduardo deve:

| Item | Ação |
|------|------|
| VPS | Provisionar servidor Ubuntu 22.04, mínimo 4GB RAM / 2 vCPU / 40GB SSD |
| Domínio | Ter acesso ao painel DNS do domínio `intellicare.ia.br` |
| Registros DNS | Criar os registros A abaixo apontando para o IP do VPS |

**Registros DNS a criar:**

```
A   intellicare.ia.br          →  <IP_VPS>
A   admin.intellicare.ia.br    →  <IP_VPS>
A   api.intellicare.ia.br      →  <IP_VPS>
A   auth.intellicare.ia.br     →  <IP_VPS>
```

---

## 2. Preparar o servidor

```bash
# Conectar via SSH
ssh root@<IP_VPS>

# Instalar Docker + Docker Compose
apt-get update && apt-get install -y docker.io docker-compose-plugin git curl
systemctl enable --now docker

# Clonar repositório
git clone https://github.com/egarabini/Intellicare.git /opt/intellicare
cd /opt/intellicare
```

---

## 3. Arquivo `.env` de produção

Criar `/opt/intellicare/infra/.env.prod` com valores **diferentes** do dev:

```bash
# PostgreSQL — senhas fortes
POSTGRES_USER=intellicare_prod
POSTGRES_PASSWORD=<SENHA_FORTE_32_CHARS>
POSTGRES_DB=intellicare_prod
POSTGRES_HOST=postgres

# Redis
REDIS_PASSWORD=<SENHA_FORTE_REDIS>
REDIS_HOST=redis

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<SENHA_FORTE_KC>
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://postgres:5432/intellicare_prod
KC_DB_USERNAME=intellicare_prod
KC_DB_PASSWORD=<SENHA_FORTE_32_CHARS>

# OLLAMA
OLLAMA_HOST=0.0.0.0
OLLAMA_ORIGINS=*
OLLAMA_API_URL=http://ollama:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Traefik
TRAEFIK_DASHBOARD_PORT=8090
LETSENCRYPT_EMAIL=egarabini@gmail.com

# Aplicação
SECRET_KEY=<SECRET_KEY_64_CHARS_ALEATORIO>
ENVIRONMENT=production
LOG_LEVEL=INFO

# Keycloak interno
KEYCLOAK_INTERNAL_URL=http://keycloak:8080
KEYCLOAK_URL=https://auth.intellicare.ia.br
KEYCLOAK_REALM=intellicare
KEYCLOAK_CLIENT_ID=intellicare-service
KEYCLOAK_CLIENT_SECRET=<SECRET_FORTE>
```

Gerar senhas fortes:
```bash
openssl rand -base64 32  # para senhas de DB/Redis
openssl rand -hex 32     # para SECRET_KEY
```

---

## 4. Atualizar `docker-compose.yml` para produção

Adicionar Traefik labels para **todos** os subdomínios:

```yaml
# No serviço intellicare-service, adicionar labels:
labels:
  - "traefik.enable=true"
  # API
  - "traefik.http.routers.api.rule=Host(`api.intellicare.ia.br`)"
  - "traefik.http.routers.api.entrypoints=websecure"
  - "traefik.http.routers.api.tls.certresolver=letsencrypt"
  - "traefik.http.services.api.loadbalancer.server.port=8000"
  # Admin UI
  - "traefik.http.routers.admin.rule=Host(`admin.intellicare.ia.br`)"
  - "traefik.http.routers.admin.entrypoints=websecure"
  - "traefik.http.routers.admin.tls.certresolver=letsencrypt"
  # Redirect HTTP → HTTPS (global)
  - "traefik.http.routers.http-catchall.rule=hostregexp(`{host:.+}`)"
  - "traefik.http.routers.http-catchall.entrypoints=web"
  - "traefik.http.routers.http-catchall.middlewares=redirect-https"
  - "traefik.http.middlewares.redirect-https.redirectscheme.scheme=https"
  - "traefik.http.middlewares.redirect-https.redirectscheme.permanent=true"

# No serviço keycloak:
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.keycloak.rule=Host(`auth.intellicare.ia.br`)"
  - "traefik.http.routers.keycloak.entrypoints=websecure"
  - "traefik.http.routers.keycloak.tls.certresolver=letsencrypt"
  - "traefik.http.services.keycloak.loadbalancer.server.port=8080"
```

---

## 5. Atualizar Keycloak para produção

Após deploy, executar `setup_keycloak.py` apontando para o Keycloak de produção,
atualizando os `redirectUris` e `webOrigins` dos clients para os domínios reais:

```
admin-ui:    https://admin.intellicare.ia.br/admin-ui/*
gestor-ui:   https://app.intellicare.ia.br/gestor-ui/*
clinico-ui:  https://app.intellicare.ia.br/clinico-ui/*
paciente-ui: https://app.intellicare.ia.br/paciente-ui/*
```

---

## 6. Deploy

```bash
cd /opt/intellicare

# Subir serviços de infra primeiro
docker compose --env-file infra/.env.prod -f infra/docker-compose.yml \
  up -d postgres redis keycloak ollama traefik

# Aguardar Keycloak ficar healthy (~2 min)
docker compose --env-file infra/.env.prod -f infra/docker-compose.yml ps

# Configurar Keycloak de produção
python tools/scripts/setup_keycloak.py \
  --keycloak-url https://auth.intellicare.ia.br \
  --seed-demo-users

# Build e subir o serviço principal
docker compose --env-file infra/.env.prod -f infra/docker-compose.yml \
  up -d --build intellicare-service

# Rodar seed de homologação
python tools/scripts/seed_demo.py
```

---

## 7. Backup automático do banco

Criar `/opt/intellicare/tools/backup_db.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/intellicare"
mkdir -p $BACKUP_DIR

docker exec intellicare-postgres pg_dump \
  -U intellicare_prod intellicare_prod \
  | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Manter apenas últimos 30 backups
ls -t $BACKUP_DIR/*.sql.gz | tail -n +31 | xargs rm -f
echo "[OK] Backup $DATE concluído"
```

Agendar via cron:
```bash
chmod +x /opt/intellicare/tools/backup_db.sh
crontab -e
# Adicionar: 0 3 * * * /opt/intellicare/tools/backup_db.sh >> /var/log/intellicare_backup.log 2>&1
```

---

## 8. Checklist de Entrega

- [ ] VPS provisionado com Docker instalado
- [ ] Registros DNS criados e propagados (verificar com `nslookup admin.intellicare.ia.br`)
- [ ] `.env.prod` criado com senhas fortes (não commitado no git)
- [ ] `docker compose up` completo sem erros
- [ ] Traefik emitiu certificados Let's Encrypt (verificar `https://admin.intellicare.ia.br`)
- [ ] Keycloak acessível em `https://auth.intellicare.ia.br`
- [ ] AdminUI acessível em `https://admin.intellicare.ia.br/admin-ui/`
- [ ] Login com `platform-admin` funciona em produção
- [ ] Seed de demo executado
- [ ] Backup cron configurado
- [ ] Commit: `feat(DEM-023): scripts de deploy producao`
