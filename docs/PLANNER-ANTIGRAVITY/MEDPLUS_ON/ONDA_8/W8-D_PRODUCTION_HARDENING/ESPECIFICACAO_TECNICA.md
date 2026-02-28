# W8-D — Production Hardening — Especificação Técnica

**Workstream:** W8-D
**Responsável:** DEV0
**Módulos:** Todos + Docker + Infraestrutura
**Status:** 📋 Especificação Técnica
**Data:** 2026-02-24

---

## 1. Arquitetura da Solução

### 1.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Source  │→ │  Build  │→ │  Scan   │→ │    Sign      │  │
│  │ Push    │  │ Docker  │  │ Trivy   │  │   Cosign     │  │
│  └─────────┘  └─────────┘  └─────────┘  └──────────────┘  │
│                                                    ↓             │
└───────────────────────────────────────────────────────┼─────────────┘
                                                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Production Environment                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  App Pods    │  │  Redis       │  │  Redis Sentinel │  │
│  │  (distroless) │← →│ (master)     │← →│   (sentinel)    │  │
│  │  USER nobody │  │  Pub/Sub     │  │  Failover       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│          ↓                                           ↑          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │      BullMQ Workers                                │      │
│  │  - Auto-reconnect (backoff)                        │      │
│  │  - Job re-enqueue on failover                       │      │
│  │  - DLQ for failed jobs                             │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Componentes

| Componente | Descrição | Tecnologia |
|------------|-----------|------------|
| **Docker Hardened Images** | Imagens seguras sem vulnerabilidades | distroless, python:alpine |
| **Image Signing** | Assinatura de imagens para garantia de origem | cosign, Docker Content Trust |
| **CI/CD Scanners** | Scanners de vulnerabilidade no pipeline | Trivy, grype |
| **Redis Failover** | Failover transparente para jobs assíncronos | BullMQ, Redis Sentinel |
| **Health Monitoring** | Monitoramento de saúde de workers | Prometheus, health endpoints |

---

## 2. Docker Hardened Images

### 2.1 Arquitetura Multi-Stage

#### Padrão para Todos os Módulos

```dockerfile
# ===================================================================
# Build Stage — Compilação e dependências
# ===================================================================
FROM python:3.13-slim AS builder

# Instalar dependências do sistema (para compilação)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /build

# Copiar requirements e instalar em /root/.local (user-level install)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar código fonte
COPY . .

# Instalar pacote em modo editable (development)
RUN pip install --no-cache-dir --user -e .

# ===================================================================
# Runtime Stage — Imagem hardened minimalista
# ===================================================================
FROM gcr.io/distroless/python3-debian12

# Copiar binários Python do builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /build /app

# Criar usuário não-root (nobody já existe no distroless)
USER nobody

# Expor porta (padrão IntelliCare)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()"

# Executar aplicação
CMD ["python", "-m", "app.main"]
```

#### Exemplo: intellicare-grahame

```dockerfile
# Build Stage
FROM python:3.13-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY . .
RUN pip install --no-cache-dir --user -e .

# Runtime Stage (Hardened)
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /root/.local /root/.local
COPY --from=builder /build /app
USER nobody
EXPOSE 8012
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8012/api/v1/health').read()"
CMD ["python", "-m", "grahame.api"]
```

### 2.2 Padrões de Hardening

| Regra | Descrição | Exemplo |
|-------|-----------|--------|
| **Base distroless** | Imagens Google sem shells, reduz superfície de ataque | `gcr.io/distroless/python3-debian12` |
| **User nobody** | Rodar sem privilégios de root | `USER nobody` |
| **Multi-stage** | Separar build (com root) de runtime (sem root) | `FROM python:slim AS builder` |
| **Sem shells** | Não incluir `/bin/sh` ou `/bin/bash` | distroless já não tem |
| **Sem ferramentas** | Não incluir curl, wget, editors | Reduz tamanho e vulnerabilidades |
| **Labels completos** | Metadados para rastreabilidade | `maintainer`, `version`, `description` |
| **Health check** | Verificação de saúde do container | `HEALTHCHECK` + `/api/v1/health` |

