#!/bin/bash
# Quick fix for Docker - Run this directly on the server

echo "Starting Docker fix..."
echo ""

# Fix OS
if [ -f /etc/debian_version ]; then
    echo "Debian/Ubuntu detected"
    export DEBIAN_FRONTEND=noninteractive

    # Remove old Docker
    echo "Removing old Docker packages..."
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Update
    echo "Updating system..."
    apt-get update -qq

    # Install prerequisites
    echo "Installing prerequisites..."
    apt-get install -y -qq apt-transport-https ca-certificates curl software-properties-common

    # Add Docker GPG key
    echo "Adding Docker GPG key..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add repository
    echo "Adding Docker repository..."
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    echo "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Enable and start
    echo "Starting Docker..."
    systemctl enable docker
    systemctl start docker

    echo ""
    echo "Docker version:"
    docker --version

elif [ -f /etc/redhat-release ]; then
    echo "RedHat/CentOS detected"
    yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    docker --version
else
    echo "Unknown OS. Please install Docker manually."
    exit 1
fi

echo ""
echo "Creating Docker network..."
docker network create intellicare-network --driver bridge 2>/dev/null || echo "Network already exists"

echo ""
echo "Restarting Traefik..."
docker restart intellicare-traefik 2>/dev/null || echo "Traefik not found"

echo ""
echo "Waiting 10 seconds..."
sleep 10

echo ""
echo "Container status:"
docker ps --filter "name=intellicare" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "Done!"
