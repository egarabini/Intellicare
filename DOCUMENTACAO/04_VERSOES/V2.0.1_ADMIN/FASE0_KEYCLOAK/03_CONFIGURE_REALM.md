# 03 - Configurar Realm e Clients

## 📋 Visão Geral

Este guia cobre a configuração do realm `bemcuidar` e dos clients Keycloak para os módulos IntelliCare.

## ✅ Realm bemcuidar

O realm já é importado automaticamente na primeira inicialização do Keycloak através do arquivo `keycloak/import/bemcuidar-realm.json`.

### Verificar Realm

```bash
# Verificar se realm existe
curl http://localhost:8080/realms/bemcuidar | jq .

# Saída esperada:
{
  "realm": "bemcuidar",
  "public_key": "...",
  "token-service": "http://auth.intellicare.ia.br/realms/bemcuidar/protocol/openid-connect",
  ...
}

# Acessar Admin Console
# URL: http://localhost:8080/admin
# User: admin
# Password: <ver .env.keycloak>
# Realm: bemcuidar
```

## 🔑 Configuração do Realm

### Roles Configuradas

| Role | Descrição | Uso |
|------|-----------|-----|
| PLATFORM_ADMIN | Administrador da plataforma (super-admin) | Acesso total ao Admin (8010) |
| PLATFORM_SUPPORT | Equipe de suporte | Visualização de tickets e chamados |
| PLATFORM_BILLING | Equipe financeira | Gestão de assinaturas e cobranças |

### Groups Configurados

| Group | Descrição |
|-------|-----------|
| platform_admins | Administradores globais da plataforma |

### Usuários Configurados

| Username | Email | Role | Senha Inicial |
|----------|-------|------|---------------|
| admin@intellicare.ia.br | admin@intellicare.ia.br | PLATFORM_ADMIN | changeme-admin (temporária) |

## 📱 Clients Configurados

### intellicare-admin

```json
{
  "clientId": "intellicare-admin",
  "name": "IntelliCare Admin Platform",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "admin-secret-change-in-production",
  "redirectUris": ["http://localhost:8010/*"],
  "webOrigins": ["http://localhost:8010"],
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": true
}
```

**Uso**: Módulo Admin (porta 8010)

### intellicare-portal

```json
{
  "clientId": "intellicare-portal",
  "name": "IntelliCare Portal",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "portal-secret-change-in-production",
  "redirectUris": [
    "http://localhost:3000/*",
    "http://localhost:5173/*"
  ],
  "webOrigins": ["http://localhost:3000", "http://localhost:5173"],
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": true
}
```

**Uso**: Portal React (porta 3001/5173)

## ➕ Adicionar Clients para Módulos

### Via Admin Console

1. Acessar: http://localhost:8080/admin
2. Selecionar realm: `bemcuidar`
3. Ir para: Clients → Create client
4. Preencher:
   - Client ID: `intellicare-<modulo>`
   - Client Type: OpenID Connect
   - Client authentication: ON
5. Configurar:
   - Valid redirect URIs: `http://<modulo>:<porta>/*`
   - Web origins: `http://<modulo>:<porta>`
   - Root URL: `http://<modulo>:<porta>`
6. Salvar e copiar client secret

### Via kcadm CLI

```bash
# Login no kcadm
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password <password>

# Criar client
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh create clients \
  -r bemcuidar \
  -s clientId=intellicare-wanda \
  -s name='IntelliCare Wanda' \
  -s enabled=true \
  -s clientAuthenticatorType=client-secret \
  -s secret=wanda-secret-change \
  -s redirectUris=\"[\"http://localhost:8004/*\"]\" \
  -s webOrigins=\"[\"http://localhost:8004\"]\" \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true

# Listar clients
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh get clients \
  -r bemcuidar \
  --fields clientId,name

# Obter client secret
docker exec -it keycloak-intellicare /opt/keycloak/bin/kcadm.sh get clients/<client-id> \
  -r bemcuidar \
  --fields id,secret
```

## 🎯 Clients para Cada Módulo

| Módulo | Porta | Client ID | Redirect URI |
|--------|-------|-----------|--------------|
| Admin | 8010 | intellicare-admin | `http://localhost:8010/*` |
| Portal | 3001 | intellicare-portal | `http://localhost:3001/*` |
| Wanda | 8004 | intellicare-wanda | `http://localhost:8004/*` |
| Florence | 8001 | intellicare-florence | `http://localhost:8001/*` |
| Oswaldo | 8002 | intellicare-oswaldo | `http://localhost:8002/*` |
| Donabedian | 8003 | intellicare-donabedian | `http://localhost:8003/*` |
| Comunicacao | 8005 | intellicare-comunicacao | `http://localhost:8005/*` |
| Geralda | 8006 | intellicare-geralda | `http://localhost:8006/*` |
| Zilda | 8007 | intellicare-zilda | `http://localhost:8007/*` |
| Minerva | 8008 | intellicare-minerva | `http://localhost:8008/*` |
| Pierre | 8009 | intellicare-pierre | `http://localhost:8009/*` |
| Gestor | 8011 | intellicare-gestor | `http://localhost:8011/*` |
| Grahame | 8012 | intellicare-grahame | `http://localhost:8012/*` |
| Nise | 8013 | intellicare-nise | `http://localhost:8013/*` |

## 🔄 Atualizar Realm JSON

Após adicionar clients via console, exportar o realm para o arquivo JSON:

```bash
# Export realm
docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get realms/bemcuidar \
  -o /tmp/bemcuidar-export.json

# Copy to host
docker cp keycloak-intellicare:/tmp/bemcuidar-export.json ./keycloak/import/bemcuidar-realm.json

# Commit to git
git add keycloak/import/bemcuidar-realm.json
git commit -m "feat: update Keycloak realm with all module clients"
```

## ✅ Checklist

- [ ] Realm bemcuidar existe
- [ ] Roles configuradas (PLATFORM_ADMIN, PLATFORM_SUPPORT, PLATFORM_BILLING)
- [ ] Client intellicare-admin configurado
- [ ] Client intellicare-portal configurado
- [ ] Secrets documentados em local seguro
- [ ] Teste de autenticação com admin

## 📝 Próximo Passo

Após configurar clients, prossiga para: **[04_INTEGRATE_MODULES.md](./04_INTEGRATE_MODULES.md)**

---

**Última Atualização**: 2026-03-01
**Responsável**: IntelliCare Team