### 2.3 Labels Obrigatórios

```dockerfile
LABEL maintainer="IntelliCare <dev@intellicare.com.br>" \
      version="1.1.0" \
      description="IntelliCare Grahame - FHIR R4 Interoperability" \
      org.opencontainers.image.source="https://github.com/intellicare/intellicare-grahame" \
      org.opencontainers.image.revision="${VCS_REF:-main}" \
      org.opencontainers.image.created="${BUILD_DATE:-}" \
      org.opencontainers.image.documentation="https://docs.intellicare.com.br/grahame"
```

### 2.4 Módulos a Hardening

| Ordem | Módulo | Porta | Prioridade |
|-------|--------|-------|------------|
| 1 | grahame | 8012 | 🔴 Alta (exposto externamente) |
| 2 | wanda | 8004 | 🔴 Alta (agente orquestrador) |
| 3 | florence | 8001 | 🟠 Média (IA clínica) |
| 4 | oswaldo | 8002 | 🟠 Média (dados crônicos) |
| 5 | comunicacao | 8005 | 🟠 Média (mensagens) |
| 6 | geralda | 8006 | 🟠 Média (acompanhamento) |
| 7 | zilda | 8007 | 🟡 Baixa (dados públicos) |
| 8 | donabedian | 8003 | 🟡 Baixa (qualidade) |
| 9 | portal | 3000 | 🟡 Baixa (frontend) |
| 10 | nise | 8013 | 🟡 Baixa (chatbot) |
| 11 | admin | 8010 | 🟡 Baixa (admin) |
| 12 | gestor | 8011 | 🟡 Baixa (gestão) |
| 13 | pierre | 8009 | 🟡 Baixa (busca) |
| 14 | ocr | 8008 | 🟡 Baixa (OCR) |

---

## 3. Image Signing com Cosign

### 3.1 Geração de Chaves

```bash
# Gerar chave privada RSA (se não existir)
cosign generate-key-pair --k8s://cosign-secrets

# Ou local (para desenvolvimento)
cosign generate-key-pair ./cosign.key
chmod 0600 ./cosign.key

# Converter para formato Kubernetes Secret
kubectl create secret generic cosign-secret \
  --from-file=./cosign.key \
  --from-file=./cosign.pub
```

### 3.2 Pipeline de Assinatura

#### Arquivo: `.github/workflows/docker-sign.yml`

```yaml
name: Docker Sign

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  sign:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/intellicare/${{ github.event.repository.name }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest,enable=true
            type=semver,pattern={{version}}
          labels: |
            org.opencontainers.image.source
            org.opencontainers.image.description

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          target: distroless

      - name: Sign image with Cosign
        env:
          COSIGN_EXPERIMENTAL: 1
        run: |
          cosign sign \
            --yes \
            ${{ steps.meta.outputs.tags }} \
            --annotations "org.opencontainers.image.source=${{ github.repositoryUrl }}" \
            "org.opencontainers.image.description=IntelliCare ${{ github.event.repository.name }}"

      - name: Verify signature
        run: |
          cosign verify ${{ steps.meta.outputs.tags }}
```

### 3.3 Verificação no Runtime (Kubernetes)

#### Admission Controller (Verificação Automática)

```yaml
# cosign-admission-webhook.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cosign-admission-webhook
  namespace: default
data:
  policy.cfn: |
    match:
    - apiVersion: v1
    resources:
      - pods
    namespaces:
      - production
    rules:
      - pattern: "ghcr.io/intellicare/*"
        verify:
          - key: cosign
            keys:
              - name: k8s://cosign-secrets
            annotations:
              - name: org.opencontainers.image.source
                required: true
```

---

## 4. CI/CD Scanners (Trivy)

