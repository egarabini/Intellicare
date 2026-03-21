# DEM-053 — Staging WhatsApp Smoke Test

> **Dev:** DEV-3/4 (execução no VPS) + Eduardo (escaneio do QR)
> **Estimativa:** ~1.5h
> **Pré-requisito:** Evolution API gerando QR (recriar instância ou atualizar para v2.2.2)
> **Dependência:** `infra/evolution_secrets_STAGING.txt` deve estar no VPS

---

## Contexto

A sprint 2026-03-21 entregou o stack multi-canal completo (WA/Email/SMS) com 53 testes
passando localmente. O staging tem rede OK (HTTP 200 para web.whatsapp.com confirmado),
mas a Evolution API v2.2.0 retorna `count:0` no connect — QR não gerado.

Esta DEM fecha o ciclo: conectar o WhatsApp real no staging e executar um smoke test
E2E completo de todos os canais.

---

## Fase A — Resolver QR Evolution

### STEP-001 — Tentar recreate da instância (v2.2.0)

```bash
# No VPS, executar sequencialmente
API_KEY="a0613608e66332167d032dd1fb062bf6e869b55b749eb26029e26b85af2843b6"
BASE="http://localhost:8081"

# Deletar instância corrompida
curl -s -X DELETE "$BASE/instance/delete/intellicare" -H "apikey: $API_KEY"

# Recriar com qrcode:true explícito
curl -s -X POST "$BASE/instance/create" \
  -H "apikey: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instanceName":"intellicare","qrcode":true,"integration":"WHATSAPP-BAILEYS"}'

sleep 5

# Conectar e capturar QR
curl -s -X GET "$BASE/instance/connect/intellicare" -H "apikey: $API_KEY"
```

**Critério:** resposta contém `"base64":"data:image/png;base64,..."` e `"count":1`.

### STEP-002 — Se count=0 persistir: atualizar para v2.2.2

Editar `infra/docker-compose.yml`:
```yaml
# De:
image: atendai/evolution-api:v2.2.0
# Para:
image: atendai/evolution-api:v2.2.2
```

```bash
cd /opt/intellicare
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  pull evolution-api
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d evolution-api
sleep 15
# Recriar instância conforme STEP-001
```

### STEP-003 — Eduardo escaneia o QR

Copiar o valor `base64` da resposta do connect e abrir no browser:
```
data:image/png;base64,<VALOR>
```
Escanear com o WhatsApp do chip +5527988358449.

Verificar:
```bash
curl -s "$BASE/instance/connectionState/intellicare" -H "apikey: $API_KEY"
# Esperado: {"instance":{"instanceName":"intellicare","state":"open"}}
```

Após `state: open` → **deletar** `infra/evolution_secrets_STAGING.txt`.

---

## Fase B — Smoke Test E2E Todos os Canais

### STEP-004 — Smoke WhatsApp

No GestorUI do staging (`https://api.intellicare.ia.br/gestor-ui/`):
1. Login como `gestor.alfa` / `Demo@1234`
2. Ir para CarePlanner → Nova Jornada
3. Selecionar canal **WhatsApp**, paciente com telefone +5527988358449
4. Disparar jornada
5. Verificar no banco:

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  exec postgres psql -U intellicare_staging -d intellicare_alfa \
  -c "SELECT correlation_id, status, channel FROM care_tasks ORDER BY created_at DESC LIMIT 3;"
```

**Critério:** status `DISPATCHED` ou `SENT` para canal `WHATSAPP`.

Responder pelo WhatsApp do chip para testar inbound:
**Critério:** status muda para `REPLIED`.

### STEP-005 — Smoke Email

1. Novo trigger, canal **Email**, paciente com email cadastrado
2. Verificar Listmonk em `http://<IP_VPS>:9001` → Transactional → mensagem enviada
3. **Critério:** log do `intellicare-service` mostra `EmailAdapter sent ok`

### STEP-006 — Smoke SMS

1. Novo trigger, canal **SMS**, paciente com telefone cadastrado
2. **Critério:** log do `intellicare-service` mostra `SMSAdapter sent` ou `SMSAdapter skipped (dry-run)`

> **Nota:** Jasmin em staging pode estar em modo dry-run sem SMSC real configurado.
> O critério é que o adapter seja invocado sem erro 500 — não que o SMS chegue ao celular.

### STEP-007 — Verificar healthcheck

```bash
curl -s https://api.intellicare.ia.br/api/health/adapters | python3 -m json.tool
```

**Critério:** `rocketchat` e `evolution` com `"ok"`. `listmonk` e `jasmin` com `"ok"` ou `"degraded"` (aceitável).

---

## Fase C — Limpeza e Commit

### STEP-008 — Deletar secrets temporários

```bash
# Apenas após connectionStatus: open
rm /opt/intellicare/infra/evolution_secrets_STAGING.txt
git -C /opt/intellicare rm --cached infra/evolution_secrets_STAGING.txt 2>/dev/null || true
```

### STEP-009 — Commitar alterações de staging

Se a versão da Evolution foi atualizada para v2.2.2:
```bash
cd /opt/intellicare
git add infra/docker-compose.yml
git commit -m "infra: evolution-api bump v2.2.0 -> v2.2.2 (QR fix staging)"
git push origin main
```

---

## Critérios de Aceite

- [ ] `connectionState/intellicare` retorna `state: open`
- [ ] Jornada WhatsApp criada com status `SENT` ou `DISPATCHED` no banco
- [ ] Inbound WhatsApp muda status para `REPLIED`
- [ ] Email adapter invocado sem erro 500
- [ ] SMS adapter invocado sem erro 500
- [ ] `GET /health/adapters` retorna JSON sem erro
- [ ] `infra/evolution_secrets_STAGING.txt` deletado após open

---

## Fallback

Se v2.2.2 também falhar no QR:
- Aceitar como limitação da imagem atendai e abrir issue no GitHub deles
- Registrar em `docs/gotchas/staging-deploy.md` entrada "Evolution API v2.x QR broken"
- Testar WhatsApp apenas localmente via mocks (DEM-050 já cobre esse cenário)
- Mover ativação real do WA para quando versão estável for identificada
