#!/bin/bash
# ============================================================================
# Apply Hardened Dockerfiles to All Modules
# ============================================================================
# This script updates all Dockerfiles to use distroless multi-stage builds
# ============================================================================

MODULES=(
    "intellicare-oswaldo"
    "intellicare-florence"
    "intellicare-donabedian"
    "intellicare-zilda"
    "intellicare-geralda"
    "intellicare-wanda"
    "intellicare-comunicacao"
)

for MODULE in "${MODULES[@]}"; do
    echo "🔧 Updating $MODULE/Dockerfile..."

    if [ ! -d "$MODULE" ]; then
        echo "⚠️  Skipping $MODULE (directory not found)"
        continue
    fi

    # Backup original Dockerfile
    if [ -f "$MODULE/Dockerfile" ]; then
        cp "$MODULE/Dockerfile" "$MODULE/Dockerfile.backup"
        echo "  ✅ Backed up original Dockerfile"
    fi

    # Create new hardened Dockerfile
    cat > "$MODULE/Dockerfile" << 'EOF'
# ============================================================================
# HARDENED MULTI-STAGE DOCKERFILE
# ============================================================================
# Production-ready image with:
# - Multi-stage build (build + runtime)
# - Distroless runtime (minimal attack surface)
# - Non-root user (nobody)
# - Health check
# - Security scanning ready (Trivy)
# ============================================================================

# ----------------------------------------------------------------------------
# BUILD STAGE — Runs as root, has build tools
# ----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install intellicare-core to /root/.local
COPY ./intellicare-core /intellicare-core
RUN pip install --no-cache-dir --user -e /intellicare-core

# Install module dependencies
COPY pyproject.toml README.md* /build/
RUN pip install --no-cache-dir --user . || true

# Copy module source and install to /root/.local
COPY . /build/MODULE
RUN pip install --no-cache-dir --user -e /build/MODULE

# ----------------------------------------------------------------------------
# RUNTIME STAGE — Distroless, runs as nobody
# ----------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian12 AS runtime

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app (if needed for static files, templates, etc.)
COPY --from=builder /build/MODULE /app/MODULE

# Ensure Python finds user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.13/site-packages:$PYTHONPATH

# Run as non-root user (distroless creates 'nobody' user)
USER nobody

# Expose port
EXPOSE 8000

# Health check (uses wget from distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/v1/health || exit 1

# ----------------------------------------------------------------------------
# API TARGET — Runs uvicorn server
# ----------------------------------------------------------------------------
FROM runtime AS api

# Run uvicorn from /root/.local/bin
CMD ["python3", "-m", "uvicorn", "MODULE.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Replace MODULE placeholder with actual module name
    sed -i "s/MODULE/$(basename $MODULE | sed 's/intellicare-//')/g" "$MODULE/Dockerfile"

    echo "  ✅ Created hardened Dockerfile for $MODULE"
    echo ""
done

echo "✨ All Dockerfiles updated successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Test build: docker build -t test-image ./intellicare-grahame"
echo "  2. Run security scan: trivy image test-image"
echo "  3. If all good, remove .backup files"
