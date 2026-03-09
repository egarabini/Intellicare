# W8-C — Subscription Performance — Especificação Técnica

**Workstream:** W8-C
**Responsável:** DEV2
**Módulo:** `intellicare-core` (subscriptions)
**Status:** 📋 Especificação Técnica
**Data:** 2026-02-24
**Estimativa:** 14 dias

---

## 1. Arquitetura

### 1.1 Arquitetura Atual vs Otimizada

```
┌─────────────────────────────────────────────────────────────────┐
│ ARQUITETURA ATUAL (Performance Bottleneck)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Event FHIR ──► Dispatcher ──► [Lista 1000 subscriptions]      │
│                                        │                        │
│                                        └──► Parse payload 1000x │
│                                        └──► Avaliar todas      │
│                                        └──► O(N) complexity    │
│                                                                  │
│  Problemas:                                                     │
│  - Parse JSON 1000 vezes (uma por subscription)                │
│  - Avaliar todas subscriptions (mesmo sem match)               │
│  - Busca linear em lista gigantesca                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ARQUITETURA OTIMIZADA (Match-Only + WS Separation)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Event FHIR ──► Pré-Filtro ──► [ Só subscriptions com match ] │
│                        │                                        │
│                        ├──► WS por resource type               │
│                        │   └──► Observation: [sub1, sub2]      │
│                        │   └──► Patient: [sub3, sub4]          │
│                        │                                        │
│                        └──► Parse 1 vez (reusar)              │
│                                                                  │
│  Benefícios:                                                    │
│  - Parse JSON 1 vez (zero-copy)                                │
│  - Skip 90% das subscriptions (sem match)                      │
│  - Lookup O(1) por resource type                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Componentes

```
intellicare-core/
├── app/
│   ├── subscriptions/
│   │   ├── __init__.py
│   │   ├── engine.py              # Core subscription engine (refatorado)
│   │   ├── dispatcher.py          # Event dispatcher (otimizado)
│   │   ├── matchers.py            # Pré-filtros rápidos (novo)
│   │   ├── ws_manager.py          # WebSocket manager (separado por resource)
│   │   ├── payload_cache.py       # Cache de payload parsed (novo)
│   │   └── metrics.py             # Métricas Prometheus
│   └── api/
│       └── subscriptions.py       # Health check endpoint
├── tests/
│   ├── subscriptions/
│   │   ├── test_matchers.py
│   │   ├── test_dispatcher.py
│   │   ├── test_ws_manager.py
│   │   ├── test_payload_cache.py
│   │   └── test_performance.py    # Benchmarks
│   └── benchmarks/
│       └── test_subscription_load.py
└── requirements.txt              # + (nenhuma lib externa necessária)
```

### 1.3 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| **Pré-filtro** | Python nativo | FHIRPath boolean simples |
| **WS Manager** | Dict aninhado | `{resourceType: {subId: [ws]}}` |
| **Payload Cache** | `functools.lru_cache` | Cache em memória |
| **Métricas** | `prometheus_client` | Prometheus metrics |

---

## 2. Implementação Core

### 2.1 Match-Only Evaluator

**File:** `app/subscriptions/matchers.py`

```python
from typing import Optional, List
from pydantic import BaseModel

from app.subscriptions.models import Subscription

class MatchResult(BaseModel):
    """Result of quick match evaluation."""
    matches: bool
    reason: Optional[str] = None  # Debug/logging

