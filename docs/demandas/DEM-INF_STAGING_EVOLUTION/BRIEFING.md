---
tipo: briefing-completo
demanda: DEM-INF
titulo: Staging Deploy — Aplicar DEMs 038–047 + Provisionar Evolution API
dev: DEV-3/4
estimativa: 1.5h
prerequisito: DEM-047 commitada (da98ce2); acesso SSH ao VPS staging; .env.staging preenchido com segredos reais
---

# DEM-INF — Staging Deploy + Provisionamento Evolution API

## Contexto

O branch `main` está 32+ commits à frente do staging. O script `deploy/staging_update.sh`
foi criado em DEM-INF anterior e está pronto. Esta demanda aplica o deploy e,
adicionalmente, faz o provisionamento inicial do **Evolution API** no staging
(criar instância + conectar WhatsApp via QR code).

---

## Pré-requisitos (verificar ANTES de começar)

- [ ] Acesso SSH ao VPS staging confirmado
- [ ] `infra/.env.staging` preenchido com segredos reais (não commitar!)
- [ ] Variáveis Evolution obrigatórias presentes no `.env.staging`:
  ```
  EVOLUTION_API_KEY=<valor real>
  EVOLUTION_WEBHOOK_SECRET=<valor real>
  EVOLUTION_INSTANCE_NAME=intellicare
  POSTGRES_PASSWORD=<valor real>
  ```
- [ ] Firewall VPS: porta `8081` acessível internamente (Evolution API)
- [ ] DNS: `chat.intellicare.ia.br`, `meet.intellicare.ia.br`, `kestra.intellicare.ia.br` resolvem para o VPS

---

## STEP-001 — Pull e verificar estado

```bash
cd /opt/intellicare
git pull origin main
git log --oneline -5
# Confirmar que da98ce2 (DEM-047) aparece no log
```

---

## STEP-002 — Rodar staging_update.sh

```bash
chmod +x deploy/staging_update.sh
bash deploy/staging_update.sh
```

O script faz:
1. Valida pré-requisitos (docker, git, .env.staging)
2. `git pull`
3. `docker compose build --no-cache`
4. `docker compose up -d`
5. Seed dos flows Kestra (incluindo `careplanner_jornada_whatsapp.yml` novo)
6. Exibe status dos containers

Critério: todos os containers em estado `Up` ou `Up (healthy)`.

---

## STEP-003 — Verificar saúde dos serviços

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml ps

# Verificar especificamente:
docker logs intellicare_evolution --tail=30
# Esperado: "Evolution API iniciada", migrations concluídas, sem FATAL

docker logs intellicare_listmonk --tail=20 2>/dev/null || echo "listmonk ainda não (DEM-048 pendente)"
```

Critério: `intellicare_evolution` UP; sem erros de conexão com Postgres.

---

## STEP-004 — Provisionar instância Evolution API

O Evolution API precisa de uma instância criada antes de poder enviar mensagens.
Fazer via REST (pode ser pelo terminal do VPS ou Postman):

```bash
curl -s -X POST http://localhost:8081/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -d '{
    "instanceName": "intellicare",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }' | python3 -m json.tool
```

Resposta esperada: `{"instance": {"instanceName": "intellicare", "status": "created"}, "qrcode": {...}}`

---

## STEP-005 — Conectar WhatsApp (QR code)

Buscar o QR code da instância:

```bash
curl -s http://localhost:8081/instance/connect/intellicare \
  -H "apikey: ${EVOLUTION_API_KEY}" | python3 -m json.tool
```

O campo `qrcode.base64` contém a imagem do QR. Converter para PNG e escanear:

```bash
# Opção 1: salvar como HTML para abrir no browser
echo "<img src='$(curl -s ... | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['qrcode']['base64'])")' />" > /tmp/qr.html
# Opção 2: usar qrencode se disponível
# Opção 3: usar o endpoint /instance/qrcode/{instance} via painel web se habilitado
```

Escanear com WhatsApp Business (o número que será o bot IntelliCare).

---

## STEP-006 — Verificar conexão

```bash
curl -s http://localhost:8081/instance/connectionState/intellicare \
  -H "apikey: ${EVOLUTION_API_KEY}"
# Esperado: {"instance": {"state": "open"}}
```

---

## STEP-007 — Smoke test WhatsApp

Com a instância conectada, enviar uma mensagem de teste:

```bash
curl -s -X POST http://localhost:8081/message/sendText/intellicare \
  -H "Content-Type: application/json" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -d '{
    "number": "<SEU_NÚMERO_PESSOAL_SEM_+>",
    "textMessage": {"text": "IntelliCare staging OK ✅"}
  }'
```

Critério: mensagem recebida no WhatsApp.

---

## STEP-008 — Verificar seed dos flows Kestra

```bash
curl -s http://localhost:8080/api/v1/flows/search?namespace=intellicare.careplanner \
  | python3 -m json.tool | grep '"id"'
# Esperado: careplanner_jornada_basica, careplanner_jornada_video, careplanner_jornada_whatsapp
```

---

## STEP-009 — Relatório de status final

Registrar resultado no canal de comunicação do time com:

```
✅ Staging atualizado — DEM-038 a DEM-047 aplicadas
   Branch: main @ da98ce2
   Containers: [lista dos que estão UP]
   Evolution API: [CONNECTED / PENDING QR / FALHOU]
   Kestra flows: [N flows seeded]
   Problemas encontrados: [nenhum / descrever]
```

---

## Observações importantes

**Segredos**: `infra/.env.staging` com os valores reais **não deve ser commitado**.
O `.gitignore` já protege este arquivo (commit `9ff6a05`).

**QR code**: O WhatsApp Business precisa estar disponível para escanear.
Coordenar com Eduardo quem tem acesso ao número de negócios do IntelliCare.

**Rollback**: Se algo falhar:
```bash
cd /opt/intellicare
git reset --hard <hash-anterior>
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml up -d --build
```
