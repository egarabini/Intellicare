#!/bin/bash
# ============================================================================
# Deploy IntelliCare Apresentação (Reveal.js Slides)
# ============================================================================

set -e

echo "🚀 Deploying IntelliCare Apresentação..."

# 1. Stop and remove existing container (if exists)
echo "📦 Removing existing container..."
docker stop intellicare-apresentacao 2>/dev/null || true
docker rm intellicare-apresentacao 2>/dev/null || true

# 2. Create container
echo "🐳 Creating Nginx container..."
docker run -d \
  --name intellicare-apresentacao \
  --network intellicare_intellicare-network \
  -v /opt/intellicare/intellicare/intellicare-apresentacao/apresentacao/web:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:alpine

# 3. Wait for container to be healthy
echo "⏳ Waiting for container..."
sleep 3

# 4. Check container status
if docker ps | grep -q intellicare-apresentacao; then
    echo "✅ Container running!"
    docker ps --filter name=intellicare-apresentacao --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Container failed to start!"
    docker logs intellicare-apresentacao
    exit 1
fi

# 5. Update Traefik configuration
echo "🔄 Updating Traefik configuration..."
cd /opt/intellicare/intellicare/traefik/dynamic/

# Backup current config
cp routes-intellicare.yml routes-intellicare.yml.backup

# Check if apresentacao route already exists
if grep -q "apresentacao:" routes-intellicare.yml; then
    echo "✅ Traefik route already configured"
else
    echo "⚠️  Traefik route NOT found - manual update needed"
fi

# 6. Restart Traefik to reload config
echo "🔄 Restarting Traefik..."
docker restart intellicare-traefik
sleep 5

# 7. Test
echo "🧪 Testing apresentacao endpoint..."
sleep 3
curl -I https://apresentacao.intellicare.ia.br 2>&1 | head -5

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ✅ IntelliCare Apresentação Deployed!                  ║"
echo "║                                                           ║"
echo "║   🌐 https://apresentacao.intellicare.ia.br              ║"
echo "║   📊 Reveal.js Slides                                    ║"
echo "║   🔐 HTTPS: Let's Encrypt (auto)                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"

