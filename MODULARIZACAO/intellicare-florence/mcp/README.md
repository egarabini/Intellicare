# Florence MCP Server

Este diretório contém a implementação do servidor MCP (Model Context Protocol) para expor o Florence (servidor FHIR) como um endpoint MCP, permitindo operações CRUD FHIR via protocolo padronizado.

## Objetivo
- Permitir que agentes (WANDA, MINERVA, PIERRE) e ferramentas externas interajam com o Florence usando o padrão MCP, facilitando orquestração, testes e integração.

## Componentes
- `florence_fhir_mcp_server.py`: Servidor principal MCP, adaptado do FHIR-AgentEval, com autenticação e integração ao Florence.
- `tests/`: Scripts de teste automatizado do endpoint MCP.

## Como rodar
```sh
python florence_fhir_mcp_server.py --host 0.0.0.0 --port 8000 --path /florence_mcp
```

## Documentação
- Toda alteração e decisão de arquitetura deve ser registrada neste diretório.
- O progresso e as decisões técnicas serão documentados em `DEVLOG.md`.
