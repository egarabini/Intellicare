# Testes MCP Server — Florence

## Objetivo
Garantir que o endpoint MCP do Florence responde corretamente às operações CRUD FHIR, com autenticação JWT.

## Casos de Teste
- [ ] Teste de autenticação JWT (válido/inválido/ausente)
- [ ] Teste de listagem de tipos de recurso (`listResourceTypes`)
- [ ] Teste de leitura de recurso (`getResourceById`)
- [ ] Teste de busca de recursos (`searchResources`)
- [ ] Teste de criação de recurso (`createResource`)
- [ ] Teste de atualização de recurso (`updateResource`)
- [ ] Teste de deleção de recurso (`deleteResource`)
- [ ] Teste de tratamento de erros (OperationOutcome)

## Como rodar

```sh
# Exemplo de chamada usando HTTPie
http POST :8000/florence_mcp tools/call name==listResourceTypes Authorization:"Bearer <TOKEN>"
```

## Observações
- Os testes automatizados serão implementados em breve (pytest ou script Python).
- Resultados e logs devem ser documentados neste arquivo.
