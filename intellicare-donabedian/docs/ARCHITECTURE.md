# 🏗️ Arquitetura Técnica

## Visão Geral

O módulo **intellicare-donabedian** segue uma arquitetura modular baseada em camadas, com separação clara de responsabilidades e foco em independência e escalabilidade.

---

## 🎯 Princípios Arquiteturais

### 1. Arquitetura LEGO (Modular)
- **Independência**: Cada módulo roda standalone
- **Isolamento**: Schema próprio no banco de dados
- **Integração**: Comunicação via API REST
- **Vendabilidade**: Módulos podem ser comercializados separadamente

### 2. Clean Architecture
- **Separação de Camadas**: Models, Schemas, Routes, Services
- **Inversão de Dependências**: Dependências apontam para abstrações
- **Testabilidade**: Cada camada pode ser testada isoladamente

### 3. Async First
- **SQLAlchemy Async**: Operações de banco assíncronas
- **FastAPI Async**: Endpoints assíncronos
- **httpx Async**: Cliente HTTP assíncrono

### 4. Type Safety
- **Pydantic**: Validação de dados em runtime
- **Type Hints**: Anotações de tipo em todo o código
- **SQLAlchemy 2.0 Mapped**: Type-safe ORM

---

## 📦 Estrutura de Camadas

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │  Streamlit   │  │   FastAPI       │ │
│  │  Dashboard   │  │   REST API      │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          Application Layer              │
│  ┌──────────────────────────────────┐  │
│  │      Pydantic Schemas            │  │
│  │  (Validation & Serialization)    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           Domain Layer                  │
│  ┌──────────────────────────────────┐  │
│  │    SQLAlchemy Models             │  │
│  │  (Business Logic & Rules)        │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        Infrastructure Layer             │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │  PostgreSQL  │  │   Alembic       │ │
│  │   Database   │  │  Migrations     │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 🗄️ Modelo de Dados

### Schema Isolation

Cada módulo IntelliCare usa seu próprio schema PostgreSQL:

```sql
-- Schema do módulo Donabedian
CREATE SCHEMA intellicare_donabedian;

-- Tabelas dentro do schema
intellicare_donabedian.pillars
intellicare_donabedian.indicators
intellicare_donabedian.indicator_pillars
intellicare_donabedian.measurements
```

**Vantagens**:
- Isolamento de dados entre módulos
- Facilita backup/restore por módulo
- Permite deploy independente
- Evita conflitos de nomes de tabelas

### Diagrama ER

```
┌─────────────────┐
│     Pillar      │
│─────────────────│
│ id (PK)         │
│ name            │
│ description     │
│ display_order   │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│  IndicatorPillar    │
│─────────────────────│
│ id (PK)             │
│ indicator_id (FK)   │◄─────┐
│ pillar_id (FK)      │      │
│ weight              │      │ N:1
└─────────────────────┘      │
                             │
                    ┌────────┴────────┐
                    │   Indicator     │
                    │─────────────────│
                    │ id (PK)         │
                    │ name            │
                    │ description     │
                    │ formula         │
                    │ unit            │
                    │ triad_dimension │
                    │ target_value    │
                    │ target_operator │
                    │ created_at      │
                    │ updated_at      │
                    └─────────────────┘
                             │
                             │ 1:N
                             ▼
                    ┌─────────────────┐
                    │  Measurement    │
                    │─────────────────│
                    │ id (PK)         │
                    │ indicator_id(FK)│
                    │ value           │
                    │ period_start    │
                    │ period_end      │
                    │ period_type     │
                    │ status          │
                    │ created_at      │
                    └─────────────────┘
```

### Relacionamentos

1. **Pillar ↔ Indicator**: N:N através de `IndicatorPillar`
   - Um pilar pode ter múltiplos indicadores
   - Um indicador pode pertencer a múltiplos pilares
   - Cada associação tem um `weight` (peso)

2. **Indicator → Measurement**: 1:N
   - Um indicador pode ter múltiplas medições
   - Uma medição pertence a um único indicador

### Enums

