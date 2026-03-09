# DEMANDA: Fix dos Subdomínios de Produção

---

## METADADOS

| Campo | Valor |
|---|---|
| **ID** | DEM-001 |
| **Status** | `EM_REVISAO` |
| **Módulo(s)** | `intellicare-portal` · `traefik` |
| **Branch** | `fix/infra-subdominios-producao` |
| **Dev responsável** | @infra |
| **Criado por** | Claude + Eduardo |
| **Data criação** | 2026-03-07 |
| **Data início dev** | 2026-03-07 |
| **Data conclusão** | — |
| **Spec funcional** | [SPEC-URL-FIXES.md](../../SPEC-URL-FIXES.md) |
| **PR** | — |
| **Deploy staging** | — |

---

## 1. CONTEXTO E MOTIVAÇÃO

Ao testar os subdomínios de produção após a migração do Keycloak para o realm `bemcuidar`,
foram identificados 3 problemas que impedem o acesso correto ao portal e ao módulo gestor.
Os usuários que tentam fazer login no portal são redirecionados para o realm errado
(`intellicare`, que não existe), resultando em falha de autenticação total.

---

## 2. ESCOPO APROVADO

### O que será feito (in-scope)

- [ ] Rebuild do container `intellicare-portal` no servidor com imagem atualizada
- [ ] Deploy do arquivo `traefik/dynamic/routes-intellicare.yml` com router para `gestor.intellicare.ia.br`

### O que NÃO será feito (out-of-scope)

- React Admin Dashboard — V2.0.2 (tarefa futura)
- Alterações no Keycloak — realm `bemcuidar` já está correto

### Critérios de aceite

- [ ] `https://portal.intellicare.ia.br` → login redireciona para `/realms/bemcuidar/`
- [ ] Login com usuário do realm `bemcuidar` funciona e retorna ao portal autenticado
- [ ] `https://gestor.intellicare.ia.br/api/v1/health` responde HTTP 200 ou 401 (não 404)
- [ ] `https://www.intellicare.ia.br` continua redirecionando para portal

### Arquivos principais esperados

```
traefik/dynamic/routes-intellicare.yml   → router gestor.intellicare.ia.br adicionado
intellicare-portal/frontend/             → rebuild da imagem Docker (sem alteração de código)
```

---

## 3. LOG DE EXECUÇÃO

### STEP-001 — Adicionar router Traefik para gestor.intellicare.ia.br

**Data/hora:** 2026-03-07 17:03
**Dev:** Claude (pré-executado na análise)

**O que foi feito:**
Adicionado bloco de router `gestor` no arquivo `traefik/dynamic/routes-intellicare.yml`,
apontando para o serviço `gestor-svc` que já existia na seção de services do mesmo arquivo.

**Arquivos alterados/criados:**
```
traefik/dynamic/routes-intellicare.yml   → adicionado router gestor antes do router portal
```

**Decisões técnicas tomadas:**
O `gestor-svc` já estava definido (usado pela rota `api.intellicare.ia.br/v1/gestor`).
Reutilizado em vez de criar novo service. Middleware `api-chain` aplicado — mesmo padrão
dos outros módulos backend.

**Problemas encontrados:** Nenhum.

**Como foi resolvido:** N/A

---

### STEP-002 — Rebuild do container portal no servidor

**Data/hora:** — (a executar pelo dev)
**Dev:** @infra

**O que foi feito:** [DEV PREENCHE após executar]

**Arquivos alterados/criados:**
```
# Nenhum arquivo de código alterado — apenas rebuild da imagem Docker
# A correção (authService.ts e .env.production) já estava no repositório
```

**Decisões técnicas tomadas:** [DEV PREENCHE]

**Problemas encontrados:** [DEV PREENCHE]

**Como foi resolvido:** [DEV PREENCHE]

---

### STEP-003 — Deploy do routes-intellicare.yml no servidor

**Data/hora:** — (a executar pelo dev)
**Dev:** @infra

**O que foi feito:** [DEV PREENCHE — registrar scp executado e confirmação do Traefik]

**Arquivos alterados/criados:**
```
/etc/traefik/dynamic/routes-intellicare.yml   → no servidor de produção
```

**Decisões técnicas tomadas:**
Traefik aplica automaticamente via file watcher — sem restart necessário.

**Problemas encontrados:** [DEV PREENCHE]

**Como foi resolvido:** [DEV PREENCHE]

---

## 4. REVISÃO

### Checklist de revisão

- [ ] Escopo aprovado foi completamente implementado
- [ ] Critérios de aceite verificados
- [ ] Nenhum arquivo fora do escopo foi alterado
- [ ] Log de execução preenchido
- [ ] Sem credenciais ou dados sensíveis no código

### Observações da revisão

Aguardando dev concluir STEPs 002 e 003.

### Resultado

- [ ] Aprovado para PR e deploy
- [ ] Aprovado com ressalvas
- [ ] Reprovado

---

## 5. PR E DEPLOY

| Campo | Valor |
|---|---|
| **Branch origem** | `fix/infra-subdominios-producao` |
| **Branch destino** | `staging` |
| **PR número** | — |
| **PR criado por** | Claude |
| **PR aprovado por** | Eduardo |
| **Deploy em** | — |
| **Smoke test** | — |

---

## 6. APRENDIZADOS E REFERÊNCIA FUTURA

### O que funcionou bem
- Traefik file provider permite adicionar rotas sem downtime ou restart.
- `git reset --hard origin/$BRANCH` no deploy.yml protege contra edições diretas no servidor.

### O que pode melhorar
- `VITE_KEYCLOAK_*` deveriam ser passadas explicitamente como build args no `docker-compose.full.yml`.
- Smoke test deveria verificar o realm retornado pelo portal após deploy.

### Referências para specs futuras
- Toda nova rota Traefik vai em `traefik/dynamic/routes-intellicare.yml` — nunca via Docker labels.
- Container portal precisa `--no-cache` sempre que `authService.ts` ou `.env.production` mudar.
- `gestor.intellicare.ia.br` → `intellicare-gestor:8011` via `gestor-svc`.

---

*Template: docs/NORMAS_E_PADROES/20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md*
