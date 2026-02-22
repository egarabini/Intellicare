# Relatório de Análise: FHIR-AgentEval-main
## Relevância para o Projeto IntelliCare

**Data:** Junho 2025  
**Autor:** Equipe de Arquitetura IntelliCare  
**Módulo Analisado:** `FHIR-AgentEval-main/`  
**Arquivos Lidos:** 25+ arquivos-fonte, ~6.000 linhas de código  

---

## 1. Resumo Executivo

O **FHIR-AgentEval** é um sandbox modular para avaliar agentes LLM em workflows clínicos FHIR de ponta a ponta. Contém **43 tarefas clínicas reutilizáveis**, uma camada MCP para CRUD FHIR, um sistema de memória de longo prazo baseado em Reflexion (FAISS), e um framework completo de avaliação com validação determinística + LLM.

**Veredicto: ALTAMENTE RELEVANTE para IntelliCare.** O módulo oferece padrões arquiteturais, código reutilizável e metodologias que podem fortalecer significativamente WANDA, MINERVA, PIERRE e o ecossistema FHIR do projeto (Florence/Oswaldo).

---

## 2. O que é o FHIR-AgentEval

### 2.1 Visão Geral
- **Propósito:** Framework de benchmark para avaliar quão bem agentes LLM executam tarefas clínicas FHIR
- **43 tarefas modulares** cobrindo: cadastro de pacientes, histórico médico, planos cirúrgicos, seguros, agendamento, listas de espera, pedidos de testes genéticos
- **Model-agnostic:** Funciona com qualquer LLM via LangChain/LangGraph
- **MCP-first:** Todas as interações FHIR via servidores MCP (Model Context Protocol)

### 2.2 Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                    Experiment Runner                         │
│  (run_experiment_fhir.py - 5 configs de agente)             │
├──────────────┬──────────────┬───────────────────────────────┤
│   Baseline   │ Plan-Execute │    Plan-Execute v2            │
│   (ReAct)    │   v1         │  (OpenAI Tools API)           │
├──────────────┴──────────────┴───────────────────────────────┤
│              AgentConfig / FHIRAgentInterface                │
├─────────────────────────────────────────────────────────────┤
│           ToolProviders (MCP / REST / Multi-MCP)            │
├──────────┬───────────┬──────────────────────────────────────┤
│ FHIR MCP │ Specs MCP │     Memory MCP (Reflexion LTM)      │
│ Server   │ Server    │  (FAISS macro + micro reflections)   │
├──────────┴───────────┴──────────────────────────────────────┤
│              HAPI FHIR Server (Docker)                      │
└─────────────────────────────────────────────────────────────┘
           ↕                        ↕
    Deterministic              Soft Validator
     Validator                  (LLM-based)
