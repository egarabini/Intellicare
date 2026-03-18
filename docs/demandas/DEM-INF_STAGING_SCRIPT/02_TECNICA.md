---
tipo: especificacao-tecnica
demanda: DEM-INF
titulo: Staging Update Script
---

# DEM-INF Staging — Especificação Técnica

## Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `deploy/staging_update.sh` | Script principal de deploy |
| `infra/.env.staging.example` | Template completo de segredos |
| `deploy/README.md` | Instruções de deploy passo a passo |

---

## Bloco 1 — `deploy/staging_update.sh` (completo)

```bash
#!/bin/bash
# deploy/staging_update.sh
# Atualiza o staging IntelliCare com as DEMs mais recentes.
# Uso: STAGING_ENV_FILE=infra/.env.staging bash deploy/staging_update.sh
set -euo pipefail

ENV_FILE="${STAGING_ENV_FILE:-infra/.env.staging}"
COMPOSE="docker compose --env-file $ENV_FILE -f infra/docker-compose.yml"

echo "======================================"
echo " IntelliCare Staging Update"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

# Pré-requisitos
echo ""
echo "==> [1/6] Validando pré-requisitos..."
[ -f "$ENV_FILE" ] || { echo "ERRO: $ENV_FILE nao encontrado. Copiar de infra/.env.staging.example"; exit 1; }
command -v docker >/dev/null || { echo "ERRO: docker nao instalado"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERRO: docker compose plugin nao instalado"; exit 1; }
echo "     OK"

# Atualizar código
echo ""
echo "==> [2/6] Atualizando codigo (git pull)..."
git pull origin main
echo "     Commit atual: $(git rev-parse --short HEAD)"

# Rebuild serviço principal
echo ""
echo "==> [3/6] Rebuild intellicare-service..."
$COMPOSE build --no-cache intellicare-service
echo "     Build concluido"

# Subir serviço (aplica migrations no startup)
echo ""
echo "==> [4/6] Subindo intellicare-service (migrations + seed automaticos)..."
$COMPOSE up -d --no-deps intellicare-service
echo "     Aguardando inicializacao (20s)..."
sleep 20

# Seed dos flows Kestra
echo ""
echo "==> [5/6] Seeding Kestra flows CarePlanner..."
$COMPOSE exec intellicare-service python infra/kestra/seed_flows.py \
  || echo "AVISO: seed_flows falhou (Kestra pode estar inicializando — repetir manualmente se necessario)"

# Verificação final
echo ""
echo "==> [6/6] Verificando saude dos servicos..."
$COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "======================================"
echo " Deploy concluido!"
echo " Verificar:"
echo "   https://api.intellicare.ia.br/health"
echo "   https://gestor.intellicare.ia.br/gestor-ui/"
echo "   https://kestra.intellicare.ia.br"
echo "======================================"
```

---

## Bloco 2 — `infra/.env.staging.example`

```bash
# =====================================================
# IntelliCare V3 — Staging Environment Template
# =====================================================
# Copiar para infra/.env.staging e preencher os valores.
# NUNCA commitar o .env.staging com valores reais.
# =====================================================

# --- PostgreSQL ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<gerar: openssl rand -base64 32>
POSTGRES_DB=intellicare

# --- Aplicação ---
SECRET_KEY=<gerar: openssl rand -hex 32>
ENVIRONMENT=staging
DEBUG=false

# --- Keycloak ---
KEYCLOAK_URL=https://auth.intellicare.ia.br
KEYCLOAK_REALM=intellicare
KEYCLOAK_CLIENT_ID=intellicare-api
KEYCLOAK_CLIENT_SECRET=<copiar do Keycloak Admin Console > Clients > intellicare-api > Credentials>
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<senha forte, min 16 chars>

# --- Rocket.Chat ---
ROCKETCHAT_URL=https://chat.intellicare.ia.br
ROCKETCHAT_ADMIN_USER=rc-admin
ROCKETCHAT_ADMIN_PASSWORD=<senha forte>
ROCKETCHAT_WEBHOOK_TOKEN=<gerar no RC: Admin > Integrations > Incoming > Token>
ROCKETCHAT_BOT_USER=intellicare-bot
ROCKETCHAT_BOT_PASSWORD=<senha do bot RC>

# --- Jitsi ---
JITSI_PUBLIC_URL=https://meet.intellicare.ia.br
JITSI_APP_ID=intellicare
JITSI_APP_SECRET=<gerar: openssl rand -hex 32>
JICOFO_AUTH_USER=focus
JICOFO_AUTH_PASSWORD=<gerar: openssl rand -hex 16>
JVB_AUTH_USER=jvb
JVB_AUTH_PASSWORD=<gerar: openssl rand -hex 16>
JITSI_INTERNAL_MUC_MODULE_ADMINS=focus

# --- Kestra ---
KESTRA_URL=http://kestra:8080
KESTRA_API_KEY=<gerar no Kestra UI: Settings > API Keys > Create>
KESTRA_NAMESPACE=intellicare.careplanner

# --- Redis ---
REDIS_URL=redis://redis:6379/0

# --- Grafana ---
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<senha forte>

# --- SMTP (Grafana Alertas) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email do sistema>
SMTP_PASSWORD=<app password do Gmail>
SMTP_FROM=noreply@intellicare.ia.br

# --- Domínios ---
DOMAIN=intellicare.ia.br
API_URL=https://api.intellicare.ia.br
```

---

## Bloco 3 — `deploy/README.md`

```markdown
# IntelliCare V3 — Deploy Staging

## Pré-requisitos no VPS

- Docker >= 24 com plugin Compose
- Git configurado com acesso ao repositório
- Domínios DNS apontados para o VPS:
  - api.intellicare.ia.br
  - admin.intellicare.ia.br
  - gestor.intellicare.ia.br
  - chat.intellicare.ia.br
  - meet.intellicare.ia.br
  - kestra.intellicare.ia.br
  - auth.intellicare.ia.br
  - grafana.intellicare.ia.br

## Primeira vez (setup inicial)

1. Copiar template de segredos:
   ```bash
   cp infra/.env.staging.example infra/.env.staging
   # Preencher todos os valores com <...>
   ```

2. Subir todos os serviços:
   ```bash
   docker compose --env-file infra/.env.staging -f infra/docker-compose.yml up -d
   ```

3. Criar banco Kestra:
   ```bash
   docker compose --env-file infra/.env.staging exec postgres \
     psql -U postgres -c "CREATE DATABASE kestra;"
   ```

4. Aguardar Kestra inicializar (~60s) e fazer seed dos flows:
   ```bash
   docker compose --env-file infra/.env.staging exec intellicare-service \
     python infra/kestra/seed_flows.py
   ```

## Atualização (DEMs novas)

```bash
STAGING_ENV_FILE=infra/.env.staging bash deploy/staging_update.sh
```

## Pendências de infraestrutura

- [ ] Firewall VPS: abrir porta UDP 10000 para Jitsi JVB
- [ ] Configurar KV Store do Kestra com JWT por tenant:
      `kestra KV set intellicare_jwt_<tenant_slug> <jwt_token>`
```
