# 🚀 Servidor de Homologação - Quick Start

## 📋 Informações Rápidas

| Item | Valor |
|------|-------|
| **IP** | `167.86.97.142` |
| **User** | `root` |
| **Password** | `Soeuso419863` |
| **GitHub** | `https://github.com/eduardo/intellicare` |
| **Recursos** | 12 vCPU, 48 GB RAM, 250 GB NVMe |

---

## 🔥 Deploy Rápido (5 Minutos)

### 1. Conectar ao Servidor

```bash
ssh root@167.86.97.142
```

### 2. Instalar Dependências (Primeira Vez)

```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Instalar Git
apt install -y git
```

### 3. Clonar Repositório

```bash
mkdir -p /opt/intellicare
cd /opt/intellicare
git clone https://github.com/eduardo/intellicare.git
cd intellicare
```

### 4. Configurar Ambiente

```bash
# Copiar arquivo de configuração
cp .env.homologacao .env

# (Opcional) Editar senhas
vim .env
```

### 5. Deploy Automático

```bash
# Dar permissão ao script
chmod +x scripts/deploy_homologacao.sh

# Executar deploy
./scripts/deploy_homologacao.sh
```

**Pronto! 🎉**

---

## 🌐 Acessar Serviços

Após o deploy, acesse:

- **Portal:** http://167.86.97.142:3001
- **Florence API:** http://167.86.97.142:8001/docs
- **Oswaldo API:** http://167.86.97.142:8002/docs
- **Donabedian API:** http://167.86.97.142:8003/docs
- **Wanda API:** http://167.86.97.142:8004/docs
- **Comunicacao API:** http://167.86.97.142:8005/docs
- **Geralda API:** http://167.86.97.142:8006/docs
- **Grafana:** http://167.86.97.142:3000
- **Prometheus:** http://167.86.97.142:9090

---

## 🔧 Comandos Úteis

```bash
# Ver status
cd /opt/intellicare/intellicare
docker-compose -f docker-compose.full.yml ps

# Ver logs
docker-compose -f docker-compose.full.yml logs -f

# Reiniciar tudo
docker-compose -f docker-compose.full.yml restart

# Parar tudo
docker-compose -f docker-compose.full.yml down

# Atualizar código
git pull origin main
./scripts/deploy_homologacao.sh
```

---

## 📚 Documentação Completa

Ver: `docs/SERVIDOR_HOMOLOGACAO_CONTABO.md`

---

## 🆘 Problemas?

### Container não inicia

```bash
docker-compose -f docker-compose.full.yml logs NOME_DO_SERVICO
```

### Porta em uso

```bash
netstat -tulpn | grep :PORTA
```

### Limpar tudo e recomeçar

```bash
docker-compose -f docker-compose.full.yml down -v
./scripts/deploy_homologacao.sh
```

---

## ✅ Checklist Pós-Deploy

- [ ] Todos os containers rodando (`docker-compose ps`)
- [ ] Portal acessível (http://167.86.97.142:3001)
- [ ] APIs respondendo (/health endpoints)
- [ ] Smoke tests passando
- [ ] Senha root alterada
- [ ] Firewall configurado
- [ ] Backup automático configurado

---

**Servidor:** Contabo VPS 40 NVMe  
**Ambiente:** Homologação  
**Custo:** USD 20.80/mês

