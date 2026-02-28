# HL7v2 API Key Authentication

Este documento descreve como usar o sistema de autenticação por API Key para o endpoint HL7v2 do Grahame.

## 📋 Visão Geral

O endpoint `/api/v1/hl7v2/adt-a04` requer autenticação via API Key para garantir que apenas sistemas autorizados possam enviar mensagens HL7v2.

**Features:**
- ✅ API Keys únicas por sistema/hospital
- ✅ Expiração configurável
- ✅ Rate limiting (requisições por minuto)
- ✅ IP whitelist (opcional)
- ✅ Auditoria completa de todas as requisições
- ✅ Desabilitação de keys sem exclusão

---

## 🚀 Setup Inicial

### 1. Executar Migrations

Primeiro, crie as tabelas no banco de dados:

```bash
cd ./intellicare-grahame

# Executar migrations
alembic upgrade head
```

### 2. Criar uma API Key

Use o script de gerenciamento para criar uma nova API Key:

```bash
python scripts/manage_hl7v2_api_keys.py create \
  --system "Hospital São Paulo - Tasy" \
  --identifier "HSP-TASY" \
  --description "Sistema Tasy do Hospital São Paulo" \
  --expires-days 365 \
  --rate-limit 120 \
  --allowed-ips "192.168.1.100,192.168.1.101"
```

**Parâmetros:**
- `--system`: Nome do sistema/hospital (obrigatório)
- `--identifier`: Identificador único (obrigatório, ex: HSP-TASY)
- `--description`: Descrição adicional (opcional)
- `--expires-days`: Dias até expiração (opcional, padrão: nunca expira)
- `--rate-limit`: Requisições por minuto (opcional, padrão: 60)
- `--allowed-ips`: IPs permitidos separados por vírgula (opcional, padrão: todos)

**Output:**
```
✅ API Key created successfully!

System: Hospital São Paulo - Tasy
Identifier: HSP-TASY
API Key: xK9mP2vL8nQ4wR7tY3zF6hJ1sD5gA0bC
Expires: 2027-02-25T12:00:00+00:00
Rate Limit: 120 req/min
Allowed IPs: 192.168.1.100,192.168.1.101

⚠️  IMPORTANT: Save this API Key securely. It cannot be retrieved later!
```

---

## 📡 Usando a API Key

### Enviar Mensagem HL7v2

```bash
curl -X POST http://localhost:8012/api/v1/hl7v2/adt-a04 \
  -H "X-API-Key: xK9mP2vL8nQ4wR7tY3zF6hJ1sD5gA0bC" \
  -H "Content-Type: application/x-hl7-v2" \
  --data-binary @message.hl7
```

**Headers obrigatórios:**
- `X-API-Key`: Sua API Key
- `Content-Type`: `application/x-hl7-v2` ou `text/plain`

**Exemplo de mensagem (message.hl7):**
```
MSH|^~\&|HOSPITAL|FACILITY|GRAHAME|INTELLICARE|20260224100000||ADT^A04|MSG00001|P|2.5
PID|1||12345^^^HOSPITAL^MR||Silva^João||19800115|M
PV1|1|I|WARD1^101^A^HOSPITAL||||||||||||||||VN123456
```

**Resposta de sucesso (200 OK):**
```
MSH|^~\&|GRAHAME|INTELLICARE|HOSPITAL|FACILITY|20260224100001||ACK^A04|ACK00001|P|2.5
MSA|AA|MSG00001|Message accepted and processed
```

---

## 🔐 Segurança

### Erros de Autenticação

**401 Unauthorized - API Key ausente:**
```json
{
  "detail": "Missing X-API-Key header"
}
```

**401 Unauthorized - API Key inválida:**
```json
{
  "detail": "Invalid API Key"
}
```

**401 Unauthorized - API Key expirada:**
```json
{
  "detail": "API Key is inactive or expired"
}
```

**403 Forbidden - IP não autorizado:**
```json
{
  "detail": "IP 192.168.1.200 is not whitelisted for this API Key"
}
```

### Rate Limiting

Se você exceder o limite de requisições por minuto, receberá um erro 429:

```json
{
  "detail": "Rate limit exceeded. Maximum 120 requests per minute."
}
```

---

## 🛠️ Gerenciamento de API Keys

### Listar todas as API Keys

```bash
python scripts/manage_hl7v2_api_keys.py list
```

