# Segurança IAM (Keycloak)

O WANDA suporta autenticação e autorização centralizadas via Keycloak, usando a biblioteca `intellicare-auth`.

## Como integrar
1. Execute `setup_keycloak.py` em `intellicare-auth` para gerar `keycloak_client_secrets.json`.
2. Adicione a dependência `intellicare-auth` ao requirements.txt do módulo.
3. Importe e configure o middleware/authenticator do intellicare-auth no seu app (exemplo FastAPI):

```python
from intellicare_auth.fastapi import configure_auth
from fastapi import FastAPI

app = FastAPI()
configure_auth(app, secrets_path="keycloak_client_secrets.json")
```

4. Proteja endpoints sensíveis com autenticação JWT e roles:

```python
from intellicare_auth.fastapi import require_role

@app.get("/dados-sensiveis")
@require_role("clinico")
def dados():
  ...
```

## Referências
- Veja `INTEGRACAO_SEGURANCA_IAM.md` para plano completo e exemplos
- Consulte a documentação do intellicare-auth para detalhes de configuração

---
# FHIR Specs Server

O WANDA agora inclui um servidor de especificações FHIR para servir schemas, exemplos e documentação customizada via API REST.

## Como usar
Execute o servidor:

```bash
uvicorn fhir_specs_server:app --reload
```

Endpoints disponíveis:
- `/schemas/{resource}` — retorna o schema JSON do recurso (ex: Patient)
- `/examples/{resource}` — retorna exemplo JSON do recurso
- `/docs/{resource}` — retorna documentação (placeholder)

Exemplo:
```bash
curl http://localhost:8000/schemas/Patient
curl http://localhost:8000/examples/Patient
```

Os schemas e exemplos podem ser expandidos conforme necessário para suportar múltiplos perfis e versões FHIR.

---
# Framework de Avaliação

O WANDA agora suporta testes automatizados e avaliação de agentes, inspirado no padrão FHIR-AgentEval.

## Componente
- `EvaluationHarness`: executa testes, coleta métricas e exporta resultados

## Como usar
No `PresentationEngine`, o framework já está integrado:

```python
engine = PresentationEngine()
...
# Adicionar teste
engine.add_evaluation_test(name="Test slide count", func=lambda: engine.slide_manager.get_total_slides(), expected=10)
# Rodar todos os testes
engine.run_evaluation()
# Exportar resultados
results = engine.export_evaluation_results()
```

## Exportação
O método `export_evaluation_results()` retorna lista de dicionários com nome, saída, esperado, status e metadados de cada teste.

---
# Reflexion Memory

O WANDA agora suporta memória iterativa de reflexões de agentes, inspirada no padrão FHIR-AgentEval.

## Componente
- `ReflexionMemory`: armazena reflexões/memórias de agentes (ex: perguntas e respostas, raciocínio incremental)

## Como usar
No `PresentationEngine`, a memória já está integrada:

```python
engine = PresentationEngine()
...
# Adicionar reflexão
engine.append_reflexion(agent="wanda", content="Texto da reflexão")
# Consultar últimas reflexões
mems = engine.query_reflexion_memory(agent="wanda", limit=5)
# Exportar todas
all_mems = engine.export_reflexion_memory()
```

Exemplo de registro automático:
- Ao responder pergunta para Wanda: pergunta e resposta são gravadas como reflexão

## Exportação
O método `export_reflexion_memory()` retorna lista de dicionários prontos para análise, exportação ou integração com frameworks de avaliação.

---
# Observabilidade e Tracing

O WANDA agora suporta tracing detalhado de chamadas de ferramentas e uso de LLMs, inspirado no padrão FHIR-AgentEval.

## Componentes
- `ToolCallRecorder`: registra chamadas de ferramentas (ex: navegação de slides, agentes MCP, etc)
- `LLMUsageRecorder`: registra prompts/respostas de LLMs (ex: perguntas para Wanda)

## Como usar
No `PresentationEngine`, os gravadores já estão integrados:

