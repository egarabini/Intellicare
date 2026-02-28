# ============================================================================
# IntelliCare — DNS + Certificados SSL Setup Guide
# ============================================================================
# Prerequisito: T1-F3 (Traefik) ✅ implementado
# ============================================================================

# ── PASSO 1: Registrar DNS Records ─────────────────────────
#
# Painel: Cloudflare (ou registrador do domínio)
# IP do servidor: substitua 203.0.113.10 pelo IP real
#
# ┌──────────────────────────────────────────────────────────┐
# │ intellicare.ia.br                                        │
# ├──────┬──────────────┬───────────────┬─────┬──────────────┤
# │ Tipo │ Nome         │ Conteúdo      │ TTL │ Proxy        │
# ├──────┼──────────────┼───────────────┼─────┼──────────────┤
# │ A    │ @            │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ admin        │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ portal       │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ api          │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ keycloak     │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ traefik      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ grafana      │ 203.0.113.10  │ 300 │ DNS only     │
# │ CNAME│ *            │ intellicare…  │ 300 │ DNS only     │
# └──────┴──────────────┴───────────────┴─────┴──────────────┘
#
# ┌──────────────────────────────────────────────────────────┐
# │ saudeplanner.com.br                                    │
# ├──────┬──────────────┬───────────────┬─────┬──────────────┤
# │ Tipo │ Nome         │ Conteúdo      │ TTL │ Proxy        │
# ├──────┼──────────────┼───────────────┼─────┼──────────────┤
# │ A    │ @            │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ oswaldo      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ florence     │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ zilda        │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ donabedian   │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ comunicacao  │ 203.0.113.10  │ 300 │ DNS only     │
# │ CNAME│ *            │ saudeconect…  │ 300 │ DNS only     │
# └──────┴──────────────┴───────────────┴─────┴──────────────┘
#
# ⚠️  IMPORTANTE:
#   - Usar "DNS only" (sem Proxy da Cloudflare) quando Traefik gerencia TLS
#   - Se usar Cloudflare Proxy, desabilitar TLS no Traefik (Cloudflare faz)
#   - Wildcard (*.dominio) NÃO funciona com proxy Cloudflare no plano free

# ── PASSO 2: Criar API Token no Cloudflare ─────────────────
#
# Para wildcard certs, Traefik precisa do DNS Challenge.
# O DNS Challenge requer um API Token da Cloudflare.
#
# 1. Acesse: https://dash.cloudflare.com/profile/api-tokens
# 2. Crie um token com estas permissões:
#    - Zone → DNS → Edit
#    - Zone → Zone → Read
# 3. Limitar a:
#    - Zone: intellicare.ia.br
#    - Zone: saudeplanner.com.br
# 4. Copie o token e coloque no .env:
#    CF_DNS_API_TOKEN=<seu-token-aqui>

# ── PASSO 3: Configurar .env ───────────────────────────────
#
# Copie o template:
#   cp .env.traefik.template .env.traefik
# Edite com seus valores:
#   nano .env.traefik
# E depois:
#   set -a && source .env.traefik && set +a

# ── PASSO 4: Subir o Traefik ───────────────────────────────
#
# Produção:
#   docker-compose -f docker-compose.full.yml -f docker-compose.traefik.yml up -d
#
# Dev local:
#   docker-compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml up -d

# ── PASSO 5: Verificar Certificados ────────────────────────
#
# Execute o script de verificação:
#   bash scripts/dns/verify_certs.sh
#
# Ou manualmente:
#   curl -I https://admin.intellicare.ia.br
#   curl -I https://portal.intellicare.ia.br
#   curl -I https://api.intellicare.ia.br/v1/oswaldo/api/v1/health