```

### 2.3 Stack Tecnológica

| Componente | Tecnologia | Versão |
|------------|-----------|--------|
| Orquestração LLM | LangChain + LangGraph | 0.3.27 / 0.6.4 |
| Protocolo MCP | fastmcp | 2.11.2 |
| Memória vetorial | FAISS (CPU) | 1.8.0 |
| Embeddings | OpenAI text-embedding-3-small | - |
| Servidor FHIR | HAPI FHIR (Docker) | R4 |
| HTTP assíncrono | httpx | - |
| Validação | OpenAI API (o3/o4-mini) | - |

---

## 3. Componentes Analisados em Detalhe

### 3.1 Servidor MCP FHIR (`environment/mcp/baseline_server/fhir_mcp_server.py`)

**416 linhas** — Servidor FastMCP expondo 5 ferramentas FHIR CRUD:

| Tool MCP | Operação FHIR | Descrição |
|----------|---------------|-----------|
| `listResourceTypes` | GET /metadata | Lista tipos de recurso suportados |
| `getResourceById` | GET /{type}/{id} | Lê recurso individual |
| `searchResources` | GET /{type}?params | Busca com paginação automática |
| `createResource` | POST /{type} | Cria recurso (body JSON string) |
| `updateResource` | PUT /{type}/{id} | Substitui recurso completo |
| `deleteResource` | DELETE /{type}/{id} | Remove recurso |

**Padrões Notáveis:**
- **Error handling sofisticado:** Erros HTTP não causam exceções — retornam objetos estruturados com `OperationOutcome` parseado (issue codes, diagnostics, expressions)
- **Paginação transparente:** `searchResources` segue `Bundle.link[next]` automaticamente
- **SearchParams Pydantic:** Validação e normalização de parâmetros de busca FHIR com aliases (`count` → `_count`, `sort` → `_sort`)
- **Conditional Create:** Suporte a `If-None-Exist` header para idempotência
- **Self-test:** Modo `--selftest` para verificação rápida de conectividade

### 3.2 Servidor MCP de Memória Reflexion (`environment/mcp/memory_servers/fhir_memory_mcp_server.py`)

**165 linhas** — Servidor MCP expondo 4 ferramentas de memória de longo prazo:

| Tool MCP | Função |
|----------|--------|
| `search_memory` | Busca flexível (macro ou micro) — entrada principal |
| `search_macro_reflections` | Busca semântica de reflexões de alto nível |
| `search_micro_tips` | Busca filtrada por (resource, operation) |
| `memory_stats` | Contagem de vetores para debug |

**Padrão Reflexion:**
- **Memória Macro:** Lições de alto nível (estratégia, ordenação de ferramentas, pré-condições) — busca por similaridade semântica via FAISS
- **Memória Micro:** Tips atômicas vinculadas a pares (resource, operation) — busca por metadata filter + recência
- **FAISS + JSONL:** Índices persistidos em disco, metadata em JSONL para auditabilidade
- **Re-init a cada chamada:** Garante que novas reflexões adicionadas por outro processo sejam visíveis

### 3.3 Servidor MCP de Referência FHIR (`environment/mcp/memory_servers/fhir_ref_mcp_server.py`)

**395 linhas** — Servidor MCP que expõe especificações FHIR R4 locais (sem chamadas ao servidor FHIR live):

| Tool MCP | Função |
|----------|--------|
| `listResources` | Descobre quais specs estão disponíveis localmente |
| `getStructureDefinition` | StructureDefinition snapshot (campos obrigatórios, tipos, bindings) |
| `getSearchParams` | SearchParameters (códigos, tipos, comparadores, chains) |
| `getDataTypeDefinition` | Specs de data types complexos (Identifier, Address, etc.) |

**Relevância:** Permite que o agente **consulte a especificação FHIR** em runtime antes de construir payloads, reduzindo erros de schema.

### 3.4 Workflow de Reflexion (`training/fhir_reflexion_workflow.py`)

**759 linhas** — Loop de auto-aprendizado:

```
Para cada tarefa × max_trials:
  1. ACTOR: Agente ReAct local executa tarefa com ferramentas FHIR
  2. TRAJECTORY: Coleta completa de tool calls (RAW para juízes)
  3. DETERMINISTIC EVAL: validate_response() com assertions
  4. FAILURE DIAGNOSTICS: identify_failure_mode() (seleção, ordem, recurso, proibidos)
  5. LLM EVALUATOR: GPT-4.1 analisa trajetória + constraints → score + critique
  6. SELF-REFLECTION: o4-mini (com acesso a specs FHIR) → reflection_text + micro tips + heuristic
  7. STORE TO LTM: Salva macro + micro no FAISS para próximas tentativas
  
  Se passou → para. Se falhou → retry com memória atualizada.
