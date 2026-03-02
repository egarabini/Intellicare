#!/bin/bash
set -e

echo "============================================================================"
echo "IntelliCare - Docker Fix Script"
echo "============================================================================"
echo ""

echo "Step 1: Check Docker Version"
echo "============================="
docker --version 2>&1 || echo "Docker not found"
echo ""

echo "Step 2: Check OS"
echo "================="
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $PRETTY_NAME"
fi
echo ""

echo "Step 3: Check Docker Network"
echo "=============================="
if docker network inspect intellicare-network &>/dev/null; then
    echo "Network intellicare-network: OK"
else
    echo "Creating intellicare-network..."
    docker network create intellicare-network --driver bridge
fi
echo ""

echo "Step 4: List Containers"
echo "======================="
docker ps --all --filter "name=intellicare" --format "table {{.Names}}\t{{.Status}}"
echo ""

echo "Step 5: Fix Docker (Ubuntu/Debian)"
echo "===================================="
read -p "Update Docker now? (y/N): " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    if [ -f /etc/debian_version ]; then
        echo "Detected Debian/Ubuntu system"
        echo "Removing old Docker..."
        apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        echo "Updating packages..."
        apt-get update -qq
        echo "Installing dependencies..."
        apt-get install -y -qq ca-certificates curl gnupg
        echo "Adding Docker GPG key..."
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
        echo "Adding Docker repository..."
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        echo "Installing Docker..."
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        echo "Enabling Docker..."
        systemctl enable docker
        systemctl start docker
        echo "Docker updated:"
        docker --version
    else
        echo "Non-Debian system detected. Please update manually."
        echo "See: https://docs.docker.com/engine/install/"
    fi
fi
echo ""

echo "Step 6: Restart Traefik"
echo "======================="
read -p "Restart Traefik? (y/N): " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    docker restart intellicare-traefik 2>/dev/null || echo "Traefik container not found"
fi
echo ""

echo "============================================================================"
echo "Done!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "1. Check container logs: docker logs <container-name> --tail 50"
echo "2. Restart failed containers: docker restart <container-name>"
echo "3. Check endpoints: curl -I https://portal.intellicare.ia.br"
echo ""