```python
# Dimensões da Tríade de Donabedian
class TriadDimension(str, Enum):
    STRUCTURE = "structure"
    PROCESS = "process"
    OUTCOME = "outcome"

# Operadores de Comparação
class TargetOperator(str, Enum):
    GREATER = "greater"
    GREATER_EQUAL = "greater_equal"
    LESS = "less"
    LESS_EQUAL = "less_equal"
    EQUAL = "equal"

# Status de Medição
class MeasurementStatus(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

# Tipo de Período
class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
```

---

## 🔌 Integração com IntelliCare

### Padrão de Integração

```
┌──────────────────────┐
│  intellicare-core    │
│  (Módulo Central)    │
└──────────┬───────────┘
           │
           │ REST API
           │
    ┌──────┴──────┬──────────────┬─────────────┐
    │             │              │             │
    ▼             ▼              ▼             ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│donabedian│ │ oswaldo  │ │  outros  │ │  outros  │
│ (schema) │ │ (schema) │ │ (schema) │ │ (schema) │
└─────────┘ └──────────┘ └──────────┘ └──────────┘
```

**Características**:
- **Sem Foreign Keys entre schemas**: Evita acoplamento
- **Comunicação via API**: Cada módulo expõe REST API
- **IDs como strings**: Referências entre módulos via IDs
- **Eventos**: Futuramente, comunicação assíncrona via message broker

---

## 🚀 Stack Tecnológico

### Backend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Python | 3.11+ | Linguagem principal |
| FastAPI | 0.109+ | Framework web assíncrono |
| SQLAlchemy | 2.0+ | ORM assíncrono |
| Pydantic | 2.5+ | Validação de dados |
| asyncpg | 0.29+ | Driver PostgreSQL assíncrono |
| Alembic | 1.13+ | Migrations de banco |

### Frontend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Streamlit | 1.30+ | Dashboard interativo |
| Plotly | 5.18+ | Gráficos interativos |
| Pandas | 2.1+ | Manipulação de dados |
| httpx | 0.26+ | Cliente HTTP assíncrono |

### Database

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| PostgreSQL | 15+ | Banco de dados principal |
| SQLite | 3.40+ | Testes (in-memory) |

### DevOps

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Docker | 24+ | Containerização |
| Docker Compose | 2.20+ | Orquestração local |
| pytest | 8.0+ | Framework de testes |
| pytest-asyncio | 0.23+ | Testes assíncronos |
| pytest-cov | 4.1+ | Cobertura de testes |

---

## 🎨 Padrões de Design

### 1. Repository Pattern (Implícito)

SQLAlchemy sessions funcionam como repositories:

```python
async def get_indicator(db: AsyncSession, indicator_id: int):
    result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    return result.scalar_one_or_none()
```

### 2. Dependency Injection

FastAPI usa DI para injetar dependências:

```python
@router.get("/indicators/{id}")
async def get_indicator(
    id: int,
    db: AsyncSession = Depends(get_db)  # DI
):
    return await get_indicator(db, id)
```

### 3. Schema Pattern

Separação entre modelos de domínio e DTOs:

```python
# Domain Model
class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

# DTO (Data Transfer Object)
class IndicatorCreate(BaseModel):
    name: str = Field(..., max_length=200)

class IndicatorResponse(BaseModel):
    id: int
    name: str
```

### 4. Factory Pattern

Fixtures de teste usam factory pattern:

```python
@pytest.fixture
async def sample_indicator(db_session: AsyncSession):
    indicator = Indicator(
        name="Test Indicator",
        formula="test",
        unit="%"
    )
    db_session.add(indicator)
    await db_session.commit()
    return indicator
```

---

## 🔒 Segurança

### Validação de Dados

- **Pydantic**: Validação automática de entrada
- **SQLAlchemy**: Validação de tipos no ORM
- **Constraints**: Unique, NOT NULL, Foreign Keys

### SQL Injection

- **Parametrized Queries**: SQLAlchemy usa queries parametrizadas
- **ORM**: Abstração protege contra SQL injection

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Autenticação (Planejada)

- JWT tokens
- OAuth2 com Password Flow
- Role-based access control (RBAC)

---

## 📊 Performance

### Database

