# FASE 4 - INCIDENTE DE SEGURANÇA: CREDENCIAIS EXPOSTAS
**Data:** 2026-02-27
**Severidade:** CRÍTICA
**Status:** EM TRATAMENTO

## Resumo do Incidente

O arquivo `.env.homologacao` foi commitado no repositório Git contendo **credenciais reais** em texto plano. Este arquivo está versionado e suas credenciais fazem parte do histórico do Git, representando um vazamento de segurança.

## Credenciais Expostas

| Serviço | Variável | Valor Exposto | Tipo | Risco |
|---------|----------|---------------|------|-------|
| PostgreSQL | `POSTGRES_PASSWORD` | `IntelliCare@Homolog2026!Pg` | Banco de dados | ALTO - Acesso completo ao DB |
| Redis | `REDIS_PASSWORD` | `IntelliCare@Homolog2026!Redis` | Cache | ALTO - Dados em cache sensíveis |
| Grafana | `GRAFANA_ADMIN_PASSWORD` | `IntelliCare@Homolog2026!Grafana` | Monitoring | MÉDIO - Dashboards/métricas |
| Rocket.Chat Admin | `ROCKETCHAT_ADMIN_PASSWORD` | `IntelliCare@Homolog2026!RocketChat` | Comunicação | ALTO - Acesso administrativo |
| Rocket.Chat Bot | `ROCKETCHAT_BOT_PASSWORD` | `IntelliCare@Homolog2026!Bot` | Automação | MÉDIO - Credenciais de bot |
| Jitsi | `JITSI_APP_SECRET` | `IntelliCare@Homolog2026!Jitsi` | Videoconferência | MÉDIO - Chave de app |
| Flowise | `FLOWISE_PASSWORD` | `IntelliCare@Homolog2026!Flowise` | AI Workflows | BAIXO - Acesso Flowise |
| Keycloak | `KEYCLOAK_CLIENT_SECRET` | `IntelliCare@Homolog2026!Keycloak` | Identidade | BAIXO - Ainda não em uso |

## Plano de Remediação Imediata

### Passo 1: Rotação de Credenciais (Servidor Contabo)

Execute os seguintes comandos no servidor `167.86.97.142`:

#### 1.1 PostgreSQL
```bash
# Acessar container
docker exec -it intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db

# Alterar senha do usuário
ALTER USER intellicare_admin WITH PASSWORD 'NOVA_SENHA_FORTE_AQUI';
\q
```

#### 1.2 Redis
```bash
# Editar configuration
docker exec -it intellicare-redis-1 redis-cli
CONFIG SET requirepass 'NOVA_SENHA_FORTE_AQUI'
AUTH 'NOVA_SENHA_FORTE_AQUI'
exit
```

**Nota:** Para persistir, atualizar `docker-compose.full.yml` ou `.env.staging`.

#### 1.3 Grafana
```bash
# Acessar container
docker exec -it intellicare-grafana-1 grafana-cli admin reset-admin-password NOVA_SENHA_FORTE_AQUI
```

#### 1.4 Rocket.Chat
```bash
# Acessar container
docker exec -it intellicare-rocketchat-1 bash

# Entrar no mongo do Rocket.Chat
meteor mongo

# No mongo shell
use rocketchat
db.users.update({username: "admin"}, {$set: { "services.password.bcrypt": "$2a$10$NOVO_HASH_AQUI" }})
db.users.update({username: "intellicare"}, {$set: { "services.password.bcrypt": "$2a$10$NOVO_HASH_AQUI" }})
exit
```

**Nota:** Gerar novos hashes bcrypt com `htpasswd -bnBC 10 "" NOVA_SENHA | tr -d ':\n'`

#### 1.5 Jitsi
```bash
# Gerar nova secret app
docker exec -it intellicare-jitsi-prosody-1 bash

# Editar configuração prosody
echo 'app_secret="NOVA_SECRETA_AQUI"' >> /etc/prosody/conf.d/intellicare_staging.cfg.lua
```

#### 1.6 Flowise
```bash
# Acessar container
docker exec -it intellicare-flowise-1 bash

# Variável de ambiente está no docker-compose
# Alterar .env.staging e recriar container
```

### Passo 2: Atualizar Arquivo de Configuração

```bash
# No servidor
cd /opt/intellicare

# Criar novo .env.staging com as NOVAS senhas
cp .env.staging .env.staging.old
nano .env.staging  # Inserir novas senhas

# Copiar para .env ativo
cp .env.staging .env

# Recriar serviços afetados
docker compose --env-file .env.full -f docker-compose.full.yml up -d postgres redis grafana rocketchat
```

