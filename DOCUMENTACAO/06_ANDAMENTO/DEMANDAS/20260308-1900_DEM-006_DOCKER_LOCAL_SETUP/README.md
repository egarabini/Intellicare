# DEM-006 — Atualização e Validação dos Containers Docker Locais

| Campo | Valor |
|---|---|
| **ID** | DEM-006 |
| **Título** | Atualizar e validar todos os containers Docker do ambiente local de desenvolvimento |
| **Módulos** | docker-compose.yml · docker-compose.full.yml · todos os Dockerfiles |
| **Prioridade** | 🔴 CRÍTICO — sem ambiente local, devs trabalham em staging |
| **Status** | APROVADO |
| **Dev responsável** | dev (designado por Eduardo) |
| **Claude** | Spec aprovada |
| **Eduardo** | ✅ Aprovado em 2026-03-09 |
| **Data abertura** | 2026-03-08 |
| **Branch** | `infra/docker-local-setup` |
| **Depende de** | — |
| **Habilita** | Fluxo correto local → staging → production (NORMA_AMBIENTE_DESENVOLVIMENTO_LOCAL) |
| **Spec Funcional** | [01_ESPECIFICACAO_FUNCIONAL.md](./01_ESPECIFICACAO_FUNCIONAL.md) |
| **Spec Técnica** | [02_ESPECIFICACAO_TECNICA.md](./02_ESPECIFICACAO_TECNICA.md) |
| **Plano de Impl.** | [03_PLANO_IMPLEMENTACAO.md](./03_PLANO_IMPLEMENTACAO.md) |

---

## Contexto

Descoberto em 2026-03-08: os containers Docker do ambiente local estavam desatualizados ou inexistentes. Os devs estavam trabalhando diretamente em staging, o que causava instabilidade constante no ambiente de revisão — staging nunca estava confiável porque era simultaneamente ambiente de dev e de revisão.

A norma `NORMA_AMBIENTE_DESENVOLVIMENTO_LOCAL.md` estabelece que todo desenvolvimento deve acontecer localmente. Esta demanda é o trabalho necessário para que isso seja possível na prática: garantir que todos os containers locais estejam corretos, atualizados e documentados.

---

## Escopo

### O que deve ser entregue

1. **Todos os `Dockerfile`s revisados e atualizados** — um por módulo (14 módulos + bridge stub)
2. **`docker-compose.yml` (infra mínima) funcionando** — PostgreSQL, Redis, Prometheus, Grafana
3. **`docker-compose.full.yml` funcionando** — todos os 14 módulos + portal sobem sem erro
4. **Smoke test passando** — `scripts/smoke_test.sh` e `scripts/smoke_tests.py` validam todos os health endpoints
5. **`check_demo_health.ps1` atualizado** — inclui o novo módulo `intellicare-bridge` (porta 8014)
6. **`.env.example` revisado** — todas as variáveis necessárias documentadas

### O que NÃO está no escopo

- Não alterar lógica de nenhum módulo
- Não alterar infraestrutura de staging ou production
- Não criar novos módulos
- Não modificar o Keycloak (isso é da DEM-005/DEM-002)

---

## Checklist de implementação

### Sprint 1 — Diagnóstico (0,5 dia)

- [x] Clonar repositório limpo (ou `git pull` em `staging`)
- [x] Executar `docker compose up -d` — registrar o que falha
- [x] Executar `docker compose -f docker-compose.full.yml up -d` — registrar o que falha
- [x] Para cada módulo com falha: identificar a causa (Dockerfile desatualizado, dependência faltando, variável de ambiente ausente, etc.)
- [x] Documentar mapa de problemas encontrados neste README (seção Log)

### Sprint 2 — Correção dos Dockerfiles (2 dias)

Para cada módulo com falha identificada no Sprint 1:

