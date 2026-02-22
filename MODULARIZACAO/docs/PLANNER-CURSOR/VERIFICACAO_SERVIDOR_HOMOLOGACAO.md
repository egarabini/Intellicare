# Verificação — Servidor de Homologação e v1.0.0

**Data:** 2026-02-20  
**Objetivo:** Conferir se está tudo ok para configuração do servidor; identificar gaps; criar plano de execução

---

## 1. O que está OK ✅

| Item | Status | Localização |
|------|--------|-------------|
| Documentação do servidor | ✅ Completa | `docs/SERVIDORES/` |
| Informações do servidor | ✅ Detalhadas | IP 167.86.97.142, 12 vCPU, 48 GB RAM |
| docker-compose.full.yml | ✅ Existe | 6 backends + portal + infra |
| .env.homologacao | ✅ Existe | Variáveis configuradas |
| deploy_homologacao.sh | ✅ Existe | Script de deploy automático |
| smoke_tests.py | ✅ Existe | Validação pós-deploy |
| GUIA_DEPLOY.md | ✅ Existe | Guia geral |
| SERVIDOR_HOMOLOGACAO_CONTABO.md | ✅ Completo | Passo a passo detalhado |
| Schemas PostgreSQL | ✅ No script | deploy_homologacao cria schemas |

---

## 2. O que precisa de atenção ⚠️

### 2.1 Crítico — Segurança

| Item | Problema | Ação |
|------|----------|------|
| **Senha em texto** | `SERVIDOR_HOMOLOGACAO_README.md` contém senha root (`Soeuso419863`) em texto plano | **Remover imediatamente** do documento; usar variável ou gerenciador de senhas; alterar senha no servidor após primeiro acesso |

### 2.2 Smoke tests — Script incorreto

| Item | Problema | Ação |
|------|----------|------|
| **smoke_tests.sh** | `deploy_homologacao.sh` (linha 155) chama `scripts/smoke_tests.sh` | O arquivo existente é `scripts/smoke_tests.py` | Corrigir deploy_homologacao.sh para chamar `python scripts/smoke_tests.py` ou criar wrapper `smoke_tests.sh` que invoca o .py |

### 2.3 Caminho do repositório

| Item | Problema | Ação |
|------|----------|------|
| **Path após clone** | SERVIDOR_HOMOLOGACAO_README diz `cd intellicare/MODULARIZACAO`; SERVIDOR_HOMOLOGACAO_CONTABO diz `cd intellicare/intellicare/MODULARIZACAO` | Verificar estrutura real do repo `eduardo/intellicare`; ajustar documentação conforme o path correto |

### 2.4 Dependências opcionais (Comunicacao)

| Item | Problema | Ação |
|------|----------|------|
| **Rocket.Chat, Jitsi** | .env.homologacao referencia `ROCKETCHAT_URL`, `JITSI_*` mas docker-compose.full.yml não inclui esses serviços | Comunicacao pode iniciar com features desabilitadas; validar se o módulo sobe sem eles ou se precisa de configuração mínima |

### 2.5 FHIR Server

| Item | Problema | Ação |
|------|----------|------|
| **INTELLICARE_FHIR_SERVER_URL** | .env referencia `http://fhir-server:8080/fhir` mas não há serviço fhir-server no docker-compose.full.yml | Módulos podem ter fallback; validar se Florence/Oswaldo/Donabedian sobem sem FHIR |

---

## 3. Dependência das Fases — Podemos configurar agora?

### Resposta direta

**Sim, podemos iniciar a configuração do servidor agora**, com ressalvas:

| Etapa | Depende de Fase 1? | Pode fazer agora? |
|-------|--------------------|-------------------|
| **1. Preparar servidor** (apt, Docker, firewall, SSH) | Não | ✅ Sim |
| **2. Clonar repositório** | Não | ✅ Sim |
| **3. Configurar .env** | Não | ✅ Sim |
| **4. Subir Postgres + Redis** | Não | ✅ Sim |
| **5. Build e subir backends** | **Sim** | ⚠️ Depende de Fase 1 |
| **6. Subir portal** | **Sim** | ⚠️ Depende de Fase 1 |
| **7. Smoke tests** | **Sim** | ⚠️ Após deploy |

### Explicação

- **Fase 1 (Estabilização):** Garante que a demo funciona localmente (venv, módulos sobem, sem crash). O `docker-compose.full.yml` faz **build** das imagens a partir do código. Se houver erros de build (Dockerfile quebrado, dependência faltando) ou se os módulos não estiverem estáveis, o deploy falhará.
- **Fase 2 (Git):** Não bloqueia o deploy; mas a tag v0.1.0-demo ou v1.0.0 ajuda a saber qual versão está no servidor.
- **Fases 3, 4, 5:** Não bloqueiam a primeira configuração.

