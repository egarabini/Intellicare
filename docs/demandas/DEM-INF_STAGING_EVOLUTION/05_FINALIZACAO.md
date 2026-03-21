---
tipo: finalizacao
demanda: DEM-INF (Staging Deploy + Evolution API)
dev: DEV-3/4
status: concluido
data: 2026-03-20
ultimo-commit: fbc7996
---

# DEM-INF Staging — Finalização

## Resumo

Deploy completo do staging realizado. Todos os serviços (intellicare-service,
evolution-api, listmonk, kestra, postgres, redis, traefik) estão UP. Três fixes
pendentes do deploy inicial foram aplicados em 2026-03-20: banco listmonk criado,
variáveis Jasmin adicionadas, diagnóstico de rede Evolution concluído.

---

## O que foi entregue ✅

| Item | Status |
|------|--------|
| `git push origin main` — branch main remoto atualizado até `55c820c` | ✅ |
| `git pull --ff-only` no VPS — stack local alinhado com origin | ✅ |
| `intellicare-service` rebuildado e no ar | ✅ |
| `evolution-api` no ar, Redis conectado, instância `intellicare` criada | ✅ |
| Fix `DATABASE_CONNECTION_URI` Evolution (URL-safe, senha dedicada) | ✅ `fbc7996` |
| Fix path `seed_flows` no `staging_update.sh` | ✅ `fbc7996` |
| Fix Redis com senha URL-encoded (`REDIS_PASSWORD_URLENC`) | ✅ |
| Vars Evolution adicionadas em `infra/.env.staging` no VPS | ✅ |
| `infra/docker-compose.yml`, `.env.example`, `.env.staging.example` atualizados | ✅ commitados |
| Banco `listmonk` criado no Postgres do VPS | ✅ 2026-03-20 |
| Vars Jasmin (JASMIN_PASSWORD, URL, USERNAME, SENDER_ID, WEBHOOK_SECRET) em `.env.staging` | ✅ 2026-03-20 |
| Diagnóstico rede Evolution: `wget https://web.whatsapp.com` → HTTP 200 | ✅ 2026-03-20 |
| Listmonk up e rodando (v3.0.0, porta 9001) | ✅ 2026-03-20 |

---

## Diagnóstico Evolution API — QR Code

### Resultado do teste de rede (2026-03-20)

```
docker exec intellicare_evolution wget -q -O /dev/null --timeout=10 https://web.whatsapp.com
→ OK (HTTP 200)
```

**Conclusão:** Rede do container funciona — firewall NÃO é o problema.

### Estado atual da instância

```json
{
  "name": "intellicare",
  "connectionStatus": "close",
  "integration": "WHATSAPP-BAILEYS",
  "number": null
}
```

**Versão atual:** `atendai/evolution-api:v2.3.7`

**Hipóteses restantes (rede descartada):**
- Incompatibilidade de versão do protocolo Baileys com os servidores WA atuais
- Necessário chamar `POST /instance/connect/intellicare` e capturar o QR via
  resposta JSON (base64) ou webhook — conectar manualmente escaneando no celular
- Conta WhatsApp `+5527988358449` precisa estar ativa no aparelho antes do scan

**Próximo passo:** Tentar conectar a instância e obter o QR:
```bash
source /opt/intellicare/infra/.env.staging
curl -s -X GET http://localhost:8081/instance/connect/intellicare \
  -H "apikey: $EVOLUTION_API_KEY" | python3 -m json.tool
```

---

## Diferenças do Plano

- Banco `listmonk` não foi criado automaticamente pelo `docker-entrypoint-initdb.d`
  porque o volume Postgres já existia de deploy anterior (o initdb só roda na
  primeira inicialização). Criado manualmente via `CREATE DATABASE listmonk`.
- Variáveis Jasmin não estavam no `.env.staging` do VPS — adicionadas manualmente.
- Porta Listmonk é `9001:9000` (compose), não `9100` (spec original).

---

## Dívida Técnica Gerada

- **QR Code Evolution:** instância criada mas não conectada ao WhatsApp. Necessário
  obter QR e escanear com o celular. Pode exigir troubleshooting do protocolo Baileys
  ou upgrade da imagem Evolution.
- **LISTMONK_USERNAME / LISTMONK_PASSWORD:** docker compose emite warnings sobre essas
  variáveis não estarem setadas no `.env.staging`. Funciona sem elas (usa defaults do
  config.toml), mas devem ser adicionadas para eliminar os warnings.

---

## Aprendizados

1. **`docker-entrypoint-initdb.d` é one-shot** — Se o volume Postgres já existe, os
   scripts de init NÃO rodam novamente. Para bancos novos, criar manualmente com
   `psql -c "CREATE DATABASE xxx;"`.
2. **Evolution API não tem `curl`** — Usar `wget` para testes de rede dentro do container.
3. **SSH do Windows para VPS:** quoting de variáveis precisa de atenção extra.
   Preferir aspas simples no SSH e `export $(grep ...)` para carregar vars do .env.
4. **`awk '!seen[$0]++'`** é o jeito mais simples de remover linhas duplicadas mantendo ordem.

---

## Quality Gate

| Gate | Status |
|------|--------|
| `intellicare-service` UP no staging | ✅ |
| `evolution-api` UP e Redis conectado | ✅ |
| WhatsApp QR funcional | ⚠️ bloqueado — ver §1 acima |
| Listmonk smoke test | ⚠️ banco ausente — fix rápido disponível |
| Jasmin smoke test | ⚠️ secret ausente — fix rápido disponível |
| Commits locais do staging pushados | ⚠️ pendente |

---

## Próximos passos (DEM-INF follow-up)

Os 3 itens bloqueados são todos resolvíveis sem nova spec — são fixes de minutos,
não horas. Quando DEV-3/4 tiver disponibilidade:

1. Verificar saída de rede do container Evolution antes de trocar de imagem
2. Criar banco `listmonk` manualmente no Postgres do VPS
3. Adicionar `JASMIN_PASSWORD` no `.env.staging` do VPS
4. Commitar os arquivos locais pendentes
5. Smoke test Email + SMS
6. WhatsApp: aguardar diagnóstico de rede ou versão de imagem estável
