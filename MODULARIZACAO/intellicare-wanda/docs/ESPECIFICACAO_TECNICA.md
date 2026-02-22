# intellicare-wanda — Especificacao Tecnica

## 1. Estrutura

```
intellicare-wanda/
├── wanda/
│   ├── __init__.py
│   ├── config.py                # WandaConfig extends BaseConfig
│   ├── state.py                 # LangGraph state definition
│   │
│   ├── graph/                   # LangGraph orchestration
│   │   ├── main_graph.py        # Grafo principal
│   │   ├── supervisor.py        # No de supervisao (routing)
│   │   └── aggregator.py        # Agregacao de respostas
│   │
│   ├── discovery/               # NOVO: descoberta de modulos
│   │   ├── registry.py          # ModuleRegistry
│   │   └── health_checker.py    # HealthChecker (ping periodico)
│   │
│   ├── adapters/                # Adaptadores para sistemas externos
│   │   ├── mcp_adapter.py       # MCP tool adapter
│   │   └── module_adapter.py    # NOVO: adapter generico para modulos
│   │
│   ├── rules/                   # Regras de seguranca
│   │   └── safety_rules.py
│   │
│   ├── prompts/                 # System prompts
│   │   └── system_prompt.py
│   │
│   ├── api/                     # API REST (para o Portal)
│   │   ├── app.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── chat.py          # POST /api/v1/chat (conversa orquestrada)
│   │       └── modules.py       # GET /api/v1/modules (modulos ativos)
│   │
│   └── cli.py                   # Interface de linha de comando
│
├── tests/
│   ├── conftest.py
│   ├── test_graph.py
│   ├── test_orchestrator.py
│   ├── test_state.py
│   ├── test_discovery.py        # NOVO
│   ├── test_safety_rules.py
│   └── test_multi_module.py     # NOVO: testes com 2+ modulos
│
├── Dockerfile
├── docker-compose.yml           # Inclui 2+ modulos para teste
├── pyproject.toml
└── .env.example
```

## 2. Migracao do Monolito

| Origem | Destino | Adaptacao |
|--------|---------|-----------|
| `wanda/graph/` | `wanda/graph/` | Manter logica, trocar imports |
| `wanda/adapters/mcp_adapter.py` | `wanda/adapters/` | Manter |
| `wanda/rules/safety_rules.py` | `wanda/rules/` | Manter |
| `wanda/prompts/system_prompt.py` | `wanda/prompts/` | Manter |
| `wanda/state.py` | `wanda/state.py` | Manter |
| `wanda/config.py` | `wanda/config.py` | Extends BaseConfig |
| `wanda/subagents/` | REMOVIDO | Substituido por discovery + module_adapter |
| `wanda/tests/` | `tests/` | Adaptar para novo discovery |

### Mudanca Chave: De Subagents para Discovery

**Antes (monolito):**
```python
# Import direto do agente
from agentes.oswaldo.subagent import OswaldoSubagent
agent = OswaldoSubagent()
result = agent.analyze(...)
```

**Depois (LEGO):**
```python
# Descoberta via HTTP
registry = ModuleRegistry(["http://oswaldo:8000", "http://florence:8000"])
modules = await registry.discover()

# Chamada via API padrao
result = await registry.call("intellicare-oswaldo", "analyze", {...})
```

## 3. Dependencias

```toml
[project]
dependencies = [
    "intellicare-core>=1.0.0,<2.0.0",
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "langchain-openai>=0.2.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "httpx>=0.27.0",
]
```

## 4. Maturidade Atual: 7/10 (precisa adaptar discovery)
