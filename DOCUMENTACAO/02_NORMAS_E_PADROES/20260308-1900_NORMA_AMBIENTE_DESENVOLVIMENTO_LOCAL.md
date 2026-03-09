# NORMA — Ambiente de Desenvolvimento Local

**Vigência:** a partir de 2026-03-08
**Aplica-se a:** todos os desenvolvedores do IntelliCare
**Criado por:** Eduardo + Claude
**Motivação:** containers locais estavam desatualizados ou inexistentes — devs trabalhavam diretamente em staging, causando instabilidade constante no ambiente de revisão.
**Status:** 🔴 OBRIGATÓRIO

---

## Regra fundamental

> **Todo desenvolvimento acontece localmente.**
> Staging recebe código apenas via merge de PR revisado e aprovado.
> Nenhum dev acessa staging para testar código em andamento.

---

## Fluxo correto

```
Dev clona/atualiza repositório
    ↓
Dev sobe stack local (docker-compose ou make)
    ↓
Dev trabalha na branch feature/fix
    ↓
Testa localmente (http://localhost:80XX)
    ↓
Abre PR → Claude + Eduardo revisam
    ↓
Merge em staging → GitHub Actions deploya
    ↓
Staging estável para revisão e demonstração
```

---

## O que cada ambiente é

| Ambiente | Propósito | Quem acessa | Como chega código |
|---|---|---|---|
| **Local** | desenvolvimento e testes do dev | Dev (somente ele) | direto na máquina |
| **Staging** | revisão de entregas, demos | Eduardo + Claude + devs (leitura) | apenas via PR mergeado |
| **Production** | clientes reais | usuários finais | apenas via release aprovado |

### O que staging NÃO é
- ❌ Não é ambiente de desenvolvimento
- ❌ Não é onde o dev testa suas alterações
- ❌ Não é onde o dev faz push direto para "ver funcionando"
- ❌ Não é substituto para rodar localmente

---

## Setup do ambiente local

### Pré-requisitos

```
Docker Desktop (Windows) — versão atual
Docker Compose v2
Git
Python 3.11+
Node.js 20+
```

### Subindo a infra mínima (banco + cache + métricas)

```bash
# Na raiz do projeto (C:\Users\egara\INTELLICARE)
docker compose up -d
# Sobe: PostgreSQL 15 (5432) · Redis 7 (6379) · Prometheus (9090) · Grafana (3000)
```

### Subindo o stack completo (todos os 13 módulos + portal)

```bash
docker compose -f docker-compose.full.yml up -d
```

### Atalhos Windows

```powershell
.\start_demo.bat         # Inicia todos os serviços
.\kill_demo.bat          # Para todos os serviços
.\check_demo_health.ps1  # Verifica saúde de todos os endpoints
```

### Smoke test (verificar que tudo subiu corretamente)

```bash
bash scripts/smoke_test.sh
# ou
python scripts/smoke_tests.py
```

---

## Portas locais dos módulos

| Módulo | Porta local | URL health |
|---|---|---|
| FLORENCE | 8001 | http://localhost:8001/api/v1/health |
| OSWALDO | 8002 | http://localhost:8002/api/v1/health |
| DONABEDIAN | 8003 | http://localhost:8003/api/v1/health |
| WANDA | 8004 | http://localhost:8004/api/v1/health |
| COMUNICACAO | 8005 | http://localhost:8005/api/v1/health |
| GERALDA | 8006 | http://localhost:8006/api/v1/health |
| ZILDA | 8007 | http://localhost:8007/api/v1/health |
| MINERVA | 8008 | http://localhost:8008/api/v1/health |
| PIERRE | 8009 | http://localhost:8009/api/v1/health |
| ADMIN | 8010 | http://localhost:8010/api/v1/health |
| GESTOR | 8011 | http://localhost:8011/api/v1/health |
| GRAHAME | 8012 | http://localhost:8012/api/v1/health |
| NISE | 8013 | http://localhost:8013/api/v1/health |
| BRIDGE (stub) | 8014 | http://localhost:8014/api/v1/health |
| Portal | 3001 | http://localhost:3001 |
| Admin Frontend | 3003 | http://localhost:3003 |
| Grafana | 3000 | http://localhost:3000 |
| Keycloak | 8080 | http://localhost:8080 |

---

## Rodando um módulo individualmente (desenvolvimento ativo)

Quando um dev está trabalhando em um módulo específico, pode subir só aquele
módulo fora do Docker para ter hot-reload:

```bash
# Exemplo: trabalhar no intellicare-admin
cd intellicare-admin
pip install -e ../intellicare-core -e ../intellicare-auth -e ".[dev]"
uvicorn admin.api.app:app --reload --port 8010

# O resto da stack (outros módulos + infra) fica rodando via docker compose
```

---

## Atualizando os containers após mudanças

Após qualquer merge em staging que altere um módulo:

```bash
# Rebuild do módulo específico
docker compose -f docker-compose.full.yml build intellicare-admin
docker compose -f docker-compose.full.yml up -d intellicare-admin

# Rebuild completo (quando mudar intellicare-core ou dependências base)
docker compose -f docker-compose.full.yml build
docker compose -f docker-compose.full.yml up -d
```

---

## Checklist antes de abrir PR

O dev deve confirmar que todos estes itens passam **localmente** antes de abrir PR:

```
[ ] docker compose up -d → infra sobe sem erro
[ ] módulo em desenvolvimento sobe sem erro (uvicorn ou docker)
[ ] GET /api/v1/health → 200
[ ] make test → todos os testes passando
[ ] make lint → sem erros
[ ] make typecheck → sem erros (módulos Python)
[ ] npm run test → passando (módulos frontend)
[ ] npm run lint → sem erros (módulos frontend)
[ ] funcionalidade testada manualmente no browser/Postman
[ ] nenhum print/console.log de debug esquecido
[ ] nenhuma credencial hardcoded
```

---

## O que NÃO fazer

| Proibido | Por quê |
|---|---|
| Push direto para `staging` | Quebra o ambiente de revisão para todos |
| Push direto para `main` | Vai para produção sem revisão |
| Testar código em staging antes do PR | Staging não é ambiente de dev |
| Commitar `.env` ou secrets | Expõe credenciais no repositório |
| Deixar containers locais desatualizados | Causa divergência com staging, bugs difíceis de reproduzir |
| Trabalhar sem rodar os testes localmente | PR com testes quebrados desperdiça tempo de revisão |

---

## Responsabilidades

| Quem | O quê |
|---|---|
| **Dev** | Manter containers locais atualizados; testar localmente antes do PR |
| **Eduardo** | Revisar PRs antes do merge em staging; não aprovar PR sem teste local confirmado |
| **Claude** | Criar branches antes de repassar ao dev; revisar código no PR; garantir que spec define ambiente esperado |
| **Todos** | Reportar imediatamente se staging estiver instável — não é normal e deve ser investigado |
