# Starting Additional IntelliCare Modules

## Overview

The IntelliCare platform includes 13 backend modules. The base deployment includes 6 core modules:

**Core Modules (Already Running):**
- Florence (8001) - RAG + Protocolos Clínicos
- Oswaldo (8002) - Análise Clínica + FHIR
- Donabedian (8003) - Qualidade + Indicadores
- Wanda (8004) - Orquestrador IA
- Comunicacao (8005) - WhatsApp + Email + SMS
- Geralda (8006) - Gestão + Administrativo

**Additional Modules (Can be started):**
- Zilda (8007) - CNES + DATASUS Integration
- Minerva (8008) - OCR + Document Extraction (MCP Server)
- Pierre (8009) - Scientific Search PubMed+Tavily (MCP Server)
- Admin (8010) - System Administration
- Gestor (8011) - Clinical Module Management
- Grahame (8012) - FHIR R4 + CDS Hooks + Terminology
- Nise (8013) - Chatbot + Training (Flowise/Kestra)

## Prerequisites

Before starting additional modules, ensure:
1. Base services are running (postgres, redis, traefik)
2. Core modules are healthy (florence, oswaldo, donabedian, wanda, comunicacao, geralda)
3. Environment variables are configured in `.env`

## Quick Start

### Option 1: Using docker-compose (Recommended)

```bash
cd /opt/intellicare

# Start all additional modules at once
docker-compose -f docker-compose.full.yml up -d zilda minerva pierre admin gestor grahame nise

# Check status
docker-compose -f docker-compose.full.yml ps

# View logs
docker-compose -f docker-compose.full.yml logs -f [module_name]
```

### Option 2: Using the provided script

```bash
cd /opt/intellicare
bash scripts/server/start_additional_modules_simple.sh
```

### Option 3: Start modules individually

```bash
cd /opt/intellicare

# Start Zilda (CNES + DATASUS)
docker-compose -f docker-compose.full.yml up -d zilda

# Start Minerva (OCR)
docker-compose -f docker-compose.full.yml up -d minerva

# Start Pierre (Scientific Search)
docker-compose -f docker-compose.full.yml up -d pierre

# Start Admin
docker-compose -f docker-compose.full.yml up -d admin

# Start Gestor
docker-compose -f docker-compose.full.yml up -d gestor

# Start Grahame (FHIR)
docker-compose -f docker-compose.full.yml up -d grahame

# Start Nise (Chatbot)
docker-compose -f docker-compose.full.yml up -d nise
```

## Verifying Module Health

After starting, verify each module is healthy:

```bash
# Check all module health endpoints
for port in 8007 8008 8009 8010 8011 8012 8013; do
    echo "Checking port $port..."
    curl -f http://localhost:$port/api/v1/health || echo "Module on port $port is not healthy"
done
```

Or check individual modules:
```bash
curl http://localhost:8007/api/v1/health  # Zilda
curl http://localhost:8008/api/v1/health  # Minerva
curl http://localhost:8009/api/v1/health  # Pierre
curl http://localhost:8010/api/v1/health  # Admin
curl http://localhost:8011/api/v1/health  # Gestor
curl http://localhost:8012/api/v1/health  # Grahame
curl http://localhost:8013/api/v1/health  # Nise
```

## Module Details

### Zilda (8007) - CNES + DATASUS
**Purpose:** Integration with Brazilian health systems (CNES, DATASUS)

**Dependencies:**
- PostgreSQL
- Redis
- External APIs (CNES, DATASUS)

**Environment Variables:**
```bash
ZILDA_PORT=8007
INTELLICARE_ZILDA_DATABASE_URL=postgresql+psycopg://intellicare_admin:password@postgres:5432/intellicare_db
```

### Minerva (8008) - OCR + Document Extraction
**Purpose:** Extract text and data from documents (PDFs, images, etc.)

**Dependencies:**
- PostgreSQL
- Redis
- OLLAMA (for AI processing)

**Environment Variables:**
```bash
MINERVA_PORT=8008
INTELLICARE_MINERVA_DATABASE_URL=postgresql+psycopg://intellicare_admin:password@postgres:5432/intellicare_db
OLLAMA_URL=http://ollama:11434
```

