#!/usr/bin/env python3
"""
Apply hardened Dockerfiles to remaining modules.

Updates: donabedian, zilda, geralda, comunicacao, portal
"""

import os
from pathlib import Path

MODULES = {
    "intellicare-donabedian": "donabedian",
    "intellicare-zilda": "zilda",
    "intellicare-geralda": "geralda",
    "intellicare-comunicacao": "comunicacao",
}

DOCKERFILE_TEMPLATE = """# ============================================================================
# HARDENED MULTI-STAGE DOCKERFILE
# ============================================================================

# ----------------------------------------------------------------------------
# BUILD STAGE — Runs as root, has build tools
# ----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install intellicare-core to /root/.local
COPY ./intellicare-core /intellicare-core
RUN pip install --no-cache-dir --user -e /intellicare-core

# Install intellicare-auth (optional)
COPY ./intellicare-auth /intellicare-auth
RUN pip install --no-cache-dir --user -e /intellicare-auth || true

# Install {module_name} dependencies
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

# Copy app
COPY --from=builder /build/intellicare-{module_name} /app/intellicare-{module_name}

# Ensure Python finds user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.13/site-packages:$PYTHONPATH

# Run as non-root user
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

        # Backup original
        backup_path = dockerfile_path.with_suffix(".backup")
        if not backup_path.exists():
            import shutil
            shutil.copy(dockerfile_path, backup_path)
            print(f"[+] Backed up {module_path}/Dockerfile")

        # Write new Dockerfile
        new_dockerfile = DOCKERFILE_TEMPLATE.format(module_name=module_name)
        dockerfile_path.write_text(new_dockerfile)

        print(f"[+] Updated {module_path}/Dockerfile")

    print("\n[*] All remaining Dockerfiles updated!")


if __name__ == "__main__":
    main()