### Passo 3: Verificação de Revogação

```bash
# Testar que senhas ANTIGAS não funcionam mais

# PostgreSQL (deve falhar)
docker exec -it intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db -h localhost -c "SELECT 1"
# Use senha antiga: IntelliCare@Homolog2026!Pg
# Esperado: FATAL: password authentication failed

# Redis (deve falhar)
docker exec -it intellicare-redis-1 redis-cli -a IntelliCare@Homolog2026!Redis PING
# Esperado: NOAUTH Authentication required

# Grafana (deve falhar)
curl -u admin:IntelliCare@Homolog2026!Grafana http://localhost:3000/api/health
# Esperado: 401 Unauthorized
```

### Passo 4: Limpeza do Histórico Git

**AVANÇADO:** Para remover completamente as credenciais do histórico Git:

```bash
# Usar BFG Repo-Cleaner ou git filter-branch
# ⚠️ ATENÇÃO: Isso reescreve o histórico Git

# Opção 1: BFG (mais rápido)
bfg --replace-text passwords.txt  # passwords.txt contém as senhas expostas
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Opção 2: git filter-branch (manual)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env.homologacao" \
  --prune-empty --tag-name-filter cat -- --all

# Push forçado (⚠️ cuidado com branches compartilhados)
git push origin --force --all
git push origin --force --tags
```

### Passo 5: Invalidar Sessões Ativas

```bash
# Reiniciar serviços para derrubar conexões existentes
docker compose --env-file .env.full -f docker-compose.full.yml restart postgres redis rocketchat grafana

# Verificar não há sessões ativas com credenciais antigas
docker exec -it intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db -c "SELECT * FROM pg_stat_activity WHERE usename='intellicare_admin';"
```

## Checklist de Remediação

- [ ] **Backup pré-remediação:** Snapshot do servidor antes de mudanças
- [ ] **Rotação PostgreSQL:** Nova senha gerada e testada
- [ ] **Rotação Redis:** Nova senha gerada e testada
- [ ] **Rotação Grafana:** Nova senha gerada e testada
- [ ] **Rotação Rocket.Chat:** Novas senhas admin e bot geradas
- [ ] **Rotação Jitsi:** Nova app secret gerada
- [ ] **Rotação Flowise:** Nova senha gerada
- [ ] **Rotação Keycloak:** Nova secret gerada (se em uso)
- [ ] **Atualização .env.staging:** Novas credenciais inseridas
- [ ] **Recriação de containers:** Serviços reiniciados com novas credenciais
- [ ] **Teste de revogação:** Senhas antigas confirmadas como inválidas
- [ ] **Limpeza .env.homologacao:** Substituído por placeholders no Git
- [ ] **Limpeza histórico Git (opcional):** Credenciais removidas do histórico
- [ ] **Registro no diário:** Incidente documentado
- [ ] **Comunicação:** Time informado sobre mudança de credenciais

## Medidas de Prevenção Futura

1. **Pre-commit hooks:** Bloquear commits de arquivos `.env` com credenciais reais
2. **git-secrets:** Instalar e configurar para detectar padrões de senha
3. **Secret management:** Usar cofre de segredos (HashiCorp Vault, AWS Secrets Manager)
4. **Educação:** Treinar time sobre não versionar credenciais

```bash
# Exemplo de pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
if git diff --cached --name-only | grep -E '\.env$'; then
  echo "ERROR: Attempting to commit .env file with credentials!"
  echo "Use .env.example or .env.staging with placeholders only."
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## Registro de Evidências

| Ação | Responsável | Data/Hora | Evidência |
|------|-------------|-----------|-----------|
| Identificação do vazamento | DEV0 | 2026-02-27 | Relatório FASE1 |
| Rotação PostgreSQL | - | - | - |
| Rotação Redis | - | - | - |
| Rotação Grafana | - | - | - |
| Rotação Rocket.Chat | - | - | - |
| Verificação de revogação | - | - | - |
| Limpeza Git | - | - | - |

## Contato em Caso de Emergência

- **Security Lead:** [PREENCHER]
- **Platform Owner:** [PREENCHER]
- **On-Call:** [PREENCHER]

---

**Documento criado:** 2026-02-27
**Status:** Aguardando execução da rotação de credenciais
**Próxima revisão:** Após conclusão da rotação
