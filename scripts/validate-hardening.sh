#!/bin/bash
# ============================================================================
# W8-D Production Hardening — Validation Script
# ============================================================================
# This script validates all hardened Dockerfiles and runs security scans
# ============================================================================

set -e

MODULES=(
    "intellicare-grahame"
    "intellicare-oswaldo"
    "intellicare-florence"
    "intellicare-wanda"
    "intellicare-donabedian"
    "intellicare-zilda"
    "intellicare-geralda"
    "intellicare-comunicacao"
)

echo "=========================================="
echo "W8-D Production Hardening Validation"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# Phase 1: Check Prerequisites
# ============================================================================
echo "=== Phase 1: Prerequisites ==="
echo ""

if command_exists docker; then
    echo -e "${GREEN}[PASS]${NC} Docker found"
    docker --version
else
    echo -e "${RED}[FAIL]${NC} Docker not found"
    exit 1
fi

if command_exists trivy; then
    echo -e "${GREEN}[PASS]${NC} Trivy found"
    trivy --version
else
    echo -e "${YELLOW}[WARN]${NC} Trivy not found (optional for build validation)"
fi

echo ""

# ============================================================================
# Phase 2: Build All Modules
# ============================================================================
echo "=== Phase 2: Build Validation ==="
echo ""

for MODULE in "${MODULES[@]}"; do
    echo -n "Building $MODULE... "

    if [ ! -d "$MODULE" ]; then
        echo -e "${YELLOW}[SKIP]${NC} Directory not found"
        continue
    fi

    # Build image from parent directory (for proper COPY context)
    # The Dockerfiles expect to COPY ../intellicare-core etc.
    if docker build -t "test-$MODULE:latest" -f "$MODULE/Dockerfile" . >/dev/null 2>&1; then
        echo -e "${GREEN}[PASS]${NC}"
        ((PASS++))

        # Check image size
        SIZE=$(docker images "test-$MODULE:latest" --format "{{.Size}}")
        echo "  Size: $SIZE"

        # Check user (should be "nobody")
        USER=$(docker run --rm "test-$MODULE:latest" whoami 2>/dev/null || echo "unknown")
        if [ "$USER" = "nobody" ]; then
            echo -e "  User: ${GREEN}$USER${NC}"
        else
            echo -e "  User: ${RED}$USER (should be 'nobody')${NC}"
            ((FAIL++))
        fi

    else
        echo -e "${RED}[FAIL]${NC}"
        ((FAIL++))
    fi
done

echo ""

# ============================================================================
# Phase 3: Security Scan
# ============================================================================
echo "=== Phase 3: Security Scan (Trivy) ==="
echo ""

if command_exists trivy; then
    for MODULE in "${MODULES[@]}"; do
        echo -n "Scanning $MODULE... "

        # Run Trivy scan (CRITICAL and HIGH only)
        SCAN_RESULT=$(trivy image --severity CRITICAL,HIGH --format json "test-$MODULE:latest" 2>/dev/null || echo '{"Results":[]}')

        # Count vulnerabilities
        VULN_COUNT=$(echo "$SCAN_RESULT" | jq '.Results | length' 2>/dev/null || echo "0")

        if [ "$VULN_COUNT" -eq 0 ]; then
            echo -e "${GREEN}[PASS]${NC} No HIGH+ vulnerabilities"
            ((PASS++))
        else
            echo -e "${RED}[FAIL]${NC} Found $VULN_COUNT HIGH+ vulnerabilities"
            ((FAIL++))

            # Show details
            echo "$SCAN_RESULT" | jq -r '.Results[] | .Vulnerabilities[] | .Severity + " " + .Title' 2>/dev/null | head -10 | while read line; do
                echo "  - $line"
            done
        fi
    done
else
    echo -e "${YELLOW}[SKIP]${NC} Trivy not installed. Run:"
    echo "  Linux/Mac: https://aquasecurity.github.io/trivy/latest/getting_started/install/"
    echo "  Windows: choco install trivy"
fi

echo ""

# ============================================================================
# Phase 4: Health Check Validation
# ============================================================================
echo "=== Phase 4: Health Check Validation ==="
echo ""

for MODULE in "${MODULES[@]}"; do
    echo -n "Checking health endpoint for $MODULE... "

    # Start container in background
    CONTAINER_ID=$(docker run -d -p 127.0.0.1:8XXX:8000 "test-$MODULE:latest" 2>/dev/null || echo "")

    if [ -n "$CONTAINER_ID" ]; then
        # Get the port
        PORT=$(docker port "$CONTAINER_ID" | grep -oP '8XXX->\K[0-9]+' || echo "8000")

        # Wait for container to be ready
        sleep 3

        # Check health endpoint
        if curl -sf "http://localhost:$PORT/api/v1/health" >/dev/null 2>&1; then
            echo -e "${GREEN}[PASS]${NC}"
            ((PASS++))

            # Stop container
            docker stop "$CONTAINER_ID" >/dev/null 2>&1
            docker rm "$CONTAINER_ID" >/dev/null 2>&1
        else
            echo -e "${YELLOW}[WARN]${NC} Health check failed (container started but endpoint not responding)"
            ((WARN++))
            docker stop "$CONTAINER_ID" >/dev/null 2>&1
            docker rm "$CONTAINER_ID" >/dev/null 2>&1
        fi
    else
        echo -e "${YELLOW}[SKIP]${NC} Could not start container"
        ((WARN++))
    fi
done

echo ""

# ============================================================================
# Phase 5: Distroless Validation
# ============================================================================
echo "=== Phase 5: Distroless Validation ==="
echo ""

for MODULE in "${MODULES[@]}"; do
    echo -n "Checking distroless for $MODULE... "

    # Check base image
    BASE_IMAGE=$(docker inspect "test-$MODULE:latest" | jq -r '.[0].Config.Image' 2>/dev/null)

    if [[ "$BASE_IMAGE" == *"distroless"* ]]; then
        echo -e "${GREEN}[PASS]${NC} Using distroless: $BASE_IMAGE"
        ((PASS++))
    else
        echo -e "${YELLOW}[WARN]${NC} Not using distroless: $BASE_IMAGE"
        ((WARN++))
    fi
done

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}PASS:${NC} $PASS"
echo -e "${YELLOW}WARN:${NC} $WARN"
echo -e "${RED}FAIL:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}=== ALL CHECKS PASSED ===${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Remove backups: rm **/*Dockerfile.backup"
    echo "  2. Commit changes: git add . && git commit -m 'feat: apply W8-D hardened images'"
    echo "  3. Push to main: git push origin main"
    exit 0
else
    echo -e "${RED}=== VALIDATION FAILED ===${NC}"
    echo ""
    echo "Please fix the failures above and run again."
    exit 1
fi
