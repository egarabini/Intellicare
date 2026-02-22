# FLOWISE + OLLAMA - GUIA DE INSTALAÇÃO E CONFIGURAÇÃO

## 📋 INFORMAÇÕES GERAIS

**Projeto**: NISE - Treinamento Assistido  
**Módulo**: Flowise + Ollama Setup  
**Versão**: 1.0  
**Data**: 11/03/2026  
**Responsável**: DEV2

---

## 🎯 OBJETIVO

Configurar **Flowise** (RAG + Chatbots + LLM Workflows) e **Ollama** (LLM Engine local) para o módulo NISE, permitindo:

1. **Chatbot "Dr. Nise"**: Assistente virtual para treinamento
2. **RAG (Retrieval Augmented Generation)**: Busca contextual em guidelines clínicas
3. **Avaliação LLM**: Análise automática de decisões clínicas
4. **Workflows LLM**: Automação de processos de treinamento

---

## 🏗️ ARQUITETURA

```
┌─────────────────────────────────────────────────────────────┐
│                     NISE TRAINING MODULE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   FastAPI    │◄────►│   Flowise    │◄────►│  Ollama   │ │
│  │   Backend    │      │  (Port 3000) │      │(Port 11434)│ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                      │  │
│  │  - nise_training (dados FHIR)                        │  │
│  │  - flowise (chatflows, credentials)                  │  │
│  │  - pgvector (embeddings para RAG)                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 COMPONENTES

### 1. **Flowise** (flowiseai/flowise:latest)
- **Função**: Plataforma visual para criar chatflows LLM
- **Porta**: 3000
- **Features**:
  - Interface visual drag-and-drop
  - RAG (Retrieval Augmented Generation)
  - Integração com múltiplos LLMs
  - Armazenamento de chatflows
  - API REST completa

### 2. **Ollama** (ollama/ollama:latest)
- **Função**: Engine para rodar LLMs localmente
- **Porta**: 11434
- **Features**:
  - Execução local (privacidade)
  - Suporte GPU (opcional)
  - Múltiplos modelos
  - API REST

### 3. **PostgreSQL** (postgres:15-alpine)
- **Função**: Banco de dados compartilhado
- **Schemas**:
  - `nise_training`: Dados FHIR do NISE
  - `flowise`: Dados do Flowise
  - `pgvector`: Embeddings para RAG

---

## 🚀 INSTALAÇÃO

### Pré-requisitos:
- Docker 24+
- Docker Compose 2.0+
- 8GB RAM mínimo
- 20GB espaço em disco

### Passo 1: Navegar para o diretório
```bash
cd Documentacao/consolidacao/docs_DEV1/nise/docker
```

### Passo 2: Executar script de setup
```bash
chmod +x setup-flowise-ollama.sh
./setup-flowise-ollama.sh
```

### Passo 3: Aguardar instalação
O script irá:
1. ✅ Verificar Docker
2. ✅ Criar diretórios
3. ✅ Configurar variáveis de ambiente
4. ✅ Iniciar serviços
5. ✅ Baixar modelo llama2:7b (~4GB)
6. ✅ Testar integração

**Tempo estimado**: 10-15 minutos (dependendo da internet)

---

## 🔐 ACESSO

### Flowise UI:
- **URL**: http://localhost:3000
- **Usuário**: admin
- **Senha**: admin123

### Flowise API:
- **URL**: http://localhost:3000/api/v1
- **Docs**: http://localhost:3000/api-docs

### Ollama API:
- **URL**: http://localhost:11434
- **Health**: http://localhost:11434/api/health

---

## 🤖 MODELOS OLLAMA

### Modelo Padrão (Instalado):
- **llama2:7b** (4GB)
  - Propósito geral
  - Boa performance
  - Baixo consumo de recursos

### Modelos Médicos (Opcionais):
```bash
# Meditron (especializado em medicina)
docker exec nise-ollama ollama pull meditron:7b

# BioMistral (biomedicina)
docker exec nise-ollama ollama pull biomistral:7b

# MedAlpaca (Q&A médico)
docker exec nise-ollama ollama pull medalpaca:7b
```

### Listar modelos instalados:
```bash
docker exec nise-ollama ollama list
```

---

## 🧪 TESTES

### Teste 1: Ollama funcionando
```bash
docker exec nise-ollama ollama run llama2:7b "Olá, você está funcionando?"
```

### Teste 2: Flowise acessível
```bash
curl http://localhost:3000/api/v1/health
```

### Teste 3: Integração Flowise + Ollama
1. Acesse http://localhost:3000
2. Login com admin/admin123
3. Crie novo Chatflow
4. Adicione nó "Ollama"
5. Configure: http://ollama:11434
6. Selecione modelo: llama2:7b
7. Teste o chat

---

## 📊 MONITORAMENTO

### Ver logs:
```bash
# Todos os serviços
docker-compose -f docker-compose.flowise.yml logs -f

# Apenas Flowise
docker-compose -f docker-compose.flowise.yml logs -f flowise

# Apenas Ollama
docker-compose -f docker-compose.flowise.yml logs -f ollama
```

### Status dos serviços:
```bash
docker-compose -f docker-compose.flowise.yml ps
```

---

## 🛠️ COMANDOS ÚTEIS

### Parar serviços:
```bash
docker-compose -f docker-compose.flowise.yml down
```

### Reiniciar serviços:
```bash
docker-compose -f docker-compose.flowise.yml restart
```

### Remover tudo (incluindo volumes):
```bash
docker-compose -f docker-compose.flowise.yml down -v
```

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Flowise + Ollama instalados
2. ⏳ Criar chatflow "Dr. Nise"
3. ⏳ Configurar RAG com guidelines clínicas
4. ⏳ Integrar com FastAPI backend
5. ⏳ Criar workflows de avaliação LLM

---

**Documento criado por**: DEV2  
**Data**: 11/03/2026  
**Status**: ✅ **FLOWISE + OLLAMA SETUP COMPLETO**

