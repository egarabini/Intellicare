# 🔄 Guia de Migração - Atualização de Portas v2.0.0

**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **OBRIGATÓRIO**

---

## 📋 Visão Geral

Este guia ajuda na migração de configurações antigas de portas para o **mapeamento definitivo v2.0.0**.

---

## ⚠️ Mudanças Críticas

### Portas que MUDARAM

| Módulo | Porta Antiga | Porta Nova | Motivo |
|--------|--------------|------------|--------|
| **Grahame** | ❌ Indefinida/8004 | ✅ **8012** | Conflito com Wanda resolvido |
| **Wanda** | ✅ 8004 | ✅ **8004** | Mantido (orquestrador principal) |

### Portas que PERMANECERAM

Todos os outros módulos **mantiveram suas portas originais**:
- Florence: 8001
- Oswaldo: 8002
- Donabedian: 8003
- Comunicacao: 8005
- Geralda: 8006
- Zilda: 8007
- OCR/Minerva: 8008
- Pierre: 8009
- Admin: 8010
- Gestor: 8011
- Nise: 8013
- Portal: 3001

---

## 🔧 Passo a Passo da Migração

### 1. Atualizar Arquivo `.env`

**Antes:**
```bash
# Configuração antiga (INCORRETA)
GRAHAME_PORT=8004  # ❌ Conflito com Wanda!
WANDA_PORT=8004
```

**Depois:**
```bash
# Configuração nova (CORRETA)
GRAHAME_PORT=8012  # ✅ Porta definitiva
WANDA_PORT=8004    # ✅ Mantido
```

### 2. Atualizar `docker-compose.yml` (se customizado)

Se você tem um `docker-compose.yml` customizado, atualize:

```yaml
# Antes (INCORRETO)
grahame:
  ports:
    - "8004:8000"  # ❌ Conflito!

# Depois (CORRETO)
grahame:
  ports:
    - "${GRAHAME_PORT:-8012}:8000"  # ✅ Porta definitiva
```

### 3. Atualizar URLs de Frontend

Se você tem URLs hardcoded no frontend:

**Antes:**
```typescript
// ❌ INCORRETO
const GRAHAME_URL = 'http://localhost:8004';
```

**Depois:**
```typescript
// ✅ CORRETO
const GRAHAME_URL = 'http://localhost:8012';
```

### 4. Atualizar Scripts de Deploy

Se você tem scripts customizados:

```bash
# Antes (INCORRETO)
curl http://localhost:8004/api/v1/fhir/metadata  # ❌ Isso é Wanda!

# Depois (CORRETO)
curl http://localhost:8012/api/v1/fhir/metadata  # ✅ Grahame
curl http://localhost:8004/api/v1/health         # ✅ Wanda
```

### 5. Atualizar Firewall/Proxy Reverso

Se você tem regras de firewall ou proxy reverso:

```bash
# Adicionar porta 8012 para Grahame
ufw allow 8012/tcp

# Nginx/Traefik
# Atualizar upstream para Grahame de 8004 para 8012
```

---

## ✅ Checklist de Validação

Após a migração, execute:

### 1. Verificar Variáveis de Ambiente

```bash
# Verificar .env
grep GRAHAME_PORT .env
# Deve retornar: GRAHAME_PORT=8012

grep WANDA_PORT .env
# Deve retornar: WANDA_PORT=8004
```

### 2. Testar Endpoints

```bash
# Testar Grahame (FHIR)
curl http://localhost:8012/api/v1/health
curl http://localhost:8012/api/v1/fhir/metadata

# Testar Wanda (Orquestrador)
curl http://localhost:8004/api/v1/health
curl http://localhost:8004/api/v1/info
```

### 3. Executar Smoke Tests

```bash
# Executar testes automatizados
python scripts/smoke_tests.py

# Deve mostrar:
# ✅ Grahame (8012) - healthy
# ✅ Wanda (8004) - healthy
```

### 4. Verificar Logs

```bash
# Verificar se não há erros de porta
docker logs intellicare-grahame | grep -i "port\|error"
docker logs intellicare-wanda | grep -i "port\|error"
```

---

## 🚨 Problemas Comuns

### Problema 1: "Port already allocated"

**Sintoma:**
```
Error: bind: address already in use
```

**Solução:**
```bash
# Parar todos os containers
docker-compose -f docker-compose.full.yml down

# Verificar portas em uso
netstat -tulpn | grep -E ':(8004|8012)'

# Matar processos conflitantes (se necessário)
kill -9 <PID>

# Reiniciar
docker-compose -f docker-compose.full.yml up -d
```

### Problema 2: Frontend não conecta ao Grahame

**Sintoma:**
```
Failed to fetch: http://localhost:8004/api/v1/fhir/metadata
```

**Solução:**
```bash
# Atualizar variável de ambiente do frontend
# .env.local ou .env
VITE_API_GRAHAME_URL=http://localhost:8012

# Rebuild frontend
cd intellicare-portal/frontend
npm run build
```

### Problema 3: Proxy reverso ainda aponta para porta antiga

**Sintoma:**
```
502 Bad Gateway ao acessar Grahame
```

**Solução:**
```bash
# Nginx: Atualizar upstream
# /etc/nginx/sites-available/intellicare
upstream grahame {
    server localhost:8012;  # ✅ Atualizado
}

# Recarregar Nginx
sudo nginx -t
sudo systemctl reload nginx

# Traefik: Atualizar docker-compose.traefik.yml
# Verificar labels do serviço grahame
```

---

## 📊 Mapeamento Completo (Referência)

Para referência completa, consulte:
- **Documento Principal:** `docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md`
- **CLAUDE.md:** Tabela de módulos atualizada
- **`.env.full`:** Configuração de referência

---

## 🎯 Próximos Passos

Após completar a migração:

1. ✅ Validar todos os endpoints
2. ✅ Atualizar documentação interna da equipe
3. ✅ Notificar equipe de DevOps
4. ✅ Atualizar monitoramento (Prometheus/Grafana)
5. ✅ Atualizar runbooks de troubleshooting

---

## 📞 Suporte

Se encontrar problemas durante a migração:

1. Consulte: `docs/INFRAESTRUTURA/MAPEAMENTO_PORTAS_COMPLETO.md`
2. Execute: `python scripts/smoke_tests.py --verbose`
3. Verifique logs: `docker logs <container_name>`

---

**Criado por:** Augment Agent  
**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **OBRIGATÓRIO**

