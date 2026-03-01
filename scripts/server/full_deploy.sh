#!/bin/bash
#
# IntelliCare - Full Deploy Script
# ================================
# Complete deployment: update from Git, setup environment, rebuild containers
#

set -e

echo "============================================================================"
echo "IntelliCare - Full Deploy"
echo "============================================================================"
echo ""

TARGET_DIR="/opt/intellicare"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "WARNING: Not running as root. Some operations may fail."
    echo "Consider running with: sudo bash $0"
    echo ""
fi

# ========================================================================
# Step 1: Update from Git
# ========================================================================
echo "Step 1: Updating from Git..."
echo "============================================================================"

if [ -d "$TARGET_DIR/.git" ]; then
    cd "$TARGET_DIR"
    git remote set-url origin https://github.com/egarabini/Intellicare.git 2>/dev/null || true
    git fetch origin
    git reset --hard origin/staging
    echo "✓ Git update complete"
else
    echo "ERROR: Git repository not found at $TARGET_DIR"
    echo "Please run clone_clean_from_git.sh first"
    exit 1
fi

echo ""

# ========================================================================
# Step 2: Setup Environment
# ========================================================================
echo "Step 2: Setting up environment..."
echo "============================================================================"

if [ ! -f "$TARGET_DIR/.env" ] || [ ! -f "$TARGET_DIR/.env.full" ]; then
    cd "$TARGET_DIR"
    bash scripts/server/setup_env.sh
else
    echo "✓ Environment files exist"
fi

echo ""

# ========================================================================
# Step 3: Stop Existing Containers
# ========================================================================
echo "Step 3: Stopping existing containers..."
echo "============================================================================"

cd "$TARGET_DIR"

# Check if docker-compose is running
if docker-compose -f docker-compose.full.yml ps -q 2>/dev/null | grep -q .; then
    docker-compose -f docker-compose.full.yml down
    echo "✓ Containers stopped"
else
    echo "✓ No containers running"
fi

echo ""

# ========================================================================
# Step 4: Remove Old Network (if exists with wrong labels)
# ========================================================================
echo "Step 4: Cleaning up old network..."
echo "============================================================================"

if docker network ls | grep -q "intellicare.*network"; then
    echo "Removing old intellicare networks..."
    docker network ls | grep "intellicare.*network" | awk '{print $1}' | xargs -r docker network rm || true
    echo "✓ Old networks removed"
else
    echo "✓ No old networks to remove"
fi

echo ""

# ========================================================================
# Step 5: Build Images
# ========================================================================
echo "Step 5: Building Docker images..."
echo "============================================================================"
echo "This may take several minutes..."
echo ""

cd "$TARGET_DIR"
docker-compose -f docker-compose.full.yml build --no-cache

echo ""
echo "✓ Build complete"
echo ""

# ========================================================================
# Step 6: Start Containers
# ========================================================================
echo "Step 6: Starting containers..."
echo "============================================================================"

cd "$TARGET_DIR"
docker-compose -f docker-compose.full.yml up -d

echo ""
echo "✓ Containers started"
echo ""

# Wait a bit for containers to initialize
echo "Waiting for containers to initialize..."
sleep 10

# ========================================================================
# Step 7: Check Status
# ========================================================================
echo "Step 7: Checking container status..."
echo "============================================================================"
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|intellicare|intellicare-" || true

echo ""
echo "============================================================================"
echo "Deployment Complete!"
echo "============================================================================"
echo ""

# Count running containers
RUNNING=$(docker ps --format "{{.Names}}" | grep -c "intellicare" || true)
TOTAL=$(docker-compose -f docker-compose.full.yml ps -q 2>/dev/null | wc -l)

echo "Containers: $RUNNING running (expected: ~$TOTAL)"
echo ""

# Check for restarting containers
RESTARTING=$(docker ps -a --format "{{.Names}}\t{{.Status}}" | grep "Restarting" | grep "intellicare" || true)
if [ -n "$RESTARTING" ]; then
    echo "⚠️  WARNING: Some containers are restarting:"
    echo "$RESTARTING"
    echo ""
    echo "Check logs with:"
    echo "  docker logs <container-name>"
    echo ""
else
    echo "✓ All containers healthy!"
fi

echo ""
echo "============================================================================"
echo "Quick Access"
echo "============================================================================"
echo ""
echo "Health checks:"
echo "  bash scripts/smoke_test.sh"
echo ""
echo "View logs:"
echo "  docker-compose -f docker-compose.full.yml logs -f"
echo ""
echo "Specific container logs:"
echo "  docker logs intellicare-wanda"
echo "  docker logs intellicare-florence"
echo ""
echo "Restart a container:"
echo "  docker restart intellicare-<module>"
echo ""

echo "============================================================================"
echo "Done! IntelliCare deployed successfully"
echo "============================================================================"
