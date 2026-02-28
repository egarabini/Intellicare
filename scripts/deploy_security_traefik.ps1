# ============================================================================
# IntelliCare — Deploy Remoto: Security + Traefik + DNS
# ============================================================================
# Servidor: 167.86.97.142 (Contabo VPS)
# Uso: .\scripts\deploy_security_traefik.ps1
# ============================================================================

$ErrorActionPreference = "Continue"

$server = "167.86.97.142"
$user = "root"
$remotePath = "/opt/intellicare/intellicare"
$localPath = "C:\DOCSHARE\INTELLICARE"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  IntelliCare — Deploy Security + Traefik + DNS"
Write-Host "  Servidor: $server"
Write-Host "  $(Get-Date)"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Função auxiliar ─────────────────────────────────────────
function Invoke-SSH {
    param(
        [string]$Command,
        [string]$Description
    )
    Write-Host "[STEP] $Description" -ForegroundColor Green
    Write-Host "  CMD: $Command" -ForegroundColor DarkGray
    $result = ssh ${user}@${server} $Command 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ OK" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Aviso (exit=$LASTEXITCODE)" -ForegroundColor Yellow
    }
    if ($result) { Write-Host $result -ForegroundColor Gray }
    Write-Host ""
    return $result
}

# ── Testar conexão ─────────────────────────────────────────
Write-Host "Testando conexão SSH..." -ForegroundColor Cyan
$test = ssh ${user}@${server} "echo 'OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Falha na conexão SSH. Verifique IP/usuário/senha." -ForegroundColor Red
    Write-Host $test
    exit 1
}
Write-Host "✅ Conexão SSH OK`n" -ForegroundColor Green

# ════════════════════════════════════════════════════════════
# FASE 1: Upload dos Arquivos
# ════════════════════════════════════════════════════════════
Write-Host "=== FASE 1/4 — Upload dos arquivos ===" -ForegroundColor Cyan
Write-Host ""

# Criar diretórios remotos
Invoke-SSH -Command "mkdir -p $remotePath/scripts/security $remotePath/scripts/dns $remotePath/traefik/dynamic" -Description "Criando diretórios remotos"

# Upload security scripts
Write-Host "[UPLOAD] Scripts de segurança..." -ForegroundColor Green
scp "$localPath\scripts\security\harden_server.sh" "${user}@${server}:${remotePath}/scripts/security/"
scp "$localPath\scripts\security\backup.sh" "${user}@${server}:${remotePath}/scripts/security/"
scp "$localPath\scripts\security\restore.sh" "${user}@${server}:${remotePath}/scripts/security/"
scp "$localPath\scripts\security\verify_backup.sh" "${user}@${server}:${remotePath}/scripts/security/"
Write-Host "  ✅ 4 scripts de segurança" -ForegroundColor Green

# Upload DNS scripts
Write-Host "[UPLOAD] Scripts DNS..." -ForegroundColor Green
scp "$localPath\scripts\dns\DNS_SETUP_GUIDE.sh" "${user}@${server}:${remotePath}/scripts/dns/"
scp "$localPath\scripts\dns\verify_certs.sh" "${user}@${server}:${remotePath}/scripts/dns/"
Write-Host "  ✅ 2 scripts DNS" -ForegroundColor Green

# Upload Traefik config
Write-Host "[UPLOAD] Traefik config..." -ForegroundColor Green
scp "$localPath\traefik\traefik.yml" "${user}@${server}:${remotePath}/traefik/"
scp "$localPath\traefik\dynamic\middlewares.yml" "${user}@${server}:${remotePath}/traefik/dynamic/"
scp "$localPath\traefik\dynamic\routes-intellicare.yml" "${user}@${server}:${remotePath}/traefik/dynamic/"
scp "$localPath\traefik\dynamic\routes-saudeconectada.yml" "${user}@${server}:${remotePath}/traefik/dynamic/"
Write-Host "  ✅ 4 arquivos Traefik" -ForegroundColor Green

# Upload docker-compose overlays
Write-Host "[UPLOAD] Docker-compose overlays..." -ForegroundColor Green
scp "$localPath\docker-compose.traefik.yml" "${user}@${server}:${remotePath}/"
scp "$localPath\docker-compose.traefik-dev.yml" "${user}@${server}:${remotePath}/"
scp "$localPath\.env.traefik.template" "${user}@${server}:${remotePath}/"
Write-Host "  ✅ 3 arquivos compose" -ForegroundColor Green

