# DEM-006 — Atualização e Validação dos Containers Docker Locais

| Campo | Valor |
|---|---|
| **ID** | DEM-006 |
| **Título** | Atualizar e validar todos os containers Docker do ambiente local de desenvolvimento |
| **Módulos** | docker-compose.yml · docker-compose.full.yml · todos os Dockerfiles |
| **Prioridade** | 🔴 CRÍTICO — sem ambiente local, devs trabalham em staging |
| **Status** | CONCLUÍDO |
| **Data abertura** | 2026-03-08 |

---

## 1. O que é

Esta demanda garante que qualquer desenvolvedor do IntelliCare consiga subir toda a plataforma na própria máquina com um único comando (`docker-compose -f docker-compose.full.yml up -d`) — e que o resultado seja idêntico ao que roda em staging.

Os containers Docker locais estavam desatualizados e isso transformou staging em ambiente de desenvolvimento compartilhado: instável, com código de múltiplos devs ao mesmo tempo, impossível de usar para revisões confiáveis.
Esta demanda restaurou o fluxo correto de dependências locais (e consertou o repasse de build context do `intellicare-core` nativo).

---

## 2. Escopo Entregue

1. **Todos os `Dockerfile`s revisados e atualizados** — os contextos de dependências do Python resolvidos passando explicitamente no builder via Root.
2. **`docker-compose.yml` e `docker-compose.full.yml` funcionando** — todos os 14 módulos (os 13 backend FastAPI + bridge) e infra sobem em sintonia.
3. **Smoke tests remapeados** — `scripts/smoke_test.sh`, `scripts/smoke_tests.py` e `check_demo_health.ps1` foram atualizados para incorporar toda a grid de API com o endpoint `/api/v1/health`.

---

## 3. Log de Execução

- **Diagnóstico OOM:** Devido aos OOM crashes e CPU overload locais no daemon do Docker Desktop no Windows devido ao excessivo "transferring context", o build foi realizado de maneira iterativa. As instalações usando Poetry ou PIP em arquivos "wheel" nativos para Pandas e Pyarrow rodaram sem falhas. 
- **Conflito de Redes Resolvido:** O `docker network rm` em conjunto com um `system prune` resolveram a quebra da overlay network `intellicare-network` legada durante o up dos containers.
- **Microserviços validados (14 nodes FastAPI)**:
  - Florence (8001), Oswaldo (8002), Donabedian (8003)
  - Wanda (8004), Comunicacao (8005), Geralda (8006)
  - Zilda (8007), Minerva (8008), Pierre (8009)
  - Admin (8010), Gestor (8011), Grahame (8012), Nise (8013)
  - Bridge (8014)
- **Consolidação Documental:** Efetuada a refatoração do DEM-006 para atender o Document Standard V2 (`PROPOSTA_ESTRUTURA_DOCUMENTACAO`).
