# SPEC — Correção dos Subdomínios IntelliCare

**Data:** 2026-03-07
**Prioridade:** Alta
**Responsável:** Dev Backend/Infra
**Servidor:** `root@167.86.97.142`
**Repositório local:** `C:\User\egara\INTELLICARE\`

---

## Contexto

Ao testar os subdomínios do ambiente de produção, foram identificados 3 problemas e 1 comportamento confirmado como correto:

| Subdomínio | Status | Problema |
|---|---|---|
| `www.intellicare.ia.br` | ✅ OK | Redireciona para portal |
| `portal.intellicare.ia.br` | ❌ Fix necessário | Login usa realm `intellicare` (errado — deve ser `bemcuidar`) |
| `admin.intellicare.ia.br` | ℹ️ Correto por design | Exibe dashboard HTML do módulo admin (V2.0.2 React pendente) |
| `gestor.intellicare.ia.br` | ❌ Fix necessário | Retorna 404 — rota Traefik ausente |

---

## Fix 1 — `gestor.intellicare.ia.br` retorna 404

### Causa

O arquivo `traefik/dynamic/routes-intellicare.yml` não possui router para o subdomínio `gestor.intellicare.ia.br`. O serviço `gestor-svc` (que aponta para `intellicare-gestor:8011`) já existe na seção de `services` do mesmo arquivo, mas sem o router correspondente o Traefik não encaminha as requisições.

### O que foi feito

O router já foi adicionado ao arquivo `traefik/dynamic/routes-intellicare.yml` no repositório local. O bloco adicionado foi:

```yaml
# ── Gestor (Admin por tenant) ─────────────────────────────
gestor:
  rule: "Host(`gestor.intellicare.ia.br`)"
  entryPoints:
    - websecure
  service: gestor-svc
  tls:
    certResolver: letsencrypt
  middlewares:
    - api-chain
```

### Passos para deploy

**1. Copiar o arquivo atualizado para o servidor:**

```bash
scp traefik/dynamic/routes-intellicare.yml \
    root@167.86.97.142:/etc/traefik/dynamic/routes-intellicare.yml
```

> O Traefik monitora o diretório `/etc/traefik/dynamic/` com file watcher. A mudança é aplicada automaticamente em segundos — **não é necessário reiniciar o Traefik**.

**2. Verificar que a rota foi registrada:**

```bash
# No servidor — verificar logs do Traefik
docker logs traefik --tail=20

# Ou via API do Traefik (se dashboard habilitado)
curl https://traefik.intellicare.ia.br/api/http/routers/gestor@file 2>/dev/null
```

**3. Testar o endpoint:**

```bash
curl -I https://gestor.intellicare.ia.br/api/v1/health
# Esperado: HTTP 200 ou 401 (autenticação necessária) — não 404
```

### Critério de aceite

- `https://gestor.intellicare.ia.br/api/v1/health` responde com HTTP 200 ou 401
- Navegador em `https://gestor.intellicare.ia.br/` **não** exibe 404

---

## Fix 2 — `portal.intellicare.ia.br` usa realm `intellicare`

### Causa

O container `intellicare-portal` em produção está executando uma imagem Docker compilada com uma versão antiga do código, anterior à correção do arquivo `authService.ts`. Nessa versão antiga, o fallback do realm era `'intellicare'`. O arquivo `.env.production` já possui o valor correto (`VITE_KEYCLOAK_REALM=bemcuidar`), mas como variáveis `VITE_*` são compiladas ("baked") no bundle pelo Vite em tempo de build — não em runtime — a imagem antiga ainda carrega o realm errado.

**Arquivo corrigido no repositório:**
`intellicare-portal/frontend/src/services/authService.ts`

```ts
// Linha corrigida (antes era || 'intellicare')
const REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar'
```

**Variável correta em `.env.production`:**

