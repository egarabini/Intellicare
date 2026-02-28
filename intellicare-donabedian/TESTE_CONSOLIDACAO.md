# Guide de Teste - FASE 2.3: ConsolidationConsumer Integration

**Objetivo**: Validar o pipeline completo de consolidação:
- Criação de dados via API → Publicação em Redis Streams → Consolidação em analitico

---

## Pré-requisitos

### 1. Infraestrutura Pronta

```bash
# Verificar PostgreSQL
psql -U admin_intellicare -d IntellicareDB -c "SELECT version();"

# Verificar Redis
redis-cli ping
# Output: PONG

# Verificar Keycloak (do FASE 2.1)
curl -s http://keycloak.local:8080/auth/realms/bemcuidar | jq .
```

### 2. Migrations Aplicadas

```bash
cd src
alembic current

# Output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# 005_create_donabedian_schemas

# Se não estiver em 005, rodar:
alembic upgrade head
```

### 3. Variáveis de Ambiente

```bash
# Copiar do template
cp .env.example .env

# Verificar valores:
cat .env | grep -E "REDIS_URL|DATABASE_URL|KEYCLOAK"

# Esperado:
# REDIS_URL=redis://localhost:6379
# INTELLICARE_DATABASE_URL=postgresql+asyncpg://admin_intellicare:...
# KEYCLOAK_CLIENT_SECRET=DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs
```

---

## Teste 1: Consumer Setup e Health Check

### Objetivo
Verificar se o consumer consegue conectar em Redis e PostgreSQL.

### Passos

```bash
# Terminal 1: Iniciar o consumer
cd src
python -m donabedian.consolidation.worker

# Aguardar output esperado:
# 2025-XX-XX ... INFO - Redis URL: redis://localhost:6379
# 2025-XX-XX ... INFO - Database URL: postgresql+asyncpg://admin_intellicare:...
# 2025-XX-XX ... INFO - ✅ Consumer group 'donabedian-consolidation' created for intellicare:donabedian:pilar.create
# 2025-XX-XX ... INFO - ✅ Consumer group 'donabedian-consolidation' created for intellicare:donabedian:pilar.update
# 2025-XX-XX ... INFO - ✅ Consumer group 'donabedian-consolidation' created for intellicare:donabedian:pilar.delete
# 2025-XX-XX ... INFO - 🚀 Starting consolidation consumer...
```

### Validar

```bash
# Terminal 2: Verificar consumer group no Redis
redis-cli XINFO GROUPS intellicare:donabedian:pilar.create

# Output esperado:
# 1) "name"
# 2) "donabedian-consolidation"
# 3) "consumers"
# 4) 1
# 5) "pending"
# 6) 0
```

**Resultado**: ✅ Consumer está healthy se consumer group foi criado e mostra 1 consumidor

---

## Teste 2: Pilar CREATE Event

### Objetivo
Criar um Pilar via API, verificar evento em Redis, validar consolidação em analitico.

### Passos

#### Passo 1: Obter Token Keycloak

```bash
# Terminal 2
export TOKEN=$(curl -s -X POST http://keycloak.local:8080/auth/realms/bemcuidar/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=intellicare-donabedian&client_secret=DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs&grant_type=client_credentials" \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:50}..."
```

#### Passo 2: Criar Pilar via API

```bash
# Iniciar API em Terminal 3
cd src
python -m donabedian.api.main

# Depois em Terminal 2:
PILAR_ID=$(curl -s -X POST http://localhost:8000/pilar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Efficacy - TESTE 1",
    "descricao": "Treatment effectiveness test",
    "tipo": "OUTCOME",
    "ordem_exibicao": 1
  }' | jq -r '.id')

echo "Created Pilar: $PILAR_ID"
```

#### Passo 3: Verificar evento em Redis

```bash
# Terminal 2
redis-cli XREAD STREAMS intellicare:donabedian:pilar.create 0

# Output esperado:
# 1) "intellicare:donabedian:pilar.create"
# 2) 1) 1) "1234567890000-0"
#       2) 1) "entity_id"
#          2) "<PILAR_ID_AQUI>"
#          3) "operation"
#          4) "CREATE"
#          5) "data"
#          6) "{\"old_values\": null, \"new_values\": {...}}"
#          7) "timestamp"
#          8) "2025-01-15T10:30:45..."
```

