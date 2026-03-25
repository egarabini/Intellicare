# DEM-090 — Plano de Execução

> ⚠️ **Obrigatório:** crie `04_DIARIO.md` nesta pasta antes de começar e preencha durante a execução. Crie `05_FINALIZACAO.md` ao entregar. O hash **não será registrado no dashboard** sem esses dois arquivos com conteúdo real.

## Responsável: DEV-1

## Pré-requisito

DEM-087, DEM-088 e DEM-089 commitadas e em origin/main.

## Passos

1. **git pull origin main** — confirmar todos os commits da sprint presentes
2. **Verificar migrations pendentes** — 024 deve estar na lista
3. **Rebuild `--no-deps intellicare-service`** — aplicar novas rotas e código
4. **Aplicar migration 024** — via migrator ou startup automático
5. **Smoke JWT** — token local → `/identity/pessoas` → 200 (confirma DEM-087)
6. **Smoke Traefik** — token público → `https://intellicare.ia.br/api/identity/pessoas` → 200/409
7. **Smoke professional** — criar profissional com CPF → confirmar `pessoa_id` preenchido
8. **Smoke reconcile** — `POST /identity/admin/reconcile` → relatório limpo
9. **Smoke AdminUI identity page** — navegar `/admin-ui/identity` → carrega
10. **Escrever 6 testes** e commitar
11. **Push e confirmar origin/main atualizado**

## Commit esperado

```
chore(staging): sync 2026-05-23 — identity expansion complete (DEM-090)

- migration 024 applied: professionals.pessoa_id
- JWT issuer delta closed: token local 200 ✅
- Traefik identity route closed: public 200 ✅
- Professional identity smoke ✅
- Reconciliation endpoint smoke ✅
- AdminUI identity page ✅
- 6 testes staging smoke
```
