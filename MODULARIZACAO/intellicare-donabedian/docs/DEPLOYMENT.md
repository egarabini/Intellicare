# 🚀 Guia de Deploy e Configuração

## Visão Geral

Este guia cobre a implantação do módulo **intellicare-donabedian** em diferentes ambientes: desenvolvimento local, staging e produção.

---

## 📋 Pré-requisitos

### Desenvolvimento Local
- Python 3.11+
- PostgreSQL 15+
- Git

### Docker
- Docker 24+
- Docker Compose 2.20+

### Produção
- Servidor Linux (Ubuntu 22.04 LTS recomendado)
- PostgreSQL 15+ (pode ser externo)
- Nginx (reverse proxy)
- Certificado SSL (Let's Encrypt)

---

## 🔧 Variáveis de Ambiente

### Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto:

```bash
# Database Configuration
INTELLICARE_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/intellicare
DATABASE_SCHEMA=intellicare_donabedian

# API Configuration
API_HOST=0.0.0.0
API_PORT=8003
API_RELOAD=false
API_WORKERS=4

# Dashboard Configuration
DASHBOARD_PORT=8501
DASHBOARD_API_URL=http://localhost:8003/api/v1

# Environment
ENVIRONMENT=production  # development, staging, production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# CORS (separado por vírgula)
CORS_ORIGINS=http://localhost:3000,https://app.intellicare.com.br

# Security (para versões futuras)
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
```

### Variáveis Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `INTELLICARE_DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+asyncpg://user:pass@host:5432/db` |
| `DATABASE_SCHEMA` | Schema do módulo | `intellicare_donabedian` |

### Variáveis Opcionais

| Variável | Default | Descrição |
|----------|---------|-----------|
| `API_HOST` | `0.0.0.0` | Host da API |
| `API_PORT` | `8003` | Porta da API |
| `API_RELOAD` | `false` | Auto-reload (dev only) |
| `API_WORKERS` | `4` | Número de workers |
| `DASHBOARD_PORT` | `8501` | Porta do dashboard |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `ENVIRONMENT` | `development` | Ambiente |

---

## 🐳 Deploy com Docker

### 1. Desenvolvimento Local

```bash
# Clone o repositório
git clone <repo-url>
cd MODULARIZACAO/intellicare-donabedian

# Copie o arquivo de ambiente
cp .env.example .env

# Edite o .env com suas configurações
nano .env

# Suba os containers
docker compose up -d

# Verifique os logs
docker compose logs -f

# Acesse:
# - API: http://localhost:8003
# - Dashboard: http://localhost:8501
# - Docs: http://localhost:8003/docs
```

### 2. Produção com Docker

```bash
# Use o arquivo docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d

# Ou configure variáveis de ambiente
export ENVIRONMENT=production
export API_RELOAD=false
export API_WORKERS=8
docker compose up -d
```

### 3. Comandos Úteis

```bash
# Parar containers
docker compose down

# Rebuild images
docker compose build --no-cache

# Ver logs
docker compose logs -f api
docker compose logs -f dashboard

# Executar migrations
docker compose exec api alembic upgrade head

# Acessar shell do container
docker compose exec api bash

# Limpar volumes (CUIDADO!)
docker compose down -v
```

---

## 💻 Deploy Manual (Sem Docker)

### 1. Preparação do Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Instalar Nginx
sudo apt install nginx -y

# Instalar supervisor (gerenciador de processos)
sudo apt install supervisor -y
```

### 2. Configurar PostgreSQL

```bash
# Acessar PostgreSQL
sudo -u postgres psql

# Criar usuário e banco
CREATE USER intellicare WITH PASSWORD 'senha-segura';
CREATE DATABASE intellicare OWNER intellicare;

# Criar schema
\c intellicare
CREATE SCHEMA intellicare_donabedian AUTHORIZATION intellicare;

# Sair
\q
```

### 3. Configurar Aplicação

```bash
# Criar diretório
sudo mkdir -p /opt/intellicare/donabedian
cd /opt/intellicare/donabedian

# Clonar repositório
git clone <repo-url> .

# Criar ambiente virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -e .

# Configurar .env
cp .env.example .env
nano .env

# Executar migrations
alembic upgrade head
```

### 4. Configurar Supervisor (API)

Criar arquivo `/etc/supervisor/conf.d/intellicare-donabedian-api.conf`:

```ini
[program:intellicare-donabedian-api]
directory=/opt/intellicare/donabedian
command=/opt/intellicare/donabedian/.venv/bin/uvicorn donabedian.main:app --host 0.0.0.0 --port 8003 --workers 4
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/intellicare/donabedian-api.log
environment=PYTHONPATH="/opt/intellicare/donabedian/src"
```

### 5. Configurar Supervisor (Dashboard)

Criar arquivo `/etc/supervisor/conf.d/intellicare-donabedian-dashboard.conf`:

```ini
[program:intellicare-donabedian-dashboard]
directory=/opt/intellicare/donabedian
command=/opt/intellicare/donabedian/.venv/bin/streamlit run src/donabedian/dashboard/app.py --server.port 8501
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/intellicare/donabedian-dashboard.log
environment=PYTHONPATH="/opt/intellicare/donabedian/src"
```

### 6. Iniciar Serviços

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/intellicare
sudo chown www-data:www-data /var/log/intellicare

# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar serviços
sudo supervisorctl start intellicare-donabedian-api
sudo supervisorctl start intellicare-donabedian-dashboard

# Verificar status
sudo supervisorctl status
```

### 7. Configurar Nginx (Reverse Proxy)

Criar arquivo `/etc/nginx/sites-available/intellicare-donabedian`:

```nginx
# API
server {
    listen 80;
    server_name api-donabedian.intellicare.com.br;

    location / {
        proxy_pass http://127.0.0.1:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Dashboard
server {
    listen 80;
    server_name dashboard-donabedian.intellicare.com.br;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Ativar site:

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/intellicare-donabedian /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

### 8. Configurar SSL com Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificados
sudo certbot --nginx -d api-donabedian.intellicare.com.br
sudo certbot --nginx -d dashboard-donabedian.intellicare.com.br

# Renovação automática (já configurado)
sudo certbot renew --dry-run
```

---

## 🔄 Migrations de Banco de Dados

### Executar Migrations

```bash
# Desenvolvimento
alembic upgrade head

# Docker
docker compose exec api alembic upgrade head

# Produção
cd /opt/intellicare/donabedian
source .venv/bin/activate
alembic upgrade head
```

### Criar Nova Migration

```bash
# Gerar migration automática
alembic revision --autogenerate -m "Descrição da mudança"

# Editar migration gerada
nano alembic/versions/<timestamp>_descricao.py

# Aplicar migration
alembic upgrade head
```

### Rollback

```bash
# Voltar uma migration
alembic downgrade -1

# Voltar para versão específica
alembic downgrade <revision_id>

# Ver histórico
alembic history
```

---

## 📊 Monitoramento

### Health Check

```bash
# Verificar saúde da API
curl http://localhost:8003/health

# Resposta esperada:
# {
#   "status": "healthy",
#   "database": "connected",
#   "timestamp": "2024-02-10T15:30:00"
# }
```

### Logs

```bash
# Logs da API (supervisor)
sudo tail -f /var/log/intellicare/donabedian-api.log

# Logs do Dashboard (supervisor)
sudo tail -f /var/log/intellicare/donabedian-dashboard.log

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Métricas

```bash
# Processos
ps aux | grep uvicorn
ps aux | grep streamlit

# Memória
free -h

# Disco
df -h

# Conexões de banco
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='intellicare';"
```

---

## 🔒 Segurança

### Firewall

```bash
# Permitir apenas portas necessárias
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Bloquear acesso direto às portas da aplicação
# (apenas via Nginx)
```

### PostgreSQL

```bash
# Editar pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Permitir apenas localhost
# local   all             all                                     peer
# host    all             all             127.0.0.1/32            scram-sha-256

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### Backup

```bash
# Backup do banco
pg_dump -U intellicare -h localhost intellicare > backup_$(date +%Y%m%d).sql

# Backup do schema específico
pg_dump -U intellicare -h localhost -n intellicare_donabedian intellicare > backup_donabedian_$(date +%Y%m%d).sql

# Restaurar backup
psql -U intellicare -h localhost intellicare < backup_20240210.sql

# Automatizar backup (crontab)
0 2 * * * /usr/bin/pg_dump -U intellicare -h localhost intellicare > /backup/intellicare_$(date +\%Y\%m\%d).sql
```

---

## 🐛 Troubleshooting

### API não inicia

```bash
# Verificar logs
sudo supervisorctl tail -f intellicare-donabedian-api

# Verificar porta
sudo netstat -tulpn | grep 8003

# Testar manualmente
cd /opt/intellicare/donabedian
source .venv/bin/activate
uvicorn donabedian.main:app --host 0.0.0.0 --port 8003
```

### Dashboard não carrega

```bash
# Verificar logs
sudo supervisorctl tail -f intellicare-donabedian-dashboard

# Verificar se API está acessível
curl http://localhost:8003/health

# Testar manualmente
cd /opt/intellicare/donabedian
source .venv/bin/activate
streamlit run src/donabedian/dashboard/app.py
```

### Erro de conexão com banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
psql -U intellicare -h localhost -d intellicare

# Verificar variável de ambiente
echo $INTELLICARE_DATABASE_URL

# Verificar logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Migrations falhando

```bash
# Verificar versão atual
alembic current

# Ver histórico
alembic history

# Forçar versão (CUIDADO!)
alembic stamp head

# Recriar banco (DESENVOLVIMENTO APENAS!)
alembic downgrade base
alembic upgrade head
```

---

## 📈 Performance Tuning

### PostgreSQL

Editar `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Memória
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# Conexões
max_connections = 100

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
```

### Uvicorn

```bash
# Aumentar workers (1-2 por CPU core)
uvicorn donabedian.main:app --workers 8

# Usar Gunicorn com Uvicorn workers
gunicorn donabedian.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Nginx

```nginx
# Cache de arquivos estáticos
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Compressão
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

---

## 🔄 Atualização

### Processo de Atualização

```bash
# 1. Backup do banco
pg_dump -U intellicare intellicare > backup_pre_update.sql

# 2. Parar serviços
sudo supervisorctl stop intellicare-donabedian-api
sudo supervisorctl stop intellicare-donabedian-dashboard

# 3. Atualizar código
cd /opt/intellicare/donabedian
git pull origin main

# 4. Atualizar dependências
source .venv/bin/activate
pip install --upgrade -e .

# 5. Executar migrations
alembic upgrade head

# 6. Reiniciar serviços
sudo supervisorctl start intellicare-donabedian-api
sudo supervisorctl start intellicare-donabedian-dashboard

# 7. Verificar saúde
curl http://localhost:8003/health
```

---

## 📝 Checklist de Deploy

### Pré-Deploy

- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados criado e acessível
- [ ] Migrations testadas
- [ ] Testes passando (>80% coverage)
- [ ] Backup do banco de dados

### Deploy

- [ ] Código atualizado
- [ ] Dependências instaladas
- [ ] Migrations executadas
- [ ] Serviços iniciados
- [ ] Health check OK

### Pós-Deploy

- [ ] Logs verificados
- [ ] Métricas normais
- [ ] Testes de fumaça executados
- [ ] Documentação atualizada
- [ ] Equipe notificada

---

## 📚 Referências

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

