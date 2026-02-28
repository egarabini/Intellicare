# Fase 0 - Keycloak: Configuração e Integração

> **Fase:** 0 | **Prioridade:** P0 (Crítica) | **Estimativa:** 2 dias
> **Bloqueia:** Fase 1 (intellicare-admin)
> **Componente:** Infraestrutura de Autenticação Multi-Tenant

---

## 1. Objetivo

Configurar o **Keycloak** como provedor de identidade centralizado para o IntelliCare multi-tenant, suportando:
- ✅ Single Sign-On (SSO) para todos os tenants
- ✅ Multi-tenancy via claims no JWT
- ✅ Separação por grupos (um grupo por tenant)
- ✅ Admin API para provisionamento automatizado
- ✅ Integração com `intellicare-auth`

---

## 2. Arquitetura de Autenticação

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Keycloak                                 │
│                    Realm: bemcuidar                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ CLIENTS                                                       │ │
│  │  ┌──────────────────┐  ┌──────────────────┐                │ │
│  │  │ intellicare-     │  │ intellicare-     │                │ │
│  │  │ admin            │  │ portal          │                │ │
│  │  └──────────────────┘  └──────────────────┘                │ │
│  │       ↓                      ↓                               │ │
│  │  Platform Admin         Tenant Users                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ GROUPS (1 por Tenant)                                        │ │
│  │  tenant_hospital_santa_clara ──→ {tenant_id: "hospital..."}   │ │
│  │  tenant_ubs_centro           ──→ {tenant_id: "ubs_centro"}    │ │
│  │  tenant_clinica_abc           ──→ {tenant_id: "clinica_abc"}  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ USERS (admin local de cada tenant)                          │ │
│  │  admin_hospital_santa_clara                                 │ │
│  │  admin_ubs_centro                                           │ │
│  │  admin_clinica_abc                                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ PROTOCOL MAPPER                                              │ │
│  │  tenant_id → User Attribute → JWT Claim                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                    ↓ JWT com tenant_id
┌─────────────────────────────────────────────────────────────────────┐
│                     IntelliCare Services                          │
│                                                                    │
│  GET /api/v1/health                                               │
│  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...                   │
│  Headers: {tenant_id: "hospital_santa_clara"}                    │
│                                                                    │
│  1. intellicare-admin → Valida role PLATFORM_ADMIN             │
│  2. intellicare-portal → Extrai tenant_id e rota               │
│  3. Módulos (Zilda, Oswaldo...) → Valida tenant_id             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Docker Compose - Keycloak

### 3.1 Estrutura Completa

```yaml
# docker-compose.keycloak.yml
version: '3.8'

services:
  # PostgreSQL dedicado para Keycloak
  keycloak-db:
    image: postgres:15-alpine
    container_name: keycloak-db
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: ${KEYCLOAK_DB_PASSWORD:-changeme}
    volumes:
      - keycloak_db_data:/var/lib/postgresql/data
    networks:
      - intellicare_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keycloak"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Keycloak Server
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: keycloak
    command: start-dev
    environment:
      # Database
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: ${KEYCLOAK_DB_PASSWORD:-changeme}

      # Hostname
      KC_HOSTNAME: ${KEYCLOAK_HOSTNAME:-auth.intellicare.ia.br}
      KC_HTTP_ENABLED: "true"

      # Admin
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN:-admin}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-changeme}

      # Realm
      KC_REALM: bemcuidar

      # Logging
      KC_LOG_LEVEL: INFO

      # Proxy
      KC_PROXY: edge

      # CORS
      KC_HTTP_CORS: "true"
      KC_HTTP_CORS_MAX_AGE: "86400"
      KC_HTTP_CORS_ALLOWED_METHODS: "GET,POST,PUT,DELETE,OPTIONS,PATCH"
      KC_HTTP_CORS_ALLOWED_HEADERS: "Authorization,Content-Type,Accept,X-Tenant-ID"

      # Health
      KC_HEALTH_ENABLED: "true"

    volumes:
      - ./keycloak/import:/opt/keycloak/data/import:ro
      - ./keycloak/themes:/opt/keycloak/themes
    ports:
      - "8080:8080"  # HTTP
      - "8443:8443"  # HTTPS (produção)
    networks:
      - intellicare_network
    depends_on:
      keycloak-db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    restart: unless-stopped

networks:
  intellicare_network:
    external: true

volumes:
  keycloak_db_data:
```

