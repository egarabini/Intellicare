# Guia de Execução Remota — Servidor de Homologação

**Data:** 2026-02-22  
**Servidor:** 167.86.97.142 (Contabo VPS)  
**Objetivo:** Executar Fases A, B, C remotamente via SSH  
**Tempo estimado:** ~2 horas

---

## 📋 Pré-requisitos

- ✅ Acesso SSH ao servidor (root@167.86.97.142)
- ✅ Senha: Soeuso419863
- ✅ Repositório público: https://github.com/eduardo/intellicare
- ✅ Script preparado: `scripts/setup_servidor_homologacao.sh`

---

## 🚀 Método 1: Execução Automática (RECOMENDADO)

### Passo 1: Conectar ao servidor

```bash
ssh root@167.86.97.142
# Senha: Soeuso419863
```

### Passo 2: Baixar e executar o script

```bash
# Baixar o script diretamente do repositório
curl -fsSL https://raw.githubusercontent.com/eduardo/intellicare/main/MODULARIZACAO/scripts/setup_servidor_homologacao.sh -o setup.sh

# Dar permissão de execução
chmod +x setup.sh

# Executar o script
./setup.sh
```

**O script executará automaticamente:**
- ✅ Fase A: Preparação (Docker, firewall, ferramentas)
- ✅ Fase B: Clone do repositório e configuração .env
- ✅ Fase C: Infraestrutura (PostgreSQL, Redis, schemas)

**Tempo estimado:** ~15-20 minutos

---

## 🔧 Método 2: Execução Manual (Passo a Passo)

Se preferir executar manualmente ou se o script automático falhar:

### FASE A - Preparação do Servidor

```bash
# Conectar ao servidor
ssh root@167.86.97.142

# A1. Atualizar sistema
apt update && apt upgrade -y
apt install -y curl wget git vim htop net-tools ufw

# A2. Configurar firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3001/tcp
ufw allow 8001:8006/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw --force enable
ufw status

# A3. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version

# A4. Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### FASE B - Clone e Configuração

```bash
# B1. Criar diretório e clonar repositório
mkdir -p /opt/intellicare
cd /opt/intellicare
git clone https://github.com/eduardo/intellicare.git

# B2. Navegar para MODULARIZACAO
cd intellicare/MODULARIZACAO
ls -la

# B3. Configurar .env
cp .env.homologacao .env
head -n 10 .env
```

### FASE C - Infraestrutura

```bash
# C1. Subir Postgres e Redis
cd /opt/intellicare/intellicare/MODULARIZACAO
docker-compose -f docker-compose.full.yml up -d postgres redis

# C2. Aguardar e validar
sleep 30
docker-compose -f docker-compose.full.yml ps
docker-compose -f docker-compose.full.yml logs postgres
docker-compose -f docker-compose.full.yml logs redis

# C3. Criar schemas
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
\dn
EOF
```

---

## ✅ Validação

### Verificar containers rodando

```bash
cd /opt/intellicare/intellicare/MODULARIZACAO
docker-compose -f docker-compose.full.yml ps
```

**Esperado:**
```
NAME                STATUS
postgres            Up (healthy)
redis               Up (healthy)
```

### Verificar schemas criados

```bash
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c "\dn"
```

**Esperado:**
```
intellicare_florence
intellicare_oswaldo
intellicare_donabedian
intellicare_wanda
intellicare_comunicacao
intellicare_geralda
```

### Verificar firewall

```bash
ufw status
```

**Esperado:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
3001/tcp                   ALLOW       Anywhere
8001:8006/tcp              ALLOW       Anywhere
3000/tcp                   ALLOW       Anywhere
9090/tcp                   ALLOW       Anywhere
```

---

## 📊 Checklist de Conclusão

- [ ] Fase A concluída (Docker, firewall, ferramentas)
- [ ] Fase B concluída (repositório clonado, .env configurado)
- [ ] Fase C concluída (PostgreSQL e Redis rodando)
- [ ] Schemas criados no banco
- [ ] Firewall configurado
- [ ] Containers healthy

---

## 🐛 Troubleshooting

### Erro: "Permission denied (publickey)"

```bash
# Verificar se SSH está aceitando senha
ssh -o PreferredAuthentications=password root@167.86.97.142
```

### Erro: "docker-compose: command not found"

```bash
# Verificar instalação
ls -la /usr/local/bin/docker-compose

# Reinstalar se necessário
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### Erro: "Cannot connect to Docker daemon"

```bash
# Iniciar Docker
systemctl start docker
systemctl enable docker
```

### Containers não ficam healthy

```bash
# Ver logs detalhados
docker-compose -f docker-compose.full.yml logs postgres
docker-compose -f docker-compose.full.yml logs redis

# Reiniciar containers
docker-compose -f docker-compose.full.yml restart postgres redis
```

---

## 📝 Próximos Passos

Após conclusão das Fases A, B, C:

1. ✅ Criar relatório de execução
2. ⏳ Aguardar conclusão da estabilização (Fase 1)
3. ⏳ Executar Fase D (Deploy completo)
4. ⏳ Executar Fase E (Pós-configuração)

---

## 📞 Referências

- **Plano completo:** `20260221-1000_PLANO_IMPLEMENTACAO_CONFIGURACAO_SERVIDOR.md`
- **Documentação servidor:** `docs/SERVIDORES/SERVIDOR_HOMOLOGACAO_CONTABO.md`
- **Script automático:** `scripts/setup_servidor_homologacao.sh`

