---
tipo: finalizacao
demanda: DEM-INF (Staging Deploy + Evolution API)
dev: DEV-3/4
status: parcialmente-concluido
data: 2026-03-21
ultimo-commit: fbc7996
---

# DEM-INF Staging — Finalização Parcial

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
| `infra/docker-compose.yml`, `.env.example`, `.env.staging.example` atualizados | ✅ pendente commit |

## O que ficou bloqueado ⚠️

### 1. WhatsApp QR — Evolution API (`connecting`, sem QR)

**Sintoma:** `GET /instance/connect/intellicare` retorna `{"count":0}`.
Estado da instância permanece `"connecting"` em todas as versões testadas.

**Versões testadas:** `v2.2.0`, `v2.1.1` — comportamento idêntico.
Tags disponíveis no Docker Hub: `v2.2.3`, `v2.2.2`, `v2.2.1`, `v2.1.2`, `v2.1.0`, `v2.0.10`.

**Hipóteses não descartadas:**
- Container sem saída para servidores WhatsApp (regra de firewall no VPS bloqueando porta 443 saindo do container)
- Incompatibilidade de versão do protocolo Baileys com os servidores WA atuais
- Conta WhatsApp `+5527988358449` ainda não ativada no app antes do QR scan

**Ação pendente:** Antes de tentar outra versão de imagem, verificar saída de rede do container:
```bash
docker compose exec evolution-api curl -s https://web.whatsapp.com | head -5
# Se falhar → problema de rede/firewall no VPS
# Se retornar HTML → problema é da imagem/protocolo
```

### 2. Listmonk sem banco no Postgres

**Sintoma:** crash loop ao subir o serviço `listmonk` — banco `listmonk` não existe.

**Fix (2 min no VPS):**
```bash
docker compose --env-file infra/.env.staging exec postgres \
  psql -U postgres -c "CREATE DATABASE listmonk;"

docker compose --env-file infra/.env.staging up -d listmonk --force-recreate
docker logs intellicare_listmonk --tail=20
```

O init SQL `infra/init-db/03_listmonk.sql` (criado em DEM-048) deveria ter criado
o banco automaticamente, mas provavelmente o container Postgres já havia inicializado
antes da DEM-048 — o `docker-entrypoint-initdb.d` só roda na **primeira** inicialização.
Fix permanente: `docker compose down -v && docker compose up -d` na próxima vez que
o volume Postgres for recriado do zero.

### 3. Jasmin sem JASMIN_PASSWORD no VPS

**Sintoma:** smoke test não executável — variável ausente em `infra/.env.staging`.

**Fix (1 min no VPS):**
```bash
echo "JASMIN_PASSWORD=JasminStaging2026" >> /opt/intellicare/infra/.env.staging
docker compose --env-file infra/.env.staging up -d jasmin --force-recreate
```

### 4. Porta Listmonk — divergência entre spec e compose

**Sintoma:** spec do DEM-INF referencia porta `9100`, compose do IntelliCare publica `9001:9000`.

**Ação:** smoke test deve usar `localhost:9001`, não `localhost:9100`.

---

## Pendências de commit

Os arquivos abaixo foram modificados localmente pelo DEV-3/4 durante o troubleshooting
e ainda não foram commitados:

- `infra/docker-compose.yml`
- `infra/.env.example`
- `infra/.env.staging.example`

**Repassar para DEV-3/4 commitar antes de encerrar:**
```
fix(infra): staging — Redis URL-encoded, porta listmonk, vars evolution e jasmin
```

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
