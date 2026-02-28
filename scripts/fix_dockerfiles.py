#!/usr/bin/env python3
"""
Fix all Dockerfiles with Python 3.11, libpq-dev, and correct COPY paths.
"""

import os
import shutil
from pathlib import Path

MODULES = {
    "intellicare-grahame": "grahame",
    "intellicare-oswaldo": "oswaldo",
    "intellicare-florence": "florence",
    "intellicare-wanda": "wanda",
    "intellicare-donabedian": "donabedian",
    "intellicare-zilda": "zilda",
    "intellicare-geralda": "geralda",
    "intellicare-comunicacao": "comunicacao",
}

DOCKERFILE_TEMPLATE = """# ============================================================================
# INTELLICARE-{MODULE_UPPER} — Hardened Multi-Stage Dockerfile
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
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (including libpq-dev for asyncpg/psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    g++ \\
    curl \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install intellicare-core to /root/.local AND /build for dependencies
COPY ./intellicare-core /intellicare-core
COPY ./intellicare-core /build/intellicare-core
RUN pip install --no-cache-dir --user -e /intellicare-core

# Install intellicare-auth (optional)
COPY ./intellicare-auth /intellicare-auth
RUN pip install --no-cache-dir --user -e /intellicare-auth || true

# Install {module_name} dependencies (no install itself yet)
COPY ./intellicare-{module_name}/pyproject.toml ./intellicare-{module_name}/README.md* /build/
RUN pip install --no-cache-dir --user . || true

# Copy {module_name} source and install to /root/.local
COPY ./intellicare-{module_name} /build/intellicare-{module_name}
RUN pip install --no-cache-dir --user -e /build/intellicare-{module_name}

# ----------------------------------------------------------------------------
# RUNTIME STAGE — Distroless, runs as nobody
# ----------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian12 AS runtime

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app (if needed for static files, templates, etc.)
COPY --from=builder /build/intellicare-{module_name} /app/intellicare-{module_name}

# Ensure Python finds user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.11/site-packages:$PYTHONPATH

# Run as non-root user (distroless creates 'nobody' user)
USER nobody

# Expose port
EXPOSE 8000

# Health check (uses wget from distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/v1/health || exit 1

# ----------------------------------------------------------------------------
# API TARGET — Runs uvicorn server
# ----------------------------------------------------------------------------
FROM runtime AS api

# Run uvicorn from /root/.local/bin
CMD ["python3", "-m", "uvicorn", "{module_name}.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def main():
    base_dir = Path("c:/DOCSHARE/INTELLICARE")

    for module_path, module_name in MODULES.items():
        dockerfile_path = base_dir / module_path / "Dockerfile"

        if not dockerfile_path.exists():
            print(f"[!] Skipping {module_path} (Dockerfile not found)")
            continue

        # Backup original if not already backed up
        backup_path = dockerfile_path.with_suffix(".backup")
        if not backup_path.exists() and dockerfile_path.exists():
            shutil.copy(dockerfile_path, backup_path)
            print(f"[+] Backed up {module_path}/Dockerfile")

        # Write new Dockerfile
        new_dockerfile = DOCKERFILE_TEMPLATE.format(
            module_name=module_name,
            MODULE_UPPER=module_name.upper()
        )
        dockerfile_path.write_text(new_dockerfile)

        print(f"[+] Updated {module_path}/Dockerfile")

    print("\\n[*] All Dockerfiles updated with Python 3.11 and libpq-dev!")


if __name__ == "__main__":
    main()
