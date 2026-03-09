# 🚀 Servidor de Homologação - CONTABO

## 📋 Informações do Servidor

| Item | Valor |
|------|-------|
| **Nome** | SERVER 05 - INTELLICARE |
| **IP Público** | `167.86.97.142` |
| **Provedor** | Contabo VPS |
| **Plano** | VPS 40 NVMe |
| **vCPU** | 12 Cores |
| **RAM** | 48 GB |
| **Disco** | 250 GB NVMe |
| **Rede** | 800 Mbit/s |
| **Custo** | USD 20.80/mês (12 meses) |
| **Usuário** | root |
| **Ambiente** | Homologação |

---

## 🔐 Credenciais de Acesso

```bash
# SSH
ssh root@167.86.97.142
# Senha: Soeuso419863
```

**⚠️ IMPORTANTE:** Após primeiro acesso, altere a senha root e configure autenticação por chave SSH!

---

## 📦 Repositório GitHub

```bash
# Repositório
https://github.com/eduardo/intellicare

# Clone
git clone https://github.com/eduardo/intellicare.git
cd intellicare
```

---

## 🛠️ Passo 1: Preparar o Servidor (Primeira Vez)

### 1.1. Conectar ao Servidor

```bash
ssh root@167.86.97.142
```

### 1.2. Atualizar Sistema

```bash
# Atualizar pacotes
apt update && apt upgrade -y

# Instalar utilitários básicos
apt install -y curl wget git vim htop net-tools ufw
```

### 1.3. Configurar Firewall

```bash
# Permitir SSH
ufw allow 22/tcp

# Permitir HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Permitir portas dos serviços IntelliCare
ufw allow 3001/tcp  # Portal Frontend
ufw allow 8001/tcp  # Florence
ufw allow 8002/tcp  # Oswaldo
ufw allow 8003/tcp  # Donabedian
ufw allow 8004/tcp  # Wanda
ufw allow 8005/tcp  # Comunicacao
ufw allow 8006/tcp  # Geralda

# Permitir Monitoring (opcional - apenas para IPs confiáveis)
# ufw allow from SEU_IP to any port 3000  # Grafana
# ufw allow from SEU_IP to any port 9090  # Prometheus

# Ativar firewall
ufw --force enable

# Verificar status
ufw status
```

### 1.4. Instalar Docker

```bash
# Remover versões antigas (se existirem)
apt remove -y docker docker-engine docker.io containerd runc

# Instalar dependências
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Verificar instalação
docker --version
```

### 1.5. Instalar Docker Compose

```bash
# Baixar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permissão de execução
chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker-compose --version
```

### 1.6. Configurar Git

```bash
# Configurar usuário Git
git config --global user.name "IntelliCare Homolog"
git config --global user.email "homolog@intellicare.com.br"

# Configurar credenciais GitHub (se repositório privado)
git config --global credential.helper store
```

---

## 📥 Passo 2: Clonar Repositório

```bash
# Criar diretório de projetos
mkdir -p /opt/intellicare
cd /opt/intellicare

# Clonar repositório
git clone https://github.com/eduardo/intellicare.git
cd intellicare

# Verificar branch
git branch
git status
```

---

## ⚙️ Passo 3: Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de homologação
cp .env.homologacao .env

# Editar e ajustar senhas (IMPORTANTE!)
vim .env
```

**⚠️ Senhas a Configurar:**

| Serviço | Variável | Senha Sugerida |
|---------|----------|----------------|
| PostgreSQL | `POSTGRES_PASSWORD` | `IntelliCare@Homolog2026!Pg` |
| Redis | `REDIS_PASSWORD` | `IntelliCare@Homolog2026!Redis` |
| Grafana | `GRAFANA_ADMIN_PASSWORD` | `IntelliCare@Homolog2026!Grafana` |
| Rocket.Chat Admin | `ROCKETCHAT_ADMIN_PASSWORD` | `IntelliCare@Homolog2026!RocketChat` |
| Rocket.Chat Bot | `ROCKETCHAT_BOT_PASSWORD` | `IntelliCare@Homolog2026!Bot` |
| Jitsi | `JITSI_APP_SECRET` | `IntelliCare@Homolog2026!Jitsi` |

---

## 🐳 Passo 4: Subir Infraestrutura

### 4.1. Subir PostgreSQL e Redis

```bash
cd /opt/intellicare/intellicare

