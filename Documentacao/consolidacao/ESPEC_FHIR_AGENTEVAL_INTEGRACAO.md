# Especificação Funcional e Técnica — Integração FHIR-AgentEval no IntelliCare

**Data:** 17/02/2026  
**Versão:** 1.0  
**Autor:** Arquiteto IntelliCare  

---

## 1. Objetivo

Integrar os padrões, componentes e arquitetura do FHIR-AgentEval ao ecossistema IntelliCare, com foco em:
- Expor o Florence (servidor FHIR) via MCP
- Unificar orquestração de agentes (WANDA, MINERVA, PIERRE) com MultiMCPToolProvider
- Adotar callbacks de observabilidade
- Implementar memória Reflexion para WANDA
- Criar framework de avaliação automatizada de agentes
- Disponibilizar servidor de specs FHIR para desenvolvimento

---

## 2. Escopo Funcional

### 2.1. Florence exposto via MCP (CRUD FHIR)
- Usuários e agentes poderão criar, buscar, atualizar e deletar recursos FHIR via protocolo MCP (Model Context Protocol)
- Compatível com ferramentas LangChain, WANDA, e automação de testes

### 2.2. Orquestração Multi-Agente (WANDA)
- WANDA poderá consumir ferramentas MCP de múltiplos agentes (MINERVA, PIERRE, Florence) de forma plugável
- Resolução automática de conflitos de nomes de ferramentas

### 2.3. Observabilidade e Tracing
- Todas as chamadas de ferramentas MCP e LLM serão rastreadas (ordem, tempo, tokens, input/output)
- Logs estruturados para análise de performance e troubleshooting

### 2.4. Memória Reflexion (WANDA)
- WANDA armazenará lições aprendidas (macro/micro) em FAISS, consultando-as antes de orquestrar agentes
- Memória persistente, consultável via MCP

### 2.5. Framework de Avaliação de Agentes
- Harness de testes YAML para cenários clínicos
- Validação determinística (assertions) e soft (LLM)
- Métricas: taxa de sucesso, tempo, tokens, ferramentas usadas

### 2.6. Servidor de Specs FHIR
- Serviço MCP que expõe StructureDefinitions, SearchParameters e DataTypes FHIR R4
- Usado por agentes e desenvolvedores para validação dinâmica de payloads

---

## 3. Especificação Técnica

### 3.1. Florence MCP Server
- Base: `fhir_mcp_server.py` do FHIR-AgentEval
- CRUD FHIR: `listResourceTypes`, `getResourceById`, `searchResources`, `createResource`, `updateResource`, `deleteResource`
- Adaptação: trocar endpoint HAPI pelo Florence, adicionar autenticação JWT
- Deploy: `MODULARIZACAO/intellicare-florence/mcp/florence_fhir_mcp_server.py`

### 3.2. MultiMCPToolProvider no WandaMCPClient
- Base: `tool_providers.py` (MultiMCPToolProvider)
- Refatorar `wanda/registry.py` para consumir múltiplos MCP endpoints
- Resolução de nomes automática

### 3.3. Callbacks de Observabilidade
- Base: `callbacks.py` (`ToolCallRecorder`, `LLMUsageRecorder`)
- Plug direto no pipeline LangChain de WANDA
- Logs em JSON estruturado, com opção de exportação para Grafana/Prometheus

### 3.4. Reflexion Memory
- Base: `fhir_reflexion_memory_store.py`
- Adaptar para domínio IntelliCare (categorias macro/micro)
- Deploy: `MODULARIZACAO/intellicare-wanda/wanda/memory/`
- Expor via MCP: `memory_mcp_server.py`

### 3.5. Framework de Avaliação
- Base: `run_experiment_fhir.py`, `task_interface_modular.py`, `soft_validator.py`
- YAML de cenários clínicos
- Scripts de execução e coleta de métricas
- Integração com CI/CD

### 3.6. Servidor de Specs FHIR
- Base: `fhir_ref_mcp_server.py`
- Deploy: `MODULARIZACAO/intellicare-florence/specs_mcp_server.py`
- Indexação de StructureDefinitions e SearchParameters locais

---

## 4. Plano de Implementação (Fases Paralelas)

### Fase 1 — Infraestrutura MCP Florence (Equipe A)
- [ ] Adaptar `fhir_mcp_server.py` para Florence
- [ ] Implementar autenticação JWT
- [ ] Testar CRUD FHIR via MCP

### Fase 2 — MultiMCPToolProvider em WANDA (Equipe B)
- [ ] Refatorar `wanda/registry.py` para MultiMCPToolProvider
- [ ] Testar orquestração com MINERVA, PIERRE, Florence

### Fase 3 — Observabilidade e Tracing (Equipe C)
- [ ] Integrar `ToolCallRecorder` e `LLMUsageRecorder` em WANDA
- [ ] Exportar logs para análise

### Fase 4 — Reflexion Memory (Equipe D)
- [ ] Adaptar `fhir_reflexion_memory_store.py` para WANDA
- [ ] Implementar `memory_mcp_server.py`
- [ ] Testar consulta e persistência de memórias

### Fase 5 — Framework de Avaliação (Equipe E)
- [ ] Criar YAML de cenários clínicos
- [ ] Adaptar `task_interface_modular.py` para domínios IntelliCare
- [ ] Integrar `soft_validator.py` para avaliação LLM
- [ ] Scripts de execução e coleta de métricas

### Fase 6 — Servidor de Specs FHIR (Equipe F)
- [ ] Adaptar `fhir_ref_mcp_server.py` para specs locais do Florence
- [ ] Testar consulta de StructureDefinitions e SearchParameters

---

## 5. Cronograma Sugerido

| Fase | Equipe | Duração Estimada |
|------|--------|------------------|
| 1    | A      | 1 semana         |
| 2    | B      | 1 semana         |
| 3    | C      | 3 dias           |
| 4    | D      | 1 semana         |
| 5    | E      | 2 semanas        |
| 6    | F      | 3 dias           |

---

## 6. Critérios de Aceite
- CRUD FHIR via MCP funcional e autenticado
- WANDA orquestrando MINERVA, PIERRE e Florence via MultiMCP
- Logs detalhados de ferramentas e LLMs disponíveis
- Memória Reflexion consultável e persistente
- Harness de avaliação executando cenários YAML com métricas
- Specs FHIR consultáveis via MCP

---

## 7. Observações
- Todas as fases podem ser desenvolvidas em paralelo por equipes distintas
- Recomenda-se reuniões semanais de integração
- Código deve seguir padrões de lint, tipagem e testes já adotados no IntelliCare

---

*Dúvidas ou sugestões: arquitetura@intelli.care*