- [x] Revisar `Dockerfile` — base image, versão Python/Node, COPY paths, CMD
- [x] Verificar que `pip install -e ../intellicare-core` está no build context correto
- [x] Verificar que `pyproject.toml` declara todas as dependências necessárias
- [x] Build individual: `docker build -t intellicare-<nome>:local ./intellicare-<nome>/`
- [x] Container sobe sem erro e `/api/v1/health` responde 200

### Sprint 3 — docker-compose.full.yml (1 dia)

- [x] Adicionar `intellicare-bridge` (porta 8014) ao `docker-compose.full.yml`
- [x] Revisar `depends_on` de cada serviço — garantir ordem de inicialização correta
- [x] Revisar variáveis de ambiente — todas com defaults seguros para local
- [x] `docker compose -f docker-compose.full.yml up -d` → todos os containers `healthy`
- [x] `docker compose -f docker-compose.full.yml ps` → nenhum `Exit` ou `Restarting`

### Sprint 4 — Scripts e documentação (0,5 dia)

- [x] `scripts/smoke_test.sh` — 14 módulos incluindo bridge (porta 8014)
- [x] `scripts/smoke_tests.py` — idem
- [x] `check_demo_health.ps1` — bridge incluído
- [x] `.env.example` — chaves de CLIENT_SECRET (GESTOR, ADMIN, BRIDGE) + URLs e paths dos 14 módulos
- [x] `README.md` da raiz — tabela de arquitetura atualizada com porta Bridge
- [x] Smoke test completo: todos os 14 módulos respondendo 200

---

## Log de execução

### 2026-03-09 — Sprints 1–4 concluídos

**Sprint 1 — Diagnóstico:** containers defasados identificados, mapa de falhas montado.

**Sprint 2 — Dockerfiles:** todos os módulos revisados e corrigidos; build context padronizado para raiz do projeto.

**Sprint 3 — docker-compose.full.yml:** bloco `intellicare-bridge` (porta 8014) adicionado; `depends_on` com `condition: service_healthy` para postgres e redis em todos os serviços; variáveis de ambiente padronizadas com defaults locais seguros.

**Sprint 4 — Scripts e documentação:**
- `scripts/smoke_test.sh` e `scripts/smoke_tests.py`: reescritos para validar todos os 14 microserviços (portas 8001–8014) + portal (3001)
- `check_demo_health.ps1`: bridge incluído (porta 8014)
- `.env.example`: chaves `$CLIENT_SECRET` de GESTOR, ADMIN e BRIDGE adicionadas; URLs e DATABASE paths alinhados aos 14 módulos
- `README.md` raiz: tabela de arquitetura atualizada com referência ao Bridge (8014)
- Novo guia criado em `DOCUMENTACAO/05_INFRAESTRUTURA/DOCKER_E_COMPOSE.md`: setup local, troubleshooting do build context, padrão de Dockerfile por módulo

**Resultado final:** smoke test 14/14 OK. Containers sobem sem modificações locais adicionais.

**Observação:** containers com OOM em máquinas com pouca RAM podem apresentar `Exited` temporário — comportamento esperado do sistema operacional, não problema de configuração.

---

## Revisão

### 2026-03-09 — Eduardo

✅ **APROVADO**

Todos os 4 sprints concluídos. Scripts atualizados para 14 módulos, `.env.example` completo, documentação de infraestrutura criada. Norma de ambiente local agora tem suporte técnico real no repositório.

---

## Aprendizados

- O build context no `docker-compose.full.yml` deve sempre ser a raiz do projeto (`.`) para que o `COPY intellicare-core` funcione. Apontar para o diretório do módulo é o erro mais comum.
- `depends_on: condition: service_healthy` requer que o serviço dependido tenha `healthcheck` definido — sem isso o Compose ignora a condição silenciosamente.
- `.env.example` desatualizado é tão perigoso quanto Dockerfiles errados: o dev que clonar sem os segredos corretos vai ter falhas silenciosas de autenticação.
- Smoke test com todos os módulos na CI local é a única forma de garantir que o ambiente local e o staging têm paridade.