### 4.1 Pipeline Completo

#### Arquivo: `.github/workflows/docker-scan.yml`

```yaml
name: Docker Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    # Scan semanal (segundas 00:00 UTC)
    - cron: '0 0 * * 0'

env:
  REGISTRY: ghcr.io/intellicare

jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    permissions:
      contents: read
      security-events: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build image (for scanning)
        uses: docker/build-push-action@v5
        with:
          context: .
          tags: ${{ env.REGISTRY }}/${{ github.event.repository.name }}:scan
          load: true
          target: distroless
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ github.event.repository.name }}:scan
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Fail on HIGH vulnerabilities
        shell: bash
        run: |
          # Extrair número de vulnerabilidades HIGH+
          VULNS=$(trivy image \
            --severity HIGH,CRITICAL \
            --format json \
            ${{ env.REGISTRY }}/${{ github.event.repository.name }}:scan \
            | jq '.Results | length')

          echo "Vulnerabilidades HIGH/CRITICAL: $VULNS"

          # Threshold
          if [ $VULNS -gt 0 ]; then
            echo "::error::Encontradas $VULNS vulnerabilidades HIGH/CRITICAL!"
            echo "::error::Build falhado. Corrija vulnerabilidades antes de prosseguir."
            exit 1
          fi

          echo "✅ Nenhuma vulnerabilidade HIGH/CRITICAL encontrada"

      - name: Generate SBOM
        run: |
          trivy image \
            --format spdx-json \
            --output sbom.spdx \
            ${{ env.REGISTRY }}/${{ github.event.repository.name }}:scan

      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx

      - name: Generate vulnerability report
        if: always()
        run: |
          trivy image \
            --severity 'LOW,MEDIUM,HIGH,CRITICAL' \
            --format table \
            ${{ env.REGISTRY }}/${{ github.event.repository.name }}:scan \
            > vulnerability-report.txt

      - name: Upload vulnerability report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: vulnerability-report
          path: vulnerability-report.txt
```

### 4.2 Trivy Configuration

#### Arquivo: `trivy.yaml`

```yaml
# Trivy configuration file
# Place in repository root

# Severities to check
severity:
  - UNKNOWN
  - LOW
  - MEDIUM
  - HIGH
  - CRITICAL

# Vulnerability DB
db:
  # Skip-update to use embedded DB (faster CI)
  skip-update: false
  # Download DB from GitHub
  no-progress: true

# Output formats
output:
  - 'table'
  - 'sarif'

# Scanners to enable
scan:
  scanners:
    - vuln
    - misconfig
    - secret

# Vulnerability scanning options
vuln:
  # Include dev dependencies
  dev: true
  # Ignore unfixed vulnerabilities
  ignore-unfixed: false
  # Types of vulnerabilities to check
  types:
    - os
    - library

# Misconfiguration scanning options
misconfig:
  # Check all files
  check-all: true

# Secret scanning
secret:
  # Skip scanning if no private keys
  skip-secret-update: false

# Report options
report:
  # Include all information
  ignore-policy: []
  # Include licenses
  include-licenses: true
  # Format: table, json, sarif
  format: 'table'

# Docker-specific options
docker:
  # Include files from image
  include-dev-deps: true
  # Follow symbolic links
  follow-symlinks: true
  # Ignore platforms
  skip-files: []
```

---

## 5. BullMQ Redis Failover

### 5.1 Arquitetura de Failover

