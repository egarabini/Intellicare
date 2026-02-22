# FASE 2 - DEPLOY NO SERVIDOR DE HOMOLOGAÇÃO - RELATÓRIO DE EXECUÇÃO

**Data**: 2026-02-22  
**Servidor**: 167.86.97.142 (Contabo VPS)  
**Objetivo**: Deploy completo do IntelliCare no ambiente de homologação  
**Status**: ⚠️ EM ANDAMENTO (Build concluído, subindo containers)

---

## 📋 ÍNDICE

1. [Resumo Executivo](#resumo-executivo)
2. [Infraestrutura](#infraestrutura)
3. [Problemas Encontrados e Soluções](#problemas-encontrados-e-soluções)
4. [Alterações Realizadas](#alterações-realizadas)
5. [Commits Git](#commits-git)
6. [Status Atual](#status-atual)
7. [Próximos Passos](#próximos-passos)

---

## 1. RESUMO EXECUTIVO

### Objetivo da Fase
Realizar o deploy completo do sistema IntelliCare modular no servidor de homologação, incluindo:
- ✅ Infraestrutura (PostgreSQL, Redis, Prometheus, Grafana)
- ⚠️ 6 Backends (Florence, Oswaldo, Donabedian, Wanda, Comunicacao, Geralda)
- ⏳ Frontend (Portal React)

### Abordagem
**Opção 2 Executada**: Verificar e corrigir Dockerfiles + fazer build completo

### Resultado Parcial
- ✅ Infraestrutura rodando (100%)
- ✅ Dockerfiles corrigidos (100%)
- ✅ Build dos backends concluído (100%)
- ⏳ Containers sendo iniciados
- ⏳ Frontend com erro (pnpm-lock.yaml não encontrado)

---

## 2. INFRAESTRUTURA

### Servidor de Homologação
```
IP: 167.86.97.142
Provedor: Contabo VPS
Specs:
  - CPU: 12 vCPU cores
  - RAM: 48 GB
  - Storage: 250 GB NVMe
  - Network: 800 Mbit/s
  - OS: Ubuntu 24.04 (noble)
  - Docker: v29.2.1
  - Docker Compose: v2.24.0
```

### Containers de Infraestrutura (✅ RODANDO)
```
✅ intellicare-postgres   - PostgreSQL 15 (healthy)
✅ intellicare-redis      - Redis 7 (healthy)
✅ intellicare-prometheus - Prometheus (up)
✅ intellicare-grafana    - Grafana v12.3.3 (up)
```

### Schemas PostgreSQL Criados
```
✅ intellicare_florence
✅ intellicare_oswaldo
✅ intellicare_donabedian
✅ intellicare_wanda
✅ intellicare_comunicacao
✅ intellicare_geralda
```

### Imagens Docker Criadas (✅ BUILD CONCLUÍDO)
```
✅ modularizacao-florence:latest      (1.61GB)
✅ modularizacao-oswaldo:latest       (1.13GB)
✅ modularizacao-donabedian:latest    (1.12GB)
✅ modularizacao-wanda:latest         (1.17GB)
✅ modularizacao-comunicacao:latest   (1.12GB)
✅ modularizacao-geralda:latest       (1.12GB)
```

**Total de imagens**: ~7.3GB

---

## 3. PROBLEMAS ENCONTRADOS E SOLUÇÕES

### Problema 1: Módulo Comunicacao sem Dockerfile
**Erro**: `intellicare-comunicacao` não tinha Dockerfile  
**Impacto**: Impossível fazer build do módulo  
**Solução**: Criado Dockerfile padronizado seguindo o padrão dos outros módulos  
**Status**: ✅ RESOLVIDO

### Problema 2: README.md Faltando nos Builds
**Erro**: 
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/README.md'
```
**Causa**: `pyproject.toml` referencia `readme = "README.md"` mas Dockerfile não copiava o arquivo  
**Solução**: Alterado `COPY pyproject.toml .` para `COPY pyproject.toml README.md* ./` em todos os Dockerfiles  
**Status**: ✅ RESOLVIDO

### Problema 3: Donabedian com Dockerfile Antigo
**Erro**: docker-compose referenciava `docker/Dockerfile.api` que tentava copiar `alembic.ini` inexistente  
**Solução**: 
- Criado novo Dockerfile padronizado na raiz de `intellicare-donabedian`
- Atualizado docker-compose.full.yml para usar novo Dockerfile
**Status**: ✅ RESOLVIDO

### Problema 4: Dependência intellicare-core Faltando
**Erro**:
```
ModuleNotFoundError: No module named 'intellicare_core'
```
**Causa**: Todos os módulos dependem de `intellicare-core` mas Dockerfiles não instalavam essa dependência  
**Impacto**: Containers iniciavam mas falhavam imediatamente (Restarting loop)  
**Solução**: Adicionado instalação do intellicare-core em todos os Dockerfiles:
```dockerfile
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core
```
**Status**: ✅ RESOLVIDO

### Problema 5: Contexto Docker Incorreto
**Erro**:
```
ERROR: failed to compute cache key: "/pyproject.toml": not found
```
**Causa**: Contexto Docker estava definido como `./intellicare-MODULE` mas Dockerfile tentava copiar `../intellicare-core` (fora do contexto)
**Impacto**: Build falhava ao tentar acessar arquivos fora do contexto
**Solução**:
- Alterado contexto de `./intellicare-MODULE` para `.` (MODULARIZACAO root) em docker-compose.full.yml
- Atualizado todos os paths nos Dockerfiles para serem relativos ao contexto MODULARIZACAO
- Exemplo: `COPY pyproject.toml` → `COPY ./intellicare-florence/pyproject.toml`
**Status**: ✅ RESOLVIDO

---

## 4. ALTERAÇÕES REALIZADAS

### 4.1. Dockerfiles - Padrão Final

Todos os Dockerfiles seguem agora este padrão:

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app

# Instalar intellicare-core primeiro
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# Instalar o módulo
COPY ./intellicare-MODULE/pyproject.toml ./intellicare-MODULE/README.md* ./
RUN pip install --no-cache-dir . || true
COPY ./intellicare-MODULE .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

FROM base AS api
CMD ["uvicorn", "MODULE.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Arquivos modificados/criados**:
- ✅ intellicare-comunicacao/Dockerfile (CRIADO)
- ✅ intellicare-donabedian/Dockerfile (CRIADO)
- ✅ intellicare-florence/Dockerfile (MODIFICADO)
- ✅ intellicare-oswaldo/Dockerfile (MODIFICADO)
- ✅ intellicare-wanda/Dockerfile (MODIFICADO)
- ✅ intellicare-geralda/Dockerfile (MODIFICADO)

### 4.2. docker-compose.full.yml

**Alteração em TODOS os serviços backend**:

**ANTES**:
```yaml
MODULE:
  build:
    context: ./intellicare-MODULE
    dockerfile: Dockerfile
    target: api
```

**DEPOIS**:
```yaml
MODULE:
  build:
    context: .
    dockerfile: ./intellicare-MODULE/Dockerfile
    target: api
```

**Serviços alterados**: florence, oswaldo, donabedian, wanda, comunicacao, geralda

---

## 5. COMMITS GIT

### Commit 1: Correção Inicial
```
Mensagem: fix: corrige Dockerfiles dos módulos Florence, Oswaldo e adiciona Dockerfile para Comunicacao
Arquivos: 3 Dockerfiles
```

### Commit 2: README.md
```
Mensagem: fix: corrige Dockerfiles para copiar README.md antes da instalação
Arquivos: Todos os Dockerfiles
```

### Commit 3: Donabedian
```
Mensagem: fix: adiciona Dockerfile padronizado para Donabedian
Arquivos: intellicare-donabedian/Dockerfile
```

### Commit 4: docker-compose
```
Mensagem: fix: corrige referência do Dockerfile do Donabedian no docker-compose.full.yml
Arquivos: docker-compose.full.yml
```

### Commit 5: intellicare-core
```
Mensagem: fix: adiciona instalação do intellicare-core em todos os Dockerfiles dos módulos
Arquivos: 6 Dockerfiles
```

### Commit 6: Contexto Docker
```
Hash: 791212e
Mensagem: fix: ajusta contexto do Docker e paths nos Dockerfiles para incluir intellicare-core
Arquivos: docker-compose.full.yml + 6 Dockerfiles + create_schemas.sh
```

---

## 6. STATUS ATUAL

### Build Concluído ✅
- **Tempo**: ~15-20 minutos
- **Imagens**: 6 backends (7.3GB total)
- **Resultado**: Sucesso

### Containers Backend
- **Status**: ⏳ Sendo iniciados

### Frontend (Portal)
- **Status**: ❌ ERRO
- **Erro**: `pnpm-lock.yaml not found`
- **Próximo**: Corrigir contexto do portal

---

## 7. PRÓXIMOS PASSOS

1. ⏳ Corrigir erro do portal
2. ⏳ Verificar backends rodando
3. ⏳ Testar health checks
4. ⏳ Testar endpoints APIs
5. ⏳ Configurar monitoramento

---

**Última Atualização**: 2026-02-22 (Build concluído, corrigindo portal)