# Subir apenas infraestrutura
docker-compose -f docker-compose.full.yml up -d postgres redis

# Aguardar 30 segundos para inicialização
sleep 30

# Verificar logs
docker-compose -f docker-compose.full.yml logs postgres
docker-compose -f docker-compose.full.yml logs redis

# Verificar se estão rodando
docker-compose -f docker-compose.full.yml ps
```

### 4.2. Criar Schemas no PostgreSQL

```bash
# Conectar ao PostgreSQL
docker exec -it modularizacao-postgres-1 psql -U intellicare_admin -d intellicare_db

# Executar dentro do psql:
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;

-- Verificar schemas criados
\dn

-- Sair
\q
```

---

## 🚀 Passo 5: Subir Serviços Backend

```bash
cd /opt/intellicare/intellicare

# Subir todos os backends
docker-compose -f docker-compose.full.yml up -d \
  florence \
  oswaldo \
  donabedian \
  wanda \
  comunicacao \
  geralda

# Aguardar 60 segundos para inicialização
sleep 60

# Verificar logs
docker-compose -f docker-compose.full.yml logs -f --tail=50
```

---

## 🌐 Passo 6: Subir Frontend

```bash
cd /opt/intellicare/intellicare

# Subir portal
docker-compose -f docker-compose.full.yml up -d portal

# Verificar logs
docker-compose -f docker-compose.full.yml logs -f portal
```

---

## 📊 Passo 7: Subir Monitoring (Opcional)

```bash
cd /opt/intellicare/intellicare

# Subir Prometheus e Grafana
docker-compose -f docker-compose.full.yml up -d prometheus grafana

# Verificar
docker-compose -f docker-compose.full.yml ps
```

---

## ✅ Passo 8: Validar Deploy

### 8.1. Smoke Tests

```bash
cd /opt/intellicare/intellicare

# Executar smoke tests
chmod +x scripts/smoke_tests.sh
./scripts/smoke_tests.sh
```

### 8.2. Testes Manuais

```bash
# Testar Florence
curl http://167.86.97.142:8001/health
curl http://167.86.97.142:8001/api/v1/florence/info

# Testar Oswaldo
curl http://167.86.97.142:8002/health
curl http://167.86.97.142:8002/api/v1/oswaldo/info

# Testar Donabedian
curl http://167.86.97.142:8003/health

# Testar Wanda
curl http://167.86.97.142:8004/health

# Testar Comunicacao
curl http://167.86.97.142:8005/health

# Testar Geralda
curl http://167.86.97.142:8006/health

# Testar Portal (Frontend)
curl http://167.86.97.142:3001
```

### 8.3. Acessar via Browser

Abra no navegador:

- **Portal Frontend:** http://167.86.97.142:3001
- **Florence API Docs:** http://167.86.97.142:8001/docs
- **Oswaldo API Docs:** http://167.86.97.142:8002/docs
- **Donabedian API Docs:** http://167.86.97.142:8003/docs
- **Wanda API Docs:** http://167.86.97.142:8004/docs
- **Comunicacao API Docs:** http://167.86.97.142:8005/docs
- **Geralda API Docs:** http://167.86.97.142:8006/docs
- **Grafana:** http://167.86.97.142:3000 (admin / senha configurada)
- **Prometheus:** http://167.86.97.142:9090

---

## 🔄 Comandos Úteis

### Ver Status dos Containers

```bash
cd /opt/intellicare/intellicare
docker-compose -f docker-compose.full.yml ps
```

### Ver Logs

```bash
# Todos os serviços
docker-compose -f docker-compose.full.yml logs -f

# Serviço específico
docker-compose -f docker-compose.full.yml logs -f florence
docker-compose -f docker-compose.full.yml logs -f wanda
docker-compose -f docker-compose.full.yml logs -f portal
```

### Reiniciar Serviço

```bash
# Reiniciar um serviço
docker-compose -f docker-compose.full.yml restart florence

