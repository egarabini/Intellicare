# EF-W001 — Persistencia e Registro de Modulos

> Migrar do registro em memoria para PostgreSQL com registro persistente, versionado e auditavel de todos os agentes do ecossistema.

## 1. Objetivo

Implementar persistencia PostgreSQL na Wanda para:
- Manter registro persistente de todos os agentes descobertos
- Versionar capabilities declaradas pelos agentes
- Historico de disponibilidade por agente
- Configuracoes de roteamento persistidas
- Audit log de todas as decisoes de orquestracao

## 2. Justificativa

- **Continuidade**: Reinicializar a Wanda nao perde conhecimento do ecossistema
- **Historico**: Saber quando cada agente ficou disponivel/indisponivel
- **Roteamento**: Regras de roteamento configuradas e versionadas
- **Auditoria**: Rastreabilidade completa de decisoes de orquestracao
- **v1.0 compat**: Todos os 69 testes existentes devem continuar passando

## 3. Escopo

### 3.1 Registro de Modulos (Module Registry)

```python
class ModuleRegistry:
    """
    Registro persistente de modulos do ecossistema.

    Evolucao do discovery em memoria para PostgreSQL.
    Wanda ainda descobre via HTTP (/api/v1/info),
    mas persiste o resultado com historico.
    """

    async def register_or_update(
        self,
        module_info: dict,
    ) -> RegisteredModule:
        """
        Registra ou atualiza um modulo.

        Chamado apos discovery bem-sucedida de /api/v1/info.

        Logica:
        - Se agente novo → INSERT com status=active
        - Se agente existente → UPDATE capabilities, versao
        - Se capabilities mudaram → versionar (incrementar version)
        - Registrar timestamp do ultimo check
        """

    async def get_active_modules(self) -> list[RegisteredModule]:
        """Retorna modulos com status=active e health=healthy."""

    async def get_module(self, agent_name: str) -> Optional[RegisteredModule]:
        """Retorna modulo pelo nome."""

    async def get_modules_with_capability(
        self,
        capability_id: str,
    ) -> list[RegisteredModule]:
        """
        Retorna agentes que tem a capability solicitada.

        Usado pelo router para selecionar quem pode responder.
        """

    async def mark_unhealthy(
        self,
        agent_name: str,
        reason: str,
    ) -> None:
        """Marca agente como unhealthy (nao remove — mantém historico)."""

    async def mark_healthy(
        self,
        agent_name: str,
    ) -> None:
        """Restaura agente para healthy apos recovery."""

    async def get_health_history(
        self,
        agent_name: str,
        last_n_events: int = 50,
    ) -> list[dict]:
        """Historico de saude de um agente."""
```

### 3.2 Tabelas

```sql
-- Registro de modulos
CREATE TABLE registered_modules (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(50) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    base_url VARCHAR(200) NOT NULL,
    port INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',    -- active, inactive, deprecated
    health_status VARCHAR(20) DEFAULT 'unknown',  -- healthy, unhealthy, degraded, unknown
    capabilities JSONB NOT NULL DEFAULT '[]',
    capabilities_version INTEGER DEFAULT 1,
    requires_patient_context BOOLEAN DEFAULT FALSE,
    supports_ips_first BOOLEAN DEFAULT FALSE,
    endpoints JSONB DEFAULT '{}',

    -- Timestamps
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_health_check_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_modules_name ON registered_modules(agent_name);
CREATE INDEX idx_modules_status ON registered_modules(status, health_status);

-- Historico de capabilities (versionamento)
CREATE TABLE module_capabilities_history (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL,
    capabilities JSONB NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change_type VARCHAR(20)  -- added, modified, removed
);

-- Historico de saude (uptime tracking)
CREATE TABLE module_health_events (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    event_type VARCHAR(20) NOT NULL,   -- went_healthy, went_unhealthy, went_degraded
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    reason TEXT,
    response_time_ms INTEGER,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_health_events_agent ON module_health_events(agent_name);
CREATE INDEX idx_health_events_date ON module_health_events(occurred_at);

-- Historico de execucoes de orquestracao
CREATE TABLE orchestration_executions (
    id BIGSERIAL PRIMARY KEY,
    execution_id UUID UNIQUE NOT NULL,
    request_type VARCHAR(50),            -- analyze, query, orchestrate
    query TEXT,
    patient_id VARCHAR(64),
    ips_loaded BOOLEAN DEFAULT FALSE,

    -- Roteamento
    routing_method VARCHAR(20),          -- keyword, llm, direct
    modules_queried JSONB DEFAULT '[]',  -- [{agent, capability, latency_ms}]
    modules_failed JSONB DEFAULT '[]',

    -- Resultado
    success BOOLEAN DEFAULT TRUE,
    response_summary TEXT,
    total_latency_ms INTEGER,

    -- Auditoria
    requested_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_executions_patient ON orchestration_executions(patient_id);
CREATE INDEX idx_executions_date ON orchestration_executions(created_at);
CREATE INDEX idx_executions_type ON orchestration_executions(request_type);
```

