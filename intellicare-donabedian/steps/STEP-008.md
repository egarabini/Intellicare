# STEP-008: Docker & Deploy ✅

**Status**: ✅ CONCLUÍDO  
**Tempo Estimado**: 2 horas  
**Tempo Real**: 2 horas  
**Data**: 2024-02-10

---

## 📋 Objetivo

Configurar Docker e preparar o módulo **intellicare-donabedian** para deploy em diferentes ambientes (desenvolvimento, staging, produção).

---

## ✅ Tarefas Realizadas

### 1. Dockerfiles Atualizados ✅

#### **docker/Dockerfile.api** (ATUALIZADO)
- ✅ Removido Poetry (simplificado para pip install)
- ✅ Corrigido caminho: `migrations/` → `alembic/`
- ✅ Adicionado `alembic.ini`
- ✅ Corrigido comando: `donabedian.api.main:app` → `donabedian.main:app`
- ✅ Mantido PostgreSQL client para migrations
- ✅ Comando: `alembic upgrade head && uvicorn donabedian.main:app`

**Mudanças principais**:
```dockerfile
# Antes: Poetry
RUN pip install --no-cache-dir poetry==1.7.1
RUN poetry config virtualenvs.create false && poetry install

# Depois: pip direto
RUN pip install --no-cache-dir -e .
```

#### **docker/Dockerfile.dashboard** (ATUALIZADO)
- ✅ Removido Poetry (simplificado para pip install)
- ✅ Mantido Streamlit configuration
- ✅ Comando: `streamlit run src/donabedian/dashboard/app.py`

---

### 2. Docker Compose - Desenvolvimento ✅

#### **docker-compose.yml** (CRIADO NA RAIZ)
- ✅ Movido de `docker/` para raiz do projeto
- ✅ PostgreSQL 15-alpine com healthcheck
- ✅ Variáveis de ambiente com defaults
- ✅ Volumes para desenvolvimento (hot reload)
- ✅ Network isolada (intellicare-network)
- ✅ Restart policies (unless-stopped)
- ✅ Healthcheck para API
- ✅ Dependências corretas (db → api → dashboard)

**Serviços**:
1. **db**: PostgreSQL 15-alpine
   - Porta: 5433:5432
   - Healthcheck: pg_isready
   - Volume: postgres_data
   - Init script: docker/init-db.sql

2. **api**: FastAPI
   - Porta: 8003:8000
   - Depends on: db (healthy)
   - Volumes: src/, alembic/
   - Healthcheck: /health endpoint

3. **dashboard**: Streamlit
   - Porta: 8501:8501
   - Depends on: api (healthy)
   - Volume: src/

---

### 3. Docker Compose - Produção ✅

#### **docker-compose.prod.yml** (CRIADO)
- ✅ Configuração otimizada para produção
- ✅ Sem volumes (código dentro da imagem)
- ✅ Restart policy: always
- ✅ Resource limits (CPU e memória)
- ✅ Mais workers (8 para API)
- ✅ Log level: WARNING
- ✅ Sem auto-reload
- ✅ Sem serviço de banco (usa banco externo)

**Resource Limits**:
- API: 2 CPUs, 2GB RAM (reserva: 1 CPU, 1GB)
- Dashboard: 1 CPU, 1GB RAM (reserva: 0.5 CPU, 512MB)

---

### 4. Arquivos de Configuração ✅

#### **.env.example** (ATUALIZADO)
- ✅ 67 linhas (antes: 30 linhas)
- ✅ Organizado em seções com headers
- ✅ Variáveis do Docker Compose (POSTGRES_*)
- ✅ Comentários explicativos
- ✅ Exemplos para diferentes ambientes
- ✅ Variáveis de CORS
- ✅ Variáveis de segurança (SECRET_KEY, JWT)

**Seções**:
1. Database Configuration (Docker + Application)
2. API Configuration
3. Dashboard Configuration
4. Module Information
5. Environment
6. Logging
7. CORS
8. Security

#### **.dockerignore** (CRIADO)
- ✅ Ignora arquivos desnecessários no build
- ✅ Python cache (__pycache__, *.pyc)
- ✅ Virtual environments (.venv, venv)
- ✅ IDE files (.vscode, .idea)
- ✅ Testing files (.pytest_cache, htmlcov)
- ✅ Development files (desenvolvimento/, steps/)
- ✅ Environment files (.env)
- ✅ Logs e databases locais