### Pierre (8009) - Scientific Search
**Purpose:** Search PubMed and other scientific literature

**Dependencies:**
- PostgreSQL
- Redis
- Tavily API (for web search)

**Environment Variables:**
```bash
PIERRE_PORT=8009
INTELLICARE_PIERRE_DATABASE_URL=postgresql+psycopg://intellicare_admin:password@postgres:5432/intellicare_db
TAVILY_API_KEY=your_tavily_api_key
```

### Admin (8010) - System Administration
**Purpose:** Admin panel for system configuration and management

**Dependencies:**
- PostgreSQL
- Redis

**Environment Variables:**
```bash
ADMIN_PORT=8010
INTELLICARE_ADMIN_DATABASE_URL=postgresql+asyncpg://intellicare_admin:password@postgres:5432/intellicare_db
```

### Gestor (8011) - Clinical Module Management
**Purpose:** Manage and configure clinical modules

**Dependencies:**
- PostgreSQL
- Redis

**Environment Variables:**
```bash
GESTOR_PORT=8011
INTELLICARE_GESTOR_DATABASE_URL=postgresql+asyncpg://intellicare_admin:password@postgres:5432/intellicare_db
```

### Grahame (8012) - FHIR R4 + CDS Hooks
**Purpose:** FHIR R4 server, CDS Hooks, terminology services

**Dependencies:**
- PostgreSQL
- Redis

**Environment Variables:**
```bash
GRAHAME_PORT=8012
INTELLICARE_GRAHAME_DATABASE_URL=postgresql+asyncpg://intellicare_admin:password@postgres:5432/intellicare_db
```

### Nise (8013) - Chatbot + Training
**Purpose:** AI chatbot and model training (Flowise/Kestra integration)

**Dependencies:**
- PostgreSQL
- Redis
- Flowise (separate deployment)
- Kestra (separate deployment)

**Environment Variables:**
```bash
NISE_PORT=8013
INTELLICARE_NISE_DATABASE_URL=postgresql+asyncpg://intellicare_admin:password@postgres:5432/intellicare_db
```

## Troubleshooting

### Module won't start

1. **Check logs:**
```bash
docker logs intellicare-[module-name]
```

2. **Verify database connection:**
```bash
docker exec -it intellicare-postgres psql -U intellicare_admin -d intellicare_db -c "SELECT 1;"
```

3. **Check network connectivity:**
```bash
docker network inspect intellicare_intellicare-network
```

### Module is restarting

1. **Check health status:**
```bash
docker inspect intellicare-[module-name] --format='{{.State.Health.Status}}'
```

2. **View recent logs:**
```bash
docker logs --tail 50 intellicare-[module-name]
```

3. **Common issues:**
   - Database connection failed → Check DATABASE_URL
   - Port already in use → Check port mapping
   - Missing dependencies → Check required services are running

### Database schema not created

Some modules require database migrations:

```bash
# Run migrations for a specific module
docker exec -it intellicare-[module-name] alembic upgrade head
```

## Stopping Modules

To stop additional modules (keeping core modules running):

```bash
cd /opt/intellicare
docker-compose -f docker-compose.full.yml stop zilda minerva pierre admin gestor grahame nise
```

To remove the containers:

```bash
docker-compose -f docker-compose.full.yml rm -f zilda minerva pierre admin gestor grahame nise
```

## Production Considerations

1. **Resource Usage:** Each module consumes memory and CPU. Monitor resources:
```bash
docker stats
```

2. **Database Connections:** Each module opens database connections. Ensure PostgreSQL max_connections is sufficient.

3. **API Rate Limits:** Some modules (Pierre, Minerva) call external APIs. Configure appropriate rate limits.

4. **Scaling:** For high-demand modules, consider scaling:
```bash
docker-compose -f docker-compose.full.yml up -d --scale wanda=3
```

## Next Steps

After starting additional modules:

1. Update Traefik routes (if accessing via domain)
2. Configure module-specific settings in Admin panel
3. Set up monitoring in Grafana
4. Test module functionality via smoke tests:
```bash
bash scripts/smoke_test.sh
```