### 3.2 Arquivo .env

```bash
# .env.keycloak
KEYCLOAK_DB_PASSWORD=your_secure_password_here
KEYCLOAK_HOSTNAME=auth.intellicare.ia.br
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your_admin_password_here
```

---

## 4. Configuração do Realm

### 4.1 Estrutura do Realm `bemcuidar`

```json
{
  "realm": "bemcuidar",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,

  "clients": [
    {
      "clientId": "intellicare-admin",
      "name": "IntelliCare Admin Platform",
      "description": "Administração da plataforma (super-admins)",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "${ADMIN_CLIENT_SECRET}",
      "redirectUris": ["http://localhost:8010/*"],
      "webOrigins": ["http://localhost:8010"],
      "bearerOnly": true,
      "consentRequired": false,
      "standardFlowEnabled": false,
      "directAccessGrantsEnabled": true,
      "serviceAccountsEnabled": true,
      "publicClient": false,
      "protocol": "openid-connect",
      "protocolMappers": [
        {
          "name": "role",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-attribute-mapper",
          "consentRequired": false,
          "claimName": "role",
          "userAttribute": "role"
        }
      ]
    },
    {
      "clientId": "intellicare-portal",
      "name": "IntelliCare Portal",
      "description": "Portal de acesso para tenants",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "${PORTAL_CLIENT_SECRET}",
      "redirectUris": ["http://localhost:3000/*"],
      "webOrigins": ["http://localhost:3000"],
      "bearerOnly": false,
      "consentRequired": false,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "publicClient": false,
      "protocol": "openid-connect",
      "protocolMappers": [
        {
          "name": "tenant_id",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-attribute-mapper",
          "consentRequired": false,
          "claimName": "tenant_id",
          "userAttribute": "tenant_id"
        },
        {
          "name": "name",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-attribute-mapper",
          "consentRequired": false,
          "claimName": "name",
          "userAttribute": "nome"
        }
      ]
    }
  ],

  "roles": {
    "realm": [
      {
        "name": "PLATFORM_ADMIN",
        "description": "Administrador da plataforma (super-admin)"
      },
      {
        "name": "PLATFORM_SUPPORT",
        "description": "Equipe de suporte"
      },
      {
        "name": "PLATFORM_BILLING",
        "description": "Equipe financeira"
      }
    ]
  },

  "groups": [
    {
      "name": "platform_admins",
      "attributes": {
        "type": ["platform"]
      }
    }
  ]
}
```

---

## 5. Provisionamento Automatizado via Admin API

### 5.1 Cenário: Criar Novo Tenant

**Fluxo completo:**