**Output:**
```
ID    System                         Identifier           Status     Expires              Usage     
----- ------------------------------ -------------------- ---------- -------------------- ----------
1     Hospital São Paulo - Tasy      HSP-TASY             Active     2027-02-25           1234 reqs
2     Clínica MedPlus - MV           CMP-MV               Active     Never                567 reqs  
3     Hospital Regional - Philips    HR-PHILIPS           Inactive   2026-12-31           0 reqs    
```

### Desabilitar uma API Key

```bash
python scripts/manage_hl7v2_api_keys.py disable xK9mP2vL8nQ4wR7tY3zF6hJ1sD5gA0bC
```

**Output:**
```
✅ API Key disabled: HSP-TASY
```

---

## 📊 Auditoria

Todas as requisições HL7v2 são registradas na tabela `hl7v2_audit_logs` com:

- ✅ API Key usada
- ✅ IP de origem
- ✅ Mensagem completa (raw)
- ✅ Resultado do processamento (sucesso/erro)
- ✅ Tempo de processamento
- ✅ IDs dos recursos FHIR criados (Patient, Encounter)

### Consultar Audit Logs

```sql
-- Últimas 10 requisições
SELECT 
  created_at,
  message_control_id,
  message_type,
  request_ip,
  success,
  processing_time_ms
FROM hl7v2_audit_logs
ORDER BY created_at DESC
LIMIT 10;

-- Requisições com erro
SELECT 
  created_at,
  message_control_id,
  error_message,
  request_ip
FROM hl7v2_audit_logs
WHERE success = false
ORDER BY created_at DESC;

-- Estatísticas por sistema
SELECT 
  k.system_name,
  COUNT(*) as total_requests,
  SUM(CASE WHEN a.success THEN 1 ELSE 0 END) as successful,
  AVG(a.processing_time_ms) as avg_processing_time_ms
FROM hl7v2_audit_logs a
JOIN hl7v2_api_keys k ON a.api_key_id = k.id
GROUP BY k.system_name;
```

---

## 🔄 Rotação de API Keys

Para rotacionar uma API Key:

1. Criar nova API Key para o mesmo sistema
2. Atualizar o sistema legado com a nova key
3. Testar a nova key
4. Desabilitar a key antiga

```bash
# 1. Criar nova key
python scripts/manage_hl7v2_api_keys.py create \
  --system "Hospital São Paulo - Tasy" \
  --identifier "HSP-TASY-2" \
  --expires-days 365

# 2. Atualizar sistema legado (manual)

# 3. Testar nova key
curl -X POST http://localhost:8012/api/v1/hl7v2/adt-a04 \
  -H "X-API-Key: <NOVA_KEY>" \
  -H "Content-Type: application/x-hl7-v2" \
  --data-binary @message.hl7

# 4. Desabilitar key antiga
python scripts/manage_hl7v2_api_keys.py disable <KEY_ANTIGA>
```

---

## 📝 Best Practices

1. **Nunca compartilhe API Keys** - Cada sistema deve ter sua própria key
2. **Use IP whitelist** - Restrinja acesso apenas aos IPs conhecidos
3. **Configure expiração** - Keys devem expirar periodicamente (ex: 1 ano)
4. **Monitore audit logs** - Revise regularmente os logs de auditoria
5. **Rotacione keys** - Troque as keys periodicamente
6. **Rate limiting** - Configure limites adequados para cada sistema
7. **Armazene com segurança** - Use um gerenciador de senhas ou vault

---

## 🆘 Troubleshooting

### API Key não funciona

1. Verifique se a key está ativa: `python scripts/manage_hl7v2_api_keys.py list`
2. Verifique se não expirou
3. Verifique se o IP está na whitelist (se configurado)
4. Verifique os logs de auditoria para ver o erro exato

### Rate limit muito baixo

Atualize o rate limit diretamente no banco:

```sql
UPDATE hl7v2_api_keys
SET rate_limit_per_minute = 300
WHERE system_identifier = 'HSP-TASY';
```

### Adicionar IP à whitelist

```sql
UPDATE hl7v2_api_keys
SET allowed_ips = allowed_ips || ',192.168.1.200'
WHERE system_identifier = 'HSP-TASY';
```

---

## 📚 Referências

- [HL7 v2.5 Specification](http://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
- [FHIR R4](https://www.hl7.org/fhir/R4/)
- [IntelliCare Architecture](../../../CLAUDE.md)