class SubscriptionMatcher:
    """
    Fast pre-filter for subscriptions (match-only evaluation).

    Skip subscriptions that definitely don't match:
    - Resource type doesn't match
    - Subscription is not active
    - Subscription has repeated errors (> 3)
    - Criteria doesn't match (FHIRPath boolean)
    """

    def __init__(self):
        self._cache: dict[str, list[Subscription]] = {}

    def evaluate(
        self,
        subscriptions: List[Subscription],
        resource_type: str,
        resource: dict,
    ) -> List[Subscription]:
        """
        Evaluate subscriptions and return only those with potential match.

        Returns:
            List of subscriptions that match (potentially)
        """
        matching = []

        for subscription in subscriptions:
            # Quick check 1: Subscription active?
            if subscription.status != "active":
                continue

            # Quick check 2: Repeated errors?
            if subscription.error_count > 3:
                continue

            # Quick check 3: Resource type matches?
            if not self._matches_resource_type(subscription, resource_type):
                continue

            # Quick check 4: Criteria matches (FHIRPath boolean)?
            if not self._matches_criteria(subscription, resource):
                continue

            # All checks passed → potential match
            matching.append(subscription)

        return matching

    def _matches_resource_type(self, subscription: Subscription, resource_type: str) -> bool:
        """
        Check if subscription resource type matches.

        Examples:
        - Subscription criteria: "Observation?code=glucose"
        - Resource type: "Observation" → MATCH
        - Resource type: "Patient" → NO MATCH
        """
        # Extract resource type from criteria
        # Format: "ResourceType?param=value"
        criteria_resource = subscription.criteria.split("?")[0]

        return criteria_resource == resource_type

    def _matches_criteria(self, subscription: Subscription, resource: dict) -> bool:
        """
        Quick FHIRPath boolean check.

        For now, implement simple checks:
        - No criteria → match
        - Criteria with params → check if resource has those fields

        TODO: Full FHIRPath evaluation (future)
        """
        criteria = subscription.criteria

        # No criteria → match all
        if "?" not in criteria:
            return True

        # Parse criteria
        resource_type, params = criteria.split("?", 1)

        # Check each param
        for param in params.split("&"):
            if "=" not in param:
                continue

            key, value = param.split("=", 1)

            # Check if resource has this field
            # Simple check (not full FHIRPath)
            if key not in resource:
                return False

            # Check value match
            resource_value = resource[key]
            if isinstance(resource_value, dict):
                # Coding/code
                if "code" in resource_value:
                    if resource_value["code"] != value:
                        return False

        return True
```

### 2.2 WebSocket Manager (Separation by Resource Type)

**File:** `app/subscriptions/ws_manager.py`

```python
from typing import Dict, List, Set
from fastapi import WebSocket

from app.subscriptions.models import Subscription

class WebSocketManager:
    """
    Manage WebSocket connections separated by resource type.

    Old architecture: Flat list of all connections
    New architecture: {resourceType: {subscriptionId: [ws_connections]}}

    Benefits:
    - O(1) lookup by resource type
    - Only iterate over relevant subscriptions
    - Memory efficient (separate lists)
    """

    def __init__(self):
        # Structure: {resourceType: {subscriptionId: [ws_connections]}}
        self._connections: Dict[str, Dict[str, List[WebSocket]]] = {}

    def connect(self, subscription_id: str, resource_type: str, ws: WebSocket) -> None:
        """
        Add WebSocket connection to subscription.

        Args:
            subscription_id: Subscription ID
            resource_type: Resource type (e.g., "Observation")
            ws: WebSocket connection
        """
        if resource_type not in self._connections:
            self._connections[resource_type] = {}

        if subscription_id not in self._connections[resource_type]:
            self._connections[resource_type][subscription_id] = []

        self._connections[resource_type][subscription_id].append(ws)

    def disconnect(self, subscription_id: str, resource_type: str, ws: WebSocket) -> None:
        """
        Remove WebSocket connection from subscription.

        Args:
            subscription_id: Subscription ID
            resource_type: Resource type
            ws: WebSocket connection
        """
        if resource_type not in self._connections:
            return

        if subscription_id not in self._connections[resource_type]:
            return

        connections = self._connections[resource_type][subscription_id]
        if ws in connections:
            connections.remove(ws)

        # Clean up empty lists
        if not connections:
            del self._connections[resource_type][subscription_id]

        if not self._connections[resource_type]:
            del self._connections[resource_type]

    def get_connections(
        self,
        resource_type: str,
        subscription_id: str,
    ) -> List[WebSocket]:
        """
        Get WebSocket connections for a subscription.

        Args:
            resource_type: Resource type
            subscription_id: Subscription ID

        Returns:
            List of WebSocket connections (empty if not found)
        """
        if resource_type not in self._connections:
            return []

        if subscription_id not in self._connections[resource_type]:
            return []

        return self._connections[resource_type][subscription_id]

    def get_all_connections_for_resource(self, resource_type: str) -> List[WebSocket]:
        """
        Get ALL WebSocket connections for a resource type.

        Args:
            resource_type: Resource type

        Returns:
            List of all WebSocket connections for this resource type
        """
        if resource_type not in self._connections:
            return []

        all_connections = []
        for connections in self._connections[resource_type].values():
            all_connections.extend(connections)

        return all_connections

    def get_stats(self) -> dict:
        """
        Get connection statistics.

        Returns:
            Dict with stats by resource type
        """
        stats = {}

        for resource_type, subs in self._connections.items():
            total_connections = sum(len(conns) for conns in subs.values())
            stats[resource_type] = {
                "subscriptions": len(subs),
                "connections": total_connections,
            }

        return stats