#### Passo 4: Aguardar Consolidação

```bash
# Terminal 1 (consumer) - observar logs
# 2025-XX-XX ... INFO - 📝 Processing event: 1234567890000-0 from intellicare:donabedian:pilar.create
# 2025-XX-XX ... INFO - ✅ ACK: 1234567890000-0
```

#### Passo 5: Verificar em analitico

```bash
# Terminal 2
psql -U admin_intellicare -d IntellicareDB << EOF
SELECT id, nome, descricao, tipo, consolidation_source, consolidated_at
FROM donabedian.analitico.pilar
WHERE id = '$PILAR_ID';
EOF

# Output esperado:
#                   id                  |        nome        |           descricao            |  tipo  | consolidation_source |          consolidated_at
# 550e8400-e29b-41d4-a716-446655440000 | Efficacy - TESTE 1 | Treatment effectiveness test   | OUTCOME | pilar.CREATE         | 2025-01-15 10:30:45.123456+00
```

**Resultado**: ✅ Se vir a linha acima, teste passou

---

## Teste 3: Pilar UPDATE Event

### Objetivo
Atualizar um Pilar, verificar evento de UPDATE em Redis, validar mudança em analitico.

```bash
# Terminal 2: Obter token (se expirou)
export TOKEN=$(curl -s -X POST http://keycloak.local:8080/auth/realms/bemcuidar/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=intellicare-donabedian&client_secret=DKFaLrOoVrmUzsRFN6941x2LVyzjv4Cs&grant_type=client_credentials" \
  | jq -r '.access_token')

# Atualizar o Pilar criado
curl -s -X PUT http://localhost:8000/pilar/$PILAR_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Efficacy - UPDATEDO",
    "descricao": "Updated description test",
    "tipo": "PROCESS",
    "ordem_exibicao": 2
  }' | jq

# Verificar evento de UPDATE em Redis
redis-cli XREAD STREAMS intellicare:donabedian:pilar.update 0

# Aguardar processamento (Terminal 1 - consumer logs)

# Verificar em analitico
psql -U admin_intellicare -d IntellicareDB << EOF
SELECT id, nome, tipo, consolidation_source, consolidated_at
FROM donabedian.analitico.pilar
WHERE id = '$PILAR_ID';
EOF

# Output esperado:
# consolidation_source = pilar.UPDATE
# nome = Efficacy - UPDATEDO
# tipo = PROCESS
```

**Resultado**: ✅ Se consolidation_source = pilar.UPDATE e dados foram atualizados

---

## Teste 4: Pilar DELETE Event

### Objetivo
Deletar um Pilar, verificar soft delete em analitico (valid_to setado).

```bash
# Terminal 2: Deletar Pilar
curl -s -X DELETE http://localhost:8000/pilar/$PILAR_ID \
  -H "Authorization: Bearer $TOKEN" | jq

# Verificar evento de DELETE em Redis
redis-cli XREAD STREAMS intellicare:donabedian:pilar.delete 0

# Aguardar processamento (Terminal 1)

# Verificar soft delete em analitico
psql -U admin_intellicare -d IntellicareDB << EOF
SELECT id, nome, valid_to, consolidation_source
FROM donabedian.analitico.pilar
WHERE id = '$PILAR_ID';
EOF

# Output esperado:
# valid_to = 2025-01-15 10:35:20.456789+00  (timestamp específico)
# consolidation_source = pilar.DELETE
```

**Resultado**: ✅ Se valid_to não é NULL, soft delete funcionou

---

## Teste 5: Consumer Group Persistence

### Objetivo
Verificar que consumer group persiste após restart do consumer.

