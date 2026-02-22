# 🚀 GUIA DE DEPLOYMENT EM PRODUÇÃO - IntelliCare NISE

**Projeto**: IntelliCare NISE - Integração Oswaldo + NISE + Kestra  
**Versão**: 1.0.0  
**Data**: 15/02/2026  
**Ambiente**: Produção

---

## 📋 ÍNDICE

1. [Pré-requisitos](#pré-requisitos)
2. [Arquitetura de Produção](#arquitetura-de-produção)
3. [Checklist Pré-Deployment](#checklist-pré-deployment)
4. [Configuração de Ambiente](#configuração-de-ambiente)
5. [Deployment Passo a Passo](#deployment-passo-a-passo)
6. [Validação Pós-Deployment](#validação-pós-deployment)
7. [Monitoramento](#monitoramento)
8. [Backup e Disaster Recovery](#backup-e-disaster-recovery)
9. [Rollback](#rollback)
10. [Manutenção](#manutenção)

---

## ✅ PRÉ-REQUISITOS

### Infraestrutura

- [ ] **Servidor de Produção**
  - CPU: 8+ cores
  - RAM: 16GB+ (recomendado 32GB)
  - Disco: 200GB+ SSD
  - OS: Ubuntu 22.04 LTS ou superior

- [ ] **Docker & Docker Compose**
  - Docker Engine 24.0+
  - Docker Compose 2.20+
  - Configurado para iniciar no boot

- [ ] **Rede**
  - Portas abertas: 80, 443, 8000, 8080, 3000
  - Firewall configurado
  - DNS configurado
  - Certificado SSL/TLS válido

- [ ] **Database Externo** (Recomendado)
  - PostgreSQL 15+ gerenciado
  - Backup automático configurado
  - Replicação configurada

- [ ] **Cache Externo** (Recomendado)
  - Redis 7.2+ gerenciado
  - Persistência configurada
  - Alta disponibilidade

### Acessos e Credenciais

- [ ] Acesso SSH ao servidor
- [ ] Credenciais de banco de dados
- [ ] Credenciais de Redis
- [ ] Tokens de API (Oswaldo, etc)
- [ ] Secrets do Kestra
- [ ] Certificados SSL/TLS
- [ ] Acesso ao registry Docker (se usar)

### Ferramentas

- [ ] Git instalado
- [ ] Docker CLI configurado
- [ ] kubectl (se usar Kubernetes)
- [ ] Ferramentas de monitoramento
- [ ] Backup tools

---

## 🏗️ ARQUITETURA DE PRODUÇÃO

### Opção 1: Single Server (Pequeno/Médio Porte)

```
┌─────────────────────────────────────────────────────────┐
│                    SERVIDOR PRODUÇÃO                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  NISE API    │  │   Flowise    │  │   Kestra     │  │
│  │  Port 8000   │  │   Port 3000  │  │   Port 8080  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │   Ollama     │  │
│  │  Port 5432   │  │   Port 6379  │  │  Port 11434  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Nginx Reverse Proxy                  │  │
│  │              Port 80/443 (SSL/TLS)               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Opção 2: Multi-Server (Grande Porte)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Load Balancer  │    │  App Server 1   │    │  App Server 2   │
│   (Nginx/HAP)   │───▶│   NISE API      │    │   NISE API      │
│   Port 80/443   │    │   Flowise       │    │   Flowise       │
└─────────────────┘    │   Kestra        │    │   Kestra        │
                       └─────────────────┘    └─────────────────┘
                                │                      │
                                └──────────┬───────────┘
                                           │
                       ┌───────────────────▼───────────────────┐
                       │     PostgreSQL Cluster (Primary +     │
                       │     Replica) - Managed Service        │
                       └───────────────────────────────────────┘
                                           │
                       ┌───────────────────▼───────────────────┐
                       │     Redis Cluster - Managed Service   │
                       └───────────────────────────────────────┘
```

**Recomendação**: Começar com Opção 1 e migrar para Opção 2 conforme crescimento.

---

## 📝 CHECKLIST PRÉ-DEPLOYMENT

### 1. Código e Testes

- [ ] **Branch de produção criada** (`main` ou `production`)
- [ ] **Todos os testes passando** (88/88)
  ```bash
  pytest tests/ -v --cov=nise
  ```
- [ ] **Cobertura de testes >= 85%**
- [ ] **Code review completo**
- [ ] **Sem vulnerabilidades de segurança**
  ```bash
  pip-audit
  safety check
  ```
- [ ] **Documentação atualizada**

### 2. Configuração

- [ ] **Variáveis de ambiente de produção definidas**
- [ ] **Secrets configurados** (não commitados!)
- [ ] **Certificados SSL/TLS obtidos**
- [ ] **DNS configurado** (nise.intellicare.com)
- [ ] **Firewall rules configuradas**
- [ ] **Backup configurado**

### 3. Infraestrutura

- [ ] **Servidor provisionado**
- [ ] **Docker instalado e configurado**
- [ ] **PostgreSQL configurado** (externo ou container)
- [ ] **Redis configurado** (externo ou container)
- [ ] **Nginx configurado** (reverse proxy)
- [ ] **Monitoramento configurado** (Prometheus, Grafana)
- [ ] **Logs centralizados** (ELK, Loki, etc)

### 4. Integrações

- [ ] **Oswaldo API acessível** (http://oswaldo-prod:8002)
- [ ] **Credenciais de integração válidas**
- [ ] **Webhooks configurados**
- [ ] **Rocket.Chat configurado** (notificações)
- [ ] **Email SMTP configurado**

### 5. Segurança

- [ ] **HTTPS habilitado** (TLS 1.2+)
- [ ] **Secrets em vault** (não em .env)
- [ ] **Rate limiting configurado**
- [ ] **CORS configurado corretamente**
- [ ] **Headers de segurança** (HSTS, CSP, etc)
- [ ] **Auditoria de acessos habilitada**

### 6. Plano de Contingência

- [ ] **Plano de rollback documentado**
- [ ] **Backup recente disponível**
- [ ] **Equipe de plantão definida**
- [ ] **Runbook de incidentes criado**
- [ ] **Contatos de emergência atualizados**

---

## ⚙️ CONFIGURAÇÃO DE AMBIENTE

### 1. Variáveis de Ambiente de Produção

Criar arquivo `.env.production` (NÃO commitar!):

```bash
# ============================================
# AMBIENTE
# ============================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# ============================================
# NISE API
# ============================================
NISE_API_HOST=0.0.0.0
NISE_API_PORT=8000
NISE_API_WORKERS=4
NISE_API_RELOAD=false

# URL pública
NISE_PUBLIC_URL=https://nise.intellicare.com

# ============================================
# SEGURANÇA
# ============================================
SECRET_KEY=<GERAR_CHAVE_SEGURA_256_BITS>
API_KEY=<GERAR_API_KEY_SEGURA>
ALLOWED_HOSTS=nise.intellicare.com,*.intellicare.com
CORS_ORIGINS=https://intellicare.com,https://app.intellicare.com

# ============================================
# DATABASE (PostgreSQL)
# ============================================
# Opção 1: Managed Service (Recomendado)
POSTGRES_HOST=postgres-prod.intellicare.com
POSTGRES_PORT=5432
POSTGRES_DB=intellicare_nise_prod
POSTGRES_USER=nise_prod_user
POSTGRES_PASSWORD=<SENHA_FORTE_GERADA>
POSTGRES_SSL_MODE=require

# Pool de conexões
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10
POSTGRES_POOL_TIMEOUT=30

# ============================================
# REDIS (Cache)
# ============================================
# Opção 1: Managed Service (Recomendado)
REDIS_HOST=redis-prod.intellicare.com
REDIS_PORT=6379
REDIS_PASSWORD=<SENHA_FORTE_GERADA>
REDIS_DB=0
REDIS_SSL=true

# Cache TTL
REDIS_TTL_DEFAULT=300
REDIS_TTL_PACIENTE=600

# ============================================
# OSWALDO INTEGRATION
# ============================================
OSWALDO_API_URL=https://oswaldo.intellicare.com
OSWALDO_API_KEY=<API_KEY_OSWALDO_PROD>
OSWALDO_TIMEOUT=30
OSWALDO_RETRY_ATTEMPTS=3

# ============================================
# FLOWISE
# ============================================
FLOWISE_PORT=3000
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=<SENHA_FORTE_GERADA>
FLOWISE_API_KEY=<API_KEY_FLOWISE>

# ============================================
# OLLAMA
# ============================================
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_GPU=1
OLLAMA_NUM_THREAD=8

# ============================================
# KESTRA
# ============================================
KESTRA_PORT=8080
KESTRA_API_URL=https://kestra.intellicare.com
KESTRA_USERNAME=admin
KESTRA_PASSWORD=<SENHA_FORTE_GERADA>

# ============================================
# NOTIFICAÇÕES
# ============================================
# Rocket.Chat
ROCKETCHAT_WEBHOOK_URL=https://chat.intellicare.com/hooks/<WEBHOOK_ID>
ROCKETCHAT_CHANNEL=#alertas-producao

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=nise@intellicare.com
SMTP_PASSWORD=<SENHA_APP_GMAIL>
SMTP_FROM=nise@intellicare.com
SMTP_TLS=true

# ============================================
# MONITORAMENTO
# ============================================
# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Sentry (Error Tracking)
SENTRY_DSN=https://<KEY>@sentry.io/<PROJECT>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# ============================================
# BACKUP
# ============================================
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # 2 AM diariamente
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=intellicare-backups-prod
BACKUP_S3_REGION=us-east-1

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ============================================
# SSL/TLS
# ============================================
SSL_CERT_PATH=/etc/ssl/certs/intellicare.crt
SSL_KEY_PATH=/etc/ssl/private/intellicare.key
```

### 2. Gerar Secrets Seguros

```bash
# SECRET_KEY (256 bits)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# API_KEY
python -c "import secrets; print('nise_' + secrets.token_urlsafe(48))"

# Passwords
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3. Docker Compose para Produção

Criar `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nise-api:
    image: intellicare/nise-api:1.0.0
    container_name: nise-api-prod
    restart: always
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    networks:
      - intellicare-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  flowise:
    image: flowiseai/flowise:1.4.0
    container_name: flowise-prod
    restart: always
    env_file:
      - .env.production
    ports:
      - "3000:3000"
    volumes:
      - flowise_data:/root/.flowise
    networks:
      - intellicare-network
    depends_on:
      - postgres
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-prod
    restart: always
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - intellicare-network
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          memory: 4G

  kestra:
    image: kestra/kestra:latest
    container_name: kestra-prod
    restart: always
    env_file:
      - .env.production
    ports:
      - "8080:8080"
    volumes:
      - kestra_data:/app/storage
      - ./kestra:/app/flows
    networks:
      - intellicare-network
    depends_on:
      - postgres
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G

  # Usar PostgreSQL e Redis externos em produção (recomendado)
  # Se usar containers, descomentar abaixo:
  
  # postgres:
  #   image: postgres:15-alpine
  #   container_name: postgres-prod
  #   restart: always
  #   environment:
  #     POSTGRES_DB: ${POSTGRES_DB}
  #     POSTGRES_USER: ${POSTGRES_USER}
  #     POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   networks:
  #     - intellicare-network

  # redis:
  #   image: redis:7-alpine
  #   container_name: redis-prod
  #   restart: always
  #   command: redis-server --requirepass ${REDIS_PASSWORD}
  #   ports:
  #     - "6379:6379"
  #   volumes:
  #     - redis_data:/data
  #   networks:
  #     - intellicare-network

  nginx:
    image: nginx:alpine
    container_name: nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    networks:
      - intellicare-network
    depends_on:
      - nise-api
      - flowise
      - kestra

volumes:
  flowise_data:
  ollama_data:
  kestra_data:
  # postgres_data:
  # redis_data:

networks:
  intellicare-network:
    driver: bridge
```

### 4. Configuração Nginx (Reverse Proxy)

Criar `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=chatbot_limit:10m rate=20r/m;

    # Upstream servers
    upstream nise_api {
        server nise-api:8000;
    }

    upstream flowise {
        server flowise:3000;
    }

    upstream kestra {
        server kestra:8080;
    }

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name nise.intellicare.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS - NISE API
    server {
        listen 443 ssl http2;
        server_name nise.intellicare.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/intellicare.crt;
        ssl_certificate_key /etc/nginx/ssl/intellicare.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=10 nodelay;

            proxy_pass http://nise_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Chatbot endpoints (higher timeout)
        location /api/v1/chatbot/ {
            limit_req zone=chatbot_limit burst=5 nodelay;

            proxy_pass http://nise_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check (no rate limit)
        location /health {
            proxy_pass http://nise_api;
            access_log off;
        }

        # Docs
        location /docs {
            proxy_pass http://nise_api;
            proxy_set_header Host $host;
        }
    }

    # HTTPS - Flowise
    server {
        listen 443 ssl http2;
        server_name flowise.intellicare.com;

        ssl_certificate /etc/nginx/ssl/intellicare.crt;
        ssl_certificate_key /etc/nginx/ssl/intellicare.key;
        ssl_protocols TLSv1.2 TLSv1.3;

        location / {
            proxy_pass http://flowise;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # HTTPS - Kestra
    server {
        listen 443 ssl http2;
        server_name kestra.intellicare.com;

        ssl_certificate /etc/nginx/ssl/intellicare.crt;
        ssl_certificate_key /etc/nginx/ssl/intellicare.key;
        ssl_protocols TLSv1.2 TLSv1.3;

        location / {
            proxy_pass http://kestra;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## 🚀 DEPLOYMENT PASSO A PASSO

### Fase 1: Preparação do Servidor

#### 1.1. Conectar ao Servidor

```bash
# SSH para o servidor de produção
ssh user@nise-prod.intellicare.com

# Atualizar sistema
sudo apt update && sudo apt upgrade -y
```

#### 1.2. Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version

# Configurar Docker para iniciar no boot
sudo systemctl enable docker
```

#### 1.3. Criar Estrutura de Diretórios

```bash
# Criar diretórios
sudo mkdir -p /opt/intellicare/nise
sudo mkdir -p /opt/intellicare/nise/logs
sudo mkdir -p /opt/intellicare/nise/nginx/ssl
sudo mkdir -p /opt/intellicare/nise/nginx/logs
sudo mkdir -p /opt/intellicare/nise/kestra
sudo mkdir -p /opt/intellicare/nise/backups

# Definir permissões
sudo chown -R $USER:$USER /opt/intellicare/nise
cd /opt/intellicare/nise
```

---

### Fase 2: Configuração

#### 2.1. Clonar Repositório

```bash
# Clonar código
git clone https://github.com/intellicare/nise.git .

# Checkout branch de produção
git checkout production

# Verificar versão
git describe --tags
```

#### 2.2. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env.production

# Editar variáveis (usar editor seguro)
nano .env.production

# IMPORTANTE: Gerar secrets seguros!
# Não usar valores de exemplo!
```

#### 2.3. Configurar SSL/TLS

```bash
# Opção 1: Let's Encrypt (Recomendado)
sudo apt install certbot
sudo certbot certonly --standalone -d nise.intellicare.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/nise.intellicare.com/fullchain.pem nginx/ssl/intellicare.crt
sudo cp /etc/letsencrypt/live/nise.intellicare.com/privkey.pem nginx/ssl/intellicare.key

# Opção 2: Certificado próprio
# Copiar arquivos .crt e .key para nginx/ssl/
```

#### 2.4. Configurar Nginx

```bash
# Copiar configuração
cp nginx/nginx.conf.example nginx/nginx.conf

# Editar se necessário
nano nginx/nginx.conf

# Validar configuração
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx nginx -t
```

---

### Fase 3: Build e Deploy

#### 3.1. Build de Imagens Docker

```bash
# Build da imagem NISE API
docker build -t intellicare/nise-api:1.0.0 .

# Tag como latest
docker tag intellicare/nise-api:1.0.0 intellicare/nise-api:latest

# (Opcional) Push para registry
# docker push intellicare/nise-api:1.0.0
```

#### 3.2. Iniciar Serviços

```bash
# Subir serviços em background
docker-compose -f docker-compose.prod.yml up -d

# Verificar status
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### 3.3. Aguardar Inicialização

```bash
# Aguardar health checks (pode levar 1-2 minutos)
echo "Aguardando serviços iniciarem..."
sleep 60

# Verificar health
curl http://localhost:8000/health
```

---

### Fase 4: Configuração Inicial

#### 4.1. Configurar Database

```bash
# Executar migrations (se houver)
docker exec nise-api-prod alembic upgrade head

# Criar usuário admin (se necessário)
docker exec nise-api-prod python scripts/create_admin.py
```

#### 4.2. Configurar Flowise

```bash
# Acessar Flowise UI
# https://flowise.intellicare.com

# 1. Criar conta admin
# 2. Importar chatflow: flowise/dr-nise-chatflow.json
# 3. Configurar LangChain Tools:
#    - OswaldoPatientTool → https://nise.intellicare.com/api/v1
#    - FraminghamRiskTool → https://nise.intellicare.com/api/v1
#    - WorkflowTriggerTool → https://kestra.intellicare.com/api/v1
# 4. Testar chatflow
```

#### 4.3. Importar Workflows Kestra

```bash
# Via script
for workflow in kestra/*.yml; do
  curl -X POST "https://kestra.intellicare.com/api/v1/flows" \
    -H "Content-Type: application/yaml" \
    --data-binary @$workflow
done

# Ou via UI:
# https://kestra.intellicare.com
# Flows → Create → Cole YAML → Save
```

#### 4.4. Configurar Secrets Kestra

```bash
# Via UI Kestra:
# Settings → Secrets → Add Secret

# Secrets necessários:
# - oswaldo_api_key
# - nise_api_key
# - rocketchat_webhook
# - smtp_password
```

---

### Fase 5: Validação

#### 5.1. Testes de Fumaça

```bash
# Health check
curl https://nise.intellicare.com/health

# Info
curl https://nise.intellicare.com/api/v1/info

# Oswaldo integration
curl https://nise.intellicare.com/api/v1/oswaldo/paciente/PAC001/resumo

# Framingham
curl -X POST "https://nise.intellicare.com/api/v1/framingham/calcular" \
  -H "Content-Type: application/json" \
  -d '{
    "sexo": "M",
    "idade": 55,
    "colesterol_total": 220,
    "hdl": 45,
    "pa_sistolica": 140,
    "tabagismo": true,
    "diabetes": false
  }'

# Chatbot
curl -X POST "https://nise.intellicare.com/api/v1/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Olá, Dr. Nise!",
    "session_id": "test-prod"
  }'

# Workflow
curl -X POST "https://nise.intellicare.com/api/v1/workflows/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "intellicare.nise",
    "flow_id": "avaliacao-risco-cardiovascular",
    "inputs": {"paciente_id": "PAC001"}
  }'
```

#### 5.2. Verificar Logs

```bash
# Logs NISE API
docker logs nise-api-prod --tail 100

# Logs Nginx
tail -f nginx/logs/access.log
tail -f nginx/logs/error.log

# Logs Kestra
docker logs kestra-prod --tail 100

# Verificar erros
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

#### 5.3. Verificar Performance

```bash
# Testar latência
time curl https://nise.intellicare.com/health

# Testar carga (usar Apache Bench)
ab -n 100 -c 10 https://nise.intellicare.com/health

# Verificar recursos
docker stats
```

---

## ✅ VALIDAÇÃO PÓS-DEPLOYMENT

### Checklist de Validação

- [ ] **Todos os serviços rodando**
  ```bash
  docker-compose -f docker-compose.prod.yml ps
  # Todos devem estar "Up" e "healthy"
  ```

- [ ] **Health checks passando**
  ```bash
  curl https://nise.intellicare.com/health
  curl https://flowise.intellicare.com/api/v1/health
  curl https://kestra.intellicare.com/api/v1/health
  ```

- [ ] **HTTPS funcionando**
  ```bash
  curl -I https://nise.intellicare.com
  # Deve retornar 200 OK com headers de segurança
  ```

- [ ] **Endpoints principais funcionando**
  - [ ] GET /health
  - [ ] GET /api/v1/info
  - [ ] GET /api/v1/oswaldo/paciente/{id}/resumo
  - [ ] POST /api/v1/framingham/calcular
  - [ ] POST /api/v1/chatbot/message
  - [ ] POST /api/v1/workflows/trigger

- [ ] **Integrações funcionando**
  - [ ] Oswaldo API acessível
  - [ ] Redis cache funcionando
  - [ ] PostgreSQL conectado
  - [ ] Flowise respondendo
  - [ ] Kestra executando workflows

- [ ] **Monitoramento ativo**
  - [ ] Prometheus coletando métricas
  - [ ] Grafana exibindo dashboards
  - [ ] Alertas configurados
  - [ ] Logs sendo coletados

- [ ] **Backup configurado**
  - [ ] Backup automático agendado
  - [ ] Teste de restore bem-sucedido
  - [ ] Retenção configurada

- [ ] **Segurança validada**
  - [ ] HTTPS obrigatório
  - [ ] Rate limiting ativo
  - [ ] Headers de segurança presentes
  - [ ] Secrets não expostos

---

## 📊 MONITORAMENTO

### 1. Prometheus + Grafana

#### 1.1. Instalar Prometheus

```bash
# Criar docker-compose.monitoring.yml
cat > docker-compose.monitoring.yml <<EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - intellicare-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: always
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=<SENHA_FORTE>
    networks:
      - intellicare-network
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:

networks:
  intellicare-network:
    external: true
EOF

# Subir monitoramento
docker-compose -f docker-compose.monitoring.yml up -d
```

#### 1.2. Configurar Prometheus

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nise-api'
    static_configs:
      - targets: ['nise-api:8000']
    metrics_path: '/metrics'

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
```

#### 1.3. Dashboards Grafana

Importar dashboards:
- **NISE API**: Dashboard customizado (criar)
- **Docker**: Dashboard ID 1229
- **Nginx**: Dashboard ID 12708
- **PostgreSQL**: Dashboard ID 9628
- **Redis**: Dashboard ID 11835

### 2. Alertas

#### 2.1. Configurar Alertmanager

```yaml
# prometheus/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'rocketchat'

receivers:
  - name: 'rocketchat'
    webhook_configs:
      - url: 'https://chat.intellicare.com/hooks/<WEBHOOK_ID>'
        send_resolved: true
```

#### 2.2. Regras de Alerta

```yaml
# prometheus/alerts.yml
groups:
  - name: nise_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Alta taxa de erros em {{ $labels.instance }}"
          description: "Taxa de erros: {{ $value }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alta latência em {{ $labels.instance }}"
          description: "P95 latência: {{ $value }}s"

      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Serviço {{ $labels.job }} está down"

      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto uso de memória em {{ $labels.container_label_com_docker_compose_service }}"
          description: "Uso de memória: {{ $value | humanizePercentage }}"

      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto uso de CPU em {{ $labels.container_label_com_docker_compose_service }}"
```

### 3. Logs Centralizados

#### 3.1. Configurar Loki (Opcional)

```bash
# Adicionar ao docker-compose.monitoring.yml
  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: always
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    networks:
      - intellicare-network

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    restart: always
    volumes:
      - /var/log:/var/log
      - ./promtail/config.yml:/etc/promtail/config.yml
    networks:
      - intellicare-network
```

---

## 💾 BACKUP E DISASTER RECOVERY

### 1. Estratégia de Backup

#### 1.1. O que fazer backup

- **PostgreSQL Database** (Diário)
- **Redis Data** (Diário)
- **Flowise Data** (Semanal)
- **Kestra Workflows** (A cada mudança)
- **Configurações** (.env, nginx.conf, etc)
- **Logs** (Últimos 30 dias)

#### 1.2. Script de Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/intellicare/nise/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Criar diretório de backup
mkdir -p $BACKUP_DIR/$DATE

# Backup PostgreSQL
docker exec postgres-prod pg_dump -U nise_prod_user intellicare_nise_prod | gzip > $BACKUP_DIR/$DATE/postgres_$DATE.sql.gz

# Backup Redis
docker exec redis-prod redis-cli --rdb /data/dump.rdb
docker cp redis-prod:/data/dump.rdb $BACKUP_DIR/$DATE/redis_$DATE.rdb

# Backup Flowise
docker cp flowise-prod:/root/.flowise $BACKUP_DIR/$DATE/flowise_data

# Backup Kestra workflows
cp -r kestra/*.yml $BACKUP_DIR/$DATE/kestra_workflows/

# Backup configurações
cp .env.production $BACKUP_DIR/$DATE/
cp nginx/nginx.conf $BACKUP_DIR/$DATE/
cp docker-compose.prod.yml $BACKUP_DIR/$DATE/

# Compactar
cd $BACKUP_DIR
tar -czf backup_$DATE.tar.gz $DATE/
rm -rf $DATE/

# Upload para S3 (opcional)
# aws s3 cp backup_$DATE.tar.gz s3://intellicare-backups-prod/nise/

# Limpar backups antigos
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup concluído: backup_$DATE.tar.gz"
```

#### 1.3. Agendar Backup (Cron)

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 2 AM)
0 2 * * * /opt/intellicare/nise/backup.sh >> /opt/intellicare/nise/logs/backup.log 2>&1
```

### 2. Disaster Recovery

#### 2.1. Procedimento de Restore

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Uso: ./restore.sh <backup_file.tar.gz>"
  exit 1
fi

# Extrair backup
tar -xzf $BACKUP_FILE

BACKUP_DIR=$(basename $BACKUP_FILE .tar.gz | sed 's/backup_//')

# Parar serviços
docker-compose -f docker-compose.prod.yml down

# Restore PostgreSQL
gunzip < $BACKUP_DIR/postgres_*.sql.gz | docker exec -i postgres-prod psql -U nise_prod_user intellicare_nise_prod

# Restore Redis
docker cp $BACKUP_DIR/redis_*.rdb redis-prod:/data/dump.rdb
docker restart redis-prod

# Restore Flowise
docker cp $BACKUP_DIR/flowise_data flowise-prod:/root/.flowise
docker restart flowise-prod

# Restore Kestra workflows
cp $BACKUP_DIR/kestra_workflows/*.yml kestra/

# Restore configurações
cp $BACKUP_DIR/.env.production .
cp $BACKUP_DIR/nginx.conf nginx/

# Reiniciar serviços
docker-compose -f docker-compose.prod.yml up -d

echo "Restore concluído!"
```

#### 2.2. Teste de Restore (Mensal)

```bash
# Criar ambiente de teste
# Executar restore
# Validar funcionamento
# Documentar resultado
```

---

## 🔄 ROLLBACK

### Procedimento de Rollback

#### 1. Rollback Rápido (Mesma Versão)

```bash
# Parar serviços
docker-compose -f docker-compose.prod.yml down

# Restore do último backup
./restore.sh backups/backup_<TIMESTAMP>.tar.gz

# Subir serviços
docker-compose -f docker-compose.prod.yml up -d

# Validar
curl https://nise.intellicare.com/health
```

#### 2. Rollback para Versão Anterior

```bash
# Checkout versão anterior
git checkout v0.9.0

# Rebuild imagens
docker build -t intellicare/nise-api:0.9.0 .

# Atualizar docker-compose
# Mudar image: intellicare/nise-api:1.0.0 → 0.9.0

# Restart
docker-compose -f docker-compose.prod.yml up -d

# Validar
curl https://nise.intellicare.com/health
```

#### 3. Rollback de Database

```bash
# Se houver migrations
docker exec nise-api-prod alembic downgrade -1

# Ou restore completo
./restore.sh backups/backup_<TIMESTAMP>.tar.gz
```

---

## 🔧 MANUTENÇÃO

### Manutenção Regular

#### Diária
- [ ] Verificar logs de erro
- [ ] Verificar alertas
- [ ] Verificar métricas de performance
- [ ] Verificar espaço em disco

#### Semanal
- [ ] Revisar logs completos
- [ ] Verificar backups
- [ ] Atualizar dependências (se necessário)
- [ ] Revisar métricas de uso

#### Mensal
- [ ] Teste de restore de backup
- [ ] Análise de performance
- [ ] Revisão de segurança
- [ ] Limpeza de logs antigos
- [ ] Atualização de documentação

#### Trimestral
- [ ] Disaster recovery drill
- [ ] Revisão de capacidade
- [ ] Auditoria de segurança
- [ ] Planejamento de upgrades

### Atualizações

#### Atualizar Aplicação

```bash
# 1. Backup
./backup.sh

# 2. Pull nova versão
git pull origin production

# 3. Rebuild
docker build -t intellicare/nise-api:1.1.0 .

# 4. Atualizar docker-compose.prod.yml
# Mudar versão da imagem

# 5. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 6. Validar
curl https://nise.intellicare.com/health

# 7. Monitorar logs
docker logs -f nise-api-prod
```

#### Atualizar Dependências

```bash
# Atualizar imagens Docker
docker-compose -f docker-compose.prod.yml pull

# Restart com novas imagens
docker-compose -f docker-compose.prod.yml up -d

# Validar
docker-compose -f docker-compose.prod.yml ps
```

### Troubleshooting em Produção

#### Serviço não responde

```bash
# 1. Verificar status
docker-compose -f docker-compose.prod.yml ps

# 2. Ver logs
docker logs nise-api-prod --tail 100

# 3. Verificar recursos
docker stats

# 4. Restart se necessário
docker-compose -f docker-compose.prod.yml restart nise-api

# 5. Se persistir, rollback
./restore.sh backups/backup_<LAST_GOOD>.tar.gz
```

#### Performance degradada

```bash
# 1. Verificar métricas
# Acessar Grafana

# 2. Verificar cache Redis
docker exec redis-prod redis-cli INFO stats

# 3. Verificar conexões DB
docker exec postgres-prod psql -U nise_prod_user -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Verificar logs de slow queries
docker logs postgres-prod | grep "duration"

# 5. Limpar cache se necessário
docker exec redis-prod redis-cli FLUSHDB
```

---

## 📞 SUPORTE E CONTATOS

### Equipe de Plantão

| Função | Nome | Contato | Horário |
|--------|------|---------|---------|
| **DevOps Lead** | [Nome] | [Email/Tel] | 24/7 |
| **Backend Lead** | [Nome] | [Email/Tel] | 8h-18h |
| **DBA** | [Nome] | [Email/Tel] | 8h-18h |
| **Segurança** | [Nome] | [Email/Tel] | On-call |

### Escalação

1. **Nível 1**: DevOps on-call
2. **Nível 2**: Backend Lead + DBA
3. **Nível 3**: CTO

### Canais de Comunicação

- **Slack**: #intellicare-producao
- **PagerDuty**: [Link]
- **Email**: ops@intellicare.com
- **Telefone**: +55 11 XXXX-XXXX

---

## ✅ CONCLUSÃO

Este guia cobre todo o processo de deployment em produção do IntelliCare NISE.

### Pontos-Chave

✅ **Segurança em primeiro lugar**: HTTPS, secrets, rate limiting
✅ **Monitoramento ativo**: Prometheus, Grafana, alertas
✅ **Backup regular**: Diário, testado, com retenção
✅ **Disaster recovery**: Procedimentos documentados e testados
✅ **Manutenção planejada**: Checklists diários, semanais, mensais

### Próximos Passos Após Deployment

1. ✅ Monitorar primeiras 24h intensivamente
2. ✅ Coletar feedback de usuários
3. ✅ Ajustar configurações baseado em métricas reais
4. ✅ Documentar lições aprendidas
5. ✅ Planejar melhorias contínuas

---

**Status**: ✅ **PRONTO PARA PRODUÇÃO**

**Versão do Guia**: 1.0.0
**Última Atualização**: 15/02/2026
**Autor**: IntelliCare DevOps Team


