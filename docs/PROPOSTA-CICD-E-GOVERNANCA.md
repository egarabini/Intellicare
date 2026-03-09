# PROPOSTA — CI/CD e Governança de Deploy IntelliCare

**Data:** 2026-03-07
**Status:** Rascunho para discussão
**Contexto:** Entrada em fase de desenvolvimento paralelo com múltiplos devs

---

## Diagnóstico: qual é o problema real?

O problema **não é falta de ferramenta** — você já tem GitHub Actions (`deploy.yml`, `ci-portal.yml`), scripts PowerShell em `PADRAO_ENTREGA/`, e um processo documentado. O problema é que o **caminho errado está aberto** e é mais fácil do que o caminho certo:

| O dev faz | Impacto |
|---|---|
| Edita arquivo diretamente no servidor staging | Mudança existe só no servidor, nunca entra no git |
| Outro dev faz `git pull` correto no servidor | Sobrescreve o fix do primeiro — bug volta |
| Dev local commita sem testar | CI passa mas funcionalidade quebrada chega ao staging |
| Dev altera módulo de outro dev sem avisar | Conflito silencioso — produz erro em runtime |

**Raiz do problema:** o servidor de staging aceita modificações de qualquer dev com acesso SSH, tornando o git opcional em vez de obrigatório.

---

## O que já existe e funciona

Antes de propor o que adicionar, é importante registrar o que já foi construído:

- `.github/workflows/deploy.yml` — deploy automático via SSH quando há push em `staging` ou `master` ✅
- `.github/workflows/ci-portal.yml` — build + lint do portal em todo PR ✅
- `PADRAO_ENTREGA/GIT/publish-module.ps1` — script PowerShell para commit/push por módulo ✅
- `PADRAO_ENTREGA/STAGING/deploy-module.ps1` — deploy por módulo no servidor ✅
- Regra documentada: git pull --ff-only, nunca cópia direta ✅

O problema é que **nada impede o desvio**. As regras existem no papel, não no código.

---

## Proposta: 3 Pilares

### Pilar 1 — Git como única fonte de verdade (tornar o caminho errado impossível)

**O que é:** bloquear modificação direta no servidor para todos os devs, exceto via deploy automatizado.

**Como funciona:**
- O servidor mantém um usuário `deploy` com acesso restrito — só executa o script de deploy, não abre shell livre
- Ou, mais simples: os devs continuam com acesso SSH normal, mas o servidor tem um **hook de proteção** que detecta e reverte qualquer mudança fora do processo de deploy
- A única forma de código chegar ao staging é via GitHub Actions (push na branch `staging`)

**Impacto imediato:** o dev que edita direto no servidor vê o erro na próxima vez que o Actions rodar — o deploy sobrescreve com o código do git. Isso por si só já educa rapidamente.

**Custo de implementação:** baixo — ajuste de permissões SSH + regra no deploy.yml para fazer `git reset --hard origin/staging` antes de aplicar.

> O `deploy.yml` atual já faz `git reset --hard origin/$BRANCH` — isso significa que qualquer mudança manual no servidor é automaticamente apagada no próximo deploy. Você só precisa garantir que o deploy roda com frequência suficiente.

---

### Pilar 2 — CODEOWNERS: isolamento de módulos por dono

**O que é:** o arquivo `.github/CODEOWNERS` que você mencionou ter visto. É um arquivo do GitHub que associa diretórios/arquivos a donos (devs ou times).

**Como funciona:**
```
# .github/CODEOWNERS
intellicare-core/          @lead-dev
intellicare-auth/          @dev-segurança
intellicare-portal/        @dev-frontend
intellicare-wanda/         @dev-ia
intellicare-florence/      @dev-ia
intellicare-oswaldo/       @dev-clinico
intellicare-grahame/       @dev-fhir
traefik/                   @lead-dev @dev-infra
.github/                   @lead-dev
```

**O que o GitHub faz automaticamente quando um dev abre um PR:**
- Detecta quais arquivos foram alterados
- Compara com o CODEOWNERS
- Adiciona automaticamente o dono como revisor obrigatório do PR
- O PR só pode ser mergeado com aprovação do dono — o GitHub bloqueia o merge

**Por que isso resolve o problema do desenvolvimento paralelo:**
- Dev A altera `intellicare-oswaldo/` → o dono de oswaldo recebe notificação e precisa aprovar
- Dev B altera `intellicare-portal/` → não afeta oswaldo, processos paralelos sem interferência
- Dev C tenta alterar `intellicare-core/` → o lead-dev precisa aprovar — proteção da base compartilhada

