# Changelog - IntelliCare NISE

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [1.0.0] - 2026-02-15

### 🎉 Lançamento Inicial - Semana 1 Completa

Implementação completa da **Semana 1** do Projeto 06 - Integração Oswaldo + NISE + Kestra.

---

## 📅 Dia 1 - Cliente HTTP Oswaldo (15/02/2026)

### ✅ Adicionado

#### **Cliente HTTP Oswaldo** (`oswaldo_client.py`)
- Cliente HTTP async com httpx para integração com módulo Oswaldo
- Métodos implementados:
  - `get_diagnosticos()`: Busca diagnósticos de doenças crônicas
  - `get_alertas()`: Busca alertas clínicos
  - `get_plano_cuidado()`: Busca plano de cuidado
  - `get_resumo()`: Busca resumo completo do paciente
- Error handling completo com logging estruturado
- Timeout configurável (default: 10s)

#### **Serviço de Cache Redis** (`cache.py`)
- Cache service com Redis para otimização de performance
- Métodos implementados:
  - `get()`: Buscar valor do cache
  - `set()`: Armazenar valor com TTL
  - `delete()`: Remover valor
  - `exists()`: Verificar existência
  - `clear_pattern()`: Limpar por padrão
  - `get_stats()`: Estatísticas de hit rate
- TTL configurável (default: 5 minutos)
- JSON serialization automática

#### **API REST FastAPI** (`app.py`, `oswaldo.py`)
- 5 endpoints REST criados:
  - `GET /health`: Health check
  - `GET /api/v1/info`: Informações do módulo
  - `GET /api/v1/oswaldo/paciente/{id}/resumo`: Resumo do paciente
  - `GET /api/v1/oswaldo/paciente/{id}/diagnosticos`: Diagnósticos
  - `GET /api/v1/oswaldo/paciente/{id}/alertas`: Alertas
- Dependency injection com FastAPI Depends
- Documentação OpenAPI automática
- CORS configurado

#### **Modelos Pydantic**
- `DiagnosticoResponse`: Modelo de diagnóstico
- `AlertaResponse`: Modelo de alerta
- `PlanoCuidadoResponse`: Modelo de plano de cuidado
- `ResumoPacienteResponse`: Modelo de resumo

#### **Testes**
- 18 testes unitários implementados
- Cobertura de código: 85%+
- Mocks com pytest-mock

#### **Documentação**
- `README.md`: Guia completo do módulo
- `pyproject.toml`: Configuração do projeto
- `IMPLEMENTACAO_DIA_1_COMPLETO.md`: Relatório detalhado

---

## 📅 Dia 2 - Docker + E2E Tests (15/02/2026)

### ✅ Adicionado

#### **Docker Compose** (`docker-compose.yml`)
- Stack completa com 5 serviços:
  - **nise**: API FastAPI (Port 8000)
  - **redis**: Cache (Port 6379)
  - **postgres**: Database (Port 5432)
  - **flowise**: Chatbot builder (Port 3000)
  - **ollama**: LLM engine (Port 11434)
- Networks configuradas
- Volumes persistentes
- Health checks

#### **Dockerfile**
- Multi-stage build para otimização
- Python 3.11-slim base image
- Dependências instaladas via pip
- Non-root user para segurança

#### **Database** (`init.sql`)
- Schema PostgreSQL com 5 tabelas:
  - `chat_sessions`: Sessões de chat
  - `chat_messages`: Histórico de mensagens
  - `cache_stats`: Estatísticas de cache
  - `api_logs`: Logs de API
  - `flowise_chatflows`: Configurações de chatflows

#### **Configuração** (`config.py`)
- Pydantic Settings para configuração centralizada
- Variáveis de ambiente:
  - API settings (host, port)
  - Redis settings (URL, TTL)
  - Oswaldo integration (base URL)
  - Flowise integration (URL, API key)
  - Ollama integration (URL, model)
- Arquivo `.env.example` com valores padrão

#### **Testes E2E** (`test_e2e_integration.py`)
- 8 testes de integração end-to-end
- Testes com serviços reais (Docker)
- Validação de fluxos completos

#### **Documentação**
- `.env.example`: Exemplo de configuração
- `pytest.ini`: Configuração de testes
- `IMPLEMENTACAO_DIA_2_COMPLETO.md`: Relatório detalhado
- `RESUMO_SEMANA_1_DIAS_1_2.md`: Resumo consolidado

---

## 📅 Dia 3 - Integração Flowise (15/02/2026)

### ✅ Adicionado

