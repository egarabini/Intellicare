# 🚀 IntelliCare - Guia de Deploy

**Versão:** 0.1.0-demo
**Data:** 2026-02-20
**Status:** Fase 3 - Deploy Mínimo Viável

---

## 📚 Documentação Específica de Servidores

Para configurações detalhadas de servidores específicos, consulte:

- **Servidor de Homologação (Contabo):** [`docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md`](docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md)
- **Quick Start Homologação:** [`docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_README.md`](docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_README.md)
- **Índice de Servidores:** [`docs/SERVIDORES/README.md`](docs/SERVIDORES/README.md)

Este guia contém instruções **gerais** de deploy. Para instruções específicas de cada ambiente, consulte a documentação acima.

---

## 📋 Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Deploy Local (Desenvolvimento)](#2-deploy-local-desenvolvimento)
3. [Deploy em VPS (Staging/Produção)](#3-deploy-em-vps-stagingprodução)
4. [Configuração HTTPS](#4-configuração-https)
5. [Smoke Tests](#5-smoke-tests)
6. [Troubleshooting](#6-troubleshooting)
7. [Rollback](#7-rollback)
8. [Monitoramento](#8-monitoramento)

---

## 1. Pré-requisitos

### 1.1 Software Necessário

#### Desenvolvimento Local
- **Docker** 24.0+ ([Instalar](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.20+ (incluído no Docker Desktop)
- **Git** 2.40+
- **Python** 3.11+ (para smoke tests)

#### VPS/Produção
- **Ubuntu** 22.04 LTS ou superior
- **Docker** 24.0+
- **Docker Compose** 2.20+
- **Nginx** (para reverse proxy e HTTPS)
- **Certbot** (para Let's Encrypt)
- **Git** 2.40+

### 1.2 Recursos Mínimos

#### Desenvolvimento Local
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 20 GB livres

#### Staging
- **CPU:** 4 cores (2.5 GHz+)
- **RAM:** 16 GB
- **Disco:** 50 GB SSD

#### Produção
- **CPU:** 8 cores (3.0 GHz+)
- **RAM:** 32 GB
- **Disco:** 100 GB SSD
- **Rede:** 100 Mbps+

### 1.3 Portas Necessárias

| Serviço | Porta | Protocolo | Público |
|---------|-------|-----------|---------|
| Portal (Frontend) | 3001 | HTTP | ✅ Sim |
| Florence | 8001 | HTTP | ❌ Não |
| Oswaldo | 8002 | HTTP | ❌ Não |
| Donabedian | 8003 | HTTP | ❌ Não |
| Wanda | 8004 | HTTP | ❌ Não |
| Comunicacao | 8005 | HTTP | ❌ Não |
| Geralda | 8006 | HTTP | ❌ Não |
| PostgreSQL | 5432 | TCP | ❌ Não |
| Redis | 6379 | TCP | ❌ Não |
| Prometheus | 9090 | HTTP | ⚠️ Interno |
| Grafana | 3000 | HTTP | ⚠️ Interno |
| HTTPS (Nginx) | 443 | HTTPS | ✅ Sim |

---

## 2. Deploy Local (Desenvolvimento)

### 2.1 Clone do Repositório

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/intellicare.git
cd intellicare/MODULARIZACAO

# Verificar branch
git branch
# Deve estar em: main ou develop
```

### 2.2 Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar variáveis (IMPORTANTE!)
# Windows: notepad .env
# Linux/macOS: nano .env
```

**Variáveis críticas para alterar:**
```bash
# Senhas (MUDAR EM PRODUÇÃO!)
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION
REDIS_PASSWORD=CHANGE_ME_IN_PRODUCTION
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_IN_PRODUCTION

# URLs dos backends (localhost para desenvolvimento)
VITE_API_FLORENCE_URL=http://localhost:8001
VITE_API_OSWALDO_URL=http://localhost:8002
# ... (manter localhost para dev)
```

### 2.3 Subir Infraestrutura

```bash
# Subir apenas infraestrutura (PostgreSQL, Redis, Prometheus, Grafana)
docker-compose up -d

# Verificar logs
docker-compose logs -f postgres redis
```

### 2.4 Subir Stack Completa

```bash
# Subir todos os serviços (6 backends + 1 frontend + 4 infra)
docker-compose -f docker-compose.full.yml up -d

# Verificar status
docker-compose -f docker-compose.full.yml ps

# Verificar logs de um serviço específico
docker-compose -f docker-compose.full.yml logs -f florence
```

### 2.5 Executar Smoke Tests

```bash
# Instalar dependências do script
pip install requests

# Executar smoke tests
python scripts/smoke_tests.py

# Resultado esperado: ✅ TODOS OS SERVIÇOS ESTÃO SAUDÁVEIS!
```

### 2.6 Acessar Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Portal** | http://localhost:3001 | - |
| **Florence API** | http://localhost:8001/docs | - |
| **Oswaldo API** | http://localhost:8002/docs | - |
| **Donabedian API** | http://localhost:8003/docs | - |
| **Wanda API** | http://localhost:8004/docs | - |
| **Comunicacao API** | http://localhost:8005/docs | - |
| **Geralda API** | http://localhost:8006/docs | - |
| **Grafana** | http://localhost:3000 | admin / (ver .env) |
| **Prometheus** | http://localhost:9090 | - |

---

## 3. Deploy em VPS (Staging/Produção)

### 3.1 Preparar VPS

```bash
# Conectar ao VPS
ssh usuario@seu-vps.com

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Instalar Nginx
sudo apt install nginx -y

# Instalar Certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y

# Reiniciar sessão para aplicar grupo docker
exit
ssh usuario@seu-vps.com
```

### 3.2 Clone e Configuração

```bash
# Clone do repositório
git clone https://github.com/seu-usuario/intellicare.git
cd intellicare/MODULARIZACAO

# Criar .env de produção
cp .env.example .env
nano .env
```

**Variáveis críticas para PRODUÇÃO:**
```bash
# ENVIRONMENT
ENVIRONMENT=production
LOG_LEVEL=INFO
DOMAIN=intellicare.com.br

# SENHAS FORTES (gerar com: openssl rand -base64 32)
POSTGRES_PASSWORD=<senha-forte-aqui>
REDIS_PASSWORD=<senha-forte-aqui>
GRAFANA_ADMIN_PASSWORD=<senha-forte-aqui>

# URLs dos backends (usar domínio de produção)
VITE_API_FLORENCE_URL=https://api.intellicare.com.br/florence
VITE_API_OSWALDO_URL=https://api.intellicare.com.br/oswaldo
VITE_API_DONABEDIAN_URL=https://api.intellicare.com.br/donabedian
VITE_API_WANDA_URL=https://api.intellicare.com.br/wanda
VITE_API_COMUNICACAO_URL=https://api.intellicare.com.br/comunicacao
VITE_API_GERALDA_URL=https://api.intellicare.com.br/geralda

# Analytics (habilitar em produção)
VITE_ENABLE_ANALYTICS=true
```

### 3.3 Build e Deploy

```bash
# Build das imagens
docker-compose -f docker-compose.full.yml build

# Subir stack completa
docker-compose -f docker-compose.full.yml up -d

# Verificar status
docker-compose -f docker-compose.full.yml ps

# Verificar logs
docker-compose -f docker-compose.full.yml logs -f
```

### 3.4 Configurar Nginx como Reverse Proxy

```bash
# Criar configuração do Nginx
sudo nano /etc/nginx/sites-available/intellicare
```

**Conteúdo do arquivo:**
```nginx
# Frontend (Portal)
server {
    listen 80;
    server_name intellicare.com.br www.intellicare.com.br;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API Gateway (Backends)
server {
    listen 80;
    server_name api.intellicare.com.br;

    # Florence
    location /florence {
        rewrite ^/florence/(.*) /$1 break;
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Oswaldo
    location /oswaldo {
        rewrite ^/oswaldo/(.*) /$1 break;
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Donabedian
    location /donabedian {
        rewrite ^/donabedian/(.*) /$1 break;
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Wanda
    location /wanda {
        rewrite ^/wanda/(.*) /$1 break;
        proxy_pass http://localhost:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Comunicacao
    location /comunicacao {
        rewrite ^/comunicacao/(.*) /$1 break;
        proxy_pass http://localhost:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Geralda
    location /geralda {
        rewrite ^/geralda/(.*) /$1 break;
        proxy_pass http://localhost:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Monitoramento (Grafana) - Acesso restrito
server {
    listen 80;
    server_name monitoring.intellicare.com.br;

    # Restringir acesso por IP (opcional)
    # allow 203.0.113.0/24;  # Seu IP
    # deny all;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Ativar configuração:**
```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/intellicare /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

---

## 4. Configuração HTTPS

### 4.1 Obter Certificado SSL (Let's Encrypt)

```bash
# Obter certificado para todos os domínios
sudo certbot --nginx -d intellicare.com.br -d www.intellicare.com.br \
  -d api.intellicare.com.br -d monitoring.intellicare.com.br

# Seguir instruções interativas
# Email: seu-email@example.com
# Aceitar termos: Y
# Compartilhar email: N (opcional)
# Redirect HTTP -> HTTPS: 2 (Sim, recomendado)
```

### 4.2 Renovação Automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Certbot já configura cron job automático
# Verificar: sudo systemctl status certbot.timer
```

### 4.3 Verificar HTTPS

```bash
# Testar certificado
curl -I https://intellicare.com.br
curl -I https://api.intellicare.com.br/florence/health

# Resultado esperado: HTTP/2 200
```

---

## 5. Smoke Tests

### 5.1 Testes Locais

```bash
# Testar localhost
python scripts/smoke_tests.py

# Salvar relatório
python scripts/smoke_tests.py --json smoke_test_local.json
```

### 5.2 Testes em Produção

```bash
# Testar produção
python scripts/smoke_tests.py --url https://intellicare.com.br

# Salvar relatório com timestamp
python scripts/smoke_tests.py \
  --url https://intellicare.com.br \
  --json smoke_test_prod_$(date +%Y%m%d_%H%M%S).json
```

### 5.3 Integração com CI/CD

```yaml
# Exemplo: GitHub Actions
- name: Run Smoke Tests
  run: |
    python scripts/smoke_tests.py --url https://staging.intellicare.com.br
  continue-on-error: false
```

---

## 6. Troubleshooting

### 6.1 Serviço Não Inicia

**Problema:** Container não sobe ou reinicia constantemente

**Diagnóstico:**
```bash
# Ver logs do serviço
docker-compose -f docker-compose.full.yml logs florence

# Ver status detalhado
docker inspect intellicare-florence

# Ver uso de recursos
docker stats
```

**Soluções:**
- Verificar variáveis de ambiente no `.env`
- Verificar se PostgreSQL está saudável: `docker-compose logs postgres`
- Verificar se Redis está saudável: `docker-compose logs redis`
- Aumentar `start_period` no health check (docker-compose.full.yml)

### 6.2 Erro de Conexão com Database

**Problema:** `FATAL: password authentication failed`

**Solução:**
```bash
# 1. Verificar senha no .env
grep POSTGRES_PASSWORD .env

# 2. Recriar volume do PostgreSQL (CUIDADO: apaga dados!)
docker-compose down -v
docker-compose up -d postgres

# 3. Verificar conectividade
docker exec -it intellicare-postgres psql -U intellicare_admin -d intellicare_db
```

### 6.3 Frontend Não Carrega APIs

**Problema:** CORS errors ou 404 ao chamar backends

**Diagnóstico:**
```bash
# Verificar variáveis VITE_* foram injetadas no build
docker exec intellicare-portal cat /usr/share/nginx/html/assets/index-*.js | grep VITE_API
```

**Solução:**
```bash
# Rebuild do frontend com variáveis corretas
docker-compose -f docker-compose.full.yml build portal
docker-compose -f docker-compose.full.yml up -d portal
```

### 6.4 Porta Já Em Uso

**Problema:** `Bind for 0.0.0.0:8001 failed: port is already allocated`

**Diagnóstico:**
```bash
# Windows
netstat -ano | findstr :8001

# Linux/macOS
lsof -i :8001
```

**Solução:**
```bash
# Opção 1: Parar processo que está usando a porta
# Windows: taskkill /PID <PID> /F
# Linux: kill -9 <PID>

# Opção 2: Mudar porta no .env
# Editar .env e mudar FLORENCE_PORT=8001 para FLORENCE_PORT=8011
# Rebuild: docker-compose -f docker-compose.full.yml up -d florence
```

### 6.5 Disco Cheio

**Problema:** `no space left on device`

**Diagnóstico:**
```bash
# Ver uso de disco
df -h

# Ver uso do Docker
docker system df
```

**Solução:**
```bash
# Limpar containers parados
docker container prune -f

# Limpar imagens não usadas
docker image prune -a -f

# Limpar volumes não usados (CUIDADO!)
docker volume prune -f

# Limpar tudo (CUIDADO: apaga dados!)
docker system prune -a --volumes -f
```

### 6.6 SSL/HTTPS Não Funciona

**Problema:** `ERR_SSL_PROTOCOL_ERROR` ou certificado inválido

**Diagnóstico:**
```bash
# Verificar certificado
sudo certbot certificates

# Testar SSL
openssl s_client -connect intellicare.com.br:443 -servername intellicare.com.br
```

**Solução:**
```bash
# Renovar certificado
sudo certbot renew --force-renewal

# Recarregar Nginx
sudo systemctl reload nginx

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 7. Rollback

### 7.1 Rollback de Versão (Git Tags)

```bash
# Listar tags disponíveis
git tag -l

# Exemplo de output:
# v0.1.0-demo
# v0.2.0-beta
# v1.0.0

# Fazer checkout de versão anterior
git checkout v0.1.0-demo

# Rebuild e redeploy
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d

# Executar smoke tests
python scripts/smoke_tests.py
```

### 7.2 Rollback de Serviço Específico

```bash
# Parar serviço com problema
docker-compose -f docker-compose.full.yml stop florence

# Fazer checkout de versão anterior do módulo
cd intellicare-florence
git log --oneline -10  # Ver últimos commits
git checkout <commit-hash-anterior>
cd ..

# Rebuild apenas o serviço
docker-compose -f docker-compose.full.yml build florence
docker-compose -f docker-compose.full.yml up -d florence

# Verificar saúde
curl http://localhost:8001/health
```

### 7.3 Rollback de Database (Alembic)

```bash
# Listar migrações
docker exec intellicare-florence alembic history

# Fazer downgrade para revisão anterior
docker exec intellicare-florence alembic downgrade -1

# Ou para revisão específica
docker exec intellicare-florence alembic downgrade <revision-id>
```

### 7.4 Backup e Restore

**Backup:**
```bash
# Backup do PostgreSQL
docker exec intellicare-postgres pg_dump -U intellicare_admin intellicare_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup de volumes
docker run --rm -v intellicare_postgres-data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data
```

**Restore:**
```bash
# Restore do PostgreSQL
cat backup_20260220_153000.sql | docker exec -i intellicare-postgres psql -U intellicare_admin intellicare_db

# Restore de volume
docker run --rm -v intellicare_postgres-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/postgres_backup_20260220_153000.tar.gz -C /
```

---

## 8. Monitoramento

### 8.1 Acessar Grafana

```bash
# URL: http://localhost:3000 (dev) ou https://monitoring.intellicare.com.br (prod)
# Usuário: admin
# Senha: (ver GRAFANA_ADMIN_PASSWORD no .env)
```

**Dashboards disponíveis:**
- **IntelliCare - Overview**: Visão geral de todos os módulos
- **IntelliCare - Florence**: Métricas do módulo Florence
- **IntelliCare - Oswaldo**: Métricas do módulo Oswaldo
- **IntelliCare - Comunicacao**: Métricas do módulo Comunicacao
- **IntelliCare - Infrastructure**: PostgreSQL, Redis, Docker

### 8.2 Acessar Prometheus

```bash
# URL: http://localhost:9090 (dev)
```

**Queries úteis:**
```promql
# Taxa de requisições por segundo
rate(http_requests_total[5m])

# Latência P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Uso de memória
container_memory_usage_bytes{name=~"intellicare-.*"}

# Erros HTTP 5xx
rate(http_requests_total{status=~"5.."}[5m])
```

### 8.3 Logs Centralizados

```bash
# Ver logs de todos os serviços
docker-compose -f docker-compose.full.yml logs -f

# Ver logs de serviço específico
docker-compose -f docker-compose.full.yml logs -f florence

# Ver logs com timestamp
docker-compose -f docker-compose.full.yml logs -f --timestamps

# Ver últimas 100 linhas
docker-compose -f docker-compose.full.yml logs --tail=100 florence
```

### 8.4 Alertas (Prometheus + Grafana)

**Configurar alertas no Grafana:**
1. Acessar Grafana → Alerting → Alert rules
2. Criar nova regra:
   - **Nome:** High Error Rate
   - **Query:** `rate(http_requests_total{status=~"5.."}[5m]) > 0.1`
   - **Threshold:** > 0.1 (10% de erros)
   - **Notification:** Email, Slack, PagerDuty

**Alertas pré-configurados** (ver `alerts.yml`):
- High CPU usage (> 80%)
- High memory usage (> 90%)
- High error rate (> 5%)
- Service down (health check failed)
- Database connection pool exhausted

---

## 9. Checklist de Deploy

### 9.1 Pré-Deploy

- [ ] Código revisado e aprovado (Pull Request)
- [ ] Testes unitários passando (pytest)
- [ ] Testes de integração passando
- [ ] Variáveis de ambiente configuradas (`.env`)
- [ ] Senhas fortes geradas (PostgreSQL, Redis, Grafana)
- [ ] Backup do banco de dados criado
- [ ] Documentação atualizada

### 9.2 Deploy

- [ ] Git pull da versão correta (tag ou branch)
- [ ] Build das imagens (`docker-compose build`)
- [ ] Subir stack completa (`docker-compose up -d`)
- [ ] Verificar status dos containers (`docker-compose ps`)
- [ ] Executar smoke tests (`python scripts/smoke_tests.py`)
- [ ] Verificar logs (`docker-compose logs`)

### 9.3 Pós-Deploy

- [ ] Smoke tests passando (100% healthy)
- [ ] Frontend acessível e funcional
- [ ] APIs respondendo corretamente
- [ ] HTTPS funcionando (certificado válido)
- [ ] Grafana mostrando métricas
- [ ] Alertas configurados
- [ ] Backup pós-deploy criado
- [ ] Documentar versão deployada (tag Git)

---

## 10. Referências

### 10.1 Documentação Interna

- **[.env.example](/.env.example)** - Template de variáveis de ambiente
- **[docker-compose.full.yml](/docker-compose.full.yml)** - Orquestração completa
- **[scripts/smoke_tests.py](/scripts/smoke_tests.py)** - Script de validação
- **[CHANGELOG.md](/CHANGELOG.md)** - Histórico de mudanças

### 10.2 Documentação dos Módulos

- **[Florence](/intellicare-florence/README.md)** - RAG + Protocolos Clínicos
- **[Oswaldo](/intellicare-oswaldo/README.md)** - Análise Clínica + FHIR
- **[Donabedian](/intellicare-donabedian/README.md)** - Qualidade + Indicadores
- **[Wanda](/intellicare-wanda/README.md)** - Orquestração + Workflows
- **[Comunicacao](/intellicare-comunicacao/README.md)** - Comunicação + Notificações
- **[Geralda](/intellicare-geralda/README.md)** - Gestão + Administrativo
- **[Portal](/intellicare-portal/frontend/DEPLOY.md)** - Frontend React

### 10.3 Documentação Externa

- **[Docker Docs](https://docs.docker.com/)** - Documentação oficial do Docker
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestração de containers
- **[Nginx](https://nginx.org/en/docs/)** - Reverse proxy e web server
- **[Let's Encrypt](https://letsencrypt.org/docs/)** - Certificados SSL gratuitos
- **[Prometheus](https://prometheus.io/docs/)** - Monitoramento e alertas
- **[Grafana](https://grafana.com/docs/)** - Visualização de métricas

---

## 11. Suporte

### 11.1 Contatos

- **Equipe de Desenvolvimento:** dev@intellicare.com.br
- **Suporte Técnico:** suporte@intellicare.com.br
- **Emergências (24/7):** +55 11 9999-9999

### 11.2 Canais

- **Slack:** #intellicare-deploy
- **GitHub Issues:** https://github.com/seu-usuario/intellicare/issues
- **Documentação:** https://docs.intellicare.com.br

---

**Versão do Guia:** 1.0
**Última Atualização:** 2026-02-20
**Próxima Revisão:** 2026-03-20

