# Gotchas Staging e Deploy

Entradas baseadas em DEM-INF_STAGING_SCRIPT, DEM-INF_STAGING_EVOLUTION, DEM-047, DEM-048, DEM-049 e nos incidentes reproduzidos no VPS em 2026-03-20/21.

## `git push` antes do deploy no VPS

### Situacao real
- O fluxo de staging depende de `git pull origin main` no VPS, conforme o briefing de [`docs/demandas/DEM-INF_STAGING_EVOLUTION/BRIEFING.md`](/c:/Users/egara/INTELLICARE/docs/demandas/DEM-INF_STAGING_EVOLUTION/BRIEFING.md).

### Sintoma
- O VPS reporta `already up to date`, mas a DEM mais recente nunca entrou porque o commit so existia na maquina do dev.

### Fix
- O dev que fechou a ultima DEM faz `git push origin main` antes de pedir deploy para DEV-3/4.

## `docker-entrypoint-initdb.d` so roda no primeiro boot do Postgres

### Situacao real
- O staging mostrou isso duas vezes:
- o banco `evolution` precisou ser recriado manualmente durante o debug do WhatsApp
- o `listmonk` entrou em crash loop porque o banco `listmonk` nao existia, apesar de o compose prever o servico

### Sintoma
- Container sobe, mas o banco esperado nao aparece.
- Logs do `listmonk`: `pq: database "listmonk" does not exist`.

### Fix
- Criar o banco manualmente quando o volume do Postgres ja existe.
- Exemplo operacional:

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  exec postgres psql -U intellicare_staging -d postgres -c "CREATE DATABASE listmonk;"
```

## Senha com caractere especial quebra URI

### Situacao real
- No staging, `REDIS_PASSWORD=IC_Staging#Redis2025` quebrou o `CACHE_REDIS_URI` do Evolution.
- O container so estabilizou depois de usar senha URL-encoded em variavel separada.

### Sintoma
- `redis disconnected`, `NOAUTH` ou `WRONGPASS` mesmo com Redis `healthy`.

### Fix
- Criar variavel dedicada URL-encoded, por exemplo `REDIS_PASSWORD_URLENC`.
- Nao interpolar senha bruta com `#`, `@` ou `!` direto em URI.

## Porta publicada e porta interna nao sao a mesma coisa

### Situacao real
- O compose atual publica:
- `listmonk` em `9001:9000`
- `evolution-api` em `8081:8080`

### Sintoma
- Smoke test em `localhost:9100` ou `localhost:9000` falha mesmo com servico corretamente configurado no container.

### Fix
- Usar sempre a porta do host no checklist operacional.
- Antes de testar, conferir o bloco `ports:` em [`infra/docker-compose.yml`](/c:/Users/egara/INTELLICARE/infra/docker-compose.yml).

## Segredo ausente faz serviço subir torto ou ficar inutilizavel

### Situacao real
- Em 2026-03-21 o staging estava sem `LISTMONK_USERNAME`, `LISTMONK_PASSWORD` e `JASMIN_PASSWORD` no `.env.staging`.
- O `jasmin` subiu, mas o smoke test nao era executavel com a credencial esperada.
- O `listmonk` ainda acusava warning de env ausente antes mesmo de falhar pelo banco faltante.

### Sintoma
- Warnings do compose sobre variavel defaultando para vazio.
- Smoke test falha sem distinguir claramente se o problema e credencial ou servico.

### Fix
- Tratar `.env.staging` como artefato de provisionamento, nao detalhe de ultima hora.
- Validar segredos obrigatorios por canal antes de subir servico.

## `infra/letsencrypt/` suja working tree do VPS

### Situacao real
- O proprio workflow de staging ja documenta que Traefik gera artefatos de runtime em `infra/letsencrypt/`.

### Sintoma
- `git status` no VPS mostra arquivo nao rastreado ou diretório sujo, mesmo sem alteracao funcional no codigo.

### Fix
- Garantir `infra/letsencrypt/` no `.gitignore` e nao usar esse ruido como sinal de deploy incompleto.

## `redis_pubsub.py` usa senha bruta e quebra a URL

### Situacao real
- O `.env.staging` tinha `REDIS_PASSWORD_URLENC=IC_Staging%23Redis2025` corretamente,
  mas `redis_pubsub.py` montava a URL com `{s.redis_password}` (senha bruta com `#`).
- O parser de URL interpreta `IC_Staging` como o campo de porta, gerando
  `ValueError: Port could not be cast to integer value as 'IC_Staging'`.

### Sintoma
- Logs do `dispatcher_worker` poluídos com `ValueError: Port could not be cast`.
- `GET /health/adapters` pode mascarar o erro, mas dispatcher fica inoperante.

### Fix
- `redis_pubsub.py` deve usar `REDIS_PASSWORD_URLENC` (ou `os.getenv("REDIS_PASSWORD_URLENC")`)
  ao montar a URI, nunca a senha bruta.
- Verificar toda montagem de URI Redis no código — busca rápida:
  ```bash
  grep -rn "redis_password" modules/ --include="*.py"
  ```

## Evolution API v2.2.x nao gera QR Code — usar v2.3.7

### Situacao real
- Em 2026-03-21, as imagens `atendai/evolution-api:v2.2.0`, `v2.2.1` e `v2.2.2` foram
  testadas no staging do IntelliCare. Todas retornam `{"count":0}` no
  `GET /instance/connect/{name}` e ficam presas em `connectionStatus: "connecting"`
  indefinidamente, mesmo com banco limpo, Redis limpo e Prisma migrations aplicadas.
- O problema foi isolado ao binario Node/Baileys v6 dessas imagens: o worker do WebSocket
  morre silenciosamente sem emitir o evento `qr`, sem log de erro visivel.
- A imagem do ambiente de desenvolvimento local ja usava `evoapicloud/evolution-api:v2.3.7`,
  que corrige race conditions no motor do Baileys.

### Sintoma
- `GET /instance/connect/{name}` retorna `{"count":0}`.
- `GET /instance/connectionState/{name}` retorna `{"state":"connecting"}` para sempre.
- Logs com `grep -iE "baileys|qr|error"` ficam mudos apos o `instance/create`.

### Fix
- Usar `evoapicloud/evolution-api:v2.3.7` (registry diferente de `atendai/`).
- No `infra/docker-compose.yml`:
  ```yaml
  image: evoapicloud/evolution-api:v2.3.7
  ```
- Apos troca de imagem, recriar a instancia do zero (DELETE + POST create) porque
  sessoes anteriores ficam com estado invalido no Postgres/Redis.
