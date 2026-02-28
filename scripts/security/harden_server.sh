#!/usr/bin/env bash
# ============================================================================
# IntelliCare — Server Security Hardening Script
# ============================================================================
# Run: sudo bash scripts/security/harden_server.sh
# Designed for Ubuntu 22.04/24.04 LTS
# ============================================================================
set -euo pipefail

LOG_FILE="/var/log/intellicare-hardening.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"; }
warn() { echo "[$TIMESTAMP] ⚠️  $1" | tee -a "$LOG_FILE"; }
ok() { echo "[$TIMESTAMP] ✅ $1" | tee -a "$LOG_FILE"; }

# ── Check root ──────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Execute como root: sudo bash $0"
    exit 1
fi

echo "============================================================"
echo "  IntelliCare — Server Security Hardening"
echo "  $(date)"
echo "============================================================"

# ════════════════════════════════════════════════════════════
# 1. SYSTEM UPDATES
# ════════════════════════════════════════════════════════════
log "1/6 — Atualizando sistema..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq ufw fail2ban unattended-upgrades logwatch curl
ok "Sistema atualizado"

# ════════════════════════════════════════════════════════════
# 2. UFW FIREWALL
# ════════════════════════════════════════════════════════════
log "2/6 — Configurando firewall (UFW)..."

# Reset rules
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH (rate limited)
ufw limit 22/tcp comment "SSH rate-limited"

# HTTP/HTTPS (Traefik)
ufw allow 80/tcp comment "HTTP (Traefik redirect)"
ufw allow 443/tcp comment "HTTPS (Traefik)"

# Traefik Dashboard (apenas localhost ou rede interna)
# ufw allow from 10.0.0.0/8 to any port 8080 comment "Traefik Dashboard (interno)"

# Docker internal — NÃO abrir portas de módulos (8001-8011)
# Traefik roteia internamente via Docker network

# Enable
ufw --force enable
ok "Firewall configurado"

echo ""
echo "Regras UFW ativas:"
ufw status verbose
echo ""

# ════════════════════════════════════════════════════════════
# 3. FAIL2BAN
# ════════════════════════════════════════════════════════════
log "3/6 — Configurando Fail2Ban..."

# SSH jail configuration
cat > /etc/fail2ban/jail.d/intellicare-ssh.conf << 'EOF'
[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
findtime = 600
bantime  = 3600
action   = %(action_mwl)s

[sshd-ddos]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 10
findtime = 30
bantime  = 86400
EOF

# Traefik auth failure jail (optional — for future)
cat > /etc/fail2ban/jail.d/intellicare-traefik.conf << 'EOF'
[traefik-auth]
enabled  = false
port     = http,https
filter   = traefik-auth
logpath  = /var/log/traefik/access.log
maxretry = 10
findtime = 300
bantime  = 3600
EOF

# Traefik filter (for when enabled)
cat > /etc/fail2ban/filter.d/traefik-auth.conf << 'EOF'
[Definition]
failregex = ^.*"clientAddr":"<HOST>:\d+".*"DownstreamStatus":401.*$
            ^.*"clientAddr":"<HOST>:\d+".*"DownstreamStatus":403.*$
ignoreregex =
EOF

systemctl restart fail2ban
systemctl enable fail2ban
ok "Fail2Ban configurado e ativo"

# ════════════════════════════════════════════════════════════
# 4. SSH HARDENING
# ════════════════════════════════════════════════════════════
log "4/6 — Hardening SSH..."

SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_BACKUP="/etc/ssh/sshd_config.backup.$(date +%Y%m%d)"

# Backup original
cp "$SSHD_CONFIG" "$SSHD_BACKUP"
ok "Backup do sshd_config em $SSHD_BACKUP"

# Create hardened drop-in config
cat > /etc/ssh/sshd_config.d/99-intellicare-hardening.conf << 'EOF'
# IntelliCare SSH Hardening
# Generated: auto

# Disable root login
PermitRootLogin prohibit-password

# Disable password auth (key-based only)
PasswordAuthentication no
ChallengeResponseAuthentication no

# Limit login attempts
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 30

# Disable empty passwords
PermitEmptyPasswords no

# Disable X11 forwarding
X11Forwarding no

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2

# Protocol
Protocol 2

# Logging
LogLevel VERBOSE
EOF

# Validate config before restarting
if sshd -t; then
    systemctl restart sshd
    ok "SSH hardened (key-only, root prohibited)"
else
    warn "Erro na config SSH — restaurando backup"
    cp "$SSHD_BACKUP" "$SSHD_CONFIG"
    rm -f /etc/ssh/sshd_config.d/99-intellicare-hardening.conf
fi

# ════════════════════════════════════════════════════════════
# 5. AUTOMATIC SECURITY UPDATES
# ════════════════════════════════════════════════════════════
log "5/6 — Configurando updates automáticos de segurança..."

cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "admin@intellicare.ia.br";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

systemctl enable unattended-upgrades
ok "Updates automáticos de segurança ativados"

# ════════════════════════════════════════════════════════════
# 6. KERNEL / SYSCTL HARDENING
# ════════════════════════════════════════════════════════════
log "6/6 — Hardening do kernel..."

cat > /etc/sysctl.d/99-intellicare-hardening.conf << 'EOF'
# IntelliCare Kernel Hardening

# Disable IP forwarding (Docker manages its own)
# net.ipv4.ip_forward = 1  # Docker needs this enabled

# Protection against SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# Ignore ICMP redirect
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Ignore source-routed packets
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Log martian packets
net.ipv4.conf.all.log_martians = 1

# Prevent IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1

# File system hardening
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF

sysctl --system > /dev/null 2>&1
ok "Kernel hardened"

# ════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo "  ✅ Server hardening completo!"
echo "============================================================"
echo ""
echo "  UFW:          $(ufw status | head -1)"
echo "  Fail2Ban:     $(systemctl is-active fail2ban)"
echo "  SSH:          Key-only, root prohibited"
echo "  Auto-updates: $(systemctl is-enabled unattended-upgrades)"
echo "  Kernel:       Hardened (sysctl)"
echo ""
echo "  Log: $LOG_FILE"
echo ""
echo "  ⚠️  IMPORTANTE:"
echo "  1. Certifique-se de ter uma chave SSH configurada ANTES"
echo "     de desconectar (PasswordAuthentication = no)"
echo "  2. Teste conexão SSH em OUTRO terminal antes de sair"
echo "============================================================"
