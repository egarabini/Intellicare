# COMANDOS SSH PRONTOS - COPIAR E COLAR
**Sem necessidade de copiar arquivos para o servidor**

---

## PASSO 1: Conectar ao Servidor

```bash
ssh root@167.86.97.142
# Senha: Soeuso410863
```

---

## PASSO 2: Ir para o diretório do projeto

```bash
cd /opt/intellicare
```

---

## PASSO 3: Atualizar Git para o branch correto

```bash
git fetch --all
git checkout chore/v1-close-staging-standard
git pull origin chore/v1-close-staging-standard --ff-only
```

---

## PASSO 4: Fazer Deploy do Admin (Simplificado)

```bash
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin
```

---

## PASSO 5: Aguardar e Verificar Health

```bash
sleep 15
curl http://localhost:8010/api/v1/health
```

**Esperado:** `{"status": "healthy"...}`

---

## PASSO 6: Verificar Logs

```bash
docker compose --env-file .env.full -f docker-compose.full.yml logs --tail 30 admin
```

**Esperado:** Sem erros críticos

---

## OPÇÃO: Rotação de Credenciais (Se Necessário)

⚠️ **ATENÇÃO:** Só execute se quiser rotacionar as credenciais agora.

### Rotação Rápida (PostgreSQL + Redis)

```bash
# Gerar novas senhas
NEW_PG_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
NEW_REDIS_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)

# Mostrar senhas (salve estas!)
echo "POSTGRES_PASSWORD=$NEW_PG_PASS"
echo "REDIS_PASSWORD=$NEW_REDIS_PASS"

# Aplicar PostgreSQL
docker exec intellicare-postgres-1 psql -U intellicare_admin -d intellicare_db -c "ALTER USER intellicare_admin WITH PASSWORD '$NEW_PG_PASS';"

# Aplicar Redis
docker exec intellicare-redis-1 redis-cli -a "IntelliCare@Homolog2026!Redis" CONFIG SET requirepass "$NEW_REDIS_PASS"

# Atualizar .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PG_PASS/" .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$NEW_REDIS_PASS/" .env
sed -i "s/IntelliCare@Homolog2026!Pg/$NEW_PG_PASS/g" .env
sed -i "s/IntelliCare@Homolog2026!Redis/$NEW_REDIS_PASS/g" .env

# Recriar containers
docker compose --env-file .env.full -f docker-compose.full.yml up -d postgres redis admin

echo "✅ Credenciais rotacionadas!"
```

---

## TESTE DE ROLLBACK (Opcional)

```bash
# Criar commit de teste
echo "# TEST BUG" >> README.md
git add README.md
git commit -m "test: bug"
git push origin chore/v1-close-staging-standard

# Deploy do bug
git pull --ff-only
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Aguardar
sleep 10

# ROLLBACK
git reset --hard HEAD~1
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin

# Verificar
sleep 15
curl http://localhost:8010/api/v1/health
```

---

## CONFIRMAÇÃO FINAL

```bash
# Ver tudo rodando
docker compose --env-file .env.full -f docker-compose.full.yml ps

# Health check final
curl http://localhost:8010/api/v1/health
```

**Se tudo estiver verde:**
```
✓ V1 100% COMPLETA
✓ V2 OFICIALMENTE INICIADA
✓ Deploy Admin funcionando
✓ Health check OK
```

---

## SOLUÇÃO DE PROBLEMAS

### Health check falha?
```bash
# Ver logs
docker logs <container_id_admin>

# Ver se porta está livre
netstat -tlnp | grep 8010

# Recriar
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin
```

### Git permission denied?
```bash
# Verificar remote
git remote -v

# Se necessário, adicionar token ou usar SSH key
# Ou pular push do teste de rollback
```

### Container não sobe?
```bash
# Ver todos os containers
docker ps -a

# Ver logs específicos
docker compose --env-file .env.full -f docker-compose.full.yml logs admin
```

---

## RESUMO EXECUÇÃO MÍNIMA

**Se você quer apenas testar o deploy mais rápido:**

```bash
ssh root@167.86.97.142
cd /opt/intellicare
git checkout chore/v1-close-staging-standard
git pull --ff-only
docker compose --env-file .env.full -f docker-compose.full.yml up -d --force-recreate admin
sleep 15
curl http://localhost:8010/api/v1/health
docker compose --env-file .env.full -f docker-compose.full.yml ps admin
```

Isso é suficiente para validar o deploy!
