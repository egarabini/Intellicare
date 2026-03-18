---
tipo: especificacao-funcional
demanda: DEM-046
titulo: CI/CD Pipeline — GitHub Actions (pytest + Playwright + build)
sprint: "4.4"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-INF-weasyprint]
habilita: []
tags: [infra, ci, github-actions, pytest, playwright, p2]
---

# DEM-046 — CI/CD Pipeline (GitHub Actions)

## Objetivo

Hoje não há validação automática de PRs ou pushes. Os testes rodam manualmente
pelo desenvolvedor antes do commit. Esta DEM adiciona um workflow GitHub Actions
que roda pytest e build do GestorUI a cada push em qualquer branch, garantindo
que regressões sejam detectadas antes de chegar ao main.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-046 |
|------|------|---------|
| Testes rodam automaticamente em CI | ❌ | ✅ a cada push/PR |
| pytest global passa | ✅ (após fix weasyprint) | mantido + automático |
| Build GestorUI validado no CI | ❌ | ✅ `npm run build` |
| Relatório de cobertura | ❌ | ✅ `--cov` com summary no PR |
| Badge de status no README | ❌ | ✅ |

---

## Critérios de Aceite

1. Arquivo `.github/workflows/ci.yml` criado com jobs:
   - `test-backend`: instala dependências Python, roda
     `pytest packages/intellicare-core/tests/ -q --tb=short`
     — passa com os testes existentes (fases A–G + outros)
   - `build-frontend`: instala Node 20, roda `npm install && npm run build`
     no `frontend/GestorUI`

2. O workflow é disparado em `push` para qualquer branch e em `pull_request`
   para `main`.

3. `test-backend` usa PostgreSQL service do GitHub Actions para testes que
   requerem banco. Se os testes usam mocks (sem banco real), usar apenas
   `ubuntu-latest` sem service.

4. Falha em qualquer job bloqueia o merge (configurar como required check
   nas instruções — Eduardo ativa no GitHub Settings).

5. Badge `[![CI](https://github.com/.../.../actions/workflows/ci.yml/badge.svg)]`
   adicionado ao `README.md` (ou criado se não existir).

6. Playwright **não** entra no CI neste momento — requer servidor rodando
   localmente (complexidade alta para CI; fica como DEM futura).

---

## O que NÃO está incluído

- Deploy automático para staging (CD)
- Testes Playwright no CI
- Build dos outros frontends (ClinicoUI, AdminUI, PacienteUI) — apenas GestorUI
- Docker build no CI
- Notificação Slack/email em falha

---

## Notas para o Agente Desenvolvedor

- Verificar se o repositório GitHub está em `github.com/egarabini/INTELLICARE`
  ou outro endereço — ajustar o badge URL.

- Os testes Python **não usam banco real** (usam mocks e fixtures locais)?
  Verificar nos arquivos `test_careplanner_phase_*.py`. Se usarem `asyncpg`
  com banco real, adicionar service PostgreSQL:
  ```yaml
  services:
    postgres:
      image: postgres:16
      env:
        POSTGRES_PASSWORD: postgres
      ports: ['5432:5432']
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  ```

- weasyprint no CI: adicionar `apt-get install -y libpango-1.0-0 libcairo2
  libgdk-pixbuf-2.0-0` antes do `pip install` para garantir que weasyprint
  instala com sucesso no Ubuntu do CI (em vez de apenas skippar).

- `npm run build` do GestorUI pode precisar de `NODE_OPTIONS=--max-old-space-size=4096`
  (já documentado no Dockerfile). Adicionar como variável de ambiente no step.

- Usar cache de dependências:
  ```yaml
  - uses: actions/cache@v4
    with:
      path: ~/.npm
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
  ```