- **Connection Pooling**: SQLAlchemy pool
- **Async I/O**: asyncpg para operações não-bloqueantes
- **Indexes**: Criados em colunas frequentemente consultadas
- **Schema Isolation**: Reduz tamanho de tabelas

### API

- **Async Endpoints**: FastAPI assíncrono
- **Paginação**: `skip` e `limit` em listagens
- **Caching**: Planejado (Redis)

### Dashboard

- **Streamlit Cache**: `@st.cache_data` para dados
- **Lazy Loading**: Dados carregados sob demanda
- **Plotly**: Renderização client-side

---

## 🧪 Estratégia de Testes

### Pirâmide de Testes

```
        ┌─────┐
        │  E2E │  (Planejado)
        └─────┘
      ┌─────────┐
      │Integration│  (API + DB)
      └─────────┘
    ┌─────────────┐
    │    Unit     │  (Models, Schemas)
    └─────────────┘
```

### Tipos de Testes

1. **Unit Tests** (277 casos):
   - Models (31 testes)
   - Schemas (26 testes)
   - Utilities

2. **Integration Tests**:
   - API endpoints
   - Database operations

3. **E2E Tests** (Planejado):
   - Dashboard flows
   - API workflows

### Test Database

- **SQLite in-memory**: Rápido e isolado
- **StaticPool**: Compartilha conexão
- **Schema-less**: `DATABASE_SCHEMA="NONE"`

```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,  # Importante para SQLite
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
```

---

## 🔄 CI/CD (Planejado)

### Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│   Lint   │──▶│   Test   │──▶│  Build   │──▶│  Deploy  │
│ (ruff)   │   │ (pytest) │   │ (Docker) │   │ (K8s)    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Stages

1. **Lint**: ruff, mypy
2. **Test**: pytest com coverage >80%
3. **Build**: Docker image
4. **Deploy**: Kubernetes ou Docker Swarm

---

## 📈 Monitoramento (Planejado)

### Métricas

- **Application**: Prometheus + Grafana
- **Database**: pg_stat_statements
- **Logs**: ELK Stack ou Loki

### Health Checks

```python
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
```

---

## 🚀 Escalabilidade

### Horizontal Scaling

- **Stateless API**: Múltiplas instâncias
- **Load Balancer**: Nginx ou Traefik
- **Database**: PostgreSQL com replicação

### Vertical Scaling

- **Connection Pool**: Ajustar tamanho do pool
- **Worker Processes**: Uvicorn workers
- **Database**: Aumentar recursos (CPU, RAM)

---

## 📝 Decisões Arquiteturais

### Por que SQLAlchemy 2.0?

- **Type Safety**: Mapped syntax com type hints
- **Async Support**: Nativo e performático
- **Migrations**: Integração com Alembic
- **Maturidade**: Framework maduro e estável

### Por que FastAPI?

- **Performance**: Um dos frameworks mais rápidos
- **Type Safety**: Integração com Pydantic
- **Async**: Suporte nativo a async/await
- **Documentação**: Swagger UI automático

### Por que Streamlit?

- **Rapidez**: Desenvolvimento rápido de dashboards
- **Python-only**: Sem necessidade de HTML/CSS/JS
- **Interatividade**: Componentes interativos built-in
- **Plotly**: Integração nativa com Plotly

### Por que PostgreSQL?

- **Schemas**: Suporte a múltiplos schemas
- **Performance**: Excelente para OLTP
- **JSON**: Suporte a tipos JSON
- **Maturidade**: Banco maduro e confiável

---

## 🔮 Roadmap Técnico

### Curto Prazo (3 meses)

- [ ] Implementar autenticação JWT
- [ ] Adicionar caching com Redis
- [ ] Implementar rate limiting
- [ ] Adicionar testes E2E

### Médio Prazo (6 meses)

- [ ] Implementar message broker (RabbitMQ/Kafka)
- [ ] Adicionar monitoramento (Prometheus)
- [ ] Implementar CI/CD pipeline
- [ ] Adicionar logs estruturados

### Longo Prazo (12 meses)

- [ ] Migrar para microserviços
- [ ] Implementar event sourcing
- [ ] Adicionar GraphQL API
- [ ] Implementar multi-tenancy

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