```bash
# Terminal 1: Parar consumer (Ctrl+C)
^C
# 2025-XX-XX ... INFO - Consumer cancelled
# 2025-XX-XX ... INFO - ✅ Consolidation consumer closed

# Terminal 2: Criar novo evento enquanto consumer está offline
curl -s -X POST http://localhost:8000/pilar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Pilar While Offline",
    "descricao": "Created while consumer was down",
    "tipo": "OUTCOME",
    "ordem_exibicao": 3
  }' | jq -r '.id' > /tmp/new_pilar_id.txt

redis-cli XLEN intellicare:donabedian:pilar.create
# Output: N (número de eventos não processados)

# Terminal 1: Reiniciar consumer
python -m donabedian.consolidation.worker

# Observar que consumer processa eventos antigos:
# 2025-XX-XX ... INFO - 📝 Processing event: ... from intellicare:donabedian:pilar.create
# 2025-XX-XX ... INFO - ✅ ACK: ...

# Terminal 2: Verificar que novos dados foram consolidados
NEW_PILAR_ID=$(cat /tmp/new_pilar_id.txt)
psql -U admin_intellicare -d IntellicareDB -c "
  SELECT id, nome, consolidation_source 
  FROM donabedian.analitico.pilar 
  WHERE id = '$NEW_PILAR_ID'"
```

**Resultado**: ✅ Se dados foram consolidados mesmo após restart, consumer group persistence funciona

---

## Teste 6: Pytest Suite Automático

### Objetivo
Rodar suite de testes automatizados (mais abrangente).

```bash
# Terminal 2: Parar API (Ctrl+C) se estiver rodando
^C

# Parar Consumer se estiver rodando
# Terminal 1: Ctrl+C
^C

# Rodar pytest
cd src
pytest donabedian/consolidation/test_consolidation.py -v -s --tb=short

# Output esperado:
# test_pilar_create_event_consolidation PASSED                                    [ 16%]
# test_pilar_update_event_consolidation PASSED                                    [ 33%]
# test_pilar_delete_event_consolidation PASSED                                    [ 50%]
# test_consolidation_consumer_worker PASSED                                       [ 66%]
# test_consolidated_at_timestamp PASSED                                           [ 83%]
# test_invalid_entity_type_returns_false PASSED                                   [100%]

# ========================= 6 passed in X.XXs =========================
```

**Resultado**: ✅ Se todos os testes passam

### Se algum teste falhar:

```bash
# Rodar só o teste que falhou com mais debug
pytest donabedian/consolidation/test_consolidation.py::TestConsolidationConsumer::test_pilar_create_event_consolidation -vvv -s --tb=long

# Verificar logs detalhados
# - Check PostgreSQL connection: psql -U admin_intellicare -d IntellicareDB -c "SELECT 1"
# - Check Redis connection: redis-cli ping
# - Check migrations: alembic current
```

---

## Teste 7: Performance & Throughput

### Objetivo
Medir latência e throughput do pipeline.

```bash
# Terminal 2: Script para criar 10 Pilares
for i in {1..10}; do
  TIME_START=$(date +%s%N)
  
  PILAR_ID=$(curl -s -X POST http://localhost:8000/pilar \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"nome\": \"Pilar $i\",
      \"descricao\": \"Performance test $i\",
      \"tipo\": \"OUTCOME\",
      \"ordem_exibicao\": $i
    }" | jq -r '.id')
  
  # Aguardar consolidação (aprox 100ms)
  sleep 0.2
  
  TIME_END=$(date +%s%N)
  TIME_DIFF=$(( (TIME_END - TIME_START) / 1000000 ))
  
  echo "Pilar $i: ${TIME_DIFF}ms ($PILAR_ID)"
done

# Resultado esperado: ~100-200ms por pilar
```

### Medir Consumer Throughput:

```bash
# Terminal 1: Observar logs do consumer
# Contar quantos "ACK" em 1 minuto
tail -f /var/log/donabedian.log | grep ACK | wc -l

# Se criar 100 eventos rápido:
# Esperado: processar 100 em ~1-2 segundos = 50-100 eventos/segundo
```

---

## Teste 8: Error Scenarios

### 8.1 - Event inválido (sem timestamp)

