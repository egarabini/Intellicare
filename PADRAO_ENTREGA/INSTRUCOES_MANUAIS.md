# INSTRUÇÕES MANUAIS - EXECUÇÃO NO SERVIDOR
**Para quando você preferir executar manualmente ao invés do script automatizado**

---

## MÉTODO 1: Script Automatizado (RECOMENDADO)

### Passo 1: Copiar script para o servidor
```bash
# No seu Windows (PowerShell)
scp C:\DOCSHARE\INTELLICARE\PADRAO_ENTREGA\EXECUCAO_SERVIDOR_COMPLETA.sh root@167.86.97.142:/root/
```

### Passo 2: Executar no servidor
```bash
# SSH no servidor
ssh root@167.86.97.142

# Ir para o diretório e executar
cd /root
chmod +x EXECUCAO_SERVIDOR_COMPLETA.sh
bash -x EXECUCAO_SERVIDOR_COMPLETA.sh
```

O script irá:
- ✅ Fazer backup de segurança
- ✅ Rotacionar todas as 8 credenciais
- ✅ Atualizar arquivos de configuração
- ✅ Verificar revogação
- ✅ Deploy do Admin
- ✅ Health check e smoke test
- ✅ Teste de rollback controlado

---

## MÉTODO 2: Execução Passo a Passo Manual

### PASSO 1: SSH no Servidor
```bash
ssh root@167.86.97.142
# Senha: Soeuso410863
```

### PASSO 2: Fazer Backup
```bash
# Criar diretório de backup
mkdir -p /opt/intellicare/backups/manual_$(date +%Y%m%d_%H%M%S)

# Backup do .env
cp /opt/intellicare/.env /opt/intellicare/backups/manual_$(date +%Y%m%d_%H%M%S)/.env.backup
```

### PASSO 3: Rotacionar PostgreSQL
```bash
# Gerar nova senha
NEW_PG_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Nova senha PostgreSQL: $NEW_PG_PASS"

# Aplicar no PostgreSQL
docker exec -i intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db <<SQL
ALTER USER intellicare_admin WITH PASSWORD '$NEW_PG_PASS';
SELECT 'Password changed' as result;
SQL

# Atualizar .env
cd /opt/intellicare
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PG_PASS/" .env
sed -i "s/IntelliCare@Homolog2026!Pg/$NEW_PG_PASS/g" .env
```

### PASSO 4: Rotacionar Redis
```bash
# Gerar nova senha
NEW_REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Nova senha Redis: $NEW_REDIS_PASS"

# Aplicar no Redis
docker exec -i intellicare-redis-1 redis-cli <<EOF
AUTH IntelliCare@Homolog2026!Redis
CONFIG SET requirepass $NEW_REDIS_PASS
AUTH $NEW_REDIS_PASS
PING
EOF

# Atualizar .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$NEW_REDIS_PASS/" .env
sed -i "s/REDIS_URL=.*/REDIS_URL=redis:\/\/:$NEW_REDIS_PASS@redis:6379/" .env
sed -i "s/IntelliCare@Homolog2026!Redis/$NEW_REDIS_PASS/g" .env
```

### PASSO 5: Rotacionar Grafana
```bash
# Gerar nova senha
NEW_GRAFANA_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Nova senha Grafana: $NEW_GRAFANA_PASS"

# Aplicar no Grafana
docker exec -i intellicare-grafana-1 grafana-cli admin reset-admin-password "$NEW_GRAFANA_PASS"

# Atualizar .env
sed -i "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=$NEW_GRAFANA_PASS/" .env
```