```

**Inovações Chave:**
- **Wrapped tools:** Agente vê versão resumida dos outputs; juízes veem RAW completo
- **Budget management:** `budgeted_json()` preserva estrutura mas limita tamanho
- **OperationOutcome preservation:** Erros FHIR são mantidos integralmente para os juízes
- **Prompt paraphrasing:** Testa robustez com variações do prompt original

### 3.5 Soft Validator (`utils/soft_validator.py`)

**245 linhas** — Validador LLM complementar:

| Flag | Significado |
|------|-------------|
| `agreement_success` | Ambos (determinístico + LLM) concordam: sucesso |
| `agreement_failure` | Ambos concordam: falha |
| `validator_too_strict` | Determinístico falhou, LLM diz que passou (falso negativo) |
| `validator_too_loose` | Determinístico passou, LLM diz que falhou (falso positivo) |

**Adicional:** Classifica o último tool call em `syntax_error`, `logical_error`, `none`, ou `unclear`.

### 3.6 Tool Providers (`utils/tool_providers.py`)

**254 linhas** — Abstração para carregamento de ferramentas:

- `MCPToolProvider`: Carrega ferramentas de um servidor MCP via SSE
- `MultiMCPToolProvider`: Combina ferramentas de múltiplos servidores MCP com resolução de conflitos de nomes
- `RESTToolProvider`: Envelopa endpoint REST FHIR em 5 StructuredTools LangChain

### 3.7 Callbacks (`utils/callbacks.py`)

- `ToolCallRecorder`: Registra ordem, args, output, duração de cada tool call
- `LLMUsageRecorder`: Captura tokens (prompt/completion), timing, por chamada LLM
- `HistorySink`: Mantém histórico de conversação estilo OpenAI Tools API

### 3.8 Agente Plan-and-Execute v2 (`agent/fhir_plan_execute_agent_v2.py`)

**432 linhas** — Arquitetura de 3 fases:

1. **Planner** (OpenAI Tools agent): Usa ferramentas (incluindo memória e specs) para criar plano JSON com steps e tool assignments
2. **Executor** (OpenAI Tools agent persistente): Executa cada step com constraint de ferramenta permitida
3. **Finalizer** (LLM simples): Sintetiza resposta final a partir das notas de execução

### 3.9 Framework de Tarefas (`tasks/fhir_tasks_modular/`)

**48 arquivos** implementando 43+ tarefas com:

- `get_param_schema()`: JSON Schema para parâmetros variáveis
- `get_prompt()`: Prompt em linguagem natural para o agente
- `prepare_test_data()` / `cleanup_test_data()`: Setup/teardown de dados no FHIR
- `validate_response()`: Validação determinística rigorosa
- `validate_response_light()`: Validação leve (campos presentes, não valores)
- `identify_failure_mode()`: Diagnóstico estruturado (tool selection, order, resource type, prohibited)
- `execute_human_agent()`: Implementação de referência (gold standard)

### 3.10 Experiment Runner (`experiments/run_experiment_fhir.py`)

**669 linhas** — Harness de experimentação:

- **5 configurações de agente** testadas sistematicamente:
  1. Baseline (sem memória, sem specs)
  2. Baseline + References (specs FHIR)
  3. Baseline + Memory (treinada sem specs)
  4. Baseline + Memory (treinada com specs)
  5. Baseline + Memory + References (completo)
- Saída JSON reprodutível com proveniência (prompt, endpoints, model_id)
- CSV summary para análise

---

## 4. Padrões Arquiteturais de Alto Valor

### 4.1 🔑 Hierarchia de Interface de Agente

```python
BaseAgent (ABC)
  ├── ainit(), arun_text() → CoreResult
  └── AgentConfig (model_id, transport, endpoint, temperature, extra)

FHIRAgentInterface(BaseAgent)
  ├── arun_task_entry(task_entry) → Dict
  └── arun_task_variations_from_yaml(yaml_path) → List[Dict]
