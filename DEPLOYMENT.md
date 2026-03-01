# IntelliCare Deployment Guide

This guide explains how to deploy IntelliCare to a server.

## Quick Start (Server Setup)

### 1. Clone from Git

```bash
cd /opt
git clone --branch staging --single-branch https://github.com/egarabini/intellicare.git intellicare
cd intellicare
```

Or use the automated script:
```bash
bash scripts/server/clone_clean_from_git.sh
```

### 2. Setup Environment Variables

The `.env` file is NOT in Git (security). Use the provided template:

```bash
bash scripts/server/setup_env.sh
```

This creates:
- `.env` - Environment file for Docker Compose
- `.env.full` - Full environment configuration

**For production**: Edit these files and replace placeholder values with real credentials.

### 3. Start Services

```bash
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d
```

Or use the clean rebuild script:
```bash
bash scripts/server/clean_and_rebuild.sh
```

### 4. Verify Deployment

```bash
# Check all containers are running
docker ps

# Run smoke tests
bash scripts/smoke_test.sh
```

## Environment Files

### `.env.example`

Template file with all configuration options and PLACEHOLDER values for sensitive data. This file IS in Git.

### `.env` and `.env.full`

Actual environment files with real credentials. These are NOT in Git (see `.gitignore`).

### Key Configuration Sections

1. **Infrastructure**: PostgreSQL, Redis, Prometheus, Grafana
2. **Module Ports**: All 13+ backend modules
3. **Database URLs**: Connection strings for each module
4. **Service URLs**: Inter-module communication
5. **Keycloak**: Authentication configuration
6. **Traefik**: Reverse proxy settings
7. **External Services**: Rocket.Chat, Jitsi, Twilio, etc.

## Updating from Git

When changes are pushed to the `staging` branch:

```bash
cd /opt/intellicare
git fetch origin
git reset --hard origin/staging
bash scripts/server/setup_env.sh  # Regenerate .env if needed
docker-compose -f docker-compose.full.yml up -d --build
```

## Troubleshooting

### Missing .env file

If you get `.env.full not found`:

```bash
bash scripts/server/setup_env.sh
```

### Docker API version too old

```bash
bash scripts/server/UPDATE_DOCKER_SERVER.sh
```

### Network conflicts

Remove old network:
```bash
docker network rm intellicare_intellicare-network
```

### Containers restarting

Check logs:
```bash
docker logs <container-name>
```

## Security Notes

- **NEVER** commit `.env` or `.env.full` with real production credentials
- `.env.example` contains only placeholder values
- Update all `CHANGE_ME_*` values before production deployment
- Use strong passwords for production
- Rotate credentials regularly

## Module Reference

| Port | Module | Role |
|------|--------|------|
| 8001 | florence | RAG + Protocolos Clínicos |
| 8002 | oswaldo | Análise Clínica + FHIR |
| 8003 | donabedian | Qualidade + Indicadores |
| 8004 | wanda | Orquestrador IA |
| 8005 | comunicacao | WhatsApp + Email + SMS |
| 8006 | geralda | Gestão + Administrativo |
| 8007 | zilda | CNES + DATASUS |
| 8008 | minerva | Extração Documentos (MCP) |
| 8009 | pierre | Scientific Search (MCP) |
| 8010 | admin | Administração do Sistema |
| 8011 | gestor | Gestão de Módulos Clínicos |
| 8012 | grahame | FHIR R4 + CDS Hooks |
| 8013 | nise | Chatbot + Treinamento |
| 8080 | keycloak | Autenticação |
| 3001 | portal | React Portal |

## Documentation

- `CLAUDE.md` - Project overview and commands
- `docs/INFRAESTRUTURA/` - Infrastructure documentation
- `scripts/dns/DNS_SETUP_GUIDE.sh` - DNS configuration
