---
tipo: especificacao-tecnica
demanda: DEM-046
titulo: CI/CD Pipeline — GitHub Actions
---

# DEM-046 — Especificação Técnica

## Arquivo principal: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]

jobs:
  test-backend:
    name: pytest — Backend
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Instalar dependências de sistema (weasyprint)
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
            libffi-dev shared-mime-info

      - name: Configurar Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Instalar dependências Python
        run: |
          pip install -e "packages/intellicare-core[dev]"

      - name: Rodar pytest
        run: |
          pytest packages/intellicare-core/tests/ -q --tb=short \
            --co -q 2>/dev/null | tail -5 || true
          pytest packages/intellicare-core/tests/ -q --tb=short
        env:
          PYTHONPATH: ${{ github.workspace }}

  build-frontend-gestor:
    name: Build — GestorUI
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configurar Node 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/GestorUI/package-lock.json

      - name: Instalar dependências
        working-directory: frontend/GestorUI
        run: npm install

      - name: Build
        working-directory: frontend/GestorUI
        run: npm run build
        env:
          NODE_OPTIONS: '--max-old-space-size=4096'

  build-frontend-clinico:
    name: Build — ClinicoUI
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configurar Node 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/ClinicoUI/package-lock.json

      - name: Instalar dependências
        working-directory: frontend/ClinicoUI
        run: npm install

      - name: Build
        working-directory: frontend/ClinicoUI
        run: npm run build
        env:
          NODE_OPTIONS: '--max-old-space-size=4096'
```

---

## Bloco 2 — Badge no README

Criar ou atualizar `README.md` na raiz do repositório:

```markdown
# IntelliCare V3

[![CI](https://github.com/egarabini/INTELLICARE/actions/workflows/ci.yml/badge.svg)](https://github.com/egarabini/INTELLICARE/actions/workflows/ci.yml)

> Healthcare platform — FastAPI + React 18/Mantine UI 7 + PostgreSQL schema-per-tenant
```

⚠️ Ajustar `egarabini/INTELLICARE` para o endereço real do repositório GitHub.

---

## Bloco 3 — Verificações antes de commitar

```bash
# Verificar se os testes passam localmente antes do CI
pytest packages/intellicare-core/tests/ -q --tb=short

# Verificar se o build do GestorUI passa
cd frontend/GestorUI && NODE_OPTIONS="--max-old-space-size=4096" npm run build

# Verificar se há package-lock.json (necessário para cache no CI)
ls frontend/GestorUI/package-lock.json
ls frontend/ClinicoUI/package-lock.json
```

Se `package-lock.json` não existir, gerar com `npm install --package-lock-only`
ou usar `cache-dependency-path: frontend/GestorUI/package.json` no workflow.