```

**Por que importa para IntelliCare:** WANDA orquestra múltiplos agentes (MINERVA, PIERRE, Florence). Um contrato baseado em `BaseAgent` + `AgentConfig` padronizaria a interface de todos os agentes, permitindo trocá-los, testá-los e compará-los uniformemente.

### 4.2 🔑 Multi-MCP Provider

O `MultiMCPToolProvider` combina ferramentas de N servidores MCP, resolvendo conflitos de nome com prefixação automática.

**Por que importa para IntelliCare:** WANDA já conecta a MINERVA e PIERRE via MCP. Este pattern permite escalar para mais agentes sem código ad-hoc de combinação.

### 4.3 🔑 Dual Validation (Deterministic + Soft)

- **Determinístico:** Assertions exatas contra o servidor FHIR (dados realmente criados/modificados)
- **Soft (LLM):** Julgamento independente que detecta falsos positivos/negativos do validador

**Por que importa para IntelliCare:** Hoje não existe avaliação automatizada da qualidade dos agentes. Este padrão dual permitiria medir a eficácia real de WANDA na orquestração.

### 4.4 🔑 Reflexion Memory Loop

O padrão Reflexion permite que o agente **aprenda com seus próprios erros** através de memória persistente em FAISS, sem fine-tuning do modelo.

**Por que importa para IntelliCare:** WANDA poderia acumular experiência operacional — "quando OCR falha em documentos de alta, tente pré-processar com contrast enhancement" ou "para pacientes com múltiplos planos, sempre verificar vigência antes de IPS".

### 4.5 🔑 FHIR Specs at Runtime

O servidor de specs permite que o agente consulte StructureDefinitions e SearchParameters antes de construir requests FHIR.

**Por que importa para IntelliCare:** Florence e Oswaldo interagem com FHIR. Disponibilizar specs FHIR via MCP evitaria erros de schema em runtime.

---

## 5. Recomendações Concretas de Integração

### 5.1 PRIORIDADE ALTA — Adoção Imediata

#### R1: Servidor MCP FHIR para Florence/Oswaldo
**O que:** Adaptar `fhir_mcp_server.py` como interface MCP para o servidor FHIR do IntelliCare (Florence).  
**Esforço:** 2-3 dias  
**Benefício:** WANDA poderia fazer CRUD FHIR via MCP, unificando o protocolo de comunicação  
**Ação:**
```
MODULARIZACAO/intellicare-florence/mcp/
  └── florence_fhir_mcp_server.py   # Adaptado de fhir_mcp_server.py
```

#### R2: MultiMCPToolProvider no WandaMCPClient
**O que:** Substituir a lógica ad-hoc de `WandaMCPClient` pelo pattern `MultiMCPToolProvider` do FHIR-AgentEval.  
**Esforço:** 1-2 dias  
**Benefício:** Resolução automática de conflitos de nome, escalabilidade para novos agentes  

#### R3: Callbacks de Observabilidade
**O que:** Integrar `ToolCallRecorder` e `LLMUsageRecorder` na pipeline de WANDA.  
**Esforço:** 1 dia  
**Benefício:** Visibilidade completa em: quais ferramentas foram chamadas, em que ordem, quanto tempo levaram, quantos tokens consumiram  

### 5.2 PRIORIDADE MÉDIA — Próxima Fase

#### R4: Framework de Avaliação de Agentes
**O que:** Criar um harness de avaliação inspirado no `run_experiment_fhir.py` para testar WANDA sistematicamente.  
**Esforço:** 1-2 semanas  
**Componentes:**
- Tarefas de teste definidas em YAML (ex: "extraia os dados deste PDF de alta e registre no FHIR")
- Validação determinística (dados realmente chegaram ao FHIR)
- Soft validation (LLM julga qualidade da orquestração)
- Métricas: taxa de sucesso, tokens consumidos, tempo de execução, ferramentas usadas

#### R5: Memória Reflexion para WANDA
**O que:** Implementar FAISS-based LTM para que WANDA acumule experiência operacional.  
**Esforço:** 1 semana  
**Design:**
```
MODULARIZACAO/intellicare-wanda/wanda/memory/
  ├── reflexion_store.py      # Adaptado de fhir_reflexion_memory_store.py
  ├── memory_mcp_server.py    # Expõe search_memory via MCP
  └── indexes/
      ├── macro_index.faiss
      └── micro_meta.jsonl
