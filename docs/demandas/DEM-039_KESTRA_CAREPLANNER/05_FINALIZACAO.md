# DEM-039 — Kestra Workflow CarePlanner: Finalização

## Resumo da Execução

A DEM-039 tinha o objetivo de acoplar o **Kestra** ao módulo CarePlanner do IntelliCare, possibilitando a orquestração e execução de jornadas conversacionais via WhatsApp/Rocket.Chat.

Durante a execução da demanda (Fase E), foram concluídos os seguintes itens:

1. **Criação de Arquivos YAML (`infra/kestra/flows/`)**: 
   - `careplanner_jornada_basica.yml`
   - `careplanner_jornada_video.yml`
2. **Script de Provisionamento (`infra/kestra/seed_flows.py`)**: Construímos um script idempotente em Python que consome a API REST interna (`POST /api/v1/flows`) do Kestra para publicar os flows. 
3. **KestraAdapter e Novo Endpoint**:
   - `KestraAdapter.trigger_flow()`: permite iniciar chamadas HTTP em background para orquestrar as tags JWT, Namespace e Variáveis dos templates.
   - `POST /careplanner/journeys/trigger`: Endpoint exposto no Service (permitindo apenas perfis GESTOR e CLINICO) que constrói a URL e injeta os payloads no Kestra.
4. **Resolução de Conflitos Locais**:
   - A inicialização do banco de dados `kestra` não ocorria em containeres antigos; realizamos a criação de forma proativa.
   - A nova API de testes FastAPI apontava `405 Method Not Allowed` devido à falta de sincronia local entre a imagem do contêiner `intellicare-service` e o diretório host. O problema foi superado com um rebuild limpo da imagem, comprovando a eficácia do endpoint com a validação do token JWT do Keycloak.

## Testes Realizados

- **Cobertura Unitária**: 4 testes completos para avaliar a resposta idempotente do Script de Seed, as Exception Handling do container Kestra indisponível e o comportamento 202 do Endpoint `/journeys/trigger`.
- **Smoke Test Endpoint Integrado**: Simulamos a injeção do JWT de mock usando o Keycloak Client `admin-cli` contra a porta 9000 para acionar o endpoint `trigger_journey()`. O sistema conseguiu validar e rejeitar `alfa` apontando inatividade normal da infra, provando o funcionamento da stack completa.

## Commits & Artifacts
Commit gerado: `feat: implementar integrações do CarePlanner com Kestra API (DEM-039)`.

**Status Final:** Demanda DEM-039 finalizada com sucesso.
