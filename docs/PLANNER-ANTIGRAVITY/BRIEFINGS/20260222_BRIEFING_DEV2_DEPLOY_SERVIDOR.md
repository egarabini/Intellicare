# 📋 BRIEFING DEV2 — Deploy no Servidor (T1-F1 + T1-F3 + T3-F1)

**Data:** 2026-02-22  
**Prazo estimado:** 30 minutos  
**Prioridade:** 🔴 Alta  
**Servidor:** `167.86.97.142` (Contabo VPS)

---

## 🎯 Objetivo

Executar no servidor os scripts que já foram criados:
1. **Security hardening** (UFW, Fail2Ban, kernel)
2. **Traefik** (reverse proxy com SSL)
3. **Verificação** dos módulos

> [!IMPORTANT]
> **TODOS os scripts já estão prontos localmente.** Não precisa escrever nenhum código — só executar.

---

## OPÇÃO A: Script PowerShell (mais fácil)

Abra um terminal PowerShell no Windows e rode:

```powershell
cd C:\DOCSHARE\INTELLICARE
.\scripts\deploy_security_traefik.ps1
```

O script vai:
1. Pedir senha SSH para cada comando (sempre a mesma: a senha de root)
2. Fazer upload de 13 arquivos via SCP
3. Perguntar se quer rodar o hardening (responder `y`)
4. Perguntar se quer subir o Traefik (responder `y`)
5. Rodar verificação final

---

## OPÇÃO B: Passo a passo manual (se preferir)

### Passo 1 — Conectar ao servidor

```bash
ssh root@167.86.97.142
```

### Passo 2 — Upload dos arquivos (de outro terminal)

```powershell
# Do Windows, enviar todos os arquivos:
$s = "root@167.86.97.142"
$r = "/opt/intellicare/intellicare"

# Criar diretórios
ssh $s "mkdir -p $r/scripts/security $r/scripts/dns $r/traefik/dynamic"

# Security scripts
scp scripts\security\harden_server.sh ${s}:${r}/scripts/security/
scp scripts\security\backup.sh ${s}:${r}/scripts/security/
scp scripts\security\restore.sh ${s}:${r}/scripts/security/
scp scripts\security\verify_backup.sh ${s}:${r}/scripts/security/

# DNS scripts
scp scripts\dns\DNS_SETUP_GUIDE.sh ${s}:${r}/scripts/dns/
scp scripts\dns\verify_certs.sh ${s}:${r}/scripts/dns/

# Traefik config
scp traefik\traefik.yml ${s}:${r}/traefik/
scp traefik\dynamic\middlewares.yml ${s}:${r}/traefik/dynamic/
scp traefik\dynamic\routes-intellicare.yml ${s}:${r}/traefik/dynamic/
scp traefik\dynamic\routes-saudeconectada.yml ${s}:${r}/traefik/dynamic/

# Docker compose overlays
scp docker-compose.traefik.yml ${s}:${r}/
scp docker-compose.traefik-dev.yml ${s}:${r}/
scp .env.traefik.template ${s}:${r}/

# Smoke test
scp scripts\smoke_test.sh ${s}:${r}/scripts/
```

### Passo 3 — No servidor (via SSH), executar hardening

```bash
cd /opt/intellicare/intellicare

# Tornar executável
chmod +x scripts/security/*.sh scripts/dns/*.sh scripts/*.sh

# Executar hardening
bash scripts/security/harden_server.sh
```

> [!CAUTION]
> O script vai desabilitar login por senha SSH! Se quiser manter a senha, **editar o script** e comentar a seção "4 — SSH HARDENING" antes de rodar. Ou usar a Opção A (PowerShell) que já pula essa parte.

### Passo 4 — Subir Traefik

```bash
cd /opt/intellicare/intellicare

# Copiar template do .env
cp .env.traefik.template .env.traefik

# Subir Traefik
docker-compose -f docker-compose.full.yml -f docker-compose.traefik.yml up -d traefik

# Verificar
docker ps --filter name=traefik
docker logs intellicare-traefik --tail=20
```

### Passo 5 — Verificar tudo

```bash
# Status dos containers
docker-compose -f docker-compose.full.yml ps

# Smoke test dos módulos
bash scripts/smoke_test.sh

# Firewall
ufw status

# Fail2Ban
fail2ban-client status sshd
```

---

## 📁 Arquivos que já existem (não precisa criar nada)

| Arquivo | O que faz |
|---|---|
| `scripts/deploy_security_traefik.ps1` | Script PS1 que faz TUDO (Opção A) |
| `scripts/security/harden_server.sh` | UFW + Fail2Ban + SSH + sysctl |
| `scripts/security/backup.sh` | Backup PostgreSQL + volumes + configs |
| `scripts/security/restore.sh` | Restore completo |
| `scripts/security/verify_backup.sh` | Verificação de integridade |
| `scripts/dns/DNS_SETUP_GUIDE.sh` | Guia DNS + Cloudflare |
| `scripts/dns/verify_certs.sh` | Verifica DNS + certs |
| `traefik/traefik.yml` | Config estática Traefik |
| `traefik/dynamic/middlewares.yml` | Security headers, CORS, rate-limit |
| `traefik/dynamic/routes-intellicare.yml` | Rotas *.intellicare.ia.br |
| `traefik/dynamic/routes-saudeconectada.yml` | Rotas *.saudeconectada.com.br |
| `docker-compose.traefik.yml` | Overlay prod |
| `docker-compose.traefik-dev.yml` | Overlay dev |
| `.env.traefik.template` | Template de variáveis |

---

## 🏁 Critério de Conclusão

1. ✅ `ufw status` mostra: 22 (rate-limited), 80, 443 (allow)
2. ✅ `fail2ban-client status sshd` mostra jail ativo
3. ✅ `docker ps --filter name=traefik` mostra container running
4. ✅ `bash scripts/smoke_test.sh` → 0 falhas
5. ✅ Cron de backup configurado: `cat /etc/cron.d/intellicare-backup`