```env
VITE_KEYCLOAK_REALM=bemcuidar
VITE_KEYCLOAK_URL=https://auth.intellicare.ia.br
VITE_KEYCLOAK_CLIENT_ID=intellicare-portal
```

### Passos para deploy

**1. No servidor de produção, entrar no diretório do projeto:**

```bash
cd /caminho/para/intellicare
# (ajustar conforme o path real no servidor)
```

**2. Garantir que o repositório local está atualizado (pull das últimas correções):**

```bash
git pull origin main
# Ou o branch que está em produção
```

> Verificar que `intellicare-portal/frontend/src/services/authService.ts` tem `|| 'bemcuidar'`
> e que `intellicare-portal/frontend/.env.production` tem `VITE_KEYCLOAK_REALM=bemcuidar`

**3. Rebuildar apenas o container do portal (sem rebuild dos outros 13 módulos):**

```bash
docker compose -f docker-compose.full.yml build --no-cache portal
```

> `--no-cache` garante que o Vite recompila o bundle com os arquivos atuais, sem usar camadas de build anteriores.
> O build leva tipicamente 2–4 minutos.

**4. Reiniciar o container do portal:**

```bash
docker compose -f docker-compose.full.yml up -d --no-deps portal
```

> `--no-deps` evita reiniciar os outros 13 serviços de backend.

**5. Verificar os logs de inicialização:**

```bash
docker compose -f docker-compose.full.yml logs portal --tail=30
# Esperado: "nginx started" ou similar, sem erros
```

**6. Confirmar a correção no navegador:**

1. Abrir `https://portal.intellicare.ia.br`
2. Clicar em **Login**
3. A URL de redirect deve conter `/realms/bemcuidar/` — **não** `/realms/intellicare/`
4. Fazer login com um usuário válido do realm `bemcuidar`
5. Confirmar que o portal carrega corretamente após autenticação

### Critério de aceite

- URL do login Keycloak contém `/realms/bemcuidar/protocol/openid-connect/auth`
- Login com usuário do realm `bemcuidar` funciona e redireciona para o portal
- Token JWT retornado tem `"iss": "https://auth.intellicare.ia.br/realms/bemcuidar"`

---

## Info — `admin.intellicare.ia.br` (sem ação necessária)

O comportamento atual de `admin.intellicare.ia.br` está **correto por design**. O Traefik roteia este subdomínio para o módulo Python `intellicare-admin` (porta 8010), que possui sua própria interface HTML (`dashboard.html`) com autenticação via Keycloak.js (realm `bemcuidar`, clientId `intellicare-admin`).

A tela com os 3 botões que foi observada é o dashboard deste módulo:
- **OpenAPI/Docs** — link para a documentação Swagger do módulo
- **Copiar bearer token** — utilitário para testes de API
- **Sair** — logout via Keycloak

O React Admin Dashboard (mencionado no roadmap como V2.0.2) é uma tarefa futura e não está implementado ainda. **Não há bug aqui — nenhuma ação necessária.**

---

## Ordem de execução recomendada

```
1. Fix 1 (gestor) — 2 min, sem downtime, sem reinicialização
2. Fix 2 (portal) — 5–8 min, portal fica indisponível durante o rebuild/restart
```

Para minimizar impacto, executar o Fix 2 em horário de baixo uso (ex: fora do horário comercial).

---

## Rollback

**Fix 1 (gestor):** Reverter o arquivo `routes-intellicare.yml` para a versão anterior e recopiar para o servidor. Traefik aplica em segundos.

**Fix 2 (portal):** Não é possível "desfazer" o rebuild automaticamente. Se necessário, fazer rebuild novamente usando o commit anterior:

```bash
git checkout <commit-hash-anterior> -- intellicare-portal/frontend/src/services/authService.ts
docker compose -f docker-compose.full.yml build --no-cache portal
docker compose -f docker-compose.full.yml up -d --no-deps portal
```

---

*Especificação gerada automaticamente com base na análise de código e configuração do ambiente de produção.*