#### **LangChain Tools** (`flowise_oswaldo_tool.py`)
- 3 Custom Tools para integração com Oswaldo:
  - **OswaldoDiagnosticoTool**: Busca diagnósticos
  - **OswaldoAlertasTool**: Busca alertas (com emojis 🔴/🟡)
  - **OswaldoResumoTool**: Busca resumo completo
- Herdam de `BaseTool` (LangChain)
- Schemas Pydantic para validação de input
- Formatação amigável das respostas
- Error handling completo

#### **Cliente Flowise** (`flowise_client.py`)
- Cliente HTTP async para API Flowise
- Métodos implementados:
  - `chat()`: Enviar mensagem para chatbot
  - `get_chatflows()`: Listar chatflows disponíveis
  - `get_chatflow()`: Buscar detalhes de chatflow
  - `health_check()`: Verificar disponibilidade
  - `close()`: Fechar conexão
- Modelos Pydantic: `ChatRequest`, `ChatResponse`
- Suporte a API key e session ID

#### **Endpoints Chatbot** (`chatbot.py`)
- 5 endpoints REST para chatbot:
  - `POST /api/v1/chatbot/chat`: Enviar mensagem
  - `GET /api/v1/chatbot/chatflows`: Listar chatflows
  - `GET /api/v1/chatbot/chatflows/{id}`: Detalhes chatflow
  - `GET /api/v1/chatbot/health`: Health check
  - `POST /api/v1/chatbot/test`: Teste automatizado (3 perguntas)
- Dependency injection com FlowiseClient
- Documentação OpenAPI completa

#### **Testes** (`test_chatbot.py`)
- 8 testes unitários para endpoints de chatbot
- Mocks com AsyncMock
- Fixtures reutilizáveis
- Cobertura completa dos endpoints

#### **Script de Teste** (`scripts/test_chatbot.py`)
- Script Python para testar chatbot em produção
- 4 tipos de testes:
  - Health check
  - Listar chatflows
  - Perguntas individuais
  - Teste automatizado
- Output formatado com emojis

#### **Documentação**
- `docs/GUIA_CONFIGURACAO_FLOWISE.md`: Guia completo de configuração
  - Passo a passo de setup
  - JSON dos 3 Custom Tools
  - System Message para Agent
  - Troubleshooting
- `IMPLEMENTACAO_DIA_3_COMPLETO.md`: Relatório detalhado

---

## 📅 Dia 4 - Documentação Semana 1 (15/02/2026)

### ✅ Adicionado

#### **Documentação de API** (`docs/API_REFERENCE.md`)
- Referência completa da API REST
- Todos os endpoints documentados
- Modelos de dados
- Códigos de erro
- Exemplos de uso

#### **Guia de Uso** (`docs/GUIA_USO_CHATBOT.md`)
- Guia para usuários finais do chatbot
- Exemplos de perguntas
- Dicas de uso
- Perguntas frequentes
- Troubleshooting

#### **README Atualizado**
- Seção de deployment completo
- Instruções Docker
- Comandos úteis
- Links para documentação

#### **Changelog** (`CHANGELOG.md`)
- Histórico completo de mudanças
- Organizado por dia de implementação
- Formato Keep a Changelog

---

## 📊 Estatísticas Gerais - Semana 1

### Arquivos Criados
- **Total**: 30 arquivos
- **Código**: ~2.965 linhas
- **Testes**: 34 testes (85%+ cobertura)
- **Documentação**: 7 documentos

### Componentes
- **Endpoints REST**: 10 endpoints
- **LangChain Tools**: 3 tools
- **Serviços Docker**: 5 serviços
- **Schemas Pydantic**: 10 modelos

### Tempo de Implementação
- **Dia 1**: 3 horas
- **Dia 2**: 3 horas
- **Dia 3**: 3 horas
- **Dia 4**: 2 horas
- **Total**: 11 horas

---

## 🔜 Próximos Passos

### Semana 2: Kestra Workflows (10-15h)
- Workflow: Alerta Crítico → Notificação
- Workflow: Reclassificação Automática
- Workflow: Acompanhamento Periódico

### Semana 3: Framingham (8-12h)
- Calculadora de risco cardiovascular
- API REST para cálculo
- Integração com planos de cuidado

### Semana 4: Testes + Documentação (6-10h)
- Testes E2E completos
- Performance tests (<200ms p95)
- Documentação final
- Apresentação stakeholders

---

**Responsável**: DEV2  
**Projeto**: 06 - Integração Oswaldo + NISE + Kestra  
**Status**: Semana 1 - ✅ COMPLETA

