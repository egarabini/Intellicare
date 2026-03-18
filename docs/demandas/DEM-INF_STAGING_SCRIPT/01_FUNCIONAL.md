---
tipo: especificacao-funcional
demanda: DEM-INF
titulo: Staging Update Script — deploy automatizado das DEMs 038-043
sprint: "4.4"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: []
habilita: []
tags: [infra, staging, deploy, script, p2]
---

# DEM-INF — Staging Update Script

## Objetivo

O staging está de pé mas desatualizado — não tem as DEMs 038–043 (CarePlanner
completo). Eduardo precisa rodar um conjunto de comandos na sequência correta
para atualizar. Esta DEM cria um script reproduzível e documenta os segredos
necessários para que qualquer membro do time possa fazer o deploy.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-INF |
|------|------|---------|
| Staging tem DEMs 038-043 | ❌ | ✅ após execução do script |
| Script de deploy documentado | ❌ | ✅ `deploy/staging_update.sh` |
| Segredos do staging documentados | Parcial (`.env.staging` sem valores reais) | ✅ `.env.staging.example` completo |
| Checklist de pré-requisitos | No dashboard (desatualizado) | ✅ no script + README |

---

## Critérios de Aceite

1. Arquivo `deploy/staging_update.sh` criado e executável (`chmod +x`).
   Ao rodar no VPS de staging, atualiza o código e reinicia os serviços
   afetados sem downtime dos demais serviços.

2. Arquivo `infra/.env.staging.example` criado com **todos** os segredos
   necessários documentados (valor de exemplo ou descrição do que preencher),
   incluindo os novos do CarePlanner.

3. O script valida pré-requisitos antes de executar:
   - Git limpo (sem uncommited changes)
   - Docker e docker compose disponíveis
   - Variável `STAGING_ENV_FILE` apontando para `.env.staging` real

4. Script faz apenas restart dos serviços que mudaram (não full down/up).

5. `README.md` de deploy atualizado (ou criado em `deploy/README.md`) com
   instruções passo a passo incluindo como gerar os segredos reais.

---

## O que NÃO está incluído

- Deploy automático (CD pipeline — ver DEM-046)
- Rollback automático em caso de falha
- Deploy em produção
- Configuração do Jitsi JVB (UDP 10000) — requer acesso ao painel do VPS

---

## Notas para o Agente Desenvolvedor

**Conteúdo do `deploy/staging_update.sh`:**

```bash
#!/bin/bash
set -euo pipefail

ENV_FILE="${STAGING_ENV_FILE:-infra/.env.staging}"

echo "==> Validando pré-requisitos..."
[ -f "$ENV_FILE" ] || { echo "ERRO: $ENV_FILE não encontrado"; exit 1; }
command -v docker >/dev/null || { echo "ERRO: docker não encontrado"; exit 1; }

echo "==> Atualizando código..."
git pull origin main

echo "==> Rebuild dos serviços afetados (intellicare-service + kestra)..."
docker compose --env-file "$ENV_FILE" -f infra/docker-compose.yml \
  build --no-cache intellicare-service

echo "==> Aplicando migrações de banco (via startup do serviço)..."
docker compose --env-file "$ENV_FILE" -f infra/docker-compose.yml \
  up -d --no-deps intellicare-service

echo "==> Aguardando healthcheck (30s)..."
sleep 30
docker compose --env-file "$ENV_FILE" -f infra/docker-compose.yml ps

echo "==> Seeding Kestra flows CarePlanner..."
docker compose --env-file "$ENV_FILE" -f infra/docker-compose.yml \
  run --rm intellicare-service python infra/kestra/seed_flows.py

echo "==> Deploy concluido! Verificar:"
echo "    https://api.intellicare.ia.br/health"
echo "    https://gestor.intellicare.ia.br/gestor-ui/"
```

**Conteúdo do `.env.staging.example`** — incluir todos os segredos:
```
# === IntelliCare Staging .env ===
# Copiar para .env.staging e preencher os valores

POSTGRES_PASSWORD=<gerar com: openssl rand -base64 32>
SECRET_KEY=<gerar com: openssl rand -hex 32>

# Keycloak
KEYCLOAK_ADMIN_PASSWORD=<senha forte>
KEYCLOAK_REALM=intellicare
KEYCLOAK_CLIENT_SECRET=<gerar no Keycloak Admin Console>

# Rocket.Chat
ROCKETCHAT_ADMIN_PASSWORD=<senha forte>
ROCKETCHAT_WEBHOOK_TOKEN=<gerar no RC Admin > Integrações>
ROCKETCHAT_URL=https://chat.intellicare.ia.br

# Jitsi
JITSI_APP_SECRET=<gerar com: openssl rand -hex 32>
JICOFO_AUTH_PASSWORD=<gerar com: openssl rand -hex 16>
JVB_AUTH_PASSWORD=<gerar com: openssl rand -hex 16>
JITSI_PUBLIC_URL=https://meet.intellicare.ia.br

# Kestra
KESTRA_URL=http://kestra:8080
KESTRA_API_KEY=<gerar no Kestra UI > Settings > API Keys>

# Redis
REDIS_URL=redis://redis:6379/0

# Grafana
GRAFANA_ADMIN_PASSWORD=<senha forte>
```

**Atenção**: os `care_templates` são seedados automaticamente no startup do
`intellicare-service` (DEM-041). Não é necessário script separado.
