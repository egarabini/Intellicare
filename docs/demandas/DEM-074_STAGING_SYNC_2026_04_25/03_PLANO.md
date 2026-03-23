---
tipo: plano-execucao
demanda: DEM-074
titulo: Staging Sync 2026-04-25
status: em-execucao
dev: CODEX
criado: 2026-03-21
---

# DEM-074 — Plano de Execução

## Estimativa

Tempo estimado: ~2h | Complexidade: baixa-média

Operação de infra — sem desenvolvimento. O risco principal é a migration 017 falhar por constraint ou seeds duplicados. Seguir checklist em sequência.

---

## Pré-condições

- [ ] DEM-071 commit mergeado em `main`
- [ ] DEM-072 commit mergeado em `main`
- [ ] DEM-073 commit mergeado em `main`
- [ ] Staging acessível (VPS + Docker Compose rodando)

---

## Ordem de execução

### Bloco 1 — Pull e pre-check (15min)
1. `git pull origin main` no VPS staging
2. Confirmar que os 3 commits do sprint estão presentes: `git log --oneline -5`
3. Verificar que migration 016 está aplicada: `alembic current` deve mostrar `016`
4. Checar espaço em disco: `df -h` — mínimo 2GB livre para rebuild

### Bloco 2 — Rebuild (30min)
5. `docker compose build api adminui clinicoui`
6. Aguardar conclusão sem erros de build
7. `docker compose up -d`
8. `docker compose ps` — todos containers `Up` (não `Restarting`)

### Bloco 3 — Migration (15min)
9. `docker compose exec api alembic upgrade head`
10. Verificar output: `Running upgrade 016 -> 017`
11. Verificar seeds: query na tabela `platform.prompt_templates` (ver `02_TECNICA.md`)

### Bloco 4 — Smoke tests (45min)
12. Smoke timeline (ver curl em `02_TECNICA.md` §3a)
13. Smoke receituário PDF (ver curl em `02_TECNICA.md` §3b)
14. Smoke prompt versioning API (ver curl em `02_TECNICA.md` §3c)
15. Smoke AdminUI manual — PromptsPage
16. Smoke ClinicoUI manual — Timeline + Botão Receituário

### Bloco 5 — Suite de testes (15min)
17. `pytest tests/test_timeline.py tests/test_receituario.py tests/test_prompt_versioning.py -v`
18. Todos passando → staging aprovado

---

## Gotcha — Seeds duplicados na migration 017

Se a migration 017 foi rodada parcialmente (teste local do CODEX antes do merge), os INSERTs dos seeds vão falhar com `UNIQUE constraint violation`.

Solução preventiva na migration:
```python
op.execute("""
    INSERT INTO platform.prompt_templates (slug, version, content, is_active, description)
    VALUES (...)
    ON CONFLICT (slug, version) DO NOTHING;  -- idempotente
""")
```

Se já falhou: rodar `alembic downgrade 016` + corrigir migration + `alembic upgrade head`.

---

## Gotcha — WeasyPrint e fontes no container

O símbolo `℞` pode não renderizar se as fontes DejaVu não estiverem no container. Testar PDF gerado **visualmente** antes de aprovar o smoke — abrir `/tmp/receituario_test.pdf` e verificar que o símbolo aparece.

Se não aparecer: instalar fontes no container (Dockerfile):
```dockerfile
RUN apt-get install -y fonts-dejavu-core
```

---

## Gotcha — AdminUI route 404

Se `http://staging-adminui/prompts` retornar 404, verificar se a rota foi adicionada ao React Router em `AdminUI/src/App.tsx`. Rebuild do container `adminui` sozinho:
```bash
docker compose build adminui && docker compose up -d adminui
```

---

## Entrega

```
chore(staging): sync 2026-04-25 — migration 017 + DEM-071/072/073 smoke aprovado
```
Hash → enviar para o ARQUITETO fechar DEM-074 e sprint 2026-04-25.