```python
engine = PresentationEngine()
...
# Exportar traces de ferramentas
tool_calls = engine.export_tool_calls()
# Exportar uso de LLMs
llm_usage = engine.export_llm_usage()
```

Exemplo de registro automático:
- Ao avançar slide: `slide_navigation` é registrado no ToolCallRecorder
- Ao perguntar para Wanda: prompt/resposta é registrado no LLMUsageRecorder

## Exportação
Os métodos `export_tool_calls()` e `export_llm_usage()` retornam listas de dicionários prontos para análise, exportação ou integração com frameworks de avaliação.

---
# intellicare-wanda

**Orquestrador Inteligente** do IntelliCare — homenagem a **Wanda de Aguiar Horta**, enfermeira pioneira na teoria das necessidades humanas basicas.

## O que faz

- **Module Discovery**: Descobre automaticamente quais modulos IntelliCare estao online via HTTP
- **Query Routing**: Analisa a mensagem e roteia para os modulos mais adequados (keyword-based)
- **Multi-Module**: Chama multiplos modulos em paralelo e agrega as respostas
- **Safety Rules**: IPS-First rule, deteccao de dados fabricados, interacoes medicamentosas
- **REST API**: Endpoints para chat, routing preview, modulo management e capabilities

## Quick Start

```bash
# Instalar
pip install -e ".[dev]"

# Rodar API
uvicorn wanda.api.app:app --reload --port 8000

# Rodar testes
pytest tests/ -v --cov=wanda

# Docker
docker compose up --build
```

## API Endpoints

### Contrato LEGO
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/health` | Health check (inclui modules_online) |
| GET | `/api/v1/info` | Informacoes do modulo |

### Orquestracao
| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | `/api/v1/chat` | Chat principal — roteia, chama modulos, agrega |
| POST | `/api/v1/route` | Preview de routing (sem chamar modulos) |

### Modulos
| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/modules` | Status de todos os modulos |
| POST | `/api/v1/modules/discover` | Forcar re-discovery |
| GET | `/api/v1/modules/{name}` | Status de um modulo |
| GET | `/api/v1/capabilities` | Listar modulos por capability |

## Estrutura

```
intellicare-wanda/
  wanda/
    config.py                  # WandaConfig (pydantic-settings)
    api/
      app.py                   # FastAPI (8 endpoints)
    discovery/
      models.py                # ModuleInfo, ModuleResponse, RoutingDecision, OrchestrationResult
      registry.py              # ModuleRegistry (HTTP discovery + calls)
    orchestrator/
      router.py                # QueryRouter (keyword-based routing)
      aggregator.py            # ResponseAggregator (multi-module synthesis)
      orchestrator.py          # WandaOrchestrator (pipeline principal)
    rules/
      safety.py                # SafetyChecker (IPS-First, drug interactions, fabrication)
  tests/                       # 69 testes, 93% cobertura
  Dockerfile
  docker-compose.yml           # Porta 8007
```

## Routing (Keyword-based)

| Query | Modulo |
|-------|--------|
| "funcao renal", "creatinina", "diabetes" | Oswaldo |
| "exame", "laboratorio", "hemograma" | Florence |
| "UBS", "regiao", "CNES" | Zilda |
| "plano de cuidado", "lembrete", "adesao" | Geralda |
| "qualidade", "indicador", "PMAQ" | Donabedian |

## Safety Rules

- **IPS-First**: Alerta quando consulta clinica nao tem patient_id
- **Anti-fabricacao**: Detecta dados inventados nas respostas
- **Interacoes medicamentosas**: Warfarina+aspirina, metformina+alcool, etc.

## Testes

```
69 passed — 93% coverage
- test_models.py      (9 testes) — modelos de dados
- test_registry.py   (12 testes) — module discovery + calls
- test_router.py     (16 testes) — query routing
- test_aggregator.py  (8 testes) — response aggregation
- test_safety.py     (11 testes) — safety rules
- test_config.py      (3 testes) — configuracao
- test_api.py        (10 testes) — API REST
```

## Porta

| Servico | Porta |
|---------|-------|
| API | 8007 (host) -> 8000 (container) |