```bash
# Terminal 2: Publicar evento malformado diretamente
redis-cli XADD intellicare:donabedian:pilar.create "*" \
  entity_id "invalid-uuid" \
  operation "CREATE"

# Terminal 1 (consumer): Observar
# 2025-XX-XX ... WARNING - ❌ NACK (will retry): ...
# O evento será retentado (NACK = não reconhecido)
```

### 8.2 - Database desconectado

```bash
# Terminal 2: Simular falha de DB
# Parar PostgreSQL (se em Docker):
docker stop intellicare-db

# Terminal 1 (consumer): Observar
# 2025-XX-XX ... ERROR - Error in consumer loop: connection refused
# ... backoff 5s
# Consumer tenta reconectar automaticamente

# Reiniciar DB:
docker start intellicare-db

# Consumer reconecta e processa eventos atrasados
```

### 8.3 - Redis disconnect

```bash
# Terminal 2: Parar Redis
redis-cli SHUTDOWN

# Terminal 1 (consumer): Observar
# 2025-XX-XX ... ERROR - Error in consumer loop: ...
# Consumer aguarda reconnect

# Reiniciar Redis:
redis-server
```

---

## Checklist de Testes

| Teste | Expected | Status |
|-------|----------|--------|
| Consumer conecta a Redis | Consumer group criado | ✅ |
| Consumer conecta a PostgreSQL | Sem erro de conexão | ✅ |
| CREATE event consolidado | Dado em analitico | ✅ |
| UPDATE event consolidado | Dado atualizado em analitico | ✅ |
| DELETE event soft delete | valid_to setado | ✅ |
| Consumer restart processa atrasados | Dados consolidados | ✅ |
| Pytest suite | Todos 6 testes passam | ✅ |
| Performance CREATE | < 200ms | ✅ |
| Error handling NACK | Evento retentado | ✅ |
| Database recovery | Consumer reconecta | ✅ |

---

## Troubleshooting

### Consumer não conecta a Redis

```bash
# Verificar Redis está rodando
redis-cli ping
# Se erro: connection refused

# Se em Linux
redis-server /etc/redis/redis.conf

# Se em Docker
docker-compose up -d redis

# Verificar URL
echo $REDIS_URL
# Esperado: redis://localhost:6379
```

### Consumer não conecta a PostgreSQL

```bash
# Verificar DB está rodando
psql -U admin_intellicare -d IntellicareDB -c "SELECT 1;"

# Se erro, verificar URL
echo $DATABASE_URL

# Verificar permissões de usuário
psql -U admin_intellicare -d IntellicareDB -c "
  SELECT schema_name FROM information_schema.schemata 
  WHERE schema_name = 'donabedian';"
```

### Consumer não processa eventos

```bash
# Verificar consumer group
redis-cli XINFO GROUPS intellicare:donabedian:pilar.create

# Se consumers = 0, consumer morreu
# Reiniciar: python -m donabedian.consolidation.worker

# Verificar pending
redis-cli XPENDING intellicare:donabedian:pilar.create donabedian-consolidation

# Se há pending, eventos foram tentados mas consumer falhou
# Verificar logs de erro
```

### Dados não aparecem em analitico

```bash
# Verificar se evento foi ACK'd
redis-cli XINFO CONSUMERS intellicare:donabedian:pilar.create donabedian-consolidation

# idle_ms = tempo desde último ACK
# Se idle_ms = 0, evento foi processado

# Verificar migrations
alembic current
# Esperado: donabedian.analitico.pilar tabela existe

# Verificar RLS policy
psql -U admin_intellicare -d IntellicareDB -c "
  SELECT tablename FROM pg_tables 
  WHERE schemaname = 'analitico';"
```

---

## Próximos Passos

1. ✅ Completar Teste 1-8 acima
2. ⏳ Rodar tests em produção (dados reais)
3. ⏳ Monitorar consolidation lag (consolidation_source vs created_at)
4. ⏳ Replicar padrão para florence, oswaldo, zilda (FASE 2.4)
5. ⏳ Setup alerts para consumer health

---

**Duração Estimada**: 30-45 minutos para todos os testes

**Sucesso**: Quando todos 10 itens do checklist estão ✅