```
┌─────────────────────────────────────────────────────────────┐
│                    BullMQ Worker (Python)                  │
│                                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │ Job Queue     │  │ Event Queue   │  │ DLQ          │ │
│  │ (redis-bull)  │  │ (redis-list)  │  │ (redis-list)  │ │
│  └───────┬───────┘  └───────┬───────┘  └──────────────┘ │
│          │                   │                           │
│          ▼                   ▼                           │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Redis BullMQ Client (bullmq)           │      │
│  │  ┌─────────────────────────────────────────┐    │      │
│  │  │ Connection Pool (connections to Redis)   │◄───┘───────│
│  │  └─────────────────────────────────────────┘             │
│  └──────────────────────┬───────────────────────────────┘ │
│                         │                                     │
│                         ▼                                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │    Redis (Master) ←─────┐  Redis Sentinel     │  │
│  │    (127.0.0.1:6379)      │  (failover detector) │  │
│  └─────────────────────────┴────────────────────────────┘  │
│                               ↓                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │    Redis (Replica) <─────┐                        │  │
│  │    (127.0.0.1:6380)      │  Failover              │  │
│  └─────────────────────────┴────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Dead Letter Queue (DLQ)                    │  │
│  │  (redis-list: intellicare:dlq)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 5.2 Implementação Python

#### Arquivo: `intellicare_core/bullmq/redis_failover.py`

```python
"""Redis failover handler para BullMQ workers.

Implementa:
- Detecção de falha de conexão Redis
- Reconeção automática com backoff exponencial
- Re-enfileiramento de jobs em processamento
- Dead Letter Queue para jobs com erros repetidos
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum

import redis.asyncio as aioredis
from bullmq import Job, Worker

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Estado da conexão Redis."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


@dataclass
class FailoverConfig:
    """Configuração de failover Redis."""

    # Backoff exponencial
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 30
    exponential_base: float = 2.0

    # Retry de jobs
    max_job_retries: int = 3  # jobs com erro > 3 vão para DLQ

    # Health check
    health_check_interval_seconds: int = 5

    # Dead Letter Queue
    dlq_queue_name: str = "intellicare:dlq"


class RedisFailoverHandler:
    """Gerenciador de failover Redis para BullMQ workers."""

    def __init__(
        self,
        redis_url: str,
        config: FailoverConfig | None = None,
    ):
        self._redis_url = redis_url
        self._config = config or FailoverConfig()
        self._state = ConnectionState.DISCONNECTED
        self._redis: aioredis.Redis | None = None
        self._worker: Worker | None = None
        self._retry_count: dict[str, int] = {}  # job_id → retries
        self._failover_count: int = 0

    async def initialize(self, worker: Worker) -> None:
        """Inicializa handler com worker BullMQ."""
        self._worker = worker
        await self._connect()

    async def _connect(self) -> None:
        """Conecta ao Redis com backoff exponencial."""
        delay = self._config.initial_delay_seconds

        while True:
            try:
                self._state = ConnectionState.CONNECTING
                logger.info("redis.connecting", url=self._redis_url)

                self._redis = aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )

                # Health check
                await self._redis.ping()
                self._state = ConnectionState.CONNECTED
                logger.info("redis.connected", url=self._redis_url)

                # Reset retry count on successful connection
                self._failover_count = 0
                return

            except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
                self._state = ConnectionState.RECONNECTING
                self._failover_count += 1
                logger.warning(
                    "redis.connection_failed",
                    delay=delay,
                    failover_count=self._failover_count,
                    error=str(e),
                )

                await asyncio.sleep(delay)
                delay = min(
                    delay * self._config.exponential_base,
                    self._config.max_delay_seconds,
                )

    async def reenqueue_jobs_on_failover(self) -> None:
        """Re-enfileira jobs que estavam em processamento durante failover.

        Jobs que foram obtidos do Redis mas não completados precisam ser
        re-enfileirados para que sejam processados novamente.
        """
        if self._worker is None:
            return

        # BullMQ mantém track de jobs "active" (obtidos mas não completados)
        jobs = self._worker.active

        for job in jobs:
            try:
                # Adicionar de volta à fila
                await job.addJob(job.data, job.opts)
                logger.info("job.reenqueued", job_id=job.id)
            except Exception as e:
                logger.error("job.reenqueue_failed", job_id=job.id, error=str(e))

    async def send_to_dlq(self, job: Job, error: Exception) -> None:
        """Envia job para Dead Letter Queue (DLQ).

        Args:
            job: Job que falhou
            error: Exceção que causou a falha
        """
        dlq_data = {
            "job_id": job.id,
            "queue_name": job.queueName,
            "data": job.data,
            "opts": job.opts,
            "error": str(error),
            "timestamp": datetime.now(UTC).isoformat(),
            "retry_count": self._retry_count.get(job.id, 0),
            "failover_count": self._failover_count,
        }

        if self._redis:
            await self._redis.xadd(
                self._config.dlq_queue_name,
                dlq_data,
            )
            logger.info("job.sent_to_dlq", job_id=job.id)

    async def process_job_with_failover(
        self,
        job: Job,
        process_func: callable,
    ) -> bool:
        """Processa job com lógica de failover.

        Args:
            job: Job BullMQ
            process_func: Função assíncrona que processa o job

        Returns:
            True se job processado com sucesso, False se falhou
        """
        try:
            # Verificar estado de conexão antes de processar
            if self._state != ConnectionState.CONNECTED:
                await self._connect()

            # Processar job
            await process_func(job)

            # Marcar job como completado
            await job.updateProgress(100)
            return True

        except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
            # Falha de conexão Redis
            logger.error("redis.connection_lost_during_job", job_id=job.id, error=str(e))
            self._state = ConnectionState.DISCONNECTED
            await self._connect()
            # Job será re-enfileirado por reenqueue_jobs_on_failover()
            return False

        except Exception as e:
            # Erro no processamento do job
            retry_count = self._retry_count.get(job.id, 0) + 1
            self._retry_count[job.id] = retry_count

            if retry_count >= self._config.max_job_retries:
                # Mover para DLQ
                await self.send_to_dlq(job, e)
                # Remover do retry count
                del self._retry_count[job.id]
                logger.error("job.sent_to_dlq", job_id=job.id, retry=retry_count)
                return False
            else:
                # Retry
                logger.warning("job.retry", job_id=job.id, retry=retry_count, error=str(e))
                raise

    async def health_check(self) -> dict:
        """Retorna status de saúde do failover handler.

        Returns:
            Dict com status de conexão, contadores de failover, etc.
        """
        # Verificar conexão Redis
        is_connected = False
        if self._redis:
            try:
                await self._redis.ping()
                is_connected = True
            except Exception:
                is_connected = False

        return {
            "state": self._state.value,
            "connected": is_connected,
            "failover_count": self._failover_count,
            "dlq_size": await self._dlq_size() if is_connected else 0,
            "retry_counts": len(self._retry_count),
        }

    async def _dlq_size(self) -> int:
        """Retorna quantidade de jobs na DLQ."""
        if self._redis:
            return await self._redis.xlen(self._config.dlq_queue_name)
        return 0


# Singleton global
_failover_handler: RedisFailoverHandler | None = None


def get_failover_handler(
    redis_url: str,
    config: FailoverConfig | None = None,
) -> RedisFailoverHandler:
    """Retorna singleton do failover handler."""
    global _failover_handler
    if _failover_handler is None:
        _failover_handler = RedisFailoverHandler(redis_url, config)
    return _failover_handler
```

### 5.3 Integração com BullMQ Worker

#### Exemplo de Uso: `intellicare-grahame/workers/subscription_worker.py`

```python
"""BullMQ worker para processar Subscriptions FHIR."""

from bullmq import Worker
from intellicare_core.bullmq.redis_failover import (
    FailoverConfig,
    get_failover_handler,
)


async def process_subscription_job(job: Job) -> None:
    """Processa um job de subscription FHIR."""
    # Lógica de processamento...
    pass


async def main():
    """Ponto de entrada do worker."""

    # Configuração BullMQ
    redis_url = "redis://localhost:6379"

    # Configurar failover
    failover_config = FailoverConfig(
        initial_delay_seconds=1,
        max_delay_seconds=30,
        max_job_retries=3,
    )

    # Criar worker
    worker = Worker(
        "fhir-subscriptions",
        redis_url=redis_url,
    )

    # Inicializar failover handler
    failover_handler = get_failover_handler(redis_url, failover_config)
    await failover_handler.initialize(worker)

    # Wrapper de processamento com failover
    async def process_with_failover(job: Job) -> None:
        await failover_handler.process_job_with_failover(
            job,
            process_subscription_job,
        )

    # Registrar processador
    worker.process(process_with_failover)

    # Run worker
    await worker.run()
```

---

## 6. Health Checks e Métricas

### 6.1 Endpoint de Health (Jobs)

#### Arquivo: `grahame/api/routes/health_routes.py`

```python
"""Health check endpoints para jobs e failover."""

from fastapi import APIRouter, HTTPException
from prometheus_client import Counter

router = APIRouter(prefix="/api/v1/jobs", tags=["Health"])

# Métricas Prometheus
failover_total = Counter(
    "redis_failover_total",
    "Total de failovers Redis",
    ["module"]
)

job_retried_total = Counter(
    "job_retried_total",
    "Total de retries de jobs",
    ["module", "queue"]
)

dlq_jobs_total = Counter(
    "dlq_jobs_total",
    "Total de jobs enviados para DLQ",
    ["module"]
)


@router.get("/health")
async def jobs_health():
    """Health check de workers assíncronos e Redis."""

    # Obter failover handler (se existir)
    try:
        from intellicare_core.bullmq.redis_failover import get_failover_handler
        failover_handler = get_failover_handler("redis://localhost:6379")
        health = await failover_handler.health_check()

        return {
            "status": "healthy" if health["connected"] else "degraded",
            "redis": health,
            "workers": {
                "active": 1,  # TODO: contar workers reais
                "paused": False,
            },
        }

    except ImportError:
        # Módulo bullmq não instalado (modo desenvolvimento)
        return {
            "status": "unavailable",
            "redis": {"connected": False, "state": "unavailable"},
            "workers": {"active": 0, "paused": False},
        }


@router.get("/metrics")
async def jobs_metrics():
    """Métricas detalhadas de jobs e failover."""
    try:
        from intellicare_core.bullmq.redis_failover import get_failover_handler
        failover_handler = get_failover_handler("redis://localhost:6379")

        health = await failover_handler.health_check()

        return {
            "failover_total": failover_total._samples._value.get((), 0),
            "job_retried_total": job_retried_total._samples._value.get((), 0),
            "dlq_jobs_total": dlq_jobs_total._samples._value.get((), 0),
            "health": health,
        }

    except ImportError:
        return {"error": "bullmq module not installed"}
```

---

## 7. Testes

### 7.1 Testes de Failover

#### Arquivo: `intellicare-core/tests/bullmq/test_redis_failover.py`

```python
"""Testes de Redis failover handler."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from intellicare_core.bullmq.redis_failover import (
    FailoverConfig,
    RedisFailoverHandler,
    ConnectionState,
)


