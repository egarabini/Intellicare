# 07 - Deploy em Produção

## 📋 Visão Geral

Este guia cobre o deploy do Keycloak em ambiente de produção.

## ⚠️ AVISO IMPORTANTE

Produção requer:
- Senhas fortes geradas dinamicamente
- Vault para secrets management
- Certificados SSL válidos (Let's Encrypt ou CA)
- Firewall configurado corretamente
- Backup automatizado
- Alta disponibilidade (HA)
- Monitoramento 24/7

## 🌐 Configuração Produção

### URL
- **Keycloak**: https://auth.saudeconectada.com.br
- **Admin Console**: https://auth.saudeconectada.com.br/admin
- **Realm**: bemcuidar

### Servidor de Produção
- **Host**: TBD
- **User**: TBD
- **Branch**: main

## 🔐 Segurança em Produção

### 1. Vault para Secrets

Usar HashiCorp Vault para armazenar senhas:

```bash
# Instalar Vault CLI
# Configurar VAULT_ADDR e VAULT_TOKEN

# Armazenar secrets
vault kv put intellicare/keycloak/db \
  password=$(openssl rand -base64 32)

vault kv put intellicare/keycloak/admin \
  password=$(openssl rand -base64 32)

# Carregar secrets no deploy
export KEYCLOAK_DB_PASSWORD=$(vault kv get -field=password intellicare/keycloak/db)
export KEYCLOAK_ADMIN_PASSWORD=$(vault kv get -field=password intellicare/keycloak/admin)
```

### 2. Certificados SSL

Para produção, usar **Let's Encrypt via Traefik** ou certificados de CA:

```yaml
# docker-compose.keycloak.yml (produção)
keycloak:
  environment:
    KC_HOSTNAME: auth.saudeconectada.com.br
    KC_HTTP_ENABLED: "false"
    KC_HTTPS_KEYSTORE_FILE: /opt/keycloak/conf/server.keystore
    KC_HTTPS_KEYSTORE_PASSWORD: ${KEYCLOAK_KEYSTORE_PASSWORD}
    KC_PROXY: edge
```

### 3. Firewall

```bash
# Apenas portas necessárias
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
ufw enable
```

### 4. Rate Limiting

```yaml
# docker-compose.keycloak.yml
keycloak:
  environment:
    KC_SPIKE_CONNECTION_BUFFER_ENABLED: "true"
    KC_DB_POOL_MAX_SIZE: "50"
    KC_DB_POOL_MIN_SIZE: "10"
```

## 🚀 Deploy Produção

### 1. Preparar Servidor

```bash
# 1. SSH no servidor de produção
ssh root@<production-server>

# 2. Instalar Docker e Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clonar repo (branch main)
git clone -b main https://github.com/egarabini/Intellicare.git /opt/intellicare
cd /opt/intellicare

# 4. Criar rede Docker
docker network create intellicare_intellicare-network
```

### 2. Configurar Environment

```bash
# Carregar secrets do Vault
export VAULT_ADDR=https://vault.saudeconectada.com.br
export VAULT_TOKEN=<vault-token>

KEYCLOAK_DB_PASSWORD=$(vault kv get -field=password intellicare/keycloak/db)
KEYCLOAK_ADMIN_PASSWORD=$(vault kv get -field=password intellicare/keycloak/admin)

# Criar .env.production
cat > .env.production << EOF
KEYCLOAK_DB_PASSWORD=$KEYCLOAK_DB_PASSWORD
KEYCLOAK_HOSTNAME=auth.saudeconectada.com.br
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=$KEYCLOAK_ADMIN_PASSWORD
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOF

chmod 600 .env.production
```

### 3. Configurar DNS

```bash
# Adicionar registros DNS no domínio saudeconectada.com.br
# Type: CNAME
# Name: auth
# Target: saudeconectada.com.br (ou IP do servidor)

# Verificar DNS
nslookup auth.saudeconectada.com.br
dig auth.saudeconectada.com.br
```

### 4. Deploy

```bash
# 1. Iniciar infraestrutura (Traefik)
docker-compose -f docker-compose.traefik.yml up -d

# 2. Verificar Traefik
curl https://traefik.saudeconectada.com.br/dashboard

# 3. Iniciar Keycloak
docker-compose -f docker-compose.keycloak.yml --env-file .env.production up -d

# 4. Verificar status
docker ps | grep keycloak
docker logs -f keycloak-intellicare
```

### 5. Verificar Deploy

```bash
# Health check
curl https://auth.saudeconectada.com.br/health/ready

# Realm
curl https://auth.saudeconectada.com.br/realms/bemcuidar

# Testar login
curl -X POST "https://auth.saudeconectada.com.br/realms/bemcuidar/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<password>&grant_type=password&client_id=admin-cli"
```

## 📊 Backup

### Automatizar Backups

```bash
#!/bin/bash
# backup_keycloak.sh - Backup diário do Keycloak

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/keycloak"
KEYCLOAK_CONTAINER="keycloak-intellicare"

mkdir -p $BACKUP_DIR

# 1. Export realm
docker exec $KEYCLOAK_CONTAINER /opt/keycloak/bin/kcadm.sh get realms/bemcuidar \
  -o /tmp/realm-backup-$DATE.json

docker cp $KEYCLOAK_CONTAINER:/tmp/realm-backup-$DATE.json \
  $BACKUP_DIR/realm-$DATE.json

# 2. Backup database
docker exec keycloak-db pg_dump -U keycloak keycloak \
  > $BACKUP_DIR/db-$DATE.sql

# 3. Comprimir
tar -czf $BACKUP_DIR/keycloak-$DATE.tar.gz \
  $BACKUP_DIR/realm-$DATE.json \
  $BACKUP_DIR/db-$DATE.sql

# 4. Upload para S3 (ou outro storage)
aws s3 cp $BACKUP_DIR/keycloak-$DATE.tar.gz \
  s3://intellicare-backups/keycloak/

# 5. Limpar backups antigos (7 dias)
find $BACKUP_DIR -name "keycloak-*.tar.gz" -mtime +7 -delete

echo "✅ Backup concluído: keycloak-$DATE.tar.gz"
```

### Cron Job

```bash
# Adicionar ao crontab
crontab -e

# Backup diário às 3h da manhã
0 3 * * * /opt/intellicare/scripts/backup_keycloak.sh >> /var/log/keycloak_backup.log 2>&1
```

## 🔄 Restore

```bash
#!/bin/bash
# restore_keycloak.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Uso: ./restore_keycloak.sh <backup-file>"
  exit 1
fi

# 1. Parar Keycloak
docker-compose -f docker-compose.keycloak.yml stop keycloak

# 2. Restore database
docker exec -i keycloak-db psql -U keycloak keycloak < \
  $(tar -xzf $BACKUP_FILE -O --wildcards "*db-*.sql")

# 3. Import realm
docker cp $(tar -xzf $BACKUP_FILE -O --wildcards "*realm-*.json") \
  keycloak-intellicare:/tmp/realm-restore.json

docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh create realms \
  -f /tmp/realm-restore.json || \
  docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh update realms/bemcuidar \
  -f /tmp/realm-restore.json

# 4. Iniciar Keycloak
docker-compose -f docker-compose.keycloak.yml start keycloak

echo "✅ Restore concluído"
```

## 📈 Monitoramento

### Prometheus + Grafana

```yaml
# Keycloak metrics endpoint
curl -u admin:password https://auth.saudeconectada.com.br/metrics

# Métricas importantes:
# - keycloak_user_sessions
# - keycloak_failed_login_attempts
# - keycloak_successful_logins
# - JVM memory, CPU, threads
```

### Alertas

```yaml
# alerting_rules.yml
groups:
  - name: keycloak
    rules:
      - alert: KeycloakDown
        expr: up{job="keycloak"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Keycloak está down"

      - alert: KeycloakHighFailureRate
        expr: rate(keycloak_failed_login_attempts[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alta taxa de falhas de login"

      - alert: KeycloakDatabaseConnections
        expr: keycloak_database_connections < 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Poucas conexões com database"
```

## ✅ Checklist Deploy Produção

### Pré-Deploy
- [ ] Vault configurado e acessível
- [ ] DNS configurado (auth.saudeconectada.com.br)
- [ ] Firewall configurado (apenas 80, 443, 22)
- [ ] Certificados SSL válidos
- [ ] Backup automatizado configurado
- [ ] Monitoramento configurado
- [ ] Alertas configurados

### Deploy
- [ ] .env.production criado
- [ ] Secrets carregados do Vault
- [ ] Traefik rodando
- [ ] Keycloak iniciado
- [ ] Health check OK
- [ ] Realm importado
- [ ] Clients configurados
- [ ] Módulos atualizados

### Pós-Deploy
- [ ] Teste de login/logout
- [ ] Teste de token refresh
- [ ] Verificar logs de erros
- [ ] Verificar métricas
- [ ] Testar backup
- [ ] Documentar credenciais
- [ ] Comunicar time

## 🚨 Emergências

### Se Keycloak cair

```bash
# 1. Verificar logs
docker logs -f keycloak-intellicare

# 2. Verificar health
curl https://auth.saudeconectada.com.br/health/ready

# 3. Verificar database
docker exec -it keycloak-db psql -U keycloak keycloak -c "SELECT 1"

# 4. Reiniciar se necessário
docker-compose -f docker-compose.keycloak.yml restart keycloak

# 5. Se persistir, escalar para time de infra
```

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
**Importância**: CRÍTICA - Produção
