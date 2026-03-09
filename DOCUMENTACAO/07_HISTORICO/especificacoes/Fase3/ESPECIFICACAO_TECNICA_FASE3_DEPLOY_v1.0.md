# ESPECIFICACAO_TECNICA — Fase 3: Deploy Mínimo Viável

**Versão:** 1.0  
**Data:** 2026-02-20  
**Status:** Aprovado para execução  
**Referência:** `ESPECIFICACAO_FUNCIONAL_FASE3_DEPLOY_v1.0.md`  
**Pré-requisitos:** Fase 1 e Fase 2 concluídas

---

## 1. Objetivo Técnico

Implementar infraestrutura de deploy que permita colocar o IntelliCare no ar de forma reproduzível, com todos os serviços da demo acessíveis via URL pública com HTTPS.

---

## 2. Arquitetura de Deploy

### 2.1 Componentes da Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTPS (Let's Encrypt)                     │
│                    Nginx Reverse Proxy                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
│   Portal    │ │  Backend  │ │    Infra    │
│  (React)    │ │  Services │ │  Services   │
│   :3001     │ │  :8001-   │ │             │
│             │ │   8006    │ │             │
└─────────────┘ └───────────┘ └─────────────┘
                       │               │
                ┌──────┴───────┬───────┴──────┐
                │              │              │
         ┌──────▼──────┐┌─────▼─────┐┌──────▼──────┐
         │  PostgreSQL ││   Redis   ││ Prometheus  │
         │    :5432    ││   :6379   ││   :9090     │
         └─────────────┘└───────────┘└─────────────┘
```

### 2.2 Módulos Backend (6 serviços)

| Módulo | Porta | Descrição | Dependências |
|--------|-------|-----------|--------------|
| **intellicare-florence** | 8001 | RAG + Protocolos Clínicos | PostgreSQL, Redis |
| **intellicare-oswaldo** | 8002 | Análise Clínica + FHIR | PostgreSQL |
| **intellicare-donabedian** | 8003 | Qualidade + Indicadores | PostgreSQL |
| **intellicare-wanda** | 8004 | Orquestração + Workflows | PostgreSQL, Redis |
| **intellicare-comunicacao** | 8005 | Comunicação + Notificações | PostgreSQL, Redis |
| **intellicare-geralda** | 8006 | Gestão + Administrativo | PostgreSQL |

### 2.3 Infraestrutura

| Serviço | Porta | Versão | Propósito |
|---------|-------|--------|-----------|
| **PostgreSQL** | 5432 | 15-alpine | Banco de dados principal |
| **Redis** | 6379 | 7-alpine | Cache + Event Streams |
| **Prometheus** | 9090 | latest | Métricas e monitoramento |
| **Grafana** | 3000 | latest | Dashboards (opcional) |

---

## 3. Estrutura de Arquivos

### 3.1 Arquivo `.env.example`

**Localização:** `./.env.example`

**Seções:**
```bash
# ========== INFRASTRUCTURE ==========
POSTGRES_USER=intellicare_admin
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION
POSTGRES_DB=intellicare_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# ========== BACKEND SERVICES ==========
# Florence (8001)
FLORENCE_PORT=8001
FLORENCE_DATABASE_URL=postgresql+asyncpg://...

# Oswaldo (8002)
OSWALDO_PORT=8002
OSWALDO_DATABASE_URL=postgresql+asyncpg://...

# Donabedian (8003)
DONABEDIAN_PORT=8003
DONABEDIAN_DATABASE_URL=postgresql+asyncpg://...

# Wanda (8004)
WANDA_PORT=8004
WANDA_DATABASE_URL=postgresql+asyncpg://...

# Comunicacao (8005)
COMUNICACAO_PORT=8005
COMUNICACAO_DATABASE_URL=postgresql+asyncpg://...

# Geralda (8006)
GERALDA_PORT=8006
GERALDA_DATABASE_URL=postgresql+asyncpg://...

# ========== FRONTEND ==========
VITE_API_FLORENCE_URL=http://localhost:8001
VITE_API_OSWALDO_URL=http://localhost:8002
VITE_API_DONABEDIAN_URL=http://localhost:8003
VITE_API_WANDA_URL=http://localhost:8004
VITE_API_COMUNICACAO_URL=http://localhost:8005
VITE_API_GERALDA_URL=http://localhost:8006

# ========== MONITORING ==========
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_IN_PRODUCTION

