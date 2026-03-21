# DEM-064 — Staging Clinical Squad Validation — FINALIZAÇÃO

**Data de entrega:** 2026-03-21
**Dev responsável:** DEV-3/4 (CODEX)
**Commit final:** `af3e66bb`
**Sprint:** 2026-04-11

---

## Resumo executivo

Validação completa do Clinical Squad (Florence + Oswaldo + PDF Clínico + E2E) no ambiente de staging após 3 blockers resolvidos em série.

---

## Smoke tests aprovados

| Endpoint | Resultado |
|----------|-----------|
| `GET /florence/notes/encounter/1` (JWT válido) | `200 []` ✅ |
| `POST /oswaldo/suggest` `{"chief_complaint": "cefaleia intensa"}` | `200` — `cid10_code: "Z00"`, `model: "rule-based"` ✅ |
| `GET /cuidado/encounters/9e19223a-754d-45e0-aeb6-158ba52a8ac8/report.pdf` | `200` — `9035 bytes`, `%PDF` ✅ |
| `GET /instance/connectionState/intellicare` (Evolution API) | `state: "open"` ✅ |
| `GET /careplanner/health/adapters` | `200` ✅ |

---

## Blockers resolvidos (em ordem)

### P1 — Redis `ValueError: Port could not be cast to integer value as 'IC_Staging'`
- **Causa:** `redis_pubsub.py` interpolava `{s.redis_password}` diretamente na URL Redis. Senha contém `#`, que trunca a URL.
- **Fix:** Variável de ambiente `REDIS_PASSWORD_URLENC` com senha URL-encoded (`%23` em vez de `#`).
- **Commit:** `c7fabecc` — `fix(redis): usar REDIS_PASSWORD_URLENC em redis_pubsub.py`
- **Gotcha:** `docs/gotchas/staging-deploy.md` — entrada adicionada.

### P2 — ClinicoUI Docker build falha (`@tanstack/react-query` não pré-bundlado)
- **Causa:** Vite em contexto Docker/SSR não pré-bundlava `@tanstack/react-query` sem `optimizeDeps.include`.
- **Fix:** `frontend/ClinicoUI/vite.config.ts` — adicionado `optimizeDeps: { include: ['@tanstack/react-query'] }`.
- **Commit:** `055e883` — `fix(frontend): optimizeDeps react-query vite docker`
- **Tentativas descartadas:** remoção de `--prefer-offline`, `docker builder prune`, troca Node 18→20 (já era 20).

### P3 — Florence `500` no staging
- **Causa:** Commits `910f1ac` e `e369cdf` (fix Florence backend) estavam em `main` mas container não havia sido reconstruído (build travava no P2).
- **Resolução:** Desbloqueado automaticamente após P2 ser resolvido — próximo rebuild entrou no container com os fixes já presentes.
- **Smoke:** `GET /florence/notes/encounter/1` com JWT válido → `200 []`.

---

## Artefato de evidência

`deploy/staging_sync_log.txt` atualizado com:

```
=== 2026-03-21 — Clinical Squad Final Smoke ===
Florence  GET /florence/notes/encounter/1        200 []
Oswaldo   POST /oswaldo/suggest                  200 rule-based
PDF       GET /encontros/1/report.pdf            200 9035 bytes
WhatsApp  connectionState/intellicare            open
Adapters  GET /careplanner/health/adapters       200
```

---

## DEMs validadas neste smoke

| DEM | Módulo validado |
|-----|-----------------|
| DEM-055 | Florence Módulo Base |
| DEM-057 | Florence IA (rule-based fallback) |
| DEM-058 | Oswaldo Módulo Base |
| DEM-061 | Oswaldo IA (rule-based fallback) |
| DEM-062 | PDF Clínico (WeasyPrint, 9035 bytes) |
| DEM-053 | WhatsApp Evolution (`state: open`) |
| DEM-051 | Health adapters multicanal |

---

## Status pós-entrega

- Sprint 2026-04-11: **✅ Concluída** (4/4 DEMs entregues)
- Sprint 2026-04-04 DEM-060: **✅ Fechada** (mesmo staging sync)
- Próxima sprint: **2026-04-18** (DEM-065 a DEM-068, pendente planejamento)
