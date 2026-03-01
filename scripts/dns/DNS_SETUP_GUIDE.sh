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
# │ A    │ apresentacao │ 203.0.113.10  │ 300 │ DNS only     │
# │ CNAME│ *            │ intellicare…  │ 300 │ DNS only     │
# └──────┴──────────────┴───────────────┴─────┴──────────────┘
#
# ┌──────────────────────────────────────────────────────────┐
# │ saudeplanner.com.br                                      │
# ├──────┬──────────────┬───────────────┬─────┬──────────────┤
# │ Tipo │ Nome         │ Conteúdo      │ TTL │ Proxy        │
# ├──────┼──────────────┼───────────────┼─────┼──────────────┤
# │ A    │ @            │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ oswaldo      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ florence     │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ zilda        │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ donabedian   │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ comunicacao  │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ geralda      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ wanda        │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ grahame      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ nise         │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ minerva      │ 203.0.113.10  │ 300 │ DNS only     │
# │ A    │ pierre       │ 203.0.113.10  │ 300 │ DNS only     │
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

# ============================================================================
# Módulos IntelliCare — Mapeamento Completo
# ============================================================================
#
# Porta | Módulo       | Agente        | Role                           | API Path
# ------|--------------|---------------|--------------------------------|------------------
# 8001  | florence     | FLORENCE      | RAG + Protocolos Clínicos      | /v1/florence
# 8002  | oswaldo      | OSWALDO       | Análise Clínica + FHIR         | /v1/oswaldo
# 8003  | donabedian   | DONABEDIAN    | Qualidade + Indicadores        | /v1/donabedian
# 8004  | wanda        | WANDA         | Orquestrador IA                | /v1/wanda
# 8005  | comunicacao  | —             | WhatsApp + Email + SMS         | /v1/comunicacao
# 8006  | geralda      | GERALDA       | Gestão + Administrativo        | /v1/geralda
# 8007  | zilda        | ZILDA         | CNES + DATASUS                  | /v1/zilda
# 8008  | minerva      | MINERVA       | Extração Documentos (MCP)      | /v1/minerva
# 8009  | pierre       | PIERRE        | Scientific Search (MCP)        | /v1/pierre
# 8010  | admin        | —             | Administração do Sistema       | admin.intellicare.ia.br
# 8011  | gestor       | —             | Gestão de Módulos Clínicos     | /v1/gestor
# 8012  | grahame      | GRAHAME       | FHIR R4 + CDS Hooks            | /v1/grahame
# 8013  | nise         | NISE          | Chatbot + Treinamento          | /v1/nise
# 8080  | keycloak     | —             | Autenticação (Keycloak)        | keycloak.intellicare.ia.br
# 3001  | portal       | —             | React 19 + Vite Portal          | portal.intellicare.ia.br
# 5432  | postgres     | —             | Database Principal             | (internal only)
# 6379  | redis        | —             | Cache + Pub/Sub                 | (internal only)
# 3000  | grafana      | —             | Dashboards de Monitoramento    | grafana.intellicare.ia.br
# 9090  | prometheus   | —             | Métricas do Sistema            | (internal only)
# 8080  | traefik      | —             | Reverse Proxy                   | traefik.intellicare.ia.br
#
# ============================================================================
# URLs de Acesso aos Módulos
# ============================================================================
#
# Portal Principal:
#   https://portal.intellicare.ia.br
#
# API Gateway (path-based):
#   https://api.intellicare.ia.br/v1/{modulo}/api/v1/...
#
# Subdomínios diretos (saudeplanner.com.br):
#   https://oswaldo.saudeplanner.com.br
#   https://florence.saudeplanner.com.br
#   https://donabedian.saudeplanner.com.br
#   https://comunicacao.saudeplanner.com.br
#   https://geralda.saudeplanner.com.br
#   https://wanda.saudeplanner.com.br
#   https://zilda.saudeplanner.com.br
#   https://grahame.saudeplanner.com.br
#   https://nise.saudeplanner.com.br
#   https://minerva.saudeplanner.com.br
#   https://pierre.saudeplanner.com.br
#
# Ferramentas Administrativas:
#   https://admin.intellicare.ia.br        (Admin Panel)
#   https://keycloak.intellicare.ia.br      (Authentication)
#   https://traefik.intellicare.ia.br       (Proxy Dashboard)
#   https://grafana.intellicare.ia.br       (Monitoring)
#   https://apresentacao.intellicare.ia.br  (Presentation Slides)
#
# ============================================================================
