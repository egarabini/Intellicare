# DEVLOG — Florence MCP Server

## 2026-02-17 — Início do desenvolvimento

- Estruturado diretório `mcp/` dentro de `intellicare-florence`.
- Criado `README.md` com objetivos, instruções e política de documentação.
- Próximo passo: adaptação do `fhir_mcp_server.py` do FHIR-AgentEval para integração com Florence, incluindo autenticação JWT.

## Decisões técnicas
- O servidor MCP será compatível com FastMCP e exporá as operações CRUD FHIR.
- O endpoint FHIR será configurável via variável de ambiente ou argumento de linha de comando.
- Toda autenticação será feita via JWT, validando tokens em cada requisição MCP.

## TODO
- [ ] Copiar e adaptar código base do FHIR-AgentEval
- [ ] Implementar autenticação JWT
- [ ] Testar integração com Florence
- [ ] Documentar endpoints e exemplos de uso
