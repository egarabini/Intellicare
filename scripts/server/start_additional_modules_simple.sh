#!/bin/bash
#
# IntelliCare - Start Additional Modules (Simple)
# ===============================================
# Quick script to start all additional modules using docker-compose
#
# Usage: bash scripts/server/start_additional_modules_simple.sh
#

set -e

cd /opt/intellicare

echo "============================================================================"
echo "IntelliCare - Starting Additional Modules"
echo "============================================================================"
echo ""

# Start additional modules
echo "Starting additional modules: zilda, minerva, pierre, admin, gestor, grahame, nise"
echo ""

docker-compose -f docker-compose.full.yml up -d zilda minerva pierre admin gestor grahame nise

echo ""
echo "============================================================================"
echo "Waiting for modules to initialize (20 seconds)..."
echo "============================================================================"
sleep 20

echo ""
echo "Checking module status..."
echo "============================================================================"
echo ""

docker-compose -f docker-compose.full.yml ps zilda minerva pierre admin gestor grahame nise

echo ""
echo "============================================================================"
echo "✅ Additional modules started!"
echo "============================================================================"
echo ""
echo "Module health checks:"
echo "  Zilda:   curl -f http://localhost:8007/api/v1/health || echo 'Not healthy'"
echo "  Minerva: curl -f http://localhost:8008/api/v1/health || echo 'Not healthy'"
echo "  Pierre:  curl -f http://localhost:8009/api/v1/health || echo 'Not healthy'"
echo "  Admin:   curl -f http://localhost:8010/api/v1/health || echo 'Not healthy'"
echo "  Gestor:  curl -f http://localhost:8011/api/v1/health || echo 'Not healthy'"
echo "  Grahame: curl -f http://localhost:8012/api/v1/health || echo 'Not healthy'"
echo "  Nise:    curl -f http://localhost:8013/api/v1/health || echo 'Not healthy'"
echo ""