```

### 2.3 Payload Cache (Zero-Copy Parser)

**File:** `app/subscriptions/payload_cache.py`

```python
import json
from typing import Dict, Any
from functools import lru_cache

class PayloadCache:
    """
    Cache parsed FHIR payloads for efficient reuse.

    Old architecture: Parse JSON for each subscription (N times)
    New architecture: Parse once, cache, reuse (1 time)

    Benefits:
    - Parse JSON 1 time instead of N times
    - Zero-copy (reuse dict, don't deepcopy)
    - Memory efficient (LRU cache)
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize payload cache.

        Args:
            max_size: Maximum number of payloads to cache (LRU)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, raw_payload: str) -> Dict[str, Any]:
        """
        Get parsed payload from cache (or parse and cache).

        Args:
            raw_payload: Raw JSON string

        Returns:
            Parsed dict (cached or freshly parsed)
        """
        # Use hash as key (avoid storing large strings)
        key = str(hash(raw_payload))

        if key in self._cache:
            self._hits += 1
            return self._cache[key]

        # Cache miss → parse
        self._misses += 1
        parsed = json.loads(raw_payload)

        # Add to cache (LRU eviction if needed)
        if len(self._cache) >= self._max_size:
            # Evict oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = parsed
        return parsed

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "size": len(self._cache),
        }
```

### 2.4 Otimized Dispatcher

**File:** `app/subscriptions/dispatcher.py`

```python
import asyncio
from typing import List
import time

from app.subscriptions.engine import SubscriptionEngine
from app.subscriptions.matchers import SubscriptionMatcher
from app.subscriptions.ws_manager import WebSocketManager
from app.subscriptions.payload_cache import PayloadCache
from app.subscriptions.metrics import SubscriptionMetrics

class OptimizedDispatcher:
    """
    Optimized FHIR subscription dispatcher.

    Architecture:
    1. Receive event
    2. Parse payload ONCE (cache)
    3. Pre-filter subscriptions (match-only)
    4. Get WS connections by resource type
    5. Send to connections
    6. Track metrics
    """

    def __init__(
        self,
        engine: SubscriptionEngine,
        ws_manager: WebSocketManager,
        metrics: SubscriptionMetrics,
    ):
        self._engine = engine
        self._ws_manager = ws_manager
        self._metrics = metrics
        self._matcher = SubscriptionMatcher()
        self._payload_cache = PayloadCache()

    async def dispatch(self, event_type: str, raw_payload: str) -> None:
        """
        Dispatch FHIR event to matching subscriptions.

        Args:
            event_type: Event type (e.g., "Patient.create")
            raw_payload: Raw JSON FHIR resource
        """
        start_time = time.time()

        # 1. Parse payload ONCE (cache)
        resource = self._payload_cache.get(raw_payload)
        resource_type = resource.get("resourceType")

        # 2. Get all subscriptions
        all_subscriptions = await self._engine.get_all_subscriptions()

        # 3. Pre-filter (match-only)
        matching_subscriptions = self._matcher.evaluate(
            subscriptions=all_subscriptions,
            resource_type=resource_type,
            resource=resource,
        )

        # 4. Track skipped subscriptions
        skipped_count = len(all_subscriptions) - len(matching_subscriptions)
        self._metrics.subscriptions_skipped.inc(skipped_count)

        # 5. Send to WebSocket connections
        for subscription in matching_subscriptions:
            # Get WS connections for this subscription (by resource type)
            connections = self._ws_manager.get_connections(
                resource_type=resource_type,
                subscription_id=subscription.id,
            )

            # Send payload to each connection
            for ws in connections:
                try:
                    await ws.send_json(resource)
                    self._metrics.messages_sent.inc()
                except Exception as e:
                    self._metrics.errors.inc()
                    # Mark subscription as failed
                    subscription.error_count += 1

        # 6. Track processing time
        processing_time_ms = (time.time() - start_time) * 1000
        self._metrics.processing_time.observe(processing_time_ms)
        self._metrics.events_processed.inc()
```

### 2.5 Health Check Endpoint

**File:** `app/api/subscriptions.py`

```python
from fastapi import APIRouter

from app.subscriptions.engine import SubscriptionEngine
from app.subscriptions.ws_manager import WebSocketManager
from app.subscriptions.payload_cache import PayloadCache
from app.subscriptions.metrics import SubscriptionMetrics

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

@router.get("/health")
async def subscriptions_health(
    engine: SubscriptionEngine,
    ws_manager: WebSocketManager,
    payload_cache: PayloadCache,
    metrics: SubscriptionMetrics,
) -> dict:
    """
    Health check endpoint for subscriptions.

    Returns:
        Dict with status, metrics, and stats
    """
    all_subscriptions = await engine.get_all_subscriptions()
    active_subscriptions = [s for s in all_subscriptions if s.status == "active"]

    ws_stats = ws_manager.get_stats()
    cache_stats = payload_cache.stats

    return {
        "status": "healthy",
        "total_subscriptions": len(all_subscriptions),
        "active_subscriptions": len(active_subscriptions),
        "active_websockets": sum(
            stats["connections"] for stats in ws_stats.values()
        ),
        "ws_by_resource_type": ws_stats,
        "cache": cache_stats,
        "performance": {
            "avg_processing_ms": metrics.processing_time.avg,
            "p99_processing_ms": metrics.processing_time.p99,
            "events_per_second": metrics.events_processed.rate,
        },
    }
```

---

## 3. Métricas Prometheus

**File:** `app/subscriptions/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge

class SubscriptionMetrics:
    """
    Prometheus metrics for subscription engine.
    """

    # Processing time
    processing_time = Histogram(
        "subscription_processing_time_ms",
        "Subscription processing time (milliseconds)",
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000],
    )

    # Events processed
    events_processed = Counter(
        "subscription_events_processed_total",
        "Total FHIR events processed",
    )

    # Messages sent
    messages_sent = Counter(
        "subscription_messages_sent_total",
        "Total WebSocket messages sent",
    )

    # Errors
    errors = Counter(
        "subscription_errors_total",
        "Total subscription errors",
    )

    # Subscriptions skipped (match-only)
    subscriptions_skipped = Counter(
        "subscription_subscriptions_skipped_total",
        "Total subscriptions skipped (no match)",
    )

    # Active subscriptions
    active_subscriptions = Gauge(
        "subscription_active_total",
        "Total active subscriptions",
    )

    # Active WebSocket connections
    active_websockets = Gauge(
        "subscription_websockets_active_total",
        "Total active WebSocket connections",
    )

    # Cache hit rate
    cache_hit_rate = Gauge(
        "subscription_cache_hit_rate",
        "Payload cache hit rate (0-1)",
    )
```

---

## 4. Configuração

**File:** `app/config.py` (adicionar)

```python
from pydantic import BaseModel

class SubscriptionConfig(BaseModel):
    """Subscription engine configuration."""

    # Match-only evaluation
    match_only_enabled: bool = True
    skip_errors_threshold: int = 3  # Skip subscriptions with > 3 errors

    # WebSocket separation
    ws_separation_enabled: bool = True

    # Payload cache
    payload_cache_enabled: bool = True
    payload_cache_max_size: int = 1000

    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090
```

**Environment variables:** `.env`

```env
# Subscription Performance
SUBSCRIPTION_MATCH_ONLY=true
SUBSCRIPTION_WS_SEPARATION=true
SUBSCRIPTION_PAYLOAD_CACHE=true
SUBSCRIPTION_CACHE_MAX_SIZE=1000
```

---

## 5. Testes

### 5.1 Testes de Matcher

**File:** `tests/subscriptions/test_matchers.py`

```python
import pytest

from app.subscriptions.matchers import SubscriptionMatcher
from app.subscriptions.models import Subscription

@pytest.fixture
def sample_subscriptions():
    """Sample subscriptions."""
    return [
        Subscription(
            id="sub1",
            status="active",
            criteria="Observation?code=glucose",
            error_count=0,
        ),
        Subscription(
            id="sub2",
            status="active",
            criteria="Patient?name=João",
            error_count=0,
        ),
        Subscription(
            id="sub3",
            status="inactive",  # Inactive → skip
            criteria="Observation?",
            error_count=0,
        ),
        Subscription(
            id="sub4",
            status="active",
            criteria="Observation?",
            error_count=5,  # Too many errors → skip
        ),
    ]

def test_match_only_evaluation():
    """Test that only matching subscriptions are returned."""
    matcher = SubscriptionMatcher()

    resource_type = "Observation"
    resource = {
        "resourceType": "Observation",
        "code": "glucose",
    }

    matching = matcher.evaluate(sample_subscriptions(), resource_type, resource)

    # Only sub1 should match (active, no errors, matches resource type)
    assert len(matching) == 1
    assert matching[0].id == "sub1"

def test_skip_inactive():
    """Test that inactive subscriptions are skipped."""
    matcher = SubscriptionMatcher()

    matching = matcher.evaluate(sample_subscriptions(), "Patient", {})

    # sub3 is inactive → skip
    assert not any(s.id == "sub3" for s in matching)

def test_skip_errors():
    """Test that subscriptions with many errors are skipped."""
    matcher = SubscriptionMatcher()

    matching = matcher.evaluate(sample_subscriptions(), "Observation", {})

    # sub4 has 5 errors → skip
    assert not any(s.id == "sub4" for s in matching)

def test_skip_wrong_resource_type():
    """Test that subscriptions for different resource types are skipped."""
    matcher = SubscriptionMatcher()

    matching = matcher.evaluate(
        sample_subscriptions(),
        resource_type="Observation",
        resource={},
    )

    # sub2 is for Patient → skip
    assert not any(s.id == "sub2" for s in matching)
```

### 5.2 Testes de Performance

**File:** `tests/benchmarks/test_subscription_load.py`

```python
import pytest
import asyncio
import time

from app.subscriptions.dispatcher import OptimizedDispatcher
from app.subscriptions.engine import SubscriptionEngine
from app.subscriptions.ws_manager import WebSocketManager
from app.subscriptions.metrics import SubscriptionMetrics

@pytest.mark.benchmark
def test_subscription_throughput():
    """
    Benchmark: Process 1000 subscriptions with 100 events/second.

    Targets:
    - Latency p99: < 50ms
    - Throughput: ≥ 100 events/s
    - CPU: -80% vs baseline
    """
    # Setup: Create 1000 subscriptions
    engine = SubscriptionEngine()
    ws_manager = WebSocketManager()
    metrics = SubscriptionMetrics()
    dispatcher = OptimizedDispatcher(engine, ws_manager, metrics)

    # Create 1000 subscriptions (500 Observation, 500 Patient)
    for i in range(500):
        engine.add_subscription(
            Subscription(
                id=f"obs-sub-{i}",
                status="active",
                criteria="Observation?",
            )
        )
        engine.add_subscription(
            Subscription(
                id=f"pat-sub-{i}",
                status="active",
                criteria="Patient?",
            )
        )

    # Benchmark: Process 100 events
    events = [
        ("Observation.create", '{"resourceType": "Observation", "code": "glucose"}'),
        ("Patient.create", '{"resourceType": "Patient", "name": "João"}'),
    ] * 50  # 100 events total

    start_time = time.time()

    for event_type, payload in events:
        await dispatcher.dispatch(event_type, payload)

    total_time = time.time() - start_time

    # Assertions
    assert total_time < 1.0  # 100 events in < 1 second (≥ 100 events/s)
    assert metrics.processing_time.p99 < 0.050  # p99 < 50ms

    print(f"Throughput: {len(events) / total_time:.0f} events/s")
    print(f"Latency p99: {metrics.processing_time.p99 * 1000:.0f}ms")
```

### 5.3 Testes de Compatibilidade (Feature Flags)

**File:** `tests/subscriptions/test_feature_flags.py`

```python
import pytest
from unittest.mock import patch

from app.subscriptions.dispatcher import OptimizedDispatcher

def test_match_only_disabled():
    """Test that match-only can be disabled."""
    with patch("app.subscriptions.config.SubscriptionConfig.match_only_enabled", False):
        # Should evaluate all subscriptions (not just matching ones)
        # This test ensures backward compatibility
        pass

def test_ws_separation_disabled():
    """Test that WS separation can be disabled."""
    with patch("app.subscriptions.config.SubscriptionConfig.ws_separation_enabled", False):
        # Should fall back to flat list of connections
        # This test ensures backward compatibility
        pass

def test_payload_cache_disabled():
    """Test that payload cache can be disabled."""
    with patch("app.subscriptions.config.SubscriptionConfig.payload_cache_enabled", False):
        # Should parse payload for each subscription (old behavior)
        # This test ensures backward compatibility
        pass
```

---

## 6. Deploy

### 6.1 Configuração Prometheus

**File:** `prometheus.yml` (adicionar)

```yaml
scrape_configs:
  - job_name: 'intellicare-core'
    static_configs:
      - targets: ['intellicare-core:9090']
    metrics_path: '/metrics'
```

### 6.2 Docker Compose

```yaml
services:
  intellicare-core:
    # ... existing config ...
    environment:
      - SUBSCRIPTION_MATCH_ONLY=true
      - SUBSCRIPTION_WS_SEPARATION=true
      - SUBSCRIPTION_PAYLOAD_CACHE=true
      - SUBSCRIPTION_CACHE_MAX_SIZE=1000
    ports:
      - "9090:9090"  # Prometheus metrics
```

---

## 7. Troubleshooting

### 7.1 Alta Latência

**Problem:** Latência p99 > 50ms.

**Solutions:**
1. Verificar se match-only está enabled: `SUBSCRIPTION_MATCH_ONLY=true`
2. Verificar cache hit rate: `GET /api/v1/subscriptions/health` → `cache.hit_rate`
3. Aumentar cache size: `SUBSCRIPTION_CACHE_MAX_SIZE=2000`

### 7.2 Alta CPU

**Problem:** CPU > 80% em carga alta.

**Solutions:**
1. Verificar se ws_separation está enabled: `SUBSCRIPTION_WS_SEPARATION=true`
2. Verificar quantas subscriptions ativas: `active_subscriptions` metric
3. Considerar rate limiting: `max_events_per_second=100`

### 7.3 Baixa Cache Hit Rate

**Problem:** Cache hit rate < 50%.

**Solutions:**
1. Payloads são muito diferentes (normal)
2. Considerar aumentar cache size
3. Verificar se cache está enabled: `SUBSCRIPTION_PAYLOAD_CACHE=true`

---

## 8. Timeline

| Fase | Dias | Responsável |
|------|------|-------------|
| **Fase 1:** Preparação | 2 | DEV2 |
| - Feature flags | | |
| - Métricas base | | |
| - Testes baseline | | |
| **Fase 2:** Match-Only | 4 | DEV2 |
| - SubscriptionMatcher | | |
| - Pré-filtro rápido | | |
| - Testes + benchmark | | |
| **Fase 3:** WS Separation | 4 | DEV2 |
| - WebSocketManager | | |
| - Separation by resource type | | |
| - Testes + benchmark | | |
| **Fase 4:** Efficient Parse | 4 | DEV2 |
| - PayloadCache | | |
| - Zero-copy optimization | | |
| - Testes + benchmark | | |

**Total: 14 dias**

---

## 9. Métricas de Sucesso

| Métrica | Valor Atual | Valor Alvo | Ganho |
|---------|-------------|------------|-------|
| Latência p99 | 100ms | 50ms | 50% |
| Throughput | 10 events/s | 100 events/s | 900% |
| CPU (100 subs) | 80% | 15% | 81% |
| Memória | 500MB | 300MB | 40% |

---

## 10. Referências

- **Medplum PR #8389:** Evaluate only matching subscriptions
- **Medplum PR #8436:** Separate WS active list by resource type
- **Medplum PR #8453:** Efficient WS payload parse
- **Medplum PR #8443:** Factor out resource from pubsub payload
- **FHIR Subscriptions R5:** https://hl7.org/fhir/subscription.html