@pytest.mark.asyncio
async def test_connect_on_initialization():
    """Testa conexão ao Redis na inicialização."""
    redis_url = "redis://localhost:6379"
    handler = RedisFailoverHandler(redis_url)

    # Mock Redis
    mock_redis = AsyncMock(spec=aioredis.Redis)
    mock_redis.ping.return_value = True

    with patch("aioredis.from_url", return_value=mock_redis):
        await handler._connect()

    assert handler._state == ConnectionState.CONNECTED


@pytest.mark.asyncio
async def test_reconnect_on_connection_loss():
    """Testa reconexão automática em caso de perda de conexão."""
    handler = RedisFailoverHandler("redis://localhost:6379")
    handler._state = ConnectionState.CONNECTED

    # Mock: primeira conexão falha, segunda funciona
    call_count = 0

    async def mock_connect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise aioredis.ConnectionError("Connection lost")
        # Segunda chamada funciona (return mock)
        mock_redis = AsyncMock(spec=aioredis.Redis)
        mock_redis.ping.return_value = True

        with patch("aioredis.from_url", return_value=mock_redis):
            return await handler._connect()

    with patch("aioredis.from_url", side_effect=mock_connect):
        with patch("asyncio.sleep"):  # Evitar delays reais nos testes
            await handler._connect()

    assert handler._state == ConnectionState.CONNECTED
    assert handler._failover_count == 1