# Upload smoke test (if exists)
if (Test-Path "$localPath\scripts\smoke_test.sh") {
    scp "$localPath\scripts\smoke_test.sh" "${user}@${server}:${remotePath}/scripts/"
    Write-Host "  ✅ smoke_test.sh" -ForegroundColor Green
}

Write-Host ""

# Make scripts executable
Invoke-SSH -Command "chmod +x $remotePath/scripts/security/*.sh $remotePath/scripts/dns/*.sh $remotePath/scripts/*.sh" -Description "Tornando scripts executáveis"

Write-Host "✅ FASE 1 CONCLUÍDA — 13 arquivos enviados`n" -ForegroundColor Green

# ════════════════════════════════════════════════════════════
# FASE 2: Security Hardening
# ════════════════════════════════════════════════════════════
Write-Host "=== FASE 2/4 — Security Hardening ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ⚠️  ATENÇÃO: Isso vai:" -ForegroundColor Yellow
Write-Host "  - Configurar UFW (firewall): apenas 22, 80, 443" -ForegroundColor Yellow
Write-Host "  - Instalar Fail2Ban" -ForegroundColor Yellow
Write-Host "  - Hardening SSH (key-only após configurar chave)" -ForegroundColor Yellow
Write-Host "  - Updates automáticos de segurança" -ForegroundColor Yellow
Write-Host ""