# Reiniciar todos
docker-compose -f docker-compose.full.yml restart
```

### Parar Tudo

```bash
docker-compose -f docker-compose.full.yml down
```

### Parar e Remover Volumes (CUIDADO!)

```bash
docker-compose -f docker-compose.full.yml down -v
```

### Atualizar Código

```bash
cd /opt/intellicare/intellicare

# Fazer backup do .env
cp .env .env.backup

# Atualizar código
git pull origin main

# Restaurar .env se necessário
cp .env.backup .env

# Rebuild e restart
docker-compose -f docker-compose.full.yml up -d --build
```

---

## 🔒 Passo 9: Segurança (IMPORTANTE!)

### 9.1. Alterar Senha Root

```bash
# Alterar senha root
passwd root
```

### 9.2. Criar Usuário Não-Root

```bash
# Criar usuário
adduser intellicare

# Adicionar ao grupo sudo
usermod -aG sudo intellicare

# Adicionar ao grupo docker
usermod -aG docker intellicare

# Testar
su - intellicare
docker ps
exit
```

### 9.3. Configurar SSH com Chave

```bash
# No seu computador local, gerar chave SSH (se não tiver)
ssh-keygen -t ed25519 -C "intellicare@homolog"

# Copiar chave pública para o servidor
ssh-copy-id root@167.86.97.142

# Testar conexão sem senha
ssh root@167.86.97.142
```

### 9.4. Desabilitar Login Root via Senha (Opcional)

```bash
# Editar configuração SSH
vim /etc/ssh/sshd_config

# Alterar:
# PermitRootLogin yes
# Para:
# PermitRootLogin prohibit-password

# Reiniciar SSH
systemctl restart sshd
```

### 9.5. Configurar Fail2Ban

```bash
# Instalar Fail2Ban
apt install -y fail2ban

# Criar configuração
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
EOF

# Iniciar Fail2Ban
systemctl enable fail2ban
systemctl start fail2ban

# Verificar status
fail2ban-client status sshd
```

---

## 📈 Passo 10: Monitoramento

### 10.1. Verificar Recursos do Servidor

```bash
# CPU e Memória
htop

# Disco
df -h

# Uso de disco por container
docker system df

# Estatísticas de containers
docker stats
```

### 10.2. Configurar Alertas no Grafana

1. Acesse: http://167.86.97.142:3000
2. Login: admin / senha configurada
3. Vá em: Alerting → Alert Rules
4. Configure alertas para:
   - CPU > 80%
   - Memória > 90%
   - Disco > 85%
   - Serviços down

---

## 🔧 Troubleshooting

### Problema: Container não inicia

```bash
# Ver logs detalhados
docker-compose -f docker-compose.full.yml logs florence

# Ver últimas 100 linhas
docker-compose -f docker-compose.full.yml logs --tail=100 florence

# Entrar no container
docker exec -it modularizacao-florence-1 /bin/bash
```

### Problema: Porta já em uso

```bash
# Verificar o que está usando a porta
netstat -tulpn | grep :8001

# Matar processo
kill -9 PID
```

### Problema: Sem espaço em disco

```bash
# Limpar containers parados
docker container prune -f

# Limpar imagens não usadas
docker image prune -a -f

# Limpar volumes não usados (CUIDADO!)
docker volume prune -f

# Limpar tudo (MUITO CUIDADO!)
docker system prune -a -f --volumes
```

### Problema: PostgreSQL não conecta

```bash
# Verificar se está rodando
docker-compose -f docker-compose.full.yml ps postgres

# Ver logs
docker-compose -f docker-compose.full.yml logs postgres

# Testar conexão
docker exec -it modularizacao-postgres-1 psql -U intellicare_admin -d intellicare_db -c "SELECT version();"
```

### Problema: Redis não conecta

```bash
# Verificar se está rodando
docker-compose -f docker-compose.full.yml ps redis

# Testar conexão
docker exec -it modularizacao-redis-1 redis-cli ping
# Deve retornar: PONG

# Se tiver senha
docker exec -it modularizacao-redis-1 redis-cli -a "IntelliCare@Homolog2026!Redis" ping
```

---

## 📝 Backup e Restore

### Backup do Banco de Dados

```bash
# Criar diretório de backups
mkdir -p /opt/intellicare/backups