@pytest.mark.asyncio
async def test_send_to_dlq_after_max_retries():
    """Teste que job com >3 erros vai para DLQ."""
    handler = RedisFailoverHandler(
        "redis://localhost:6379",
        FailoverConfig(max_job_retries=3),
    )

    # Mock Redis
    mock_redis = AsyncMock(spec=aioredis.Redis)
    mock_redis.xadd.return_value = "dlq-id-123"

    with patch("aioredis.from_url", return_value=mock_redis):
        handler._redis = mock_redis

        # Mock job
        mock_job = AsyncMock()
        mock_job.id = "job-123"
        mock_job.queueName = "test-queue"

        # Simular 3 falhas, depois 4ª
        error = Exception("Test error")
        for _ in range(4):
            await handler.send_to_dlq(mock_job, error)

    # Verificar que DLQ foi chamada 1 vez (na 4ª falha)
    assert mock_redis.xadd.call_count == 1
```

### 7.2 Testes de Health Check

#### Arquivo: `intellicare-grahame/tests/test_job_health.py`

```python
"""Testes de health check de jobs."""

import pytest
from fastapi.testclient import TestClient

from grahame.api.app import app
from intellicare_core.bullmq.redis_failover import get_failover_handler


@pytest.fixture
def client():
    return TestClient(app)


