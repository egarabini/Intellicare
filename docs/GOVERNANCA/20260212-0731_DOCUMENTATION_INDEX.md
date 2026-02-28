# IntellICare Documentation Index

📋 **Central Hub for All Project Documentation**  
Last Updated: Post FASE 2.4.1 | Status: ✅ Complete  

---

## Quick Navigation

### 📊 Progress & Status
- **[Progress Report FASE 2.4.1](./PROGRESS_REPORT_FASE_2_4_1.md)** - Complete project status (67,814 LOC, 127+ tests)
- **[Phase Summaries](#phase-completion-status)** - Quick overview of all completed phases

### 🏗️ Architecture & Design
- **[Consolidation Pattern](./intellicare-donabedian/FASE_2_4_1_EXPAND_DONABEDIAN.md)** - Data flow, Redis → PostgreSQL
- **[Data Schema Design](#database-schema)** - operacional vs analitico schemas
- **[Module Architecture Pattern](#module-architecture-pattern)** - Template for new modules

### 💻 Implementation Guides
- **[Core Infrastructure](./intellicare-core/README.md)** - BaseDAO, EventPublisher, migrations
- **[Donabedian Module](#donabedian-module-guide)** - Ready-to-replicate template
- **[Setting Up Local Environment](#local-setup)** - Docker, venv, dependencies

### 🧪 Testing
- **[Running Tests](#testing)** - Pytest commands, fixtures, expected output
- **[Test Coverage](#test-coverage)** - 127+ tests across all phases
- **[Fixtures & Mocking](#fixtures)** - Async fixtures, database setup/teardown

### 📚 FASE Documentation
1. **[FASE 1: Core Infrastructure](#fase-1-core-infrastructure)** ✅ COMPLETE
2. **[FASE 2.1: Donabedian Module](#fase-21-donabedian-module)** ✅ COMPLETE
3. **[FASE 2.2: Event Publishing](#fase-22-event-publishing)** ✅ COMPLETE
4. **[FASE 2.3: Pilar Consolidation](#fase-23-pilar-consolidation)** ✅ COMPLETE
5. **[FASE 2.4.1: Expand Donabedian](#fase-241-expand-donabedian)** ✅ COMPLETE (NEW)
6. **[FASE 2.5+: Module Replication](#fase-25-module-replication)** 🟡 Next

---

## Phase Completion Status

### FASE 1: Core Infrastructure ✅
**Status**: Complete (5,802 LOC, 77+ tests)

**Components**:
- BaseDAO pattern (IBaseDAO interface + 2 implementations)
- EventPublisher service (Redis Streams integration)
- 5 Alembic migrations (schemas, tables, indexes)
- Docker Compose environment (PostgreSQL, Redis, PgAdmin)

**Location**: `intellicare-core/`

**Key Files**:
- `intellicare_core/data_access/base.py` - BaseDAO interface & implementations
- `intellicare_core/events/publisher.py` - EventPublisher service
- `migrations/versions/` - All 5 migrations
- `docker-compose.yml` - Infrastructure stack

**Testing**:
```bash
# Run FASE 1 tests
pytest intellicare-core/tests/ -v -s
```

---

### FASE 2.1: Donabedian Module ✅
**Status**: Complete (1,612 LOC, 25+ tests)

**Components**:
- 4 Entity Models (Pilar, Indicator, Measurement, DonabedianConfig)
- Data Access Layer (3 DAO classes)
- 18 API Endpoints (CRUD operations)
- Pydantic Schemas (validation + serialization)

**Location**: `intellicare-donabedian/`

**Key Files**:
- `src/donabedian/models/` - Entity definitions
- `src/donabedian/data_access/` - DAO classes
- `src/donabedian/api/routes/` - FastAPI endpoints
- `migrations/versions/005_create_donabedian_schemas.py` - Database setup

**Testing**:
```bash
# Run FASE 2.1 tests
pytest intellicare-donabedian/tests/test_e2e_donabedian.py -v -s
```

---

### FASE 2.2: Event Publishing ✅
**Status**: Complete (940 LOC, 10+ tests)

**Components**:
- EventPublisher service (CREATE/UPDATE/DELETE events)
- Keycloak integration (28 endpoints protected)
- PilarService example (pattern + code)
- Role-based access control (5 roles, 5 test users)

**Location**: `intellicare-donabedian/src/donabedian/services/`

**Key Files**:
- `services/pilar_service.py` - Event publishing example
- `api/app.py` - Keycloak setup
- `tests/test_event_publishing.py` - Event validation tests

**Keycloak Users**:
- admin / admin123 (realm admin)
- dev1-pilar / dev1123 (pilar manager)
- analyst1 / analyst123 (read-only)
- etc.

**Testing**:
```bash
# Run FASE 2.2 tests
pytest intellicare-donabedian/tests/test_event_publishing.py -v -s
```

---

### FASE 2.3: Pilar Consolidation ✅
**Status**: Complete (750+ LOC, 6 tests)

**Components**:
- DonabedianConsolidationService (3 methods: create/update/delete)
- DonabedianConsolidationConsumer (Redis XREADGROUP)
- Consumer groups (fault tolerance + persistence)
- E2E consolidation tests

**Location**: `intellicare-donabedian/src/donabedian/consolidation/`

**Key Files**:
- `consolidation/service.py` - Consolidation logic (SELECT → UPSERT)
- `consolidation/worker.py` - Redis consumer (XREADGROUP, batch-100)
- `consolidation/test_consolidation.py` - 6 E2E tests

**Consolidation Flow**:
```
operacional.pilares (WRITE) 
  → EventPublisher fires
  → Redis Stream: intellicare:donabedian:pilar.{create|update|delete}
  → DonabedianConsolidationConsumer (XREADGROUP)
  → consolidate_pilar_create/update/delete()
  → analitico.pilar (READ-OPTIMIZED)
  → consolidated_at = NOW()
  → consolidation_source = pilar.CREATE/UPDATE/DELETE
```

**Testing**:
```bash
# Run FASE 2.3 tests
pytest intellicare-donabedian/src/donabedian/consolidation/test_consolidation.py::TestConsolidationConsumer::test_pilar_create_event_consolidation -v -s
```

---

### FASE 2.4.1: Expand Donabedian ✅
**Status**: Complete (1,600+ LOC, 9+ tests)

**New Components**:
- 6 new consolidation methods (Indicator + Measurement)
- 2 new event processors (indicator + measurement)
- 9 new test cases (3 per entity type + full pipeline)
- 9 Redis streams (was 3, now all entity types covered)

**Location**: `intellicare-donabedian/src/donabedian/consolidation/`

**Key Changes**:
- `service.py`: +800 LOC (indicator & measurement methods)
- `worker.py`: +200 LOC (event processors added)
- `test_consolidation.py`: +600 LOC (9 new tests)

**New Streams Monitored**:
```
intellicare:donabedian:indicator.create/update/delete
intellicare:donabedian:measurement.create/update/delete
```

**Testing**:
```bash
# Run all FASE 2.4.1 tests
pytest intellicare-donabedian/src/donabedian/consolidation/test_consolidation.py -v -s

# Run full pipeline test
pytest intellicare-donabedian/src/donabedian/consolidation/test_consolidation.py::TestConsolidationConsumer::test_full_pipeline_three_entities -v -s
```

**Key Deliverable**: 
📄 **[FASE_2_4_1_EXPAND_DONABEDIAN.md](./intellicare-donabedian/FASE_2_4_1_EXPAND_DONABEDIAN.md)** - Complete technical documentation

---

### FASE 2.5: Module Replication (NEXT)
**Status**: 🟡 Planning

**Scope**: Replicate Donabedian consolidation pattern to 7 remaining modules

**Modules**:
1. Florence (Clinical Analyzer) → LabAnalysisResult consolidation
2. Oswaldo (Patient Management) → PatientProfile consolidation
3. Zilda (Epidemiology) → EpidemioData consolidation
4. Geralda (Clinical Notes) → ClinicalNote consolidation
5. Comunicacao (Messaging) → Message consolidation
6. Auth (Authentication) → AuthLog consolidation
7. Portal (Dashboard) → ContentMetric consolidation
8. Wanda (AI) → AIResponse consolidation

**Estimated Time**: 24-30 hours (~3.5h per module)

**Process**:
1. Identify main consolidation entity for module
2. Add consolidation methods to service (3 methods)
3. Add event processors to worker (2 methods)
4. Create E2E tests (3-4 tests)
5. Document operation guide

---

## Local Setup

### Prerequisites
```bash
# Install Docker Desktop (includes docker-compose)
# Download: https://www.docker.com/products/docker-desktop

# Install Python 3.10+ (if not already installed)
# Download: https://www.python.org/downloads

# Install git
git --version
```

### Step 1: Start Infrastructure
```bash
cd kestra/
docker-compose up -d

# Verify services
docker-compose ps

# Expected output:
# postgresql  | running | localhost:5432
# redis       | running | localhost:6379
# pgadmin     | running | localhost:5050
```

### Step 2: Setup Virtual Environment
```bash
cd intellicare-donabedian/

# Create venv
python -m venv .venv

# Activate venv
.venv\Scripts\activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import sqlalchemy; import redis; print('✅ Dependencies OK')"
```

### Step 3: Run Migrations
```bash
# Navigate to intellicare-donabedian
cd intellicare-donabedian/

# Run Alembic migrations
alembic upgrade head

# Verify (check PgAdmin or psql)
docker exec intellicare-db psql -U admin_intellicare -d IntellicareDB -c "\dt donabedian*"
```

### Step 4: Start API
```bash
# In intellicare-donabedian/
python -m uvicorn donabedian.api.app:app --port 8003 --reload

# Test endpoint
curl http://localhost:8003/pilares
# Requires JWT token in Authorization header
```

### Step 5: Start Consumer (in another terminal)
```bash
# Activate venv first
.venv\Scripts\activate.ps1

# Run consumer
python -m donabedian.consolidation.worker

# Expected output:
# 🚀 Starting consolidation consumer...
# Consumer loop started
```

---

## Database Schema

### Donabedian (Example Module)

#### operacional schema (Transactional)
```sql
donabedian_operacional.pilares
├─ id (UUID, PK)
├─ nome, descricao, tipo, ordem_exibicao, ativo
├─ created_by (UUID FK → keycloak_users)
├─ created_at (TIMESTAMP)
├─ updated_by (UUID FK → keycloak_users, nullable)
├─ updated_at (TIMESTAMP)
├─ valid_to (TIMESTAMP, nullable - soft delete)
└─ rowversion (INTEGER - optimistic lock)

donabedian_operacional.indicadores (same structure)
donabedian_operacional.medicoes (same structure + indicator_id FK)
```

#### analitico schema (Denormalized for Analytics)
```sql
donabedian_analitico.pilar
├─ [all operacional fields]
├─ consolidated_at (TIMESTAMP - when consolidation occurred)
└─ consolidation_source (VARCHAR - 'pilar.CREATE', 'pilar.UPDATE', etc.)

donabedian_analitico.indicador (same pattern)
donabedian_analitico.medida (same pattern)
```

### Queries

```sql
-- View non-deleted pilars
SELECT * FROM donabedian_analitico.pilar WHERE valid_to IS NULL;

-- View consolidation audit trail
SELECT id, consolidation_source, consolidated_at 
FROM donabedian_analitico.pilar 
ORDER BY consolidated_at DESC;

-- Row-level security (per user)
SELECT * FROM donabedian_analitico.pilar 
WHERE created_by = current_user_id;
```

---

## Testing

### Run All Tests
```bash
cd intellicare-donabedian/

# Run all consolidation tests
pytest src/donabedian/consolidation/test_consolidation.py -v -s

# Run specific test class
pytest src/donabedian/consolidation/test_consolidation.py::TestConsolidationConsumer -v -s

# Run with coverage
pytest src/donabedian/consolidation/test_consolidation.py --cov=donabedian.consolidation
```

### Test Structure
```python
@pytest.fixture
async def redis_client():
    """Get Redis connection"""
    
@pytest.fixture
async def db_session():
    """Get async SQL session"""
    
@pytest.fixture
async def consolidation_service():
    """Get consolidation service instance"""
    
@pytest.fixture
async def clean_redis():
    """Clear Redis streams before test"""
    
@pytest.fixture
async def clean_db():
    """Clear analitico tables before test"""

class TestConsolidationConsumer:
    async def test_pilar_create_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        # Arrange
        pilar_id = uuid.uuid4()
        
        # Act
        success = await consolidation_service.consolidate(...)
        
        # Assert
        assert success
        result = await clean_db.execute(...)
        assert result is not None
```

### Test Output
```
test_pilar_create_event_consolidation ✅ PASSED
test_pilar_update_event_consolidation ✅ PASSED
test_pilar_delete_event_consolidation ✅ PASSED
test_indicator_create_event_consolidation ✅ PASSED
test_indicator_update_event_consolidation ✅ PASSED
test_indicator_delete_event_consolidation ✅ PASSED
test_measurement_create_event_consolidation ✅ PASSED
test_measurement_update_event_consolidation ✅ PASSED
test_measurement_delete_event_consolidation ✅ PASSED
test_full_pipeline_three_entities ✅ PASSED
test_consolidation_consumer_worker ✅ PASSED
test_consolidated_at_timestamp ✅ PASSED
test_invalid_entity_type_returns_false ✅ PASSED
test_invalid_operation_returns_false ✅ PASSED

15 passed in 30.42s
```

---

## Module Architecture Pattern

Every module follows this structure (Donabedian is template):

```
intellicare-{module}/
├─ src/{module}/
│  ├─ __init__.py
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ {entity1}.py      ← Entity definitions
│  │  ├─ {entity2}.py
│  │  └─ config.py
│  ├─ data_access/
│  │  ├─ __init__.py
│  │  ├─ base.py           ← Extends IBaseDAO
│  │  ├─ operational.py    ← operacional schema DAO
│  │  └─ analytics.py      ← analitico schema DAO
│  ├─ schemas/
│  │  ├─ __init__.py
│  │  ├─ {entity}.py       ← Pydantic models
│  │  └─ trends.py         ← Analytics queries
│  ├─ services/
│  │  ├─ __init__.py
│  │  └─ {entity}_service.py  ← Business logic + event publishing
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ app.py            ← FastAPI app + Keycloak setup
│  │  └─ routes/
│  │     ├─ __init__.py
│  │     ├─ {entity}.py    ← CRUD endpoints
│  │     └─ trends.py      ← Analytics endpoints
│  └─ consolidation/
│     ├─ __init__.py
│     ├─ service.py        ← Consolidation logic (NEW for FASE 2.4+)
│     ├─ worker.py         ← Redis consumer (NEW for FASE 2.4+)
│     └─ test_consolidation.py ← E2E tests (NEW for FASE 2.4+)
├─ migrations/
│  ├─ versions/
│  │  └─ {001-nnn}_*.py    ← Alembic versions
│  ├─ env.py               ← Migration config
│  └─ script.py.mako       ← Migration template
├─ tests/
│  ├─ __init__.py
│  ├─ test_e2e_{module}.py ← FASE 2.1 tests
│  └─ test_event_publishing.py ← FASE 2.2 tests
├─ requirements.txt         ← Dependencies
├─ README.md               ← Module documentation
└─ FASE_*.md              ← Phase-specific docs
```

---

## API Documentation

### Authentication
All endpoints require JWT token from Keycloak:
```bash
curl -H "Authorization: Bearer {token}" http://localhost:8003/pilares
```

### Donabedian Endpoints

#### Pilar (Pillar)
```
GET    /pilares                    # List all pilars
GET    /pilares/{id}               # Get specific pilar
POST   /pilares                    # Create pilar
PUT    /pilares/{id}               # Update pilar
DELETE /pilares/{id}               # Delete pilar (soft)
```

#### Indicator
```
GET    /indicadores                # List all indicators
GET    /indicadores/{id}           # Get specific indicator
POST   /indicadores                # Create indicator
PUT    /indicadores/{id}           # Update indicator
DELETE /indicadores/{id}           # Delete indicator (soft)
```

#### Measurement
```
GET    /medicoes                   # List all measurements
GET    /medicoes/{id}              # Get specific measurement
POST   /medicoes                   # Create measurement
PUT    /medicoes/{id}              # Update measurement
DELETE /medicoes/{id}              # Delete measurement (soft)
```

#### Trends (Analytics)
```
GET    /trends/by-pilar/{pilar_id}  # Trend data by pilar
GET    /trends/by-indicator/{id}    # Trend data by indicator
GET    /trends/summary              # Summary statistics
```

---

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if container is running
docker ps | grep postgresql

# Check logs
docker logs intellicare-db

# Connect to container
docker exec -it intellicare-db psql -U admin_intellicare -d IntellicareDB
```

### Redis Connection Issues
```bash
# Check if container is running
docker ps | grep redis

# Check logs
docker logs intellicare-redis

# Connect to Redis
docker exec -it intellicare-redis redis-cli PING
```

### Migration Issues
```bash
# Check migration status
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Re-apply all migrations
alembic upgrade head
```

### Test Failures
```bash
# Run with verbose output
pytest -vv -s test_file.py

# Run with logging
pytest -vv -s --log-cli-level=DEBUG test_file.py

# Run single test
pytest test_file.py::TestClass::test_method -vv
```

---

## Contact & Support

### Documentation Issues
- Check if solution exists in [troubleshooting section](#troubleshooting)
- Review FASE-specific documentation
- Check test files for usage examples

### Code Questions
- Review service implementations (they contain docstrings)
- Check test cases for usage patterns
- Look at related entity implementations

### Infrastructure Issues
- Check Docker container logs: `docker logs {container_name}`
- Verify services are running: `docker ps`
- Restart infrastructure: `docker-compose down && docker-compose up -d`

---

## Key Terms & Concepts

| Term | Definition | Usage |
|------|-----------|-------|
| **operacional** | Transactional schema (writes) | Source of truth for CRUD operations |
| **analitico** | Analytics schema (reads) | Denormalized, optimized for queries |
| **Consolidation** | Process of syncing operacional → analitico | Triggers on CREATE/UPDATE/DELETE |
| **consolidation_source** | Audit field tracking what triggered consolidation | Values: "pilar.CREATE", "indicator.UPDATE", etc. |
| **consolidated_at** | Timestamp when consolidation occurred | For auditing and traceability |
| **valid_to** | Soft delete timestamp (NULL = active) | Supports temporal queries |
| **rowversion** | Optimistic lock counter | Prevents concurrent update conflicts |
| **Redis Streams** | Event queue (intellicare:donabedian:*) | Buffers consolidation events |
| **Consumer Group** | Redis consumer group for fault tolerance | Persists unACK'd events |
| **EventPublisher** | Service that publishes CRUD events | Triggered by service layer |
| **Keycloak** | Identity/access management | JWT tokens for API authentication |

---

## Quick Links

### Documentation Files
- 📄 [Progress Report](./PROGRESS_REPORT_FASE_2_4_1.md)
- 📄 [FASE 2.4.1 Detailed Docs](./intellicare-donabedian/FASE_2_4_1_EXPAND_DONABEDIAN.md)
- 📄 [Core Infrastructure](./intellicare-core/README.md)

### Code Locations
- 🔧 [Consolidation Service](./intellicare-donabedian/src/donabedian/consolidation/service.py)
- 🔧 [Consolidation Worker](./intellicare-donabedian/src/donabedian/consolidation/worker.py)
- 🧪 [Consolidation Tests](./intellicare-donabedian/src/donabedian/consolidation/test_consolidation.py)
- 🔧 [EventPublisher](./intellicare-core/intellicare_core/events/publisher.py)
- 🔧 [BaseDAO](./intellicare-core/intellicare_core/data_access/base.py)

### Infrastructure
- 🐳 [Docker Compose](./kestra/docker-compose.yml)
- 🗄️ [Migrations](./intellicare-donabedian/migrations/versions/)
- ⚙️ [Alembic Config](./intellicare-donabedian/alembic.ini)

---

**Last Updated**: 2024-01-15  
**Status**: ✅ FASE 2.4.1 Complete  
**Next Phase**: FASE 2.5 (Module Replication)  
**Document Version**: 2.4.1