**Custo de implementação:** criar um arquivo texto de ~20 linhas.

---

### Pilar 3 — Branch Protection + GitHub Environments (gate automático)

**O que é:** regras configuradas no GitHub que tornam obrigatório passar pelo CI antes de fazer merge.

**Configuração recomendada para IntelliCare:**

**Branch `staging`:**
- Bloquear push direto (todos os devs, incluindo admin do repo)
- Exigir PR para qualquer mudança
- Exigir que CI passe (build + lint + smoke test)
- Exigir 1 aprovação (preferencialmente do CODEOWNERS do módulo afetado)

**Branch `main` (produção):**
- Bloquear push direto absolutamente
- Exigir aprovação de 2 revisores
- Exigir que todos os checks passem
- Exigir que o branch esteja atualizado com `main` antes do merge

**GitHub Environments (staging + production):**
- Environment `staging`: deploy acontece automaticamente após merge em `staging`
- Environment `production`: deploy requer clique manual de aprovação por um responsável definido

**Fluxo resultante:**
```
dev/feature-branch
       ↓ (PR aberto)
   CI roda automaticamente (build + test)
       ↓ (CI verde)
   CODEOWNERS notificados para revisar
       ↓ (aprovado)
   Merge em staging
       ↓ (automático via Actions)
   Deploy no servidor staging
       ↓ (smoke test)
   Resultado notificado no PR
```

---

## Sobre GitHub Copilot para gerenciar deploys

Resposta direta: **Copilot não é a ferramenta certa para isso.** Copilot é um assistente de código (autocompletar, refatorar, sugerir) — ele não gerencia deploys, não controla branches, não faz review de PRs.

O que você provavelmente está procurando já existe e se chama **GitHub Actions** — que você já tem. A diferença é configurar as *proteções* que forçam o uso do Actions (Pilares 1 e 3 acima).

Se a ideia for ter um agente que **revisa código automaticamente** nos PRs, a ferramenta mais próxima seria:
- **GitHub Copilot for PRs** (CodeReview automático) — disponível com sua assinatura, faz review de código via IA
- **Renovate Bot** ou **Dependabot** — para atualização automática de dependências

---

## Comparativo das abordagens

| Abordagem | Impacto | Custo impl. | Disrupção para devs |
|---|---|---|---|
| `git reset --hard` no deploy (bloqueia edição direta) | Alto — fecha a brecha principal | Baixo (1 linha no deploy.yml) | Baixa |
| CODEOWNERS | Alto — isola módulos, bloqueia merges cruzados | Muito baixo (1 arquivo) | Baixa |
| Branch protection + CI obrigatório | Alto — garante qualidade | Médio (configuração GitHub) | Média — devs precisam abrir PRs |
| GitHub Environments com aprovação manual | Médio — controle de produção | Baixo | Baixa |
| Permissões SSH restritas no servidor | Alto — elimina bypass físico | Médio (infra) | Alta — muda workflow de todos |

---

## Sugestão de sequência de implementação

**Semana 1 — Quick wins sem disrupção:**
1. Adicionar `git reset --hard origin/$BRANCH` no início do script de deploy (bloqueia bypass de servidor)
2. Criar `.github/CODEOWNERS` (proteção por módulo)

**Semana 2 — Enforcement de processo:**
3. Ativar branch protection em `staging` (PR obrigatório, CI obrigatório)
4. Configurar GitHub Environments com aprovação para `main`

**Semana 3+ — Maturidade:**
5. Adicionar smoke tests automatizados no pipeline (já existem em `scripts/smoke_tests.py`)
6. Notificação de deploy no Rocket.Chat (integração simples com Actions)
7. Expandir CI para módulos Python (ruff + pytest por módulo alterado)

---

## Pergunta para discussão

Antes de decidir a abordagem, vale alinhar:

1. **Quantos devs ativos hoje** e qual o nível técnico deles com Git/PRs?
2. **O servidor staging é acessível por SSH por todos os devs?** Ou só por você?
3. **Vocês usam branches de feature** hoje, ou todo mundo commita direto em `staging`/`main`?
4. **Há um processo de code review** hoje, ou o dev resolve e já vai para staging?

A resposta a essas perguntas define se a solução é mais de **tooling** (Pilares 1-3 acima) ou mais de **processo e cultura** — que nenhuma ferramenta resolve sozinha.

---

*Documento para discussão — não implementar sem alinhamento.*
