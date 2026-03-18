---
tipo: plano-execucao
demanda: DEM-046
titulo: CI/CD Pipeline — GitHub Actions
status: pendente
dev: CODEX
criado: 2026-03-18
---

# DEM-046 — Plano de Execução

## Estimativa

Tempo estimado: 1h | Complexidade: baixa

Apenas criação de arquivos YAML e atualização de README. O risco principal
é o ambiente de CI não ter as libs de sistema do weasyprint — mitigado
com o `apt-get install` explícito no workflow.

---

## STEPs

### STEP-001 — Verificar estrutura do repositório GitHub

```bash
# Verificar se .github/workflows/ já existe
ls .github/workflows/ 2>/dev/null || echo "não existe — criar"

# Verificar endereço real do repositório (para o badge)
git remote -v
```

---

### STEP-002 — Criar `.github/workflows/ci.yml`

Conforme **Bloco 1** de `02_TECNICA.md`.

Atenção: verificar se `frontend/ClinicoUI/package-lock.json` existe.
Se não existir, remover o job `build-frontend-clinico` ou ajustar
`cache-dependency-path` para `package.json`.

Critério: arquivo criado e YAML válido (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` sem erros).

---

### STEP-003 — Criar/atualizar `README.md`

Conforme **Bloco 2** de `02_TECNICA.md`. Ajustar URL do badge com o
endereço real do repositório obtido no STEP-001.

---

### STEP-004 — Commit

```
ci: DEM-046 GitHub Actions workflow (pytest + build GestorUI + ClinicoUI)
```

Arquivos:
```
.github\workflows\ci.yml
README.md
docs\demandas\DEM-046_CI_CD_PIPELINE\
```

---

### STEP-005 — Validação (após push)

Após o commit ser enviado ao GitHub:
1. Acessar `https://github.com/<repo>/actions`
2. Verificar que o workflow `CI` aparece e passa nos 3 jobs
3. Reportar status ao Eduardo

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| weasyprint falha no CI mesmo com apt-get | Usar conftest skip condicional (já existe do DEM-INF) |
| Testes requerem PostgreSQL real | Verificar: se usam mocks, não precisa de service; adicionar service se necessário |
| `package-lock.json` ausente | Usar `package.json` no cache-dependency-path |
| URL do repositório incorreta no badge | STEP-001 verifica com `git remote -v` |
