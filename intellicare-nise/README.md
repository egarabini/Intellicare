# intellicare-nise

**NISE - Núcleo de Inteligência em Saúde e Educação** — Módulo de treinamento assistido e chatbot inteligente do IntelliCare.

Homenagem a **Nise da Silveira**, psiquiatra brasileira pioneira em tratamentos humanizados.

## 🎯 O que faz

- **Chatbot Dr. Nise**: Assistente virtual para treinamento médico
- **Integração Oswaldo**: Consulta diagnósticos, alertas e planos de cuidado
- **RAG (Retrieval Augmented Generation)**: Busca contextual em guidelines clínicas
- **Flowise Integration**: Plataforma visual para chatflows LLM
- **Ollama Integration**: LLM local (llama2, mistral)

## 🏗️ Arquitetura

```
NISE API (FastAPI)
    ↓
┌─────────────────────────────────────┐
│  Flowise Chatbot Builder            │
│  - LangChain Tools                  │
│  - RAG Workflows                    │
│  - Custom Tools (Oswaldo, Florence) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Ollama LLM Engine                  │
│  - llama2:7b                        │
│  - mistral:7b                       │
│  - Local inference                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Oswaldo API (Port 8002)            │
│  - Diagnósticos                     │
│  - Alertas                          │
│  - Planos de Cuidado                │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Instalar
pip install -e ".[dev]"

# Rodar API
uvicorn nise.api.app:app --reload --port 8000

# Rodar testes
pytest tests/ -v --cov=nise
```

## 📦 Deployment Completo

### Pré-requisitos

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Python** 3.11+ (para desenvolvimento local)
- **Git**

### Instalação com Docker (Recomendado)

```bash
# 1. Clone o repositório
cd ./intellicare-nise

# 2. Copiar arquivo de ambiente
cp .env.example .env

# 3. Editar variáveis (opcional)
nano .env

# 4. Subir todos os serviços
docker-compose up -d

# 5. Verificar status
docker-compose ps

# 6. Baixar modelo Ollama
docker exec -it intellicare-nise-ollama ollama pull llama2:7b

# 7. Verificar logs
docker-compose logs -f nise
```

### Serviços Disponíveis

Após subir os containers:

- **NISE API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Flowise**: http://localhost:3000 (admin/admin123)
- **Ollama**: http://localhost:11434
- **PostgreSQL**: localhost:5432 (nise/nise123)
- **Redis**: localhost:6379

### Configurar Chatbot Dr. Nise

1. Acessar Flowise: http://localhost:3000
2. Login: `admin` / `admin123`
3. Seguir guia: `docs/GUIA_CONFIGURACAO_FLOWISE.md`
4. Criar chatflow "Dr. Nise - Assistente Médico"
5. Testar: `python scripts/test_chatbot.py`

### Desenvolvimento Local

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -e ".[dev]"

# 3. Configurar variáveis de ambiente
cp .env.example .env
nano .env

# 4. Subir serviços auxiliares
docker-compose up -d redis postgres flowise ollama

# 5. Executar aplicação
uvicorn nise.api.app:app --reload --port 8000
```

### Comandos Úteis

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Ver logs de um serviço específico
docker-compose logs -f nise

# Reiniciar um serviço
docker-compose restart nise

# Executar comando dentro do container
docker exec -it intellicare-nise bash

# Verificar health
curl http://localhost:8000/health

# Testar endpoint
curl http://localhost:8000/api/v1/oswaldo/paciente/pac-123/resumo

# Teste automatizado do chatbot
python scripts/test_chatbot.py
```

## 📂 Estrutura

```
intellicare-nise/
  nise/
    config.py                  # NiseConfig (pydantic-settings)
    api/
      app.py                   # FastAPI
      endpoints/
        oswaldo.py             # Endpoints Oswaldo integration
        florence.py            # Endpoints Florence (chatbot)
        health.py              # Health check
    services/
      oswaldo_client.py        # Cliente HTTP Oswaldo
      flowise_client.py        # Cliente Flowise
      cache.py                 # Redis cache
      flowise_oswaldo_tool.py  # LangChain Tool para Oswaldo
      flowise_framingham_tool.py # LangChain Tool para Framingham
    models/
      oswaldo_models.py        # Modelos Pydantic
    database/
      session.py               # SQLAlchemy session
  tests/                       # Testes
  Dockerfile
  docker-compose.yml           # Porta 8000
```

## 🔌 Endpoints

### Oswaldo Integration

```http
GET /api/v1/oswaldo/paciente/{paciente_id}/resumo
```

Retorna resumo do paciente com:
- Diagnósticos ativos
- Alertas críticos
- Plano de cuidado atual
- Risco Framingham (futuro)

### Florence Chatbot

```http
POST /api/v1/florence/chat
{
  "message": "Qual o diagnóstico de diabetes do paciente João?",
  "session_id": "session-123"
}
```

## 🧪 Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=nise --cov-report=html

# Apenas integração
pytest tests/test_oswaldo_integration.py -v
```

## 🐳 Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f nise
```

## 📊 Monitoramento

- **Health**: `GET /health`
- **Info**: `GET /api/v1/info`
- **Metrics**: `GET /metrics` (Prometheus)

## 🔐 Autenticação

Integrado com **Keycloak** via `intellicare-auth`:

```python
from intellicare_auth import require_auth, require_role

@router.get("/oswaldo/paciente/{id}/resumo")
@require_auth
@require_role("medico", "enfermeiro")
async def get_resumo_paciente(id: str):
    ...
```

## 📝 Licença

MIT

## 👥 Responsáveis

- **DEV1**: Documentação
- **DEV2**: Implementação