# Backup completo
docker exec modularizacao-postgres-1 pg_dump -U intellicare_admin intellicare_db > /opt/intellicare/backups/intellicare_$(date +%Y%m%d_%H%M%S).sql

# Backup compactado
docker exec modularizacao-postgres-1 pg_dump -U intellicare_admin intellicare_db | gzip > /opt/intellicare/backups/intellicare_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore do Banco de Dados

```bash
# Restore de backup
docker exec -i modularizacao-postgres-1 psql -U intellicare_admin intellicare_db < /opt/intellicare/backups/intellicare_20260221_120000.sql

# Restore de backup compactado
gunzip < /opt/intellicare/backups/intellicare_20260221_120000.sql.gz | docker exec -i modularizacao-postgres-1 psql -U intellicare_admin intellicare_db
```

### Backup Automático (Cron)

```bash
# Criar script de backup
cat > /opt/intellicare/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/intellicare/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

# Criar backup
docker exec modularizacao-postgres-1 pg_dump -U intellicare_admin intellicare_db | gzip > ${BACKUP_DIR}/intellicare_${DATE}.sql.gz

# Remover backups antigos
find ${BACKUP_DIR} -name "intellicare_*.sql.gz" -mtime +${KEEP_DAYS} -delete

echo "Backup completed: intellicare_${DATE}.sql.gz"
EOF

# Dar permissão
chmod +x /opt/intellicare/backup.sh

# Adicionar ao cron (todo dia às 3h da manhã)
crontab -e
# Adicionar linha:
# 0 3 * * * /opt/intellicare/backup.sh >> /var/log/intellicare_backup.log 2>&1
```

---

## 🌐 Configurar Domínio (Opcional)

Se você tiver um domínio (ex: homolog.intellicare.com.br):

### 1. Configurar DNS

No seu provedor de DNS, adicione:

```
A    homolog.intellicare.com.br    167.86.97.142
A    *.homolog.intellicare.com.br  167.86.97.142
```

### 2. Instalar Nginx

```bash
apt install -y nginx

# Criar configuração
cat > /etc/nginx/sites-available/intellicare <<'EOF'
server {
    listen 80;
    server_name homolog.intellicare.com.br;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Ativar site
ln -s /etc/nginx/sites-available/intellicare /etc/nginx/sites-enabled/

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
```

### 3. Configurar HTTPS com Let's Encrypt

```bash
# Instalar Certbot
apt install -y certbot python3-certbot-nginx

# Obter certificado
certbot --nginx -d homolog.intellicare.com.br

# Renovação automática já está configurada
certbot renew --dry-run
```

---

## 📞 Suporte

### Informações de Contato

- **Ambiente:** Homologação
- **Servidor:** 167.86.97.142
- **GitHub:** https://github.com/eduardo/intellicare
- **Documentação:** `/opt/intellicare/intellicare/docs/`

### Logs Importantes

```bash
# Logs do sistema
/var/log/syslog
/var/log/auth.log

# Logs Docker
docker-compose -f docker-compose.full.yml logs

# Logs Nginx (se configurado)
/var/log/nginx/access.log
/var/log/nginx/error.log
```

---

## ✅ Checklist de Deploy

- [ ] Servidor atualizado (`apt update && apt upgrade`)
- [ ] Docker instalado e funcionando
- [ ] Docker Compose instalado
- [ ] Firewall configurado (UFW)
- [ ] Repositório clonado
- [ ] Arquivo `.env` configurado com senhas fortes
- [ ] PostgreSQL rodando e schemas criados
- [ ] Redis rodando
- [ ] Todos os 6 backends rodando (Florence, Oswaldo, Donabedian, Wanda, Comunicacao, Geralda)
- [ ] Frontend (Portal) rodando
- [ ] Smoke tests passando
- [ ] Endpoints acessíveis via browser
- [ ] Senha root alterada
- [ ] SSH configurado com chave
- [ ] Fail2Ban instalado e configurado
- [ ] Backup automático configurado
- [ ] Monitoramento (Grafana/Prometheus) configurado
- [ ] Documentação revisada

---

**🎉 Servidor de Homologação Configurado com Sucesso!**


