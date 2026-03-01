#!/bin/bash
#
# Fix Oswaldo Database Connection
# ===============================
# Change from asyncpg (async) to psycopg2 (sync) for oswaldo module
#

echo "============================================================================"
echo "Fixing Oswaldo Database Connection"
echo "============================================================================"
echo ""

ENV_FILE="/opt/intellicare/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found"
    exit 1
fi

echo "Changing oswaldo database URL from asyncpg to psycopg2..."
echo ""

# Backup original
cp "$ENV_FILE" "$ENV_FILE.bak"

# Fix oswaldo database URL - change asyncpg to psycopg2
sed -i 's/INTELLICARE_OSWALDO_DATABASE_URL=postgresql+asyncpg:/INTELLICARE_OSWALDO_DATABASE_URL=postgresql+psycopg2:/' "$ENV_FILE"

echo "✓ Updated INTELLICARE_OSWALDO_DATABASE_URL"
echo ""

# Show the diff
echo "Change made:"
echo "============"
diff "$ENV_FILE.bak" "$ENV_FILE" | grep "OSWALDO_DATABASE_URL" || true
echo ""

echo "============================================================================"
echo "Restarting oswaldo container..."
echo "============================================================================"

cd /opt/intellicare
docker-compose -f docker-compose.full.yml restart oswaldo

echo ""
echo "Waiting for container to start..."
sleep 10

echo ""
echo "Checking logs:"
docker logs intellicare-oswaldo --tail 20

echo ""
echo "✅ Fix applied! Oswaldo should start successfully now."
echo ""