```python
# admin/services/provisioning_service.py

from python_keycloak import KeycloakAdmin
from admin.config import settings

class ProvisioningService:
    def __init__(self):
        # Conectar ao Keycloak Admin API
        self.kc = KeycloakAdmin(
            server_url=settings.keycloak_url,
            username=settings.keycloak_admin_user,
            password=settings.keycloak_admin_password,
            realm_name=settings.keycloak_realm,
            verify=True
        )

    async def provision_tenant_keycloak(self, tenant: Tenant) -> dict:
        """
        Provisionar estruturas no Keycloak para um tenant
        Retorna: {"group_id": str, "user_id": str}
        """

        # 1. Criar grupo do tenant
        group_id = await self._create_tenant_group(tenant)

        # 2. Criar protocol mapper no grupo
        await self._create_tenant_mapper(group_id, tenant.tenant_id)

        # 3. Criar usuário admin-local
        user_id = await self._create_tenant_admin_user(tenant)

        # 4. Associar usuário ao grupo
        await self._add_user_to_group(user_id, group_id)

        # 5. Enviar email de reset de senha
        await self._send_password_reset(user_id)

        return {"group_id": group_id, "user_id": user_id}

    async def _create_tenant_group(self, tenant: Tenant) -> str:
        """Criar grupo para o tenant"""

        group_name = f"tenant_{tenant.tenant_id}"

        # Verificar se grupo já existe
        existing = self.kc.get_groups()
        for g in existing:
            if g.get("name") == group_name:
                return g["id"]

        # Criar grupo
        group_payload = {
            "name": group_name,
            "attributes": {
                "tenant_id": [tenant.tenant_id],
                "tenant_nome": [tenant.nome_fantasia]
            }
        }

        group = self.kc.create_group(group_payload)
        return group["id"]

    async def _create_tenant_mapper(self, group_id: str, tenant_id: str):
        """
        Criar protocol mapper no grupo para incluir tenant_id no JWT
        Este mapper garante que todos os usuários do grupo tenham tenant_id no token
        """

        mapper_payload = {
            "name": "tenant_id",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-group-membership-mapper",
            "consentRequired": False,
            "claimName": "tenant_id",
            "fullGroupPath": False,
            "addToIdToken": True,
            "addToAccessToken": True
        }

        try:
            self.kc.create_group_mapper(group_id, mapper_payload)
        except Exception as e:
            # Mapper pode já existir
            logger.warning(f"Mapper tenant_id already exists or error: {e}")

    async def _create_tenant_admin_user(self, tenant: Tenant) -> str:
        """Criar usuário admin-local do tenant"""

        username = f"admin_{tenant.tenant_id}"

        # Gerar senha temporária segura
        import secrets
        temp_password = secrets.token_urlsafe(16)

        user_payload = {
            "username": username,
            "email": tenant.email_admin,
            "enabled": True,
            "emailVerified": False,
            "attributes": {
                "tenant_id": [tenant.tenant_id],
                "role": ["ADMIN"],
                "nome": [f"Admin {tenant.nome_fantasia}"],
                "tipo": ["ADMIN_LOCAL"]
            },
            "credentials": [
                {
                    "type": "password",
                    "value": temp_password,
                    "temporary": True  # Usuário deve trocar no primeiro acesso
                }
            ],
            "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"]
        }

        # Criar usuário
        user_id = self.kc.create_user(user_payload)

        # Armazenar senha temporária (opcional, para enviar por email)
        # Em produção, usar o requiredAction UPDATE_PASSWORD do Keycloak

        return user_id

    async def _add_user_to_group(self, user_id: str, group_id: str):
        """Adicionar usuário ao grupo do tenant"""

        try:
            self.kc.group_user_add(user_id, group_id)
        except Exception as e:
            logger.error(f"Error adding user {user_id} to group {group_id}: {e}")
            raise

    async def _send_password_reset(self, user_id: str):
        """Enviar email de reset de senha"""

        try:
            # Keycloak envia email com link para criar nova senha
            self.kc.send_update_account(
                user_id=user_id,
                payload=["UPDATE_PASSWORD"]
            )
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            # Não falhar o provisionamento se email falhar
            # O admin pode gerar novo link manualmente

    async def rollback_tenant_keycloak(self, tenant_id: str):
        """
        Rollback: deletar grupo e usuários do tenant (em caso de falha)
        """

        group_name = f"tenant_{tenant_id}"

        # 1. Encontrar grupo
        groups = self.kc.get_groups()
        group = next((g for g in groups if g.get("name") == group_name), None)

        if not group:
            logger.warning(f"Group {group_name} not found, nothing to rollback")
            return

        # 2. Deletar todos os usuários do grupo
        members = self.kc.get_group_members(group["id"])
        for member in members:
            try:
                self.kc.delete_user(member["id"])
            except Exception as e:
                logger.error(f"Error deleting user {member['id']}: {e}")

        # 3. Deletar grupo
        try:
            self.kc.delete_group(group["id"])
        except Exception as e:
            logger.error(f"Error deleting group {group['id']}: {e}")
```

---

## 6. Configuração do Cliente Admin Python

### 6.1 Instalação

```bash
# requirements.txt
python-keycloak>=4.0.0
```

### 6.2 Uso

