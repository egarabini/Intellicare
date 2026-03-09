# Plano de Execução — Configuração do Servidor de Homologação

**Data:** 2026-02-20  
**Fase:** 1 (Estabilização) — deploy depende da conclusão desta fase  
**Servidor:** 167.86.97.142 (Contabo VPS)  
**Objetivo:** Configurar servidor para deploy do IntelliCare v1.0.0

---

## 1. Visão Geral

| Fase | Descrição | Pode executar agora? |
|------|-----------|----------------------|
| **A** | Preparação do servidor (Docker, firewall, SSH) | ✅ Sim |
| **B** | Clone do repositório e configuração .env | ✅ Sim |
| **C** | Subir infraestrutura (Postgres, Redis) | ✅ Sim |
| **D** | Deploy completo (backends + portal) | ⚠️ Após Fase 1 concluída |
| **E** | Pós-configuração (backup, segurança) | Após deploy OK |

---

## 2. Pré-requisitos

- [ ] Acesso SSH ao servidor (root ou usuário com sudo)
- [ ] Repositório `eduardo/intellicare` acessível (público ou com credenciais)
- [ ] Dev1 próximo ou concluindo Fase 1 (para Fase D)

---

## 3. Fase A — Preparação (≈ 75 min)

### A1. Conectar e atualizar sistema
```bash
ssh root@167.86.97.142
apt update && apt upgrade -y
apt install -y curl wget git vim htop net-tools ufw
```

### A2. Configurar firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3001/tcp
ufw allow 8001:8006/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
ufw --force enable
ufw status
```

### A3. Instalar Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version
```

### A4. Instalar Docker Compose
```bash
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### A5. Segurança (IMPORTANTE)
```bash
# Alterar senha root
passwd root

# Configurar SSH com chave (no seu computador local)
# ssh-keygen -t ed25519 -C "intellicare@homolog"
# ssh-copy-id root@167.86.97.142
```

**⚠️ Remover senha do arquivo `docs/SERVIDORES/HOMOLOGACAO/README.md`**

---

## 4. Fase B — Clone e configuração (≈ 25 min)

### B1. Clonar repositório
```bash
mkdir -p /opt/intellicare
cd /opt/intellicare
git clone https://github.com/eduardo/intellicare.git
```

### B2. Navegar para .
```bash
# Verificar estrutura do repositório
ls -la intellicare/

# Caminho esperado (ajustar conforme estrutura real):
cd intellicare
# OU
cd intellicare/
```

### B3. Configurar .env
```bash
cp .env.homologacao .env
# Revisar senhas: vim .env
```

---

## 5. Fase C — Infraestrutura (≈ 15 min)

### C1. Subir Postgres e Redis
```bash
cd /opt/intellicare/intellicare  # ou path correto
docker-compose -f docker-compose.full.yml up -d postgres redis
```

### C2. Aguardar e validar
```bash
sleep 30
docker-compose -f docker-compose.full.yml ps
docker-compose -f docker-compose.full.yml logs postgres
docker-compose -f docker-compose.full.yml logs redis
```

### C3. Criar schemas
```bash
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
EOF
```

---

## 6. Fase D — Deploy completo (≈ 60 min)

**Executar quando Fase 1 estiver concluída.**

### D1. Script de deploy
O `deploy_homologacao.sh` já está corrigido para chamar `smoke_tests.py`.
Se necessário, validar: `scripts/deploy_homologacao.sh` usa `python scripts/smoke_tests.py --url http://167.86.97.142`.

### D2. Executar deploy
```bash
cd /opt/intellicare/intellicare
chmod +x scripts/deploy_homologacao.sh
./scripts/deploy_homologacao.sh
```

### D3. Validar
```bash
docker-compose -f docker-compose.full.yml ps
python scripts/smoke_tests.py --url http://167.86.97.142
```

### D4. Acessar via browser
- Portal: http://167.86.97.142:3001
- Florence: http://167.86.97.142:8001/docs
- Oswaldo: http://167.86.97.142:8002/docs
- (demais: 8003, 8004, 8005, 8006)

---

## 7. Fase E — Pós-configuração

### E1. Backup automático
```bash
mkdir -p /opt/intellicare/backups
# Criar script backup.sh (ver docs/SERVIDORES/HOMOLOGACAO/configuracao/CONFIGURACAO_CONTABO.md)
crontab -e
# 0 3 * * * /opt/intellicare/backup.sh
```

### E2. Fail2Ban (opcional)
```bash
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 8. Ordem de execução recomendada

```
Hoje (sem depender de Fase 1):
  A1 → A2 → A3 → A4 → A5 → B1 → B2 → B3 → C1 → C2 → C3

Quando dev1 concluir Fase 1:
  D1 (validar script) → D2 → D3 → D4

Após deploy OK:
  E1 → E2
```

---

## 9. Referências

- `docs/SERVIDORES/HOMOLOGACAO/configuracao/CONFIGURACAO_CONTABO.md` — guia completo
- `docs/SERVIDORES/HOMOLOGACAO/README.md` — quick start
- `docs/SERVIDORES/HOMOLOGACAO/implementacao/Inicializacao/Fase1_Preparacao_Sistema/20260221-1000_PLANO_IMPLEMENTACAO_CONFIGURACAO_SERVIDOR.md` — plano para o DEV
- `docs/PLANNER-CURSOR/VERIFICACAO_SERVIDOR_HOMOLOGACAO.md` — checklist e gaps
