---
tipo: plano-execucao
demanda: DEM-078
titulo: Staging Sync 2026-05-02
status: em-execucao
dev: DEV-1
criado: 2026-03-22
---

# DEM-078 — Plano de Execução

## Estimativa

Tempo estimado: ~3h | Complexidade: média-alta

Mais complexo que stagings anteriores pela presença do Dify — infraestrutura nova que requer setup manual da interface web antes dos smoke tests. Reservar tempo extra para o download das imagens e primeiro boot do Dify.

---

## Pré-condições

- [ ] DEM-075 commit mergeado em `main` e push confirmado
- [ ] DEM-076 commit mergeado em `main` e push confirmado
- [ ] DEM-077 commit mergeado em `main` e push confirmado
- [ ] `.env.staging` atualizado com variáveis Marie (ver `02_TECNICA.md`)
- [ ] VPS com espaço livre suficiente: `df -h` — mínimo **4GB** (imagens Dify são ~2GB)

---

## Ordem de execução

### Bloco 1 — Pull e rebuild (30min)
1. `git pull origin main` — confirmar 3 commits do sprint
2. Adicionar variáveis Marie ao `.env.staging` (com senhas reais de staging)
3. `docker compose build api clinicoui pacienteui`
4. `docker compose up -d` — aguardar download das imagens Dify na primeira execução

### Bloco 2 — Validar containers Marie (20min)
5. `docker compose ps | grep marie` — 5 containers Up
6. `docker compose logs marie-api --tail=50` — sem erros de migration
7. Acessar Marie web (verificar porta) — tela de setup Dify aparece

### Bloco 3 — Configurar Dify (30min)
8. Criar conta admin Dify no staging
9. Criar workflow `cid10_rag` conforme `03_PLANO.md` DEM-075
10. Publicar workflow → gerar API Key
11. Adicionar `MARIE_API_KEY` ao `.env.staging` → `docker compose restart api`

### Bloco 4 — Smokes (45min)
12. Smoke interação medicamentosa (curl — ver `02_TECNICA.md` §4)
13. Smoke portal timeline do paciente (curl — §5)
14. Smoke receituário do paciente (curl — §6)
15. Smoke ClinicoUI banner de interação (manual — §8)
16. Smoke PacienteUI Meu Histórico + botão Baixar (manual)

### Bloco 5 — Suite de testes (20min)
17. `pytest tests/test_marie_client.py tests/test_portal_avancado.py tests/test_oswaldo_interactions.py -v`
18. Todos passando → staging aprovado

---

## Gotcha — Dify setup manual é necessário uma vez

O Dify não tem mecanismo de seed automático de workflows via API no bootstrap. O setup da conta + criação do workflow `cid10_rag` é **manual** na primeira vez. Nas próximas sincronizações de staging (quando o banco `marie-db` já existe), este passo é pulado.

Documentar a API Key gerada em local seguro (não commitar no repo).

---

## Gotcha — `MARIE_ENABLED=false` por default no staging também

O staging valida que o sistema funciona **sem** Marie (comportamento base) antes de testar com Marie habilitado. Manter `MARIE_ENABLED=false` durante os smokes do portal e interação — estes não dependem do Marie.

Só habilitar `MARIE_ENABLED=true` para o smoke específico do `cid10_rag` (opcional no staging inicial — pode ser feito como smoke de integração isolado).

---

## Gotcha — Conflito de merge esperado em `oswaldo/services.py`

DEM-075 (CODEX) e DEM-077 (DEV-1) ambos tocam `oswaldo/services.py`. Quem mergear por último faz `git pull --rebase` antes do push.

---

## Entrega

```
chore(staging): sync 2026-05-02 — Marie UP, interações, portal paciente smoke OK
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
