# MultiMCPToolProvider — Integração WANDA

Este módulo implementa o agregador de ferramentas MCP para WANDA, permitindo orquestração plugável de múltiplos agentes (MINERVA, PIERRE, Florence).

## Componentes
- `multi_mcp_provider.py`: Classe agregadora de ferramentas de múltiplos WandaMCPClient.
- Documentação e exemplos de uso.

## Como usar
```python
from wanda.mcp.multi_mcp_provider import MultiMCPToolProvider
from wanda.mcp.client import WandaMCPClient

minerva_client = WandaMCPClient(config_minerva)
pierre_client = WandaMCPClient(config_pierre)
florence_client = WandaMCPClient(config_florence)

multi_provider = MultiMCPToolProvider([minerva_client, pierre_client, florence_client])
await multi_provider.build()
all_tools = multi_provider.get_all_tools()
```

## Documentação
- Toda decisão técnica e integração será registrada em DEVLOG.md
