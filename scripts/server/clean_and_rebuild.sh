#!/bin/bash
#
# IntelliCare - Clean and Rebuild from Scratch
# This script will:
# 1. Stop all containers
# 2. Remove all containers
# 3. Remove all images
# 4. Remove all volumes (OPTIONAL - be careful!)
# 5. Clean networks
# 6. Rebuild everything from scratch
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}============================================================================${NC}"
echo -e "${RED}⚠️  WARNING: This will DELETE ALL containers, images and data!${NC}"
echo -e "${RED}============================================================================${NC}"
echo ""
echo -e "${YELLOW}This script will:${NC}"
echo "  1. Stop all IntelliCare containers"
echo "  2. Remove all IntelliCare containers"
echo "  3. Remove all Docker images"
echo "  4. Remove all Docker volumes (INCLUDING DATABASE DATA!)"
echo "  5. Clean Docker networks"
echo "  6. Rebuild everything from scratch"
echo ""
echo -e "${RED}⚠️  ALL DATA WILL BE LOST!${NC}"
echo ""

read -p "Type 'DELETE' to confirm: " confirm
if [ "$confirm" != "DELETE" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Starting Clean and Rebuild Process${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# STEP 1: Stop all containers
# ============================================================================
echo -e "${YELLOW}STEP 1: Stopping all containers${NC}"
echo "================================"
echo ""

cd /opt/intellicare/intellicare 2>/dev/null || cd /opt/intellicare 2>/dev/null || true

# Stop using docker-compose if available
if [ -f "docker-compose.full.yml" ]; then
    echo "Stopping containers via docker-compose..."
    docker-compose -f docker-compose.full.yml down 2>/dev/null || \
    docker compose -f docker-compose.full.yml down 2>/dev/null || true
fi

# Stop any remaining intellicare containers
echo "Stopping any remaining containers..."
docker stop $(docker ps -q --filter "name=intellicare") 2>/dev/null || true

echo -e "${GREEN}✓ All containers stopped${NC}"
echo ""

# ============================================================================
# STEP 2: Remove all containers
# ============================================================================
echo -e "${YELLOW}STEP 2: Removing all containers${NC}"
echo "================================"
echo ""

echo "Removing all containers..."
docker rm $(docker ps -aq --filter "name=intellicare") 2>/dev/null || true

echo -e "${GREEN}✓ All containers removed${NC}"
echo ""

# ============================================================================
# STEP 3: Remove all images
# ============================================================================
echo -e "${YELLOW}STEP 3: Removing all images${NC}"
echo "================================"
echo ""

echo "Removing all intellicare images..."
docker rmi $(docker images -q --filter "reference=modularizacao*") 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=intellicare*") 2>/dev/null || true

echo -e "${GREEN}✓ All images removed${NC}"
echo ""

# ============================================================================
# STEP 4: Remove volumes (WARNING: This deletes all data!)
# ============================================================================
echo -e "${RED}STEP 4: Removing all volumes${NC}"
echo "================================"
echo ""
echo -e "${RED}⚠️  This will DELETE ALL DATA including databases!${NC}"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing volumes..."
    docker volume rm $(docker volume ls -q --filter "name=modularizacao*") 2>/dev/null || true
    docker volume rm $(docker volume ls -q --filter "name=intellicare*") 2>/dev/null || true

    # Remove specific volumes
    docker volume rm modularizacao_postgres-data 2>/dev/null || true
    docker volume rm modularizacao_redis-data 2>/dev/null || true
    docker volume rm modularizacao_prometheus-data 2>/dev/null || true
    docker volume rm postgres-data 2>/dev/null || true
    docker volume rm redis-data 2>/dev/null || true
    docker volume rm prometheus-data 2>/dev/null || true

    echo -e "${GREEN}✓ All volumes removed${NC}"
else
    echo -e "${YELLOW}Skipped volume removal${NC}"
fi
echo ""

# ============================================================================
# STEP 5: Clean networks
# ============================================================================
echo -e "${YELLOW}STEP 5: Cleaning networks${NC}"
echo "================================"
echo ""

echo "Removing networks..."
docker network rm modularizacao_intellicare-network 2>/dev/null || true
docker network rm intellicare-network 2>/dev/null || true

echo "Creating fresh intellicare-network..."
docker network create intellicare-network --driver bridge --subnet 172.28.0.0/16

echo -e "${GREEN}✓ Networks cleaned${NC}"
echo ""

# ============================================================================
# STEP 6: Clean Docker system
# ============================================================================
echo -e "${YELLOW}STEP 6: Cleaning Docker system${NC}"
echo "================================"
echo ""

echo "Pruning Docker system..."
docker system prune -f --volumes

echo -e "${GREEN}✓ Docker system cleaned${NC}"
echo ""

# ============================================================================
# STEP 7: Update Docker if needed
# ============================================================================
echo -e "${YELLOW}STEP 7: Checking Docker version${NC}"
echo "================================"
echo ""

DOCKER_VERSION=$(docker --version 2>&1 | awk '{print $3}' | sed 's/,//')
DOCKER_API=$(docker version --format '{{.Server.APIVersion}}' 2>/dev/null || echo "unknown")

echo "Docker: $DOCKER_VERSION (API $DOCKER_API)"

if [ "$DOCKER_API" = "unknown" ] || [ "${DOCKER_API//./}" -lt "143" ]; then
    echo -e "${RED}⚠️  Docker is too old and needs to be updated${NC}"
    read -p "Update Docker now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bash /opt/intellicare/intellicare/scripts/server/simple_fix.sh 2>/dev/null || \
        echo "Please update Docker manually"
    fi
fi
echo ""

# ============================================================================
# STEP 8: Pull latest code
# ============================================================================
echo -e "${YELLOW}STEP 8: Pulling latest code${NC}"
echo "================================"
echo ""

cd /opt/intellicare/intellicare
if [ -d ".git" ]; then
    echo "Pulling latest code from Git..."
    git fetch origin
    git reset --hard origin/staging
    echo -e "${GREEN}✓ Code updated${NC}"
else
    echo -e "${YELLOW}Not a git repository, skipping pull${NC}"
fi
echo ""

# ============================================================================
# STEP 9: Build and start all services
# ============================================================================
echo -e "${YELLOW}STEP 9: Building and starting all services${NC}"
echo "================================"
echo ""

cd /opt/intellicare/intellicare

if [ -f "docker-compose.full.yml" ]; then
    echo "Building containers (this will take a while)..."
    docker-compose -f docker-compose.full.yml build --no-cache

    echo ""
    echo "Starting containers..."
    docker-compose -f docker-compose.full.yml up -d

    echo -e "${GREEN}✓ Containers built and started${NC}"
else
    echo -e "${RED}ERROR: docker-compose.full.yml not found${NC}"
    exit 1
fi
echo ""

# ============================================================================
# STEP 10: Wait and check status
# ============================================================================
echo -e "${YELLOW}STEP 10: Waiting for containers to start${NC}"
echo "================================"
echo ""

echo "Waiting 30 seconds for containers to initialize..."
sleep 30

echo ""
echo "Container status:"
echo "================="
docker ps --filter "name=intellicare" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# ============================================================================
# STEP 11: Health check
# ============================================================================
echo -e "${YELLOW}STEP 11: Health check${NC}"
echo "================================"
echo ""

echo "Checking container health..."
echo ""

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker ps --filter "name=intellicare-postgres" --format "{{.Status}}" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${YELLOW}⚠ Not healthy yet${NC}"
fi

# Check Redis
echo -n "Redis: "
if docker ps --filter "name=intellicare-redis" --format "{{.Status}}" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${YELLOW}⚠ Not healthy yet${NC}"
fi

# Check Traefik
echo -n "Traefik: "
if docker ps --filter "name=intellicare-traefik" --format "{{.Status}}" | grep -q -E "Up|healthy"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}⚠ Not running${NC}"
fi

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Rebuild Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo "Next steps:"
echo "============"
echo ""
echo "1. Check logs of any failing containers:"
echo "   docker logs <container-name> --tail 50"
echo ""
echo "2. Access the services:"
echo "   https://portal.intellicare.ia.br"
echo "   https://grafana.intellicare.ia.br"
echo "   https://traefik.intellicare.ia.br"
echo ""
echo "3. Check database initialization:"
echo "   docker logs intellicare-postgres --tail 50"
echo ""
echo "4. If needed, run database migrations:"
echo "   docker exec intellicare-oswaldo alembic upgrade head"
echo "   docker exec intellicare-wanda alembic upgrade head"
echo "   etc."
echo ""

echo -e "${GREEN}✓ Done! System rebuilt from scratch.${NC}"
echo ""