```
- **Macro memories:** "Para documentos de UTI, priorize OCR de MINERVA antes de buscar no Florence"
- **Micro memories:** "(DiagnosticReport, searchResources) → sempre incluir _sort=-date e _count=5"

#### R6: FHIR Specs Server para Desenvolvimento
**O que:** Disponibilizar `fhir_ref_mcp_server.py` como recurso de desenvolvimento para todos os módulos IntelliCare.  
**Esforço:** 2-3 dias  
**Benefício:** Qualquer agente pode consultar a spec FHIR antes de fazer requests, reduzindo erros de integração  

### 5.3 PRIORIDADE FUTURA — Visão Estratégica

#### R7: Plan-and-Execute para WANDA
**O que:** Evoluir WANDA de dispatcher simples para arquitetura Plan-Execute com:
- **Planner** que consulta memória + specs para criar plano
- **Executor** que chama MINERVA/PIERRE/Florence conforme o plano
- **Finalizer** que sintetiza resultado para o profissional de saúde

#### R8: Pipeline de Avaliação Contínua
**O que:** Integrar avaliação de agentes no CI/CD:
- YAML com cenários clínicos de regressão
- Comparação automática entre versões de agentes
- Dashboard de métricas (Grafana)

#### R9: Prompt Paraphrasing para Robustez
**O que:** Testar que WANDA funciona com variações linguísticas do mesmo pedido clínico.

---

## 6. Código Diretamente Reutilizável

| Arquivo Source | Destino IntelliCare | Adaptação Necessária |
|----------------|---------------------|---------------------|
| `fhir_mcp_server.py` | Florence MCP Server | Trocar HAPI URL, adicionar autenticação |
| `tool_providers.py` → `MultiMCPToolProvider` | WANDA MCP Client | Integrar no WandaToolRegistry |
| `callbacks.py` → `ToolCallRecorder`, `LLMUsageRecorder` | WANDA Core | Plug direto no LangChain |
| `fhir_reflexion_memory_store.py` | WANDA Memory | Adaptar categorias macro/micro |
| `soft_validator.py` | intellicare-eval (novo) | Generalizar prompt para cenários IntelliCare |
| `core_agent_interface.py` | Agent Interface padrão | Usar como base para todos os agentes |
| `fhir_ref_mcp_server.py` | Dev Tools | Deploy como serviço local permanente |
| `task_interface_modular.py` | Test Framework | Adaptar para cenários clínicos IntelliCare |

---

## 7. Riscos e Considerações

| Risco | Mitigação |
|-------|-----------|
| Dependência de OpenAI API (embeddings, validação) | Preparar fallback para modelos locais (Qwen, já em PIERRE) |
| FAISS sem persistência distribuída | Para MVP suficiente; evoluir para Qdrant/Milvus se escalar |
| Complexidade do Reflexion loop | Começar com memória estática (curada manualmente), depois automatizar |
| 43 tarefas são FHIR-específicas | Mapear para cenários IntelliCare; não copiar tarefas diretamente |
| Licenciamento | Verificar licença do FHIR-AgentEval antes de copiar código |

---

## 8. Resumo de Impacto

| Área IntelliCare | Impacto do FHIR-AgentEval | Nível |
|------------------|--------------------------|-------|
| WANDA (orquestração) | MultiMCP, Plan-Execute, Reflexion Memory | 🔴 ALTO |
| Florence/Oswaldo (FHIR) | MCP Server FHIR, Specs Server | 🔴 ALTO |
| MINERVA/PIERRE (agentes) | Interface padronizada, callbacks | 🟡 MÉDIO |
| Qualidade/Testes | Evaluation framework, soft validator | 🔴 ALTO |
| Observabilidade | ToolCallRecorder, LLMUsageRecorder | 🟡 MÉDIO |
| DevEx | FHIR specs at runtime | 🟡 MÉDIO |

---

## 9. Próximos Passos Sugeridos

1. **Imediato:** Copiar e adaptar `fhir_mcp_server.py` para Florence → teste de integração WANDA↔Florence via MCP
2. **Semana 1:** Integrar `ToolCallRecorder` + `LLMUsageRecorder` em WANDA para visibilidade operacional
3. **Semana 2:** Implementar `MultiMCPToolProvider` no `WandaMCPClient`
4. **Semana 3-4:** Criar primeiro YAML de cenários de teste clínico + harness de avaliação
5. **Mês 2:** Implementar Reflexion memory para WANDA com FAISS
6. **Mês 3:** Evoluir para arquitetura Plan-Execute

---

*Este relatório foi gerado após análise completa de 25+ arquivos-fonte do módulo FHIR-AgentEval-main, totalizando ~6.000 linhas de código Python e documentação.*