# ========== DEPLOYMENT ==========
ENVIRONMENT=staging
LOG_LEVEL=INFO
DOMAIN=staging.intellicare.com.br
```

### 3.2 Arquivo `docker-compose.full.yml`

**Localização:** `./docker-compose.full.yml`

**Estrutura:**
- Extends `docker-compose.yml` (infraestrutura)
- Adiciona 6 serviços backend
- Adiciona 1 serviço frontend
- Configura rede compartilhada
- Define health checks
- Configura restart policies

---

## 4. Configuração do Frontend

### 4.1 Variáveis de Ambiente (Vite)

**Arquivo:** `intellicare-portal/frontend/.env.example`

```bash
VITE_API_FLORENCE_URL=http://localhost:8001
VITE_API_OSWALDO_URL=http://localhost:8002
VITE_API_DONABEDIAN_URL=http://localhost:8003
VITE_API_WANDA_URL=http://localhost:8004
VITE_API_COMUNICACAO_URL=http://localhost:8005
VITE_API_GERALDA_URL=http://localhost:8006
```

### 4.2 Build do Frontend

**Dockerfile:** `intellicare-portal/frontend/Dockerfile`

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_FLORENCE_URL
ARG VITE_API_OSWALDO_URL
# ... outras variáveis
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 5. Script de Smoke Tests

**Localização:** `./scripts/smoke_tests.py`

**Funcionalidades:**
- Verifica `/health` de cada backend (8001-8006)
- Verifica se portal carrega (HTTP 200)
- Verifica conectividade PostgreSQL
- Verifica conectividade Redis
- Verifica Prometheus metrics
- Gera relatório JSON + console output

**Exemplo de saída:**
```json
{
  "timestamp": "2026-02-20T10:30:00Z",
  "status": "OK",
  "services": {
    "florence": {"status": "OK", "response_time_ms": 45},
    "oswaldo": {"status": "OK", "response_time_ms": 38},
    "donabedian": {"status": "OK", "response_time_ms": 52},
    "wanda": {"status": "OK", "response_time_ms": 41},
    "comunicacao": {"status": "OK", "response_time_ms": 48},
    "geralda": {"status": "OK", "response_time_ms": 39},
    "portal": {"status": "OK", "response_time_ms": 120},
    "postgres": {"status": "OK"},
    "redis": {"status": "OK"}
  }
}
```

---

## 6. Documentação de Deploy

**Localização:** `./docs/PLANNER-CURSOR/GUIA_DEPLOY.md`

**Seções:**
1. Pré-requisitos (Docker, Docker Compose, Git)
2. Clonagem do repositório
3. Configuração de variáveis de ambiente
4. Deploy local (desenvolvimento)
5. Deploy em VPS (staging/produção)
6. Configuração HTTPS (Let's Encrypt)
7. Smoke tests
8. Troubleshooting
9. Rollback

---

## 7. Comandos de Deploy

### 7.1 Deploy Local

```bash
# 1. Clonar repositório
git clone <repository-url>
cd .

# 2. Configurar variáveis
cp .env.example .env
# Editar .env com valores apropriados

# 3. Subir stack completa
docker-compose -f docker-compose.full.yml up -d

# 4. Executar smoke tests
python scripts/smoke_tests.py

# 5. Acessar
# Portal: http://localhost:3001
# APIs: http://localhost:8001-8006
```

### 7.2 Deploy em VPS

```bash
# 1. Provisionar servidor (Ubuntu 22.04 LTS)
# 2. Instalar Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Clonar repositório
git clone <repository-url>
cd .

# 4. Configurar variáveis
cp .env.example .env
nano .env  # Ajustar para produção

# 5. Deploy
docker-compose -f docker-compose.full.yml up -d

# 6. Configurar HTTPS (Nginx + Let's Encrypt)
# Ver GUIA_DEPLOY.md seção 6

# 7. Smoke tests
python scripts/smoke_tests.py --url https://staging.intellicare.com.br
```

---

## 8. Checklist de Validação

- [ ] `.env.example` criado com todas as variáveis
- [ ] `docker-compose.full.yml` sobe toda a stack
- [ ] Frontend configurado com variáveis VITE_*
- [ ] Smoke tests validam todos os serviços
- [ ] GUIA_DEPLOY.md permite deploy reproduzível
- [ ] HTTPS configurado (staging)
- [ ] Rollback testado
- [ ] Documentação completa

---

## 9. Segurança

### 9.1 Secrets Management

- **Desenvolvimento:** `.env` local (não versionado)
- **Staging/Produção:** Variáveis de ambiente do provedor ou Docker secrets

### 9.2 HTTPS

- **Let's Encrypt:** Certificados gratuitos via Certbot
- **Nginx:** Reverse proxy com SSL termination

---

## 10. Próximos Passos (Fase 4)

- CI/CD automatizado (GitHub Actions)
- Múltiplos ambientes (dev/staging/prod)
- Monitoramento avançado (alertas)
- Backup automatizado

---

## 11. Referências

- `docker-compose.yml` — Infraestrutura existente
- `README_DEMO.md` — Módulos da demo
- `ESTRATEGIA_GIT.md` — Estratégia de branches e tags

---

## 12. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-20 | Versão inicial |

