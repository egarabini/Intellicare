# 🐧 GUIA DE INSTALAÇÃO - SERVIDOR LINUX REMOTO

---

## 📋 PRÉ-REQUISITOS

- Servidor Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- Acesso SSH (root ou sudo)
- 4GB RAM mínimo
- 20GB espaço em disco
- Portas abertas: 22 (SSH), 3000 (Rocket.Chat), 8443 (Jitsi), 10000/UDP (Jitsi)

---

## 🚀 PASSO 1: CONECTAR AO SERVIDOR

### **Via SSH**:

```bash
# Conectar ao servidor
ssh usuario@IP_DO_SERVIDOR

# Ou com porta customizada
ssh -p PORTA usuario@IP_DO_SERVIDOR

# Ou com chave privada
ssh -i /caminho/para/chave.pem usuario@IP_DO_SERVIDOR
```

---

## 🐳 PASSO 2: INSTALAR DOCKER

### **Ubuntu/Debian**:

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Remover versões antigas do Docker (se existirem)
sudo apt remove docker docker-engine docker.io containerd runc

# Instalar dependências
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Adicionar chave GPG oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Verificar instalação
sudo docker --version
sudo docker run hello-world
```

### **CentOS/Rocky Linux**:

```bash
# Atualizar sistema
sudo yum update -y

# Instalar dependências
sudo yum install -y yum-utils

# Adicionar repositório Docker
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verificar instalação
sudo docker --version
```

---

## 📦 PASSO 3: INSTALAR DOCKER COMPOSE

### **Método 1: Via apt (Ubuntu 22.04+)**:

```bash
sudo apt install -y docker-compose-plugin

# Verificar
docker compose version
```

### **Método 2: Download direto (qualquer distro)**:

```bash
# Baixar última versão
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permissão de execução
sudo chmod +x /usr/local/bin/docker-compose

# Criar link simbólico (opcional)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verificar
docker-compose --version
```

---

## 👤 PASSO 4: CONFIGURAR USUÁRIO (OPCIONAL)

```bash
# Adicionar usuário ao grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Aplicar mudanças (relogar ou executar)
newgrp docker

# Testar sem sudo
docker ps
```

---

## 📁 PASSO 5: TRANSFERIR ARQUIVOS

### **Opção A: Via SCP (do seu computador)**:

```bash
# Transferir pasta completa
scp -r ./intellicare-comunicacao usuario@IP_SERVIDOR:/home/usuario/

# Ou com porta customizada
scp -P PORTA -r ./intellicare-comunicacao usuario@IP_SERVIDOR:/home/usuario/
```

### **Opção B: Via Git (no servidor)**:

```bash
# Instalar git
sudo apt install -y git  # Ubuntu/Debian
sudo yum install -y git  # CentOS/Rocky

# Clonar repositório
cd /home/usuario
git clone URL_DO_REPOSITORIO
cd INTELLICARE/intellicare-comunicacao
```

### **Opção C: Criar manualmente (no servidor)**:

```bash
# Criar diretório
mkdir -p /home/usuario/intellicare-comunicacao
cd /home/usuario/intellicare-comunicacao

# Criar docker-compose.yml
nano docker-compose.yml
# (Colar conteúdo e salvar com Ctrl+X, Y, Enter)

# Criar .env
nano .env
# (Colar conteúdo e salvar)
```

---

## 🔧 PASSO 6: CONFIGURAR VARIÁVEIS DE AMBIENTE

```bash
cd /home/usuario/intellicare-comunicacao

# Copiar exemplo
cp .env.example .env

# Editar variáveis
nano .env

# IMPORTANTE: Alterar senhas em produção!
# - MONGO_PASSWORD
# - ROCKETCHAT_ADMIN_PASSWORD
# - JICOFO_COMPONENT_SECRET
# - JVB_AUTH_PASSWORD
# - JICOFO_AUTH_PASSWORD
```

---

## 🔥 PASSO 7: CONFIGURAR FIREWALL

### **UFW (Ubuntu/Debian)**:

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir Rocket.Chat
sudo ufw allow 3000/tcp

# Permitir Jitsi
sudo ufw allow 8443/tcp
sudo ufw allow 10000/udp

# Verificar regras
sudo ufw status
```

### **Firewalld (CentOS/Rocky)**:

```bash
# Permitir portas
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --permanent --add-port=10000/udp

# Recarregar
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-all
```

---

## 🚀 PASSO 8: INICIAR SERVIÇOS

```bash
cd /home/usuario/intellicare-comunicacao

# Iniciar containers
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f

# Ver logs de serviço específico
docker-compose logs -f rocketchat
```

---

## ✅ PASSO 9: VERIFICAR INSTALAÇÃO

```bash
# Verificar containers rodando
docker ps

# Verificar logs
docker-compose logs rocketchat | tail -50

# Testar acesso local
curl http://localhost:3000/api/info

# Verificar MongoDB
docker exec comunicacao-mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 🌐 PASSO 10: ACESSAR REMOTAMENTE

### **Via IP Público**:

```
http://IP_DO_SERVIDOR:3000  (Rocket.Chat)
http://IP_DO_SERVIDOR:8443  (Jitsi)
```

### **Via Domínio (com Traefik/Nginx)**:

Configurar reverse proxy (próximo passo se necessário)

---

## 🛠️ TROUBLESHOOTING

### **Erro: "Cannot connect to Docker daemon"**

```bash
# Verificar se Docker está rodando
sudo systemctl status docker

# Iniciar Docker
sudo systemctl start docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### **Erro: "port is already allocated"**

```bash
# Verificar portas em uso
sudo netstat -tulpn | grep :3000

# Parar processo usando a porta
sudo kill -9 PID

# Ou alterar porta no docker-compose.yml
```

### **Erro: MongoDB replica set**

```bash
# Verificar logs MongoDB
docker-compose logs mongodb

# Reiniciar MongoDB
docker-compose restart mongodb mongodb-init-replica

# Verificar replica set
docker exec comunicacao-mongodb mongosh --eval "rs.status()"
```

### **Containers não iniciam**

```bash
# Ver logs detalhados
docker-compose logs

# Verificar recursos
free -h
df -h

# Limpar containers antigos
docker system prune -a
```

---

## 📊 COMANDOS ÚTEIS

```bash
# Parar todos os containers
docker-compose down

# Parar e remover volumes (CUIDADO: perde dados!)
docker-compose down -v

# Reiniciar serviço específico
docker-compose restart rocketchat

# Ver uso de recursos
docker stats

# Ver logs em tempo real
docker-compose logs -f --tail=100

# Executar comando em container
docker exec -it comunicacao-rocketchat bash
```

---

## 🔒 SEGURANÇA (PRODUÇÃO)

```bash
# 1. Alterar TODAS as senhas no .env
# 2. Configurar SSL/TLS (Traefik ou Nginx)
# 3. Configurar backup automático
# 4. Limitar acesso SSH (chave apenas)
# 5. Configurar fail2ban
# 6. Atualizar sistema regularmente
```

---

## 📞 PRÓXIMOS PASSOS

1. ✅ Docker instalado
2. ✅ Containers rodando
3. ⏳ Configurar SSL/TLS
4. ⏳ Configurar backup
5. ⏳ Integrar Keycloak SSO
6. ⏳ Configurar monitoramento

---

**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0

