#!/bin/bash
# Quick fix for apresentacao.intellicare.ia.br

echo "=== Step 1: Check current Traefik config ==="
grep -c "apresentacao:" /opt/intellicare/intellicare/traefik/dynamic/routes-intellicare.yml || echo "NOT FOUND"

echo ""
echo "=== Step 2: Check container status ==="
docker ps -a --filter name=apresentacao --format "{{.Names}} {{.Status}}" || echo "NO CONTAINER"

echo ""
echo "=== Step 3: Stop/remove old container ==="
docker stop intellicare-apresentacao 2>/dev/null || true
docker rm intellicare-apresentacao 2>/dev/null || true

echo ""
echo "=== Step 4: Create new container ==="
docker run -d \
  --name intellicare-apresentacao \
  --network intellicare_intellicare-network \
  -v /opt/intellicare/intellicare/intellicare-apresentacao/apresentacao/web:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:alpine

echo ""
echo "=== Step 5: Verify container ==="
docker ps --filter name=apresentacao --format "{{.Names}} {{.Status}}"

echo ""
echo "=== Step 6: Test container internally ==="
docker exec intellicare-apresentacao ls -la /usr/share/nginx/html/ | head -5

echo ""
echo "=== Step 7: Restart Traefik ==="
docker restart intellicare-traefik

echo ""
echo "=== Step 8: Wait for Traefik ==="
sleep 5

echo ""
echo "=== Step 9: Test endpoint ==="
curl -I http://localhost/apresentacao 2>&1 | head -3 || echo "Local test failed"

echo ""
echo "=== DONE ==="

