# 06 - Deploy em Staging

## 📋 Visão Geral

Este guia cobre o deploy do Keycloak em ambiente de staging.

## 🌐 Configuração Staging

### URL
- **Keycloak**: https://auth.intellicare.ia.br
- **Admin Console**: https://auth.intellicare.ia.br/admin
- **Realm**: bemcuidar

### Servidor
- **Host**: 167.86.97.142
- **User**: root
- **Branch**: staging

## 🚀 Passo a Passo

### 1. Preparar Certificados SSL

Para staging, usar **Traefik** com **Let's Encrypt** para gerenciar certificados automaticamente. O Keycloak está configurado no módulo `intellicare-auth/keycloak/`:

```yaml
# docker-compose.keycloak.yml (staging)
# Arquivo: raiz do projeto
keycloak:
  environment:
    KC_HTTP_ENABLED: "true"
    KC_PROXY: none
    KC_HOSTNAME_STRICT: "false"

  volumes:
    # Import realm do diretório do módulo intellicare-auth
    - ./intellicare-auth/keycloak/import:/opt/keycloak/data/import:ro
    - ./intellicare-auth/keycloak/certs:/opt/keycloak/conf:ro

  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.keycloak.rule=Host(`auth.intellicare.ia.br`)"
    - "traefik.http.routers.keycloak.entrypoints=websecure"
    - "traefik.http.routers.keycloak.tls.certresolver=letsencrypt"
    - "traefik.http.services.keycloak.loadbalancer.server.port=8080"
```

### 2. Configurar DNS

```bash
# Adicionar registro DNS no domínio intellicare.ia.br
# Type: CNAME
# Name: auth
# Target: intellicare.ia.br (ou IP do servidor)

# Verificar DNS
nslookup auth.intellicare.ia.br
```

### 3. Atualizar .env.staging

```bash
cat > .env.staging << 'EOF'
# Keycloak Staging
KEYCLOAK_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}
KEYCLOAK_HOSTNAME=auth.intellicare.ia.br
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
KEYCLOAK_HTTP_PORT=8080
KEYCLOAK_HTTPS_PORT=8443
EOF
```

### 4. Deploy no Servidor

```bash
# 1. SSH no servidor
ssh root@167.86.97.142

# 2. Ir para diretório do projeto
cd /opt/intellicare

# 3. Atualizar código
git pull origin staging

# 4. Copiar variáveis de ambiente
cp .env.staging .env.keycloak

# 5. Iniciar Keycloak com Traefik
docker-compose -f docker-compose.keycloak.yml -f docker-compose.traefik.yml up -d

# 6. Verificar status
docker ps | grep keycloak
docker logs -f keycloak-intellicare
```

### 5. Verificar Deploy

```bash
# Verificar saúde
curl https://auth.intellicare.ia.br/health/ready

# Verificar realm
curl https://auth.intellicare.ia.br/realms/bemcuidar

# Testar admin console
# Abrir browser: https://auth.intellicare.ia.br/admin
# User: admin
# Password: <ver .env.staging>
```

### 6. Atualizar Clients para Staging

Atualizar redirect URIs dos clients para usar HTTPS:

```bash
# Via Admin Console ou kcadm
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh update clients/intellicare-admin \
  -r bemcuidar \
  -s 'redirectUris=["https://admin.intellicare.ia.br/*","http://localhost:8010/*"]' \
  -s 'webOrigins=["https://admin.intellicare.ia.br","http://localhost:8010"]'

# Portal
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh update clients/intellicare-portal \
  -r bemcuidar \
  -s 'redirectUris=["https://intellicare.ia.br/*","http://localhost:3001/*"]' \
  -s 'webOrigins=["https://intellicare.ia.br","http://localhost:3001"]'
```

### 7. Atualizar Módulos para Staging

```bash
# Atualizar keycloak_client_secrets.json em cada módulo
{
  "web": {
    "auth_uri": "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/auth",
    "client_id": "intellicare-admin",
    "client_secret": "<SECRET>",
    "redirect_uris": ["https://admin.intellicare.ia.br/*"],
    "token_uri": "https://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect/token",
    "issuer": "https://auth.intellicare.ia.br/realms/bemcuidar"
  }
}
```

## 🔐 Segurança em Staging

### Configurações Importantes

- [x] HTTPS obrigatório
- [x] Certificados Let's Encrypt via Traefik
- [x] Senhas fortes (não usar padrão)
- [x] CORS configurado corretamente
- [x] Rate limiting habilitado
- [x] Audit log habilitado

### Senhas

**NUNCA** commitar senhas no Git. Usar variáveis de ambiente ou Vault.

```bash
# Gerar senha segura
openssl rand -base64 32

# Usar em .env.staging
KEYCLOAK_ADMIN_PASSWORD=<senha segura>
```

## 📊 Monitoramento

### Logs

```bash
# Ver logs em tempo real
docker logs -f keycloak-intellicare

# Ver logs de erros
docker logs keycloak-intellicare | grep ERROR

# Salvar logs
docker logs keycloak-intellicare > /var/log/keycloak.log 2>&1
```

### Métricas

```bash
# Obter métricas (requer admin)
curl -u admin:password http://localhost:8080/metrics

# Métricas disponíveis:
# - keycloak_user_sessions
# - keycloak_failed_login_attempts
# - keycloak_successful_logins
# - keycloak_login_attempts
```

### Health Checks

```bash
# Script de health check
#!/bin/bash
while true; do
  if curl -sf https://auth.intellicare.ia.br/health/ready > /dev/null; then
    echo "✅ Keycloak healthy"
  else
    echo "❌ Keycloak unhealthy"
    # Enviar alerta (Slack, PagerDuty, etc)
  fi
  sleep 60
done
```

## ✅ Checklist Deploy Staging

- [ ] DNS configurado (auth.intellicare.ia.br)
- [ ] .env.staging criado e configurado
- [ ] Traefik rodando e com Let's Encrypt
- [ ] Keycloak iniciado
- [ ] Health check respondendo
- [ ] Realm bemcuidar importado
- [ ] Clients atualizados (redirect URIs HTTPS)
- [ ] Senhas trocadas de padrão
- [ ] Módulos atualizados (keycloak_client_secrets.json)
- [ ] Teste de login/logout funcionando
- [ ] HTTPS funcionando
- [ ] CORS configurado

## 🔄 Rollback

Se algo der errado:

```bash
# Parar Keycloak
docker-compose -f docker-compose.keycloak.yml down

# Voltar para versão anterior
git checkout <commit-anterior>

# Reiniciar
docker-compose -f docker-compose.keycloak.yml up -d

# Verificar logs
docker logs -f keycloak-intellicare
```

## 📝 Próximo Passo

Após deploy em staging, prossiga para: **[07_DEPLOY_PRODUCTION.md](./07_DEPLOY_PRODUCTION.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