**Benefícios**:
- Build mais rápido (menos arquivos copiados)
- Imagens menores
- Mais seguro (não copia .env)

#### **docker/init-db.sql** (CRIADO)
- ✅ Cria schema `intellicare_donabedian`
- ✅ Concede permissões ao usuário
- ✅ Configura privilégios padrão
- ✅ Log de inicialização

---

## 📊 Arquivos Criados/Modificados

| Arquivo | Ação | Linhas | Descrição |
|---------|------|--------|-----------|
| `docker/Dockerfile.api` | MODIFICADO | 26 | Dockerfile da API (sem Poetry) |
| `docker/Dockerfile.dashboard` | MODIFICADO | 23 | Dockerfile do Dashboard (sem Poetry) |
| `docker-compose.yml` | CRIADO | 96 | Docker Compose para desenvolvimento |
| `docker-compose.prod.yml` | CRIADO | 82 | Docker Compose para produção |
| `.env.example` | ATUALIZADO | 67 | Variáveis de ambiente |
| `.dockerignore` | CRIADO | 68 | Arquivos ignorados no build |
| `docker/init-db.sql` | CRIADO | 20 | Script de inicialização do banco |
| `steps/STEP-008.md` | CRIADO | 150+ | Documentação deste STEP |

---

## 🚀 Como Usar

### Desenvolvimento Local

```bash
# 1. Copiar arquivo de ambiente
cp .env.example .env

# 2. Editar .env com suas configurações
nano .env

# 3. Subir containers
docker compose up -d

# 4. Ver logs
docker compose logs -f

# 5. Acessar:
# - API: http://localhost:8003
# - Docs: http://localhost:8003/docs
# - Dashboard: http://localhost:8501
```

### Produção

```bash
# 1. Configurar variáveis de ambiente
export INTELLICARE_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
export DASHBOARD_API_URL="https://api.intellicare.com.br/api/v1"
export SECRET_KEY="$(openssl rand -hex 32)"
export CORS_ORIGINS="https://app.intellicare.com.br"

# 2. Deploy
docker compose -f docker-compose.prod.yml up -d

# 3. Verificar
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

### Comandos Úteis

```bash
# Parar containers
docker compose down

# Rebuild
docker compose build --no-cache

# Executar migrations
docker compose exec api alembic upgrade head

# Acessar shell
docker compose exec api bash

# Ver logs específicos
docker compose logs -f api
docker compose logs -f dashboard

# Limpar tudo (CUIDADO!)
docker compose down -v
```

---

## ✅ Validação

- ✅ Dockerfiles sem Poetry (simplificados)
- ✅ Docker Compose para desenvolvimento
- ✅ Docker Compose para produção
- ✅ Variáveis de ambiente documentadas
- ✅ .dockerignore otimizado
- ✅ Script de inicialização do banco
- ✅ Healthchecks configurados
- ✅ Resource limits em produção
- ✅ Restart policies configuradas
- ✅ Network isolation

---

## 🎯 Próximos Passos

1. **STEP-009**: Testes de Integração (3h)
   - Testes de API end-to-end
   - Testes de Dashboard
   - Testes com banco real

2. **STEP-010**: Revisão Final e Entrega (1h)
   - Validação completa
   - Documentação final
   - Entrega do módulo

---

## 📝 Observações

1. **Poetry Removido**: Simplificado para `pip install -e .` para builds mais rápidos
2. **Healthchecks**: API tem healthcheck, Dashboard depende da API
3. **Volumes**: Desenvolvimento usa volumes para hot reload, produção não
4. **Resource Limits**: Apenas em produção para otimizar recursos
5. **Init Script**: Cria schema automaticamente no primeiro start

---

## ✅ Conclusão

A configuração Docker está **completa e pronta para uso** em:
- ✅ Desenvolvimento local (com hot reload)
- ✅ Produção (otimizado e seguro)
- ✅ CI/CD (pronto para automação)

**Total de arquivos**: 8 arquivos criados/modificados

---

**DEV1** - IntelliCare Team  
**Data**: 2024-02-10