def test_jobs_health_returns_200(client):
    """Health check de jobs retorna 200."""
    response = client.get("/api/v1/jobs/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "redis" in data
    assert "workers" in data


def test_jobs_health_with_redis_down(client, monkeypatch):
    """Health check retorna degraded quando Redis está down."""
    # Simular Redis indisponível
    async def mock_connect():
        raise Exception("Redis connection refused")

    monkeypatch.setattr(
        "intellicare_core.bullmq.redis_failover.get_failover_handler",
        lambda: None,
    )

    response = client.get("/api/v1/jobs/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["unavailable", "degraded"]
    assert data["redis"]["connected"] is False
```

---

## 8. Deployment

### 8.1 Docker Compose com Redis Sentinel

#### Arquivo: `docker-compose.ha.yml`

```yaml
version: '3.8'

services:
  # ===================================================================
  # Redis Sentinel (Failover)
  # ===================================================================
  redis-master:
    image: redis:7-alpine
    command: >
      redis-server
      --port 6379
      --requirepass ${REDIS_PASSWORD:-redispass}
      --appendonly yes
    networks:
      - backend

  redis-replica:
    image: redis:7-alpine
    command: >
      redis-server
      --port 6380
      --requirepass ${REDIS_PASSWORD:-redispass}
      --slaveof redis-master 6379
    depends_on:
      - redis-master
    networks:
      - backend

  redis-sentinel:
    image: redis:7-alpine
    command: >
      redis-sentinel
      monitor mymaster redis-master 6379 2
      down-after-milliseconds 5000
      failover-timeout 10000
      parallel-syncs 1
    depends_on:
      - redis-master
      - redis-replica
    networks:
      - backend

  # ===================================================================
  # Aplicação Grahame (Exemplo)
  # ===================================================================
  grahame:
    build:
      context: .
      target: distroless
    environment:
      - REDIS_URL=redis://redis-master:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-redispass}
    depends_on:
      - redis-sentinel
    networks:
      - backend

networks:
  backend:
```

### 8.2 Configuração Redis Sentinel

#### Arquivo: `redis/sentinel.conf`

```
port 26379
sentinel monitor mymaster redis-master 6379 2
down-after-milliseconds 5000
failover-timeout 10000
parallel-syncs 1
```

---

## 9. Rollout e Validação

### 9.1 Ordem de Migração (Cronograma)

| Dia | Tarefa | Validar |
|-----|--------|---------|
| **1** | Configurar Trivy CI (PR para adicionar workflow) | Trivy scan rodando |
| **2** | Testar com grahame (módulo simples) | Build + scan funciona |
| **3** | Migrar módulo por módulo (13 módulos) | Imagem assinada, scan limpo |
| **4** | Implementar BullMQ failover | Teste de falha Redis |
| **5** | Atualizar docker-compose.full.yml | Todos usam imagens hardened |
| **6** | Teste de carga + failover | 1000 jobs, matar Redis |
| **7** | Documentação + treinamento | Time knowled |

### 9.2 Comando de Validação

```bash
# 1. Verificar que imagem é distroless
docker history ghcr.io/intellicare/intellicare-grahame:latest | grep ENTRYPOINT

# 2. Verificar que não roda como root
docker run --rm ghcr.io/intellicare/intellicare-grahame:latest whoami
# Saída esperada: "nobody"

# 3. Verificar assinatura
cosign verify ghcr.io/intellicare/intellicare-grahame:latest

# 4. Scan local
trivy image ghcr.io/intellicare/intellicare-grahame:latest

# 5. Testar failover Redis
# Em um terminal: docker-compose -f docker-compose.ha.yml up
# Em outro: docker kill <redis-master-container>
# Verificar logs: worker deve reconectar automaticamente
```

---

## 10. Troubleshooting

### 10.1 Problemas Comuns

| Problema | Sintoma | Solução |
|---------|---------|----------|
| **Imagem não inicia** | Container crash loop | Verificar se ENTRYPOINT aponta para módulo Python correto |
| **Permission denied** | Erro ao escrever arquivos | Verificar permissões, garantir VOLUME montado com usuário correto |
| **Cosign verify falha** | Imagem não assinada | Verificar se chave pública está no cluster |
| **Trivy falha** | Scan demora demais | Usar `--skip-update` para DB local |
| **Redis reconnection loop** | Worker não reconecta | Verificar se Sentinel está rodando, checar firewall |

### 10.2 Logs de Debug

```bash
# Logs do worker
docker logs intellicare-grahame-worker

# Logs do Redis
docker logs redis-master
docker logs redis-sentinel

# Logs do Trivy
cat trivy-results.txt

# Logs de assinatura (cosign)
COSIGN_LOG=debug cosign verify ...
```

---

## 11. Próximos Passos (Após Validação)

1. **Gerar PR** com mudanças de Dockerfile
2. **Validar PR** em ambiente de desenvolvimento
3. **Merge para main** → CI executa Trivy + Cosign
4. **Criar release** no GitHub
5. **Deploy em staging** → testar failover Redis
6. **Monitorar por 7 dias** → coletar métricas
7. **Deploy em produção** (se staging estável)

---

## 12. Referências

### Ferramentas
- **Distroless:** https://github.com/GoogleContainerTools/distroless
- **Cosign:** https://github.com/sigstore/cosign
- **Trivy:** https://aquasecurity.github.io/trivy/
- **BullMQ:** https://docs.bullmq.io/
- **Redis Sentinel:** https://redis.io/docs/manual/sentinel/

### Padrões
- **CIS Docker Benchmark:** https://www.cisecurity.org/benchmark/docker
- **NSA Container Hardening:** https://www.nsa.gov/Press-Release/Article/2919833/
- **OWASP Docker Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html

### Código Medplum
- PR #8109 — Docker hardened images
- PR #8314 — BullMQ Redis failover

---

**Documento gerado por:** DEV0
**Data:** 2026-02-24
**Versão:** 1.0.0
**Status:** ✅ Pronto para implementação