### 3.3 Discovery Aprimorado

```python
class DiscoveryService:
    """
    Descoberta de modulos com persistencia.

    Evolucao do v1.0 InMemoryDiscovery para PostgreSQL.
    """

    def __init__(
        self,
        registry: ModuleRegistry,
        http_client,
        known_hosts: list[str],    # Lista de hosts conhecidos
    ):
        ...

    async def discover_all(self) -> DiscoveryResult:
        """
        Tenta descobrir todos os agentes conhecidos.

        Executado:
        - Na inicializacao da Wanda
        - A cada 30 segundos (health check)
        - Quando um agente emite evento de startup

        Para cada host:
        1. GET /api/v1/health → saudavel?
        2. GET /api/v1/info → capabilities
        3. registry.register_or_update()
        4. Se falhou → registry.mark_unhealthy()
        """

    async def discover_single(
        self,
        agent_name: str,
    ) -> Optional[RegisteredModule]:
        """Re-descobre um agente especifico."""

    async def get_routing_table(self) -> dict:
        """
        Retorna tabela de roteamento atual.

        {
            "analyze": {
                "chronic_disease": ["oswaldo"],
                "clinical_analysis": ["florence"],
                "care_management": ["geralda"],
                ...
            },
            "last_updated": "2026-02-16T10:00:00Z"
        }
        """
```

### 3.4 Compatibilidade com v1.0

O `ModuleRegistry` substitui o `InMemoryRegistry` atual, mantendo a mesma interface:

```python
# Interface v1.0 (deve continuar funcionando)
async def get_modules() -> list[dict]
async def get_module_info(agent: str) -> Optional[dict]
async def is_healthy(agent: str) -> bool

# Novas operacoes v2.0
async def get_health_history(agent: str, ...) -> list[dict]
async def get_capabilities_history(agent: str, ...) -> list[dict]
async def get_routing_table() -> dict
```

### 3.5 Configuracao

```env
# PostgreSQL
INTELLICARE_WANDA_DB_URL=postgresql+asyncpg://wanda:password@postgres:5432/intellicare
INTELLICARE_WANDA_DB_SCHEMA=wanda

# Discovery
INTELLICARE_WANDA_KNOWN_AGENTS=oswaldo:8001,florence:8002,zilda:8003,donabedian:8004,comunicacao:8005,geralda:8006
INTELLICARE_WANDA_DISCOVERY_INTERVAL=30      # segundos
INTELLICARE_WANDA_DISCOVERY_TIMEOUT=5        # segundos por agente
INTELLICARE_WANDA_HEALTH_CHECK_INTERVAL=60   # segundos
```

### 3.6 Endpoints Novos

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/registry` | Registro completo de modulos |
| GET | `/api/v1/registry/{agent}` | Detalhes de um agente |
| GET | `/api/v1/registry/{agent}/history` | Historico de saude |
| GET | `/api/v1/registry/routing-table` | Tabela de roteamento atual |

## 4. Testes

- ModuleRegistry: register, update, get, mark_unhealthy (8 testes)
- DiscoveryService: discover_all, discover_single, routing_table (6 testes)
- Persistencia: modulo persiste apos reinicializacao (3 testes)
- Historico: capabilities history, health history (4 testes)
- Compatibilidade v1.0: todos 69 testes passando (1 suite)
- Endpoints novos (4 testes)
- **Total**: 25+ testes novos (+ 69 existentes devem passar)

## 5. Criterios de Aceitacao

- [ ] Todos 69 testes v1.0 continuam passando
- [ ] Modulos persistidos no PostgreSQL
- [ ] Discovery continua funcionando sem interrupcao
- [ ] Historico de saude por agente
- [ ] Versionamento de capabilities
- [ ] Tabela de roteamento derivada do registry
- [ ] 4 novos endpoints funcionais
- [ ] 25+ testes novos
- [ ] Cobertura >= 85%

## 7. Suporte a Modulos MCP (V5)

> Ver **EF-W011** para especificacao completa de modulos MCP.

A tabela `registered_modules` deve incluir coluna `module_type` (`HTTP` | `MCP`) para que o registry unifique ambos os tipos. Modulos MCP (MINERVA :8008, PIERRE :8009) possuem tabelas adicionais em EF-W011 (`mcp_modules`, `mcp_tools`, `mcp_call_log`), mas devem ser registrados aqui para aparecer em `/api/v1/registry` e `/api/v1/modules`.

Adicionar a coluna `module_type VARCHAR(10) DEFAULT 'HTTP'` na tabela `registered_modules`. O health check de modulos MCP delega a `WandaMCPClient.health_check()` (EF-W011) em vez de GET HTTP.

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~4 (discovery, api, config, docker)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~25
