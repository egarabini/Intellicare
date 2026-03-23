---
tipo: especificacao-tecnica
demanda: DEM-082
titulo: Staging Sync 2026-05-09
---

# DEM-082 — Especificação Técnica

## Checklist de aplicação

### 1. Pull e rebuild

```bash
cd /opt/intellicare
git pull origin main
# Confirmar: DEM-079 + DEM-080 + DEM-081 em main

docker compose build api gestorui clinicoui
docker compose up -d
```

---

### 2. Aplicar migrations 019 e 020

```bash
# Migration 019 — professional_certificates (schema por tenant)
docker compose exec db psql -U postgres -d intellicare \
  -f /app/db/tenant_migrations/019_professional_certificates.sql

# Migration 020 — interaction_warnings_count
docker compose exec db psql -U postgres -d intellicare \
  -f /app/db/tenant_migrations/020_prescription_interaction_count.sql

# Verificar
docker compose exec db psql -U postgres -d intellicare -c \
  "\d demo.professional_certificates"
docker compose exec db psql -U postgres -d intellicare -c \
  "\d demo.prescriptions" | grep interaction
```

---

### 3. Ativar `MARIE_ENABLED=true` e criar workflow Florence

```bash
# Atualizar .env.staging
MARIE_ENABLED=true

docker compose restart api

# Criar workflow florence_soap_rag no Dify (http://staging:porta/marie-web)
# Ver spec DEM-079 §Workflow Dify
# Publicar workflow
```

---

### 4. Criar certificado de teste e fazer upload

```bash
# Gerar certificado autoassinado para smoke
openssl req -x509 -newkey rsa:2048 -keyout /tmp/key.pem -out /tmp/cert.pem \
  -days 365 -nodes -subj "/CN=DR SILVA STAGING/OU=CRM-SP 999999/C=BR"
openssl pkcs12 -export -out /tmp/test_staging.pfx \
  -inkey /tmp/key.pem -in /tmp/cert.pem -passout pass:StagingTest123

# Upload via API
curl -s -X POST http://staging:8000/professionals/me/certificate \
  -H "Authorization: Bearer $CLINICO_TOKEN" \
  -F "file=@/tmp/test_staging.pfx" \
  -F "password=StagingTest123" | jq '{subject_name, valid_until}'
```

---

### 5. Smokes

```bash
# Florence com Marie
curl -s -X POST http://staging:8000/florence/notes/suggest \
  -H "Authorization: Bearer $CLINICO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"encounter_id": "UUID"}' | jq '{soap_s, soap_a}' # soap_a deve citar histórico

# Receituário assinado
curl -s -o /tmp/receituario_assinado.pdf \
  -H "Authorization: Bearer $CLINICO_TOKEN" \
  "http://staging:8000/oswaldo/prescriptions/UUID/receituario.pdf?type=simple"
# Abrir /tmp/receituario_assinado.pdf no Chrome — verificar painel de assinaturas

# KPIs
curl -s "http://staging:8000/admin/kpis/clinical?start=2026-01-01&end=2026-12-31" \
  -H "Authorization: Bearer $GESTOR_TOKEN" | jq '{encounters, prescriptions, interactions_detected}'

# Smoke GestorUI manual: http://staging-gestor/indicadores
```

---

### 6. Suite de testes

```bash
docker compose exec api pytest \
  tests/test_florence_marie.py \
  tests/test_assinatura_digital.py \
  tests/test_clinical_kpis.py \
  -v
```

---

## Variáveis novas no `.env.staging`

```env
MARIE_ENABLED=true          # ativar neste sprint
SERVER_ENCRYPTION_KEY=      # gerar com: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Nota — Keycloak: usar REST API, não `setup_keycloak.py`

Conforme gotcha do DEM-078: criar `gestor.alfa` (se não existir) via Admin REST API:

```bash
ADMIN_TOKEN=$(curl -s -X POST http://keycloak:8080/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli&username=admin&password=IC_Staging#Kc2025&grant_type=password" \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

curl -s -X POST http://keycloak:8080/admin/realms/intellicare/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"username":"gestor.alfa","email":"gestor@demo.intellicare","enabled":true,
       "credentials":[{"type":"password","value":"Demo@1234","temporary":false}]}'
# Atribuir role GESTOR ao usuário criado (mesmo padrão do DEM-078)
```