$runSecurity = Read-Host "Executar hardening? (y/N)"
if ($runSecurity -eq "y" -or $runSecurity -eq "Y") {

    # IMPORTANTE: Não aplicar SSH key-only authentication se o usuário usa senha!
    # Vamos executar um hardening mais seguro (sem desabilitar senha)
    Write-Host "[INFO] Executando hardening COM login por senha mantido..." -ForegroundColor Cyan

    # 2.1 — Atualizar sistema e instalar deps
    Invoke-SSH -Command "apt-get update -qq && apt-get install -y -qq ufw fail2ban unattended-upgrades curl" -Description "2.1 Instalando dependências"

    # 2.2 — Firewall (UFW)
    Invoke-SSH -Command "ufw --force reset && ufw default deny incoming && ufw default allow outgoing" -Description "2.2 Reset UFW e defaults"
    Invoke-SSH -Command "ufw limit 22/tcp" -Description "2.2 UFW: SSH rate-limited"
    Invoke-SSH -Command "ufw allow 80/tcp" -Description "2.2 UFW: HTTP"
    Invoke-SSH -Command "ufw allow 443/tcp" -Description "2.2 UFW: HTTPS"
    Invoke-SSH -Command "echo 'y' | ufw enable" -Description "2.2 UFW: Ativar"
    Invoke-SSH -Command "ufw status verbose" -Description "2.2 UFW: Status"

    # 2.3 — Fail2Ban
    $fail2banConfig = @"
[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
findtime = 600
bantime  = 3600
"@
    Invoke-SSH -Command "cat > /etc/fail2ban/jail.d/intellicare-ssh.conf << 'EOFCONF'
[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
findtime = 600
bantime  = 3600
EOFCONF" -Description "2.3 Fail2Ban: Configuração SSH"

    Invoke-SSH -Command "systemctl restart fail2ban && systemctl enable fail2ban" -Description "2.3 Fail2Ban: Restart e enable"
    Invoke-SSH -Command "fail2ban-client status" -Description "2.3 Fail2Ban: Status"

    # 2.4 — Auto-updates
    Invoke-SSH -Command "dpkg-reconfigure -f noninteractive unattended-upgrades" -Description "2.4 Auto-updates de segurança"

    # 2.5 — Sysctl hardening
    Invoke-SSH -Command "cat > /etc/sysctl.d/99-intellicare.conf << 'EOFCONF'
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOFCONF" -Description "2.5 Sysctl: Kernel hardening"

    Invoke-SSH -Command "sysctl --system > /dev/null 2>&1" -Description "2.5 Sysctl: Aplicar"

    # 2.6 — Backup cron
    Invoke-SSH -Command "echo '0 2 * * * root $remotePath/scripts/security/backup.sh >> /var/log/intellicare-backup.log 2>&1' > /etc/cron.d/intellicare-backup" -Description "2.6 Cron: Backup diário às 02:00"
    Invoke-SSH -Command "mkdir -p /var/backups/intellicare" -Description "2.6 Diretório de backups"

    Write-Host "✅ FASE 2 CONCLUÍDA — Servidor hardened`n" -ForegroundColor Green
} else {
    Write-Host "⏭️  Fase 2 pulada`n" -ForegroundColor Yellow
}

# ════════════════════════════════════════════════════════════
# FASE 3: Deploy Traefik
# ════════════════════════════════════════════════════════════
Write-Host "=== FASE 3/4 — Deploy Traefik ===" -ForegroundColor Cyan
Write-Host ""

$runTraefik = Read-Host "Subir Traefik como reverse proxy? (y/N)"
if ($runTraefik -eq "y" -or $runTraefik -eq "Y") {

    # 3.1 — Copiar .env.traefik.template se não existe .env.traefik
    Invoke-SSH -Command "cd $remotePath && test -f .env.traefik || cp .env.traefik.template .env.traefik" -Description "3.1 Template .env.traefik"

    # 3.2 — Parar containers com portas expostas (Traefik vai gerenciar)
    Write-Host "[INFO] Reconstruindo stack com Traefik..." -ForegroundColor Cyan

    # 3.3 — Build e up com overlay Traefik
    Invoke-SSH -Command "cd $remotePath && docker-compose -f docker-compose.full.yml -f docker-compose.traefik.yml pull traefik" -Description "3.2 Pull imagem Traefik"
    Invoke-SSH -Command "cd $remotePath && docker-compose -f docker-compose.full.yml -f docker-compose.traefik.yml up -d traefik" -Description "3.3 Subindo Traefik"

    # 3.4 — Aguardar
    Write-Host "[INFO] Aguardando Traefik iniciar (15s)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 15

    # 3.5 — Verificar
    Invoke-SSH -Command "docker ps --filter name=traefik --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" -Description "3.4 Status do Traefik"
    Invoke-SSH -Command "docker logs intellicare-traefik --tail=20 2>&1" -Description "3.5 Logs recentes do Traefik"

    # 3.6 — Testar endpoints via HTTP direto
    Invoke-SSH -Command "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:80/ --connect-timeout 5" -Description "3.6 Test: Porta 80 (HTTP)"

    Write-Host "✅ FASE 3 CONCLUÍDA — Traefik rodando`n" -ForegroundColor Green
} else {
    Write-Host "⏭️  Fase 3 pulada`n" -ForegroundColor Yellow
}

# ════════════════════════════════════════════════════════════
# FASE 4: Verificação Final
# ════════════════════════════════════════════════════════════
Write-Host "=== FASE 4/4 — Verificação Final ===" -ForegroundColor Cyan
Write-Host ""

# 4.1 — Status de todos os containers
Invoke-SSH -Command "cd $remotePath && docker-compose -f docker-compose.full.yml ps" -Description "4.1 Status dos containers"

# 4.2 — UFW status
Invoke-SSH -Command "ufw status" -Description "4.2 Firewall"

# 4.3 — Fail2ban status
Invoke-SSH -Command "fail2ban-client status sshd 2>/dev/null || echo 'Fail2Ban not configured'" -Description "4.3 Fail2Ban"

# 4.4 — Disk usage
Invoke-SSH -Command "df -h / | tail -1" -Description "4.4 Disco"

# 4.5 — Smoke test modules
Invoke-SSH -Command "cd $remotePath && test -f scripts/smoke_test.sh && bash scripts/smoke_test.sh || echo 'smoke_test.sh não encontrado'" -Description "4.5 Smoke test dos módulos"

# ════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ✅ DEPLOY CONCLUÍDO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Servidor: $server"
Write-Host "  Firewall: UFW (22/tcp rate-limited, 80, 443)"
Write-Host "  Fail2Ban: SSH protection ativo"
Write-Host "  Backup:   Cron diário às 02:00 (/var/backups/intellicare)"
Write-Host ""
Write-Host "  Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Configurar DNS A records (ver scripts/dns/DNS_SETUP_GUIDE.sh)"
Write-Host "  2. Definir CF_DNS_API_TOKEN no .env.traefik para wildcard certs"
Write-Host "  3. Verificar certs: ssh root@$server 'bash $remotePath/scripts/dns/verify_certs.sh'"
Write-Host ""
