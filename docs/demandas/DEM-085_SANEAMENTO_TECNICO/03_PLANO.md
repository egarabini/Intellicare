---
tipo: plano-execucao
demanda: DEM-085
titulo: Saneamento Técnico
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-085 — Plano de Execução

## Estimativa

Tempo estimado: ~3h | Complexidade: baixa-média

Quatro itens independentes — podem ser tratados em paralelo pelo DEV-1 (itens 2, 3, 4) e pelo CODEX (item 1). Nenhum item bloqueia o outro.

---

## Ordem de execução

### Bloco 1 — Auditoria Git (CODEX executa em paralelo com DEV-1)
1. CODEX executa diagnóstico `origin/main..HEAD` (ver `02_TECNICA.md §1`)
2. CODEX cria `docs/saneamento/AUDITORIA_GIT_2026_05_16.md` com classificação de cada commit
3. CODEX reporta ao ARQUITETO antes de qualquer cherry-pick ou descarte
4. Após aprovação: resolver o delta (cherry-pick aprovados, descartar resto)
5. Confirmar: `git log origin/main..HEAD` retorna vazio

### Bloco 2 — Redis auth (DEV-1, 45min)
6. Executar diagnóstico de senhas (ver `02_TECNICA.md §2`)
7. Identificar variável conflitante em `.env.staging` ou `docker-compose.yml`
8. Aplicar fix e reiniciar `careplanner-worker`
9. Smoke: 60s de logs sem `invalid username-password pair`

### Bloco 3 — `clinical_notes` FK fix (DEV-1, 30min)
10. Verificar tipo atual: `\d demo.clinical_notes`
11. Verificar se há dados em `encounter_id`: `SELECT COUNT(*) FROM demo.clinical_notes WHERE encounter_id IS NOT NULL`
12. Criar `023_fix_clinical_notes_encounter_id.sql` com a abordagem adequada
13. Testar em banco de staging
14. Confirmar: `\d demo.clinical_notes` → `encounter_id UUID`

### Bloco 4 — `test_patient_response` (DEV-1, 15min)
15. `pytest tests/ -k "test_patient_response" -v` — identificar exatamente qual assertion falha
16. Localizar field rename no schema e corrigir o test
17. `pytest tests/ -k "test_patient_response" -v` → PASSED

### Bloco 5 — Integração e commit (30min)
18. `pytest -x` — suite completa sem falhas
19. Commit único com todos os 4 itens:
```
chore(saneamento): Redis auth fix, clinical_notes UUID, test_patient_response, git audit
```

---

## Entrega

```
chore(saneamento): Redis auth CarePlanner, clinical_notes encounter_id UUID, test fix, git audit
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.

**Nota:** o relatório de auditoria git (Item 1) é entregue pelo CODEX ao ARQUITETO ANTES do commit final. O commit da DEM-085 inclui apenas o arquivo `AUDITORIA_GIT_2026_05_16.md` com o relatório — não inclui cherry-picks não aprovados.
