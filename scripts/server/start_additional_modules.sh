#!/bin/bash
#
# IntelliCare - Start Additional Modules
# =====================================
# Starts modules beyond the basic 6 (florence, oswaldo, donabedian, wanda, comunicacao, geralda)
#
# Additional modules:
# - Minerva (8008) - OCR/Document extraction
# - Pierre (8009) - Scientific Search
# - Zilda (8007) - CNES + DATASUS
# - Grahame (8012) - FHIR R4 + CDS Hooks
# - Nise (8013) - Chatbot/Training
# - Admin (8010) - System Administration
# - Gestor (8011) - Module Management
#
# Usage: bash scripts/server/start_additional_modules.sh
#

set -e

cd /opt/intellicare

echo "============================================================================"
echo "IntelliCare - Starting Additional Modules"
echo "============================================================================"
echo ""

# Check if base services are running
echo "Step 1: Checking base services..."
echo "============================================================================"

BASE_SERVICES=("postgres" "redis" "florence" "oswaldo" "donabedian" "wanda" "comunicacao" "geralda")

for service in "${BASE_SERVICES[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "intellicare-$service"; then
        echo "✓ $service is running"
    else
        echo "⚠️  WARNING: $service is not running"
        echo "   Start base services first: docker-compose -f docker-compose.full.yml up -d"
        exit 1
    fi
done

echo ""
echo "✓ All base services are running"
echo ""

# Start additional modules one by one
echo "Step 2: Starting additional modules..."
echo "============================================================================"
echo ""

# Function to start a module
start_module() {
    local module_name=$1
    local module_port=$2
    local module_dir=$3
    local description=$4

    echo "Starting $module_name ($description)..."
    echo "  Port: $module_port"
    echo "  Directory: $module_dir"

    # Check if module is already running
    if docker ps --format "{{.Names}}" | grep -q "intellicare-$module_name"; then
        echo "  ✓ Already running, skipping..."
        echo ""
        return 0
    fi

    # Check if Dockerfile exists
    if [ ! -f "$module_dir/Dockerfile" ]; then
        echo "  ⚠️  WARNING: Dockerfile not found, skipping..."
        echo ""
        return 0
    fi

    # Build and start the module
    echo "  Building..."
    docker build -t intellicare-$module_name:latest -f $module_dir/Dockerfile --target api $module_dir

    echo "  Starting container..."

    # Determine database URL based on module name
    local db_url="${module_name^^}_DATABASE_URL"
    local db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"

    # Special cases for different database drivers
    if [ "$module_name" = "zilda" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "grahame" ]; then
        db_url_value="postgresql+asyncpg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "minerva" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "pierre" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "nise" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "admin" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    elif [ "$module_name" = "gestor" ]; then
        db_url_value="postgresql+psycopg://intellicare_admin:intellicare_dev@postgres:5432/intellicare_db"
    fi

    # Run container
    docker run -d \
        --name intellicare-$module_name \
        --hostname $module_name \
        --network intellicare_intellicare-network \
        -p "${module_port}:${module_port}" \
        -e INTELLICARE_ENVIRONMENT=staging \
        -e INTELLICARE_LOG_LEVEL=INFO \
        -e "INTELLICARE_${module_name^^}_PORT=${module_port}" \
        -e "INTELLICARE_${module_name^^}_DATABASE_URL=${db_url_value}" \
        -e "INTELLICARE_FHIR_SERVER_URL=http://oswaldo:8000" \
        -e "INTELLICARE_REDIS_URL=redis://redis:6379/0" \
        -e "PYTHONUNBUFFERED=1" \
        --restart unless-stopped \
        intellicare-$module_name:latest

    echo "  ✓ $module_name started"
    echo ""

    # Wait a bit for the module to initialize
    sleep 3
}

# Start Zilda (CNES + DATASUS)
start_module "zilda" "8007" "./intellicare-zilda" "CNES + DATASUS Integration"

# Start Minerva (OCR/Document extraction)
start_module "minerva" "8008" "./intellicare-minerva" "OCR + Document Extraction (MCP Server)"

# Start Pierre (Scientific Search)
start_module "pierre" "8009" "./intellicare-pierre" "Scientific Search PubMed+Tavily (MCP Server)"

# Start Admin (System Administration)
start_module "admin" "8010" "./intellicare-admin" "System Administration"

# Start Gestor (Module Management)
start_module "gestor" "8011" "./intellicare-gestor" "Clinical Module Management"

# Start Grahame (FHIR R4 + CDS Hooks)
start_module "grahame" "8012" "./intellicare-grahame" "FHIR R4 + CDS Hooks + Terminology"

# Start Nise (Chatbot/Training)
start_module "nise" "8013" "./intellicare-nise" "Chatbot + Training (Flowise/Kestra)"

echo "============================================================================"
echo "Step 3: Verifying module status..."
echo "============================================================================"
echo ""

# Wait for containers to initialize
echo "Waiting for containers to initialize (15 seconds)..."
sleep 15

# Check status of all modules
ALL_MODULES=("zilda" "minerva" "pierre" "admin" "gestor" "grahame" "nise")

RUNNING=0
TOTAL=${#ALL_MODULES[@]}

for module in "${ALL_MODULES[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "intellicare-$module"; then
        STATUS=$(docker inspect intellicare-$module --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-healthcheck")
        if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "no-healthcheck" ]; then
            echo "✓ $module is running"
            ((RUNNING++))
        else
            echo "⚠️  $module is running but health: $STATUS"
        fi
    else
        echo "✗ $module is NOT running"
    fi
done

echo ""
echo "Summary: $RUNNING/$TOTAL additional modules running"
echo ""

# Show all intellicare containers
echo "============================================================================"
echo "All IntelliCare Containers:"
echo "============================================================================"
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep intellicare

echo ""
echo "============================================================================"
echo "✅ Additional Modules Started!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  - Check module health: curl http://167.86.97.142:8007/api/v1/health (replace port)"
echo "  - View logs: docker logs -f intellicare-<module-name>"
echo "  - Run smoke test: bash scripts/smoke_test.sh"
echo ""