### Recomendação

1. **Agora:** Executar etapas 1 a 4 (preparar servidor, clonar, .env, Postgres+Redis).
2. **Quando dev1 concluir Fase 1:** Executar etapas 5 a 7 (build, backends, portal, smoke tests).
3. **Alternativa:** Se dev1 estiver no “final” da Fase 1, pode-se tentar o deploy completo e tratar falhas como parte da validação.

---

## 4. Plano de Execução da Configuração

### Fase A — Preparação (pode fazer agora)

| # | Tarefa | Tempo | Responsável |
|---|--------|-------|-------------|
| A1 | Conectar ao servidor via SSH | 5 min | Ops |
| A2 | Atualizar sistema (`apt update && apt upgrade -y`) | 10 min | Ops |
| A3 | Instalar Docker e Docker Compose | 15 min | Ops |
| A4 | Configurar firewall (UFW) — portas 22, 80, 443, 3001, 8001-8006, 9090, 3000 | 10 min | Ops |
| A5 | Instalar Git, utilitários (curl, vim, htop) | 5 min | Ops |
| A6 | **Remover senha do SERVIDOR_HOMOLOGACAO_README** e alterar senha root no servidor | 10 min | Ops |
| A7 | Configurar SSH com chave (recomendado) | 15 min | Ops |
| A8 | Instalar Fail2Ban (opcional) | 5 min | Ops |

### Fase B — Clone e configuração (pode fazer agora)

| # | Tarefa | Tempo | Responsável |
|---|--------|-------|-------------|
| B1 | Criar diretório `/opt/intellicare` | 2 min | Ops |
| B2 | Clonar repositório `eduardo/intellicare` | 5 min | Ops |
| B3 | Navegar para diretório correto (verificar path) | 2 min | Ops |
| B4 | Copiar `.env.homologacao` para `.env` | 2 min | Ops |
| B5 | Revisar e ajustar senhas no `.env` (se necessário) | 10 min | Ops |

### Fase C — Infraestrutura (pode fazer agora)

| # | Tarefa | Tempo | Responsável |
|---|--------|-------|-------------|
| C1 | Subir Postgres e Redis: `docker-compose -f docker-compose.full.yml up -d postgres redis` | 5 min | Ops |
| C2 | Aguardar 30s e verificar health | 5 min | Ops |
| C3 | Criar schemas manualmente (se deploy_homologacao não for usado ainda) | 5 min | Ops |

### Fase D — Deploy completo (aguardar Fase 1 concluída)

| # | Tarefa | Tempo | Responsável |
|---|--------|-------|-------------|
| D1 | Corrigir deploy_homologacao.sh (smoke_tests.sh → smoke_tests.py) | 5 min | Dev |
| D2 | Executar `./scripts/deploy_homologacao.sh` | 30–60 min | Ops |
| D3 | Validar containers: `docker-compose -f docker-compose.full.yml ps` | 5 min | Ops |
| D4 | Executar smoke tests: `python scripts/smoke_tests.py --url http://167.86.97.142` | 5 min | Ops |
| D5 | Acessar portal e APIs via browser | 10 min | Ops |

### Fase E — Pós-configuração (após deploy OK)

| # | Tarefa | Tempo | Responsável |
|---|--------|-------|-------------|
| E1 | Configurar backup automático (cron) | 15 min | Ops |
| E2 | Documentar path correto do repositório | 5 min | Dev |
| E3 | Revisar e remover credenciais de documentos | 10 min | Ops |

---

## 5. Checklist de Fechamento v1.0.0

Para fechar v1.0.0 e ter homologação funcional:

- [ ] **Fase 1:** Dev1 conclui estabilização (demo local 100% funcional)
- [ ] **Correção:** deploy_homologacao.sh chama smoke_tests corretamente
- [ ] **Correção:** Remover senha do SERVIDOR_HOMOLOGACAO_README
- [ ] **Fase 2:** Tag v0.1.0-demo ou v1.0.0 criada (recomendado)
- [ ] **Deploy:** Executar Fases A, B, C, D no servidor
- [ ] **Validação:** Smoke tests passando, portal acessível

---

## 6. Resumo

| Pergunta | Resposta |
|----------|----------|
| Está tudo ok? | Quase. Há 2 correções necessárias (smoke_tests, senha em doc). |
| Falta algo? | Sim: corrigir smoke_tests no deploy script; remover senha do README. |
| Podemos configurar agora? | **Sim, parcialmente.** Fases A, B, C podem ser feitas agora. Fase D (build + backends + portal) depende da Fase 1 concluída. |
| Dependemos das 5 fases? | **Não.** Dependemos principalmente da **Fase 1** para o deploy completo. Fases 2–5 não bloqueiam a primeira configuração. |