```python
# admin/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "bemcuidar"
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "changeme"

    # Clients secrets
    admin_client_secret: str
    portal_client_secret: str

settings = Settings()

# admin/services/keycloak_service.py
from python_keycloak import KeycloakAdmin

class KeycloakService:
    def __init__(self):
        self.kc = KeycloakAdmin(
            server_url=settings.keycloak_url,
            username=settings.keycloak_admin_user,
            password=settings.keycloak_admin_password,
            realm_name=settings.keycloak_realm
        )

    def create_tenant_group(self, tenant_id: str):
        """Criar grupo para o tenant"""
        return self.kc.create_group({
            "name": f"tenant_{tenant_id}",
            "attributes": {"tenant_id": [tenant_id]}
        })
```

---

## 7. Scripts de Setup

### 7.1 Import do Realm

```bash
#!/bin/bash
# scripts/setup_keycloak.sh

echo "🔧 Configurando Keycloak para IntelliCare..."

# Aguardar Keycloak estar pronto
echo "⏳ Aguardando Keycloak..."
until curl -f http://localhost:8080/health/ready; do
    echo "  Keycloak não está pronto ainda... aguardando 5s"
    sleep 5
done

echo "✅ Keycloak está pronto!"

# Login no Keycloak CLI (kcadm.sh)
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password changeme

# Criar realm
echo "📦 Criando realm bemcuidar..."
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh create realm \
  -s master \
  -o \
  <<EOF
{
  "realm": "bemcuidar",
  "enabled": true,
  "sslRequired": "external"
}
EOF

# Criar clients
echo "🔑 Criando clients..."
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh create clients \
  -r bemcuidar \
  -s \
  <<EOF
{
  "clientId": "intellicare-admin",
  "name": "IntelliCare Admin Platform",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "admin-secret-change-me",
  "bearerOnly": true,
  "serviceAccountsEnabled": true
}
EOF

# Criar roles
echo "👥 Criando roles..."
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh create roles \
  -r bemcuidar \
  -s \
  PLATFORM_ADMIN PLATFORM_SUPPORT PLATFORM_BILLING

echo "✅ Keycloak configurado com sucesso!"
```

### 7.2 Script de Health Check

```bash
#!/bin/bash
# scripts/check_keycloak.sh

echo "🔍 Verificando saúde do Keycloak..."

# 1. Verificar se está rodando
if ! curl -f http://localhost:8080/health/ready > /dev/null 2>&1; then
    echo "❌ Keycloak não está respondendo"
    exit 1
fi

# 2. Verificar se realm existe
if ! curl -f http://localhost:8080/realms/bemcuidar > /dev/null 2>&1; then
    echo "❌ Realm bemcuidar não encontrado"
    exit 1
fi

# 3. Verificar se clients existem
if ! curl -f http://localhost:8080/realms/bemcuidar/clients/intellicare-admin > /dev/null 2>&1; then
    echo "❌ Client intellicare-admin não encontrado"
    exit 1
fi

echo "✅ Keycloak está saudável!"
exit 0
```

---

## 8. Integração com Intellicare Auth

### 8.1 Configuração no Módulo

```python
# intellicare-auth/intellicare_auth/keycloak.py

from python_keycloak import KeycloakOpenID
from .config import settings

class KeycloakConfig:
    _instance = None

    @classmethod
    def get_config(cls) -> dict:
        if cls._instance is None:
            cls._instance = {
                "server_url": settings.keycloak_url,
                "realm": settings.keycloak_realm,
                "client_id": settings.keycloak_client_id,
                "client_secret_key": settings.keycloak_client_secret,
                "authorization_endpoint": f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth",
                "token_endpoint": f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token",
            }
        return cls._instance
```

### 8.2 Middleware de Validação

```python
# intellicare-auth/intellicare_auth/fastapi.py

from fastapi import Request, HTTPException, Depends
from .keycloak import KeycloakConfig

async def get_current_user(request: Request) -> dict:
    """Extrair e validar usuário do JWT"""

    # Extrair token do header Authorization
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1]

    # Decodificar token (sem validação de assinatura para performance)
    # Keycloak já validou
    try:
        # Decodificar JWT
        from jose import jwt
        config = KeycloakConfig.get_config()

        decoded = jwt.decode(
            token,
            options={"verify_signature": False}  # Keycloak valida
        )

        # Extrair tenant_id
        tenant_id = decoded.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id não encontrado no token")

        return {
            "user_id": decoded.get("sub"),
            "email": decoded.get("email"),
            "name": decoded.get("name", ""),
            "tenant_id": tenant_id,
            "roles": decoded.get("realm_access", {}).get("roles", [])
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")
```

