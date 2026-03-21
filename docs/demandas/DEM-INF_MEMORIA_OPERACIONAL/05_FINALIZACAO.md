# DEM-INF Memória Operacional — Finalização

## Status: ✅ CONCLUÍDA

- **Commit:** `7f708fb`
- **Mensagem:** `docs: DEM-INF memoria operacional - patterns, gotchas, HANDOFF template`
- **Entregador:** CODEX
- **Data:** 2026-03-21

---

## O que foi criado

### `docs/patterns/`

| Arquivo | Conteúdo |
|---|---|
| `README.md` | Índice e instruções de uso |
| `backend-modules.md` | Loader dinâmico de módulos, migrations idempotentes, seed no startup, crescimento do `CareplannerService.__init__` |
| `frontend-pages.md` | Padrões de hooks, páginas GestorUI e ClinicoUI, AuthProvider |
| `workers-webhooks.md` | Dispatcher Redis+retry, dead-letter, HMAC webhooks |

### `docs/gotchas/`

| Arquivo | Entradas reais |
|---|---|
| `careplanner.md` | 5 gotchas: fixture break por `__init__`, enum não basta, `rc_room_id` só RC, cross-tenant lookup, inbound órfão |
| `staging-deploy.md` | 6 gotchas: git push antes do deploy, `initdb.d` só no 1º boot, senha com `#` quebra URI, porta host ≠ porta container, segredo ausente, `letsencrypt/` suja working tree |
| `keycloak-auth.md` | Gotchas de OIDC/Keycloak já refletidos nos `AuthProvider.tsx` |

### `docs/demandas/_templates/HANDOFF.yml`

Template padronizado de contexto para transferência entre agentes e devs. Ancora estado atual, blockers, próximos passos e referências de código.

---

## Fora do escopo desta DEM

- Preenchimento do HANDOFF.yml com estado da sprint corrente — responsabilidade do arquiteto ao abrir cada sprint.
- Automation de geração de HANDOFF (possível futura DEM-INF).
- Gotchas de Kestra e Evolution API — não havia base suficiente de incidentes reais no momento da entrega.

---

## Como usar

### Antes de iniciar uma DEM

```bash
# Consulte padrões do domínio
cat docs/patterns/backend-modules.md
cat docs/gotchas/careplanner.md
```

### Ao encerrar uma sprint / trocar contexto

```bash
# Copie o template e preencha
cp docs/demandas/_templates/HANDOFF.yml docs/demandas/HANDOFF_<data>.yml
```

### Ao encontrar novo problema repetível

```bash
# Adicione entrada no gotcha correspondente
# Formato: ## Título curto / ### Situacao real / ### Sintoma / ### Fix
echo ">> nova entrada em docs/gotchas/<dominio>.md"
```

---

## Critérios de aceite — verificação final

- [x] `docs/gotchas/` com 3+ entradas reais ancoradas em DEMs reais
- [x] `docs/patterns/` com backend, frontend, workers
- [x] `HANDOFF.yml` template em `_templates/`
- [x] Sem TODOs ou placeholders nos arquivos entregues
- [x] Varredura textual executada pelo CODEX antes de commitar
