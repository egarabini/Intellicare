# DAGGER CI/CD - GUIA DE INSTALAÇÃO E USO

## 📋 INFORMAÇÕES GERAIS

**Projeto**: NISE - Treinamento Assistido  
**Módulo**: Dagger CI/CD Pipeline  
**Versão**: 1.0  
**Data**: 13/03/2026  
**Responsável**: DEV2

---

## 🎯 OBJETIVO

Configurar **Dagger** para CI/CD do módulo NISE, permitindo:

1. **Testes automatizados**: Executar testes em cada commit
2. **Build de imagens**: Criar imagens Docker de forma reproduzível
3. **Deploy automatizado**: Deploy para ambientes dev/staging/prod
4. **População de dados**: Automatizar população de dados sintéticos
5. **Versionamento**: Controle de versões de LLM workflows

---

## 🏗️ ARQUITETURA DAGGER

```
┌─────────────────────────────────────────────────────────────┐
│                     DAGGER PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Test    │───►│  Lint    │───►│  Build   │───►│ Deploy ││
│  │          │    │          │    │          │    │        ││
│  └──────────┘    └──────────┘    └──────────┘    └────────┘│
│       │               │                │              │      │
│       ▼               ▼                ▼              ▼      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Containers (Isolated & Reproducible)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 INSTALAÇÃO

### Pré-requisitos:
- Docker 24+
- Python 3.11+
- Dagger CLI

### Passo 1: Instalar Dagger CLI
```bash
# Linux/macOS
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Windows (PowerShell)
iwr https://dl.dagger.io/dagger/install.ps1 -useb | iex
```

### Passo 2: Verificar instalação
```bash
dagger version
```

### Passo 3: Instalar dependências Python
```bash
cd Documentacao/consolidacao/docs_DEV1/nise/dagger
pip install -r requirements.txt
```

---

## 🚀 USO

### 1. **Executar Testes**
```bash
# Executar testes do backend
dagger call test --source=../

# Saída esperada:
# ============================= test session starts ==============================
# collected 15 items
# tests/test_generators.py ........                                        [ 53%]
# tests/test_api.py .......                                                [100%]
# ============================== 15 passed in 2.34s ==============================
```

### 2. **Executar Linting**
```bash
# Executar linting do código
dagger call lint --source=../

# Saída esperada:
# All checks passed!
```

### 3. **Build de Imagem Docker**
```bash
# Build da imagem
dagger call build-image --source=../ --tag=v1.0.0

# Saída: Container image built successfully
```

### 4. **Publicar Imagem**
```bash
# Publicar no registry
dagger call publish-image \
  --source=../ \
  --registry=registry.gsi.srv.br \
  --username=admin \
  --password=env:REGISTRY_PASSWORD \
  --tag=v1.0.0

# Saída: registry.gsi.srv.br/nise-backend:v1.0.0
```

### 5. **Deploy para Desenvolvimento**
```bash
# Deploy automático
dagger call deploy-dev \
  --source=../ \
  --db-host=postgres.gsi.srv.br \
  --db-password=env:DB_PASSWORD

# Saída: ✅ Deployed to development environment
```

### 6. **Popular Dados Sintéticos**
```bash
# Popular todos os dados
dagger call populate-data \
  --source=../ \
  --db-host=postgres.gsi.srv.br \
  --db-password=env:DB_PASSWORD \
  --data-type=all

# Popular apenas pacientes
dagger call populate-data \
  --source=../ \
  --db-host=postgres.gsi.srv.br \
  --db-password=env:DB_PASSWORD \
  --data-type=patients
```

---

## 🔄 PIPELINE COMPLETO

### Pipeline de CI (Continuous Integration):
```bash
#!/bin/bash
# ci-pipeline.sh

echo "🚀 Starting CI Pipeline..."

# 1. Lint
echo "📝 Running linting..."
dagger call lint --source=../

# 2. Test
echo "🧪 Running tests..."
dagger call test --source=../

# 3. Build
echo "🏗️  Building image..."
dagger call build-image --source=../ --tag=ci-${COMMIT_SHA}

echo "✅ CI Pipeline completed!"
```

### Pipeline de CD (Continuous Deployment):
```bash
#!/bin/bash
# cd-pipeline.sh

echo "🚀 Starting CD Pipeline..."

# 1. Build & Publish
echo "📦 Building and publishing image..."
IMAGE=$(dagger call publish-image \
  --source=../ \
  --registry=registry.gsi.srv.br \
  --username=admin \
  --password=env:REGISTRY_PASSWORD \
  --tag=${VERSION})

echo "✅ Published: $IMAGE"

# 2. Deploy
echo "🚢 Deploying to environment..."
dagger call deploy-dev \
  --source=../ \
  --db-host=postgres.gsi.srv.br \
  --db-password=env:DB_PASSWORD

echo "✅ CD Pipeline completed!"
```

---

## 🎯 CASOS DE USO NISE

### 1. **Versionamento de LLM Workflows**
```bash
# Versionar chatflow do Flowise
dagger call version-llm-workflow \
  --chatflow-id=dr-nise-v1 \
  --version=1.0.0 \
  --description="Initial Dr. Nise chatbot"
```

### 2. **Deploy de Modelos Ollama**
```bash
# Deploy de novo modelo LLM
dagger call deploy-ollama-model \
  --model=meditron:7b \
  --environment=production
```

### 3. **Backup de Dados de Treinamento**
```bash
# Backup automático
dagger call backup-training-data \
  --db-host=postgres.gsi.srv.br \
  --db-password=env:DB_PASSWORD \
  --backup-path=/backups/nise
```

---

## 📊 INTEGRAÇÃO COM GITHUB ACTIONS

```yaml
# .github/workflows/nise-ci-cd.yml
name: NISE CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Dagger
        run: |
          curl -L https://dl.dagger.io/dagger/install.sh | sh
          sudo mv bin/dagger /usr/local/bin/
      
      - name: Run Tests
        run: |
          cd Documentacao/consolidacao/docs_DEV1/nise/dagger
          dagger call test --source=../
      
      - name: Run Linting
        run: |
          cd Documentacao/consolidacao/docs_DEV1/nise/dagger
          dagger call lint --source=../
      
      - name: Build Image
        run: |
          cd Documentacao/consolidacao/docs_DEV1/nise/dagger
          dagger call build-image --source=../ --tag=${{ github.sha }}
  
  cd:
    needs: ci
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          cd Documentacao/consolidacao/docs_DEV1/nise/dagger
          dagger call deploy-dev \
            --source=../ \
            --db-host=${{ secrets.DB_HOST }} \
            --db-password=env:DB_PASSWORD
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

---

## 🛠️ COMANDOS ÚTEIS

### Listar funções disponíveis:
```bash
dagger functions
```

### Ver documentação de uma função:
```bash
dagger call test --help
```

### Executar em modo debug:
```bash
dagger call test --source=../ --debug
```

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Dagger instalado e configurado
2. ⏳ Criar pipelines de CI/CD
3. ⏳ Integrar com GitHub Actions
4. ⏳ Configurar deploy automático
5. ⏳ Implementar versionamento de LLM workflows

---

**Documento criado por**: DEV2  
**Data**: 13/03/2026  
**Status**: ✅ **DAGGER SETUP COMPLETO**

