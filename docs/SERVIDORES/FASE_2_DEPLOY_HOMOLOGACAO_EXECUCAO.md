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

### Problema 6: Portal Usando pnpm ao Invés de npm
**Erro**:
```
failed to compute cache key: "/pnpm-lock.yaml": not found
```
**Causa**: Dockerfile do portal tentava usar pnpm mas o projeto usa npm
**Impacto**: Build do portal falhava ao tentar copiar `pnpm-lock.yaml` inexistente
**Solução**:
- Alterado Dockerfile para usar `package-lock.json` ao invés de `pnpm-lock.yaml`
- Alterado `pnpm install` para `npm ci`
- Alterado `pnpm build` para `npm run build`
**Status**: ✅ RESOLVIDO

### Problema 7: Erros TypeScript no Portal
**Erro**:
```
error TS6133: 'HomePage' is declared but its value is never read.
error TS6133: 'Database' is declared but its value is never read.
error TS6133: 'AlertCircle' is declared but its value is never read.
error TS6133: 'Activity' is declared but its value is never read.
error TS6133: 'Users' is declared but its value is never read.
```
**Causa**: Imports não utilizados em App.tsx, GrahamePage.tsx e ZildaPage.tsx
**Impacto**: Build do portal falhava na compilação TypeScript
**Solução**: Removidos imports não utilizados:
- App.tsx: Comentado import de HomePage
- GrahamePage.tsx: Removidos Database e AlertCircle
- ZildaPage.tsx: Removidos Activity e Users
**Status**: ✅ RESOLVIDO

### Problema 8: ENVIRONMENT Inválido no .env
**Erro**:
```
ValidationError: 1 validation error for FlorenceConfig
environment
  Input should be 'development', 'staging' or 'production' [type=enum, input_value='homologacao', input_type=str]
```
**Causa**: Arquivo `.env` configurado com `ENVIRONMENT=homologacao` mas código Pydantic só aceita: `development`, `staging` ou `production`
**Impacto**: Todos os backends falhavam ao iniciar (Restarting loop)
**Solução**: Alterar `.env` de `ENVIRONMENT=homologacao` para `ENVIRONMENT=staging`
**Comando**: `sed -i 's/ENVIRONMENT=homologacao/ENVIRONMENT=staging/g' .env`
**Status**: ⏳ AGUARDANDO EXECUÇÃO NO SERVIDOR

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

### Commit 7: Portal npm + Documentação
```
Hash: 94db371
Mensagem: fix: corrige Dockerfile do portal para usar npm ao invés de pnpm + adiciona documentação completa da Fase 2
Arquivos:
  - MODULARIZACAO/intellicare-portal/frontend/Dockerfile
  - docs/SERVIDORES/FASE_2_DEPLOY_HOMOLOGACAO_EXECUCAO.md
```

### Commit 8: TypeScript Errors
```
Hash: abd2525
Mensagem: fix: remove imports não utilizados no portal (TypeScript errors)
Arquivos:
  - MODULARIZACAO/intellicare-portal/frontend/src/App.tsx
  - MODULARIZACAO/intellicare-portal/frontend/src/pages/GrahamePage.tsx
  - MODULARIZACAO/intellicare-portal/frontend/src/pages/ZildaPage.tsx
```

---

## 6. STATUS ATUAL

### Build Concluído ✅
- **Tempo**: ~15-20 minutos
- **Imagens**: 6 backends (7.3GB total)
- **Resultado**: Sucesso

### Containers Backend
- **Status**: ⚠️ Restarting (ENVIRONMENT inválido)
- **Problema**: .env com `homologacao` ao invés de `staging`
- **Solução**: Alterar .env e reiniciar containers

### Frontend (Portal)
- **Status**: ✅ CORRIGIDO
- **Problemas resolvidos**:
  - pnpm → npm
  - TypeScript imports não utilizados
- **Próximo**: Build e deploy

---

## 7. PRÓXIMOS PASSOS

### Imediato (NO SERVIDOR)
1. ⏳ Alterar `.env`: `ENVIRONMENT=homologacao` → `ENVIRONMENT=staging`
2. ⏳ Reiniciar backends: `docker-compose -f docker-compose.full.yml restart florence oswaldo donabedian wanda comunicacao geralda`
3. ⏳ Verificar todos os containers healthy

### Validação
4. ⏳ Testar health checks de cada módulo
5. ⏳ Testar endpoints APIs (8001-8006)
6. ⏳ Testar acesso ao portal (3001)
7. ⏳ Verificar logs de todos os serviços

### Monitoramento
8. ⏳ Configurar alertas no Prometheus
9. ⏳ Criar dashboards no Grafana
10. ⏳ Documentar status final

---

**Última Atualização**: 2026-02-22 (Build concluído, corrigindo portal)

