# FASE0_KEYCLOAK - Implementação de Autenticação SSO

## 📋 Visão Geral

Esta fase implementa o servidor de autenticação **Keycloak** para o IntelliCare Multi-Tenant, provendo:

- ✅ SSO (Single Sign-On) centralizado
- ✅ Gerenciamento de identidades e acessos
- ✅ Multi-tenancy com realms por tenant
- ✅ OAuth 2.0 / OpenID Connect
- ✅ SMART on FHIR para integração clínica

## 🎯 Objetivos

1. **Ambientes**: Desenvolvimento, Staging e Produção
2. **Realm Principal**: `bemcuidar`
3. **Autenticação**: Todos os módulos backend e frontend
4. **Autorização**: Roles baseadas em tenant (PLATFORM_ADMIN, TENANT_ADMIN, etc)

## 📁 Estrutura de Arquivos

```
intellicare-auth/
├── keycloak/
│   ├── import/
│   │   └── bemcuidar-realm.json    # Configuração do realm (roles, clients, users)
│   ├── certs/                      # Certificados SSL (HTTPS)
│   │   ├── server.keystore         # Keystore para HTTPS
│   │   └── cert-creation-script.sh # Script para gerar certificados
│   └── themes/                     # Temas customizados (opcional)
│       └── intellicare/
├── intellicare_auth/              # Biblioteca Python de integração Keycloak
│   ├── client.py                  # KeycloakClient para integração
│   ├── middleware.py              # FastAPI middleware
│   └── ...
└── keycloak_client_secrets.json   # Client secrets para desenvolvimento
```

## 🔐 Credenciais Padrão

| Ambiente | Admin User | Admin Password | Database Password |
|----------|------------|----------------|-------------------|
| Desenvolvimento | `admin` | `.env.keycloak` | `.env.keycloak` |
| Staging | `admin` | `.env.keycloak` | `.env.keycloak` |
| Produção | `<SEGURANÇA>` | `<VAULT>` | `<VAULT>` |

## 🌐 URLs de Acesso

| Ambiente | Keycloak URL | Admin Console |
|----------|--------------|---------------|
| Local | `http://localhost:8080` | `http://localhost:8080/admin` |
| Staging | `https://auth.intellicare.ia.br` | `https://auth.intellicare.ia.br/admin` |
| Produção | `https://auth.saudeconectada.com.br` | `https://auth.saudeconectada.com.br/admin` |

## 📖 Guias de Implementação

1. **[01_SETUP_CERTIFICADOS.md](./01_SETUP_CERTIFICADOS.md)** - Criar certificados SSL
2. **[02_START_KEYCLOAK.md](./02_START_KEYCLOAK.md)** - Iniciar servidor Keycloak
3. **[03_CONFIGURE_REALM.md](./03_CONFIGURE_REALM.md)** - Configurar realm e clients
4. **[04_INTEGRATE_MODULES.md](./04_INTEGRATE_MODULES.md)** - Integrar módulos com Keycloak
5. **[05_TEST_AUTH.md](./05_TEST_AUTH.md)** - Testar autenticação
6. **[06_DEPLOY_STAGING.md](./06_DEPLOY_STAGING.md)** - Deploy em staging
7. **[07_DEPLOY_PRODUCTION.md](./07_DEPLOY_PRODUCTION.md)** - Deploy em produção

## 🚀 Quick Start (Desenvolvimento)

```bash
# 1. Criar diretório de certificados
mkdir -p keycloak/certs

# 2. Iniciar Keycloak
docker-compose -f docker-compose.keycloak.yml up -d

# 3. Verificar saúde
curl http://localhost:8080/health/ready

# 4. Executar setup (opcional - realm já é importado automaticamente)
./scripts/setup_keycloak.sh
```

## 📊 Status de Implementação

| Item | Status | Observações |
|------|--------|-------------|
| Infraestrutura Docker | ✅ | docker-compose.keycloak.yml |
| Realm bemcuidar | ✅ | Arquivo de import pronto e deployado |
| Realm deployado | ✅ | Realm importado no servidor staging |
| Servidor Rodando | ✅ | Keycloak rodando em staging (167.86.97.142) |
| Health Check | ✅ | http://167.86.97.142:8080/health/ready |
| Certificados SSL | ⚠️ | HTTP em staging (HTTPS via Traefik pendente) |
| Clients Configurados | ⚠️ | Apenas admin e portal configurados |
| Integração Módulos | ❌ | Pendente |
| Testes E2E | ❌ | Pendente |

## 🚀 Servidor Atual

**Staging**: 167.86.97.142:8080

```bash
# Health check
curl http://167.86.97.142:8080/health/ready

# Realm
curl http://167.86.97.142:8080/realms/bemcuidar

# Admin Console
# URL: http://167.86.97.142:8080/admin
# User: admin
# Password: Soeuso410863 (ALTERAR EM PRODUÇÃO)
```

## 🔧 Manutenção

### Logs
```bash
# Ver logs em tempo real
docker logs -f keycloak-intellicare

# Ver últimos 100 logs
docker logs --tail 100 keycloak-intellicare
```

### Restart
```bash
# Restart graceful
docker-compose -f docker-compose.keycloak.yml restart keycloak

# Recreate (aplica novas configurações)
docker-compose -f docker-compose.keycloak.yml up -d --force-recreate keycloak
```

### Backup
```bash
# Export realm atual
docker exec keycloak-intellicare /opt/keycloak/bin/kcadm.sh get realms/bemcuidar -o /tmp/realm-backup.json
docker cp keycloak-intellicare:/tmp/realm-backup.json ./intellicare-auth/keycloak/backup/

# Backup database
docker exec keycloak-db pg_dump -U keycloak keycloak > intellicare-auth/keycloak/db-backup.sql
```

## 📞 Suporte

- **Documentação Keycloak**: https://www.keycloak.org/docs
- **Admin API**: https://www.keycloak.org/docs-api/24.0/rest-api/index.html
- **Issues**: Criar issue no repo IntelliCare

## ⚠️ Notas de Segurança

1. **SENHAS**: Nunca commitar senhas no Git
2. **HTTPS**: Obrigatório em staging e produção
3. **CORS**: Configurar corretamente para evitar ataques
4. **RATE LIMIT**: Implementar rate limiting na API
5. **AUDIT**: Habilitar audit log para conformidade

---

**Última Atualização**: 2026-03-01
**Versão**: 1.0.0
**Responsável**: IntelliCare Team
