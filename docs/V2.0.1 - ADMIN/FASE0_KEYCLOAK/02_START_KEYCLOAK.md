# 02 - Iniciar Servidor Keycloak

## 📋 Visão Geral

Este guia cobre a inicialização do servidor Keycloak em todos os ambientes.

## 🚀 Quick Start

### Desenvolvimento (HTTP)

```bash
# 1. Copiar arquivo de ambiente
cp .env.keycloak .env.local

# 2. Iniciar Keycloak
docker-compose -f docker-compose.keycloak.yml up -d

# 3. Verificar health
curl http://localhost:8080/health/ready

# 4. Ver logs
docker logs -f keycloak-intellicare
```

### Staging (HTTPS via Traefik)

```bash
# 1. Exportar variáveis
export $(cat .env.staging | xargs)

# 2. Iniciar com Traefik
docker-compose -f docker-compose.keycloak.yml -f docker-compose.traefik.yml up -d

# 3. Verificar saúde
curl https://auth.intellicare.ia.br/health/ready
```

### Produção (HTTPS via Traefik)

```bash
# 1. Carregar secrets do Vault
export KEYCLOAK_DB_PASSWORD=$(vault kv get -field=password intellicare/keycloak/db)
export KEYCLOAK_ADMIN_PASSWORD=$(vault kv get -field=password intellicare/keycloak/admin)

# 2. Iniciar
docker-compose -f docker-compose.keycloak.yml -f docker-compose.traefik.yml up -d
```

## 🔧 Configurações

### Sem Keystore (Desenvolvimento)

Para desenvolvimento, podemos usar HTTP sem keystore:

```yaml
# docker-compose.keycloak.yml (desenvolvimento)
keycloak:
  command: start-dev --import-realm
  environment:
    KC_HTTP_ENABLED: "true"
    KC_HOSTNAME_STRICT: "false"
    KC_HOSTNAME_STRICT_HTTPS: "false"
```

### Com Keystore (Produção)

Para produção, usar HTTPS com keystore:

```yaml
# docker-compose.keycloak.yml (produção)
keycloak:
  command: start --import-realm
  environment:
    KC_HTTPS_ENABLED: "true"
    KC_HTTPS_KEYSTORE_FILE: /opt/keycloak/conf/server.keystore
    KC_HTTPS_KEYSTORE_PASSWORD: ${KEYCLOAK_KEYSTORE_PASSWORD}
```

## 📊 Health Checks

```bash
# Verificar se está pronto
curl http://localhost:8080/health/ready

# Verificar se está healthy
curl http://localhost:8080/health/live

# Verificar metrics (necessita autenticação)
curl -u admin:password http://localhost:8080/metrics
```

## 📝 Logs

```bash
# Logs em tempo real
docker logs -f keycloak-intellicare

# Últimos 100 linhas
docker logs --tail 100 keycloak-intellicare

# Logs com timestamp
docker logs -t keycloak-intellicare

# Salvar logs em arquivo
docker logs keycloak-intellicare > keycloak.log 2>&1
```

## 🛠️ Troubleshooting

### Erro: "Database connection failed"

```bash
# Verificar se keycloak-db está rodando
docker ps | grep keycloak-db

# Ver logs do database
docker logs keycloak-db

# Reiniciar database
docker-compose -f docker-compose.keycloak.yml restart keycloak-db
```

### Erro: "Port 8080 already in use"

```bash
# Verificar o que está usando a porta
lsof -i :8080

# Ou
netstat -tuln | grep 8080

# Mudar porta no .env
echo "KEYCLOAK_HTTP_PORT=8888" >> .env.keycloak
```

### Erro: "Realm import failed"

```bash
# Verificar se arquivo de import existe
ls -la keycloak/import/bemcuidar-realm.json

# Verificar JSON válido
cat keycloak/import/bemcuidar-realm.json | jq .

# Import manual via CLI
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh create realms -f - < keycloak/import/bemcuidar-realm.json
```

### Erro: "Admin console not accessible"

```bash
# Verificar se container está rodando
docker ps | grep keycloak

# Verificar se porta está mapeada
docker port keycloak-intellicare

# Acessar diretamente no container
docker exec -it keycloak-intellicare bash
curl http://localhost:8080/
```

## ✅ Checklist de Inicialização

- [ ] Variáveis de ambiente configuradas (.env.keycloak)
- [ ] Rede Docker criada (intellicare_intellicare-network)
- [ ] Keycloak iniciado: `docker ps | grep keycloak`
- [ ] Health check passando: `curl http://localhost:8080/health/ready`
- [ ] Realm importado: Acessar http://localhost:8080/admin
- [ ] Logar com admin/admin
- [ ] Verificar realm bemcuidar existe
- [ ] Verificar clients configurados

## 🎯 URLs Após Inicialização

| Serviço | URL Local | URL Staging |
|---------|-----------|-------------|
| Keycloak | http://localhost:8080 | https://auth.intellicare.ia.br |
| Admin Console | http://localhost:8080/admin | https://auth.intellicare.ia.br/admin |
| Realm bemcuidar | http://localhost:8080/realms/bemcuidar | https://auth.intellicare.ia.br/realms/bemcuidar |
| Account Console | http://localhost:8080/realms/bemcuidar/account | https://auth.intellicare.ia.br/realms/bemcuidar/account |

## 📝 Próximo Passo

Após iniciar o Keycloak, prossiga para: **[03_CONFIGURE_REALM.md](./03_CONFIGURE_REALM.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