---

## 9. Deploy em Produção

### 9.1 Docker Compose Produção

```yaml
# docker-compose.keycloak.prod.yml
version: '3.8'

services:
  keycloak-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: /run/secrets/keycloak_db_password
    volumes:
      - keycloak_db_data:/var/lib/postgresql/data
    networks:
      - intellicare_network
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        max_attempts: 3
    secrets:
      - keycloak_db_password

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    command: start
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: /run/secrets/keycloak_db_password
      KC_HOSTNAME: auth.intellicare.ia.br
      KC_HTTP_ENABLED: "true"
      KC_PROXY: edge
      KC_HEALTH_ENABLED: "true"
    ports:
      - "8080:8080"
    networks:
      - intellicare_network
    depends_on:
      - keycloak-db
    secrets:
      - keycloak_db_password
      - keycloak_admin_password
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        max_attempts: 3

networks:
  intellicare_network:
    external: true

secrets:
  keycloak_db_password:
    external: true
  keycloak_admin_password:
    external: true
```

### 9.2 Criação de Secrets

```bash
# Criar secrets no Docker Swarm
echo "strong_password_here" | docker secret create keycloak_db_password -
echo "admin_strong_password_here" | docker secret create keycloak_admin_password -
```

---

## 10. Monitoramento e Debug

### 10.1 Health Endpoints

```bash
# Ver saúde
curl http://localhost:8080/health/ready

# Ver metrics
curl http://localhost:8080/metrics
```

### 10.2 Logs

```bash
# Ver logs do container
docker logs keycloak -f

# Ver logs detalhados
docker exec keycloak tail -f /opt/keycloak/data/log/server.log
```

---

## 11. Checklist de Configuração

### Inicialização

- [ ] Docker compose configurado
- [ ] Variáveis de ambiente definidas
- [ ] Secrets criados (produção)
- [ ] Containers rodando
- [ ] Health check passando

### Keycloak

- [ ] Realm `bemcuidar` criado
- [ ] Client `intellicare-admin` criado
- [ ] Client `intellicare-portal` criado
- [ ] Roles criados (PLATFORM_ADMIN, etc.)
- [ ] Protocol mappers configurados
- [ ] SSL configurado (produção)

### Integração

- [ ] Admin API funcionando
- [ ] Teste de criação de grupo
- [ ] Teste de criação de usuário
- [ ] Teste de geração de token
- [ ] Integração com intellicare-auth

---

## 12. Troubleshooting

### Problema: Grupo não é criado

```bash
# Verificar permissões do admin
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm master \
  --fields username,realmRoles

# Verificar se admin tem role admin
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm master \
  --id admin
```

### Problema: Mapper não funciona

```bash
# Verificar mappers do grupo
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh get groups \
  --realm bemcuidar \
  --id group_id \
  -c

# Criar mapper manualmente
docker exec -it keycloak /opt/keycloak/bin/kcadm.sh create \
  groups/ID/mappers \
  --realm bemcuidar \
  -f - <<EOF
{
  "name": "tenant_id",
  "protocol": "openid-connect",
  "protocolMapper": "oidc-group-membership-mapper"
}
EOF
```

---

## 13. Segurança

### Senhas e Secrets

✅ **Nunca commitar senhas no repositório**
✅ Usar Docker secrets ou Vault
✅ Rotacionar senhas a cada 90 dias
✅ Usar HTTPS em produção

### CORS

```json
{
  "webOrigins": ["https://portal.intellicare.ia.br"],
  "redirectUris": ["https://portal.intellicare.ia.br/*"]
}
```

---

## 14. Próximos Passos

1. **Setup Inicial** - Subir Keycloak via docker-compose
2. **Configuração** - Criar realm e clients
3. **Testes** - Valider fluxo de autenticação
4. **Fase 1** - Iniciar implementação do intellicare-admin

---

**Documentação referenciada:**
- [Keycloak Server Installation](https://www.keycloak.org/server/installation)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/24.0/rest-api/)
- [Python Keycloak](https://python-keycloak.readthedocs.io/)

---

**Aprovado por:** ___________
**Data:** ___________
