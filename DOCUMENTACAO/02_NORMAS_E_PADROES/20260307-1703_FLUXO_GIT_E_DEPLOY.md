# Fluxo Git e Deploy — IntelliCare

Data: 2026-03-07
Versão: 1.0
Status: Ativo

---

## Princípio fundamental

> **O servidor de staging só recebe código via GitHub Actions.**
> Nenhum dev altera arquivos diretamente no servidor.
> O git é a única fonte de verdade.

---

## Branches

| Branch | Propósito | Quem faz push |
|---|---|---|
| `main` | Produção — código estável | Somente via PR aprovado de `staging` |
| `staging` | Ambiente de homologação | Somente via PR aprovado de feature branch |
| `feat/xxx` | Nova funcionalidade | Dev responsável pela demanda |
| `fix/xxx` | Correção de bug | Dev responsável pela demanda |
| `infra/xxx` | Infra, Docker, Traefik, CI | Dev de infra ou Eduardo |
| `docs/xxx` | Documentação | Qualquer dev |

### Regras de proteção (configuradas no GitHub)

- `main` e `staging`: push direto **bloqueado** para todos
- Todo código entra via Pull Request
- PR requer: CI verde (build + lint) + aprovação do CODEOWNER do módulo

---

## Nomenclatura de branches

```
tipo/modulo-descricao-curta
```

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat/gestor-kestra-fhir-sync` |
| `fix` | Correção de bug | `fix/portal-keycloak-realm` |
| `infra` | Docker, Traefik, CI/CD, scripts | `infra/traefik-gestor-subdomain` |
| `docs` | Documentação apenas | `docs/keycloak-smart-on-fhir` |
| `refactor` | Refatoração sem mudança de comportamento | `refactor/wanda-circuit-breaker` |

**Regras:** sempre minúsculas, palavras separadas por `-`, máximo ~50 caracteres.

---

## Fluxo completo passo a passo

```
1. ESPECIFICAÇÃO
   Eduardo + Claude definem escopo
   Claude gera: branch + ANDAMENTO_DEMANDA
        |
2. DESENVOLVIMENTO (DEV)
   git checkout -b feat/modulo-descricao
   → trabalha localmente
   → testa localmente (pytest / npm test)
   → preenche Log de Execução no ANDAMENTO_DEMANDA
   git push origin feat/modulo-descricao
        |
3. REVISÃO
   Dev avisa Eduardo: "DEM-NNN concluída"
   Eduardo + Claude revisam ANDAMENTO_DEMANDA
   Claude verifica diff do PR
   Eduardo aprova ou devolve com comentários
        |
4. PULL REQUEST (Claude executa)
   Claude cria PR: feat/xxx → staging
   CI roda automaticamente (build + lint + tests)
   Eduardo aprova o PR no GitHub
   Merge em staging
        |
5. DEPLOY AUTOMÁTICO (GitHub Actions)
   Push em staging → deploy.yml dispara
   git reset --hard origin/staging no servidor
   docker compose build + up do módulo afetado
   Smoke test automático
        |
6. VALIDAÇÃO
   Eduardo + Claude verificam em staging
   Status do ANDAMENTO_DEMANDA → DEPLOYED
   Índice de demandas atualizado
```

---

## O que o dev NUNCA deve fazer

| Proibido | Correto |
|---|---|
| Editar arquivo direto no servidor via SSH | Fazer commit e push — o Actions deploya |
| Push direto em `staging` ou `main` | Abrir PR a partir de feature branch |
| Criar branch sem demanda registrada | Criar branch somente após ANDAMENTO_DEMANDA gerado |
| Commitar sem testar localmente | Rodar `make test` ou `npm test` antes do push |
| Alterar módulo de outro dev sem comunicar | Verificar CODEOWNERS — o GitHub pedirá revisão |

---

## Comandos do dia a dia do dev

```bash
# Recebeu a branch da demanda — iniciar desenvolvimento
git fetch origin
git checkout feat/modulo-descricao

# Trabalho diário
git add caminho/arquivo.py
git commit -m "feat(modulo): descrição objetiva do que foi feito"
git push origin feat/modulo-descricao

# Sincronizar com staging (se demorar mais de 2 dias)
git fetch origin
git rebase origin/staging
git push origin feat/modulo-descricao --force-with-lease

# Verificar se os testes passam antes de avisar Eduardo
# Python:
make test
# Frontend:
npm test
```

### Padrão de mensagem de commit

```
tipo(modulo): descrição em minúsculas, imperativo, sem ponto final

Exemplos:
feat(gestor): adicionar endpoint de sync FHIR com Kestra
fix(portal): corrigir realm Keycloak de intellicare para bemcuidar
infra(traefik): adicionar router para gestor.intellicare.ia.br
docs(keycloak): documentar fluxo PKCE e SMART-on-FHIR
refactor(wanda): extrair circuit breaker para classe separada
test(oswaldo): adicionar cobertura para perfil CKD estágio 3
```

---

## Responsabilidades por papel

### Eduardo (Tech Owner)
- Aprova escopo das demandas com Claude
- Aprova Pull Requests no GitHub
- Valida resultado em staging antes de marcar DEPLOYED

### Claude (Tech Lead virtual)
- Cria a branch antes de repassar ao dev
- Gera o ANDAMENTO_DEMANDA
- Revisa o diff técnico antes do PR
- Cria o PR com mensagem padronizada
- Atualiza o índice de demandas

### Dev
- Trabalha apenas na branch da demanda
- Testa localmente antes de fazer push
- Preenche o Log de Execução (Seção 3 do ANDAMENTO_DEMANDA)
- Avisa Eduardo ao concluir — nunca decide sozinho que está pronto para staging

---

## Configuração GitHub necessária (única vez)

Em **Settings → Branches → Branch protection rules**, configurar para `staging` e `main`:

- [x] Require a pull request before merging
- [x] Require approvals: 1
- [x] Require review from Code Owners
- [x] Require status checks to pass: `CI — Portal`
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings
