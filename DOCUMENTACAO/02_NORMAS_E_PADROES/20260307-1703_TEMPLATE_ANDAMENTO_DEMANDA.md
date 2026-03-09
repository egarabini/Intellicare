# DEMANDA: [TITULO_DA_DEMANDA]

<!--
  INSTRUCOES DE USO
  1. Criado por Claude + Eduardo antes de repassar ao dev.
  2. OBRIGATÓRIO: criar os 3 docs de spec no módulo ANTES de repassar:
       intellicare-xxx/docs/DEM-NNN_ESPECIFICACAO_FUNCIONAL.md
       intellicare-xxx/docs/DEM-NNN_ESPECIFICACAO_TECNICA.md
       intellicare-xxx/docs/DEM-NNN_PLANO_IMPLEMENTACAO.md
     Ver norma: DOCUMENTACAO/02_NORMAS_E_PADROES/20260308-1800_NORMA_ESPECIFICACAO_DEMANDAS.md
  3. Dev preenche a Seção 3 (Log de Execução) conforme avança.
  4. Ao concluir, avisar Eduardo para revisão (Seção 4).
  5. Claude + Eduardo aprovam e executam PR + deploy (Seção 5).

  NOMENCLATURA DO ARQUIVO:
  YYYYMMDD-HHMM_DEM-NNN_MODULO_DESCRICAO.md

  ONDE SALVAR:
  DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/
-->

---

## METADADOS
<!-- Manter formato de tabela exato — usado para geração de painel -->

| Campo | Valor |
|---|---|
| **ID** | DEM-NNN |
| **Status** | `BACKLOG` |
| **Módulo(s)** | `intellicare-xxx` |
| **Branch** | `feat/xxx-descricao-curta` |
| **Dev responsável** | @nome |
| **Criado por** | Claude + Eduardo |
| **Data criação** | YYYY-MM-DD |
| **Data início dev** | — |
| **Data conclusão** | — |
| **Spec Funcional** | [DEM-NNN_ESPECIFICACAO_FUNCIONAL.md](../../intellicare-xxx/docs/DEM-NNN_ESPECIFICACAO_FUNCIONAL.md) |
| **Spec Técnica** | [DEM-NNN_ESPECIFICACAO_TECNICA.md](../../intellicare-xxx/docs/DEM-NNN_ESPECIFICACAO_TECNICA.md) |
| **Plano de Impl.** | [DEM-NNN_PLANO_IMPLEMENTACAO.md](../../intellicare-xxx/docs/DEM-NNN_PLANO_IMPLEMENTACAO.md) |
| **PR** | — |
| **Deploy staging** | — |

### Status válidos
```
BACKLOG       → aguardando início
EM_DEV        → dev trabalhando
EM_REVISAO    → dev concluiu, aguardando revisão Claude+Eduardo
APROVADO      → revisado e aprovado, aguardando PR/deploy
DEPLOYED      → em staging
BLOQUEADO     → impedimento identificado (descrever na Seção 3)
CANCELADO     → demanda cancelada (descrever motivo na Seção 4)
```

---

## 1. CONTEXTO E MOTIVAÇÃO

> Por que esta demanda existe? Qual problema resolve ou qual melhoria entrega?

[Descrever o contexto em 2-5 linhas. Incluir impacto se não for feito.]

---

## 2. ESCOPO APROVADO

> Definido por Claude + Eduardo antes do início. O dev não altera este escopo.

### O que será feito (in-scope)

- [ ] Tarefa 1
- [ ] Tarefa 2
- [ ] Tarefa 3

### O que NÃO será feito (out-of-scope)

- Item A — motivo: [razão]
- Item B — será tratado na DEM-XXX

### Critérios de aceite

- [ ] Critério 1 — [como verificar]
- [ ] Critério 2 — [como verificar]
- [ ] Smoke test passa em staging

### Arquivos principais esperados

```
intellicare-xxx/
  xxx/path/arquivo.py    → [o que muda]
  tests/test_xxx.py      → [testes a adicionar]
```

---

## 3. LOG DE EXECUÇÃO
<!-- DEV PREENCHE — um bloco por step significativo -->
<!-- Registrar TODA decisão técnica não-óbvia -->

### STEP-001 — [nome descritivo do que foi feito]

**Data/hora:** YYYY-MM-DD HH:MM
**Dev:** @nome

**O que foi feito:**
> Descrição objetiva do que foi implementado neste step.

**Arquivos alterados/criados:**
```
caminho/arquivo.py     → [o que mudou]
```

**Decisões técnicas tomadas:**
> Por que escolheu essa abordagem e não outra.

**Problemas encontrados:**
> Erros, bloqueios ou comportamentos inesperados.

**Como foi resolvido:**
> Se não resolvido, atualizar Status para BLOQUEADO e avisar Eduardo.

---

### STEP-002 — [nome descritivo]

**Data/hora:** YYYY-MM-DD HH:MM
**Dev:** @nome

**O que foi feito:**

**Arquivos alterados/criados:**
```
```

**Decisões técnicas tomadas:**

**Problemas encontrados:**

**Como foi resolvido:**

---

<!-- Adicionar STEPs conforme necessário -->

---

## 4. REVISÃO
<!-- Preenchido por Claude + Eduardo ao final do desenvolvimento -->

### Checklist de revisão

- [ ] Escopo aprovado foi completamente implementado
- [ ] Critérios de aceite verificados
- [ ] Nenhum arquivo fora do escopo foi alterado
- [ ] Testes relevantes adicionados ou atualizados
- [ ] Código segue normas do projeto (ruff, mypy, eslint)
- [ ] Log de execução preenchido (rastreabilidade ok)
- [ ] Sem credenciais ou dados sensíveis no código

### Observações da revisão

> Anotações de Claude + Eduardo sobre o que foi entregue.

### Resultado

- [ ] Aprovado para PR e deploy
- [ ] Aprovado com ressalvas (listar abaixo)
- [ ] Reprovado — retornar para dev (listar motivos abaixo)

**Ressalvas / Motivos:** [se houver]

---

## 5. PR E DEPLOY

| Campo | Valor |
|---|---|
| **Branch origem** | `feat/xxx-descricao-curta` |
| **Branch destino** | `staging` |
| **PR número** | — |
| **PR criado por** | Claude |
| **PR aprovado por** | Eduardo |
| **Deploy em** | — |
| **Smoke test** | — |
| **URL verificada** | — |

---

## 6. APRENDIZADOS E REFERÊNCIA FUTURA
<!-- Preenchido após deploy — alimenta specs futuras -->

### O que funcionou bem

### O que pode melhorar

### Referências para specs futuras
> Padrões descobertos, decisões de arquitetura, regras de negócio confirmadas
> que devem ser incorporados nas próximas especificações.

---

*Template: docs/NORMAS_E_PADROES/20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md*
