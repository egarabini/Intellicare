#!/bin/bash
#
# IntelliCare - Network Fix Script
# ================================
# Resolve Docker network conflicts and pool overlaps
#

set -e

echo "============================================================================"
echo "IntelliCare - Docker Network Fix"
echo "============================================================================"
echo ""

# Step 1: Stop all containers
echo "Step 1: Stopping all IntelliCare containers..."
echo "============================================================================"

cd /opt/intellicare
docker-compose -f docker-compose.full.yml down 2>/dev/null || true

# Also stop any remaining containers
docker ps -a --format "{{.Names}}" | grep "intellicare" | xargs -r docker stop 2>/dev/null || true

echo "✓ All containers stopped"
echo ""

# Step 2: Remove all intellicare networks
echo "Step 2: Removing all IntelliCare networks..."
echo "============================================================================"

if docker network ls | grep -q "intellicare"; then
    echo "Found intellicare networks:"
    docker network ls | grep "intellicare"
    echo ""

    echo "Disconnecting containers..."
    docker network ls | grep "intellicare" | awk '{print $1}' | while read net_id; do
        echo "  Processing network: $net_id"
        docker network inspect "$net_id" --format='{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | xargs -r -I {} docker network disconnect -f "$net_id" {} 2>/dev/null || true
    done

    echo ""
    echo "Removing networks..."
    docker network ls | grep "intellicare" | awk '{print $1}' | xargs -r docker network rm -f 2>/dev/null || true

    echo "✓ All intellicare networks removed"
else
    echo "✓ No intellicare networks found"
fi

echo ""

# Step 3: Verify no conflicts
echo "Step 3: Verifying network cleanup..."
echo "============================================================================"

REMAINING=$(docker network ls | grep -c "intellicare" || true)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  WARNING: Some intellicare networks still exist:"
    docker network ls | grep "intellicare"
    echo ""
    echo "You may need to manually remove them:"
    docker network ls | grep "intellicare" | awk '{print "docker network rm -f " $1}'
else
    echo "✓ All intellicare networks successfully removed"
fi

echo ""

# Step 4: Prune unused networks
echo "Step 4: Pruning unused Docker networks..."
echo "============================================================================"

docker network prune -f

echo "✓ Network prune complete"
echo ""

# Step 5: Show current networks
echo "Step 5: Current Docker networks..."
echo "============================================================================"

docker network ls

echo ""
echo "============================================================================"
echo "Network Fix Complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Start containers: docker-compose -f docker-compose.full.yml up -d"
echo "  2. Verify: docker ps"
echo ""