### PASSO 6: Rotacionar Rocket.Chat (SE EM USO)
```bash
# Gerar novas senhas
NEW_RC_ADMIN_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
NEW_RC_BOT_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Nova senha RC Admin: $NEW_RC_ADMIN_PASS"
echo "Nova senha RC Bot: $NEW_RC_BOT_PASS"

# Gerar hashes bcrypt
RC_ADMIN_HASH=$(htpasswd -bnBC 10 "" "$NEW_RC_ADMIN_PASS" | tr -d ':\n')
RC_BOT_HASH=$(htpasswd -bnBC 10 "" "$NEW_RC_BOT_PASS" | tr -d ':\n')

# Aplicar no MongoDB
docker exec -i intellicare-mongo-1 mongosh rocketchat <<MONGO
db.users.updateOne(
  { username: "admin" },
  { \$set: { "services.password.bcrypt": "$RC_ADMIN_HASH" } }
);
db.users.updateOne(
  { username: "intellicare" },
  { \$set: { "services.password.bcrypt": "$RC_BOT_HASH" } }
);
MONGO

# Atualizar .env
sed -i "s/ROCKETCHAT_ADMIN_PASSWORD=.*/ROCKETCHAT_ADMIN_PASSWORD=$NEW_RC_ADMIN_PASS/" .env
sed -i "s/ROCKETCHAT_BOT_PASSWORD=.*/ROCKETCHAT_BOT_PASSWORD=$NEW_RC_BOT_PASS/" .env
```

### PASSO 7: Verificar Revogação
```bash
# Testar PostgreSQL com senha antiga (DEVE FALHAR)
docker exec -i intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db -h postgres -c "SELECT 'OLD_PASSWORD_TEST' as test;" 2>&1 | grep "FATAL" && echo "✓ Senha antiga PostgreSQL revogada" || echo "✗ Senha antiga ainda funciona!"

# Testar PostgreSQL com nova senha (DEVE FUNCIONAR)
docker exec -i intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db -h postgres -c "SELECT 'NEW_PASSWORD_WORKS' as test;" 2>&1 | grep "NEW_PASSWORD_WORKS" && echo "✓ Nova senha PostgreSQL funciona" || echo "✗ Nova senha NÃO funciona!"
```

### PASSO 8: Deploy do Admin
```bash
cd /opt/intellicare

# Atualizar Git
git fetch --all
git checkout chore/v1-close-staging-standard
git pull origin chore/v1-close-staging-standard --ff-only

# Recriar container Admin
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Aguardar e verificar
sleep 15
docker compose --env-file .env.full -f docker-compose.full.yml ps admin
curl http://localhost:8010/api/v1/health
```

### PASSO 9: Teste de Rollback (Opcional)
```bash
# Criar commit de teste
cd /opt/intellicare
echo "# BUG TEST" >> README.md
git add README.md
git commit -m "test: bug"
git push origin chore/v1-close-staging-standard

# Deploy do bug
git pull --ff-only
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Rollback
git reset --hard HEAD~1
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Verificar
sleep 15
curl http://localhost:8010/api/v1/health
```

---

## MÉTODO 3: PowerShell (Direto do Windows)

Se você tiver o OpenSSH configurado no Windows:

```powershell
# No PowerShell Windows
$SERVER = "167.86.97.142"
$USER = "root"
$PASSWORD = "Soeuso410863"

# Usar plink (PuTTY) ou sshpass
# Ou executar comandos individualmente:

ssh root@$SERVER "cd /opt/intellicare && git fetch --all && git checkout chore/v1-close-staging-standard && git pull --ff-only && docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin && sleep 15 && curl http://localhost:8010/api/v1/health"
```

---

## SOLUÇÃO DE PROBLEMAS

### Problema: "Permission denied"
- Verificar senha: `Soeuso410863`
- Tentar sem chave: `ssh -o PreferredAuthentications=password root@167.86.97.142`

### Problema: "Container not found"
- Verificar nome do container: `docker ps -a`
- Usar nome correto no comando

### Problema: "Health check falha"
- Verificar logs: `docker logs <container>`
- Verificar se porta está correta: `netstat -tlnp | grep 8010`

### Problema: "Git permission denied"
- Verificar configuração do Git: `git remote -v`
- Usar SSH key ou token de acesso

---

## CONFIRMAÇÃO FINAL

Após executar, confirme:

```bash
# Verificar containers rodando
docker compose --env-file .env.full -f docker-compose.full.yml ps

# Verificar health Admin
curl http://localhost:8010/api/v1/health

# Verificar logs sem erros
docker compose --env-file .env.full -f docker-compose.full.yml logs --tail 20 admin
```

Se tudo estiver verde:
```
✓ V1 ENCERRADA OFICIALMENTE
✓ V2 INICIADA OFICIALMENTE
✓ Credenciais rotacionadas
✓ Deploy piloto funcionando
✓ Rollback testado
```
