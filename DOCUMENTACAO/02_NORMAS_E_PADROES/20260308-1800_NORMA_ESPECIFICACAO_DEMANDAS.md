# NORMA — Especificação Obrigatória de Demandas

**Vigência:** a partir de 2026-03-08
**Aplica-se a:** toda demanda (DEM-NNN) que envolva desenvolvimento de código
**Criado por:** Eduardo + Claude
**Status:** 🔴 OBRIGATÓRIO — sem os três documentos, o dev não começa

---

## Regra geral

Toda demanda de desenvolvimento deve ter **três documentos de especificação**
criados por Claude + Eduardo **antes** de ser repassada ao dev.

O dev só inicia o trabalho após receber os três documentos e confirmar que
os entendeu. Se tiver dúvidas, deve formalizá-las em um documento de dúvidas
e aguardar resposta de Eduardo antes de codificar.

---

## Os três documentos obrigatórios

### 1. `01_ESPECIFICACAO_FUNCIONAL.md`

**O que é:** visão do produto — o que a feature faz, para quem, e por quê.
Escrita em linguagem de negócio, sem código.

**Deve conter:**
- Problema que resolve (por que existe essa demanda)
- Descrição completa das funcionalidades do ponto de vista do usuário
- Fluxos de uso típicos (o que o usuário vê e faz)
- O que a feature **não faz** (out-of-scope explícito)
- Tabelas, listas e exemplos visuais — sem blocos de código

**Para quem serve:** dev entende o objetivo antes de olhar o código.
PM e Eduardo validam que o escopo está correto.

---

### 2. `02_ESPECIFICACAO_TECNICA.md`

**O que é:** visão de implementação — como construir, com código de referência.

**Deve conter:**
- Premissas e contexto técnico (o que já existe, o que pode reaproveitar)
- Novos arquivos a criar (com path completo)
- Arquivos existentes a modificar (com diff ou snippet)
- Código de referência completo ou quase completo dos componentes principais
- Modelos de dados (tabelas, schemas Pydantic)
- Endpoints novos (método, path, body, response)
- Variáveis de ambiente necessárias
- Pontos de atenção técnicos (timeouts, concorrência, limites, etc.)

**Para quem serve:** dev não precisa tomar decisões de arquitetura — elas
já estão tomadas. Ele implementa seguindo a spec.

---

### 3. `03_PLANO_IMPLEMENTACAO.md`

**O que é:** guia passo a passo de execução, dividido em sprints.

**Deve conter:**
- Instruções de setup (branch, dependências, o que ler antes de começar)
- Sprints numerados, cada um com objetivo claro e entregável testável
- Passo a passo dentro de cada sprint (comandos, ordem de criação de arquivos)
- FAQ — perguntas que qualquer dev faria, respondidas de antemão
- Checklist de entrega (backend + frontend + qualidade)
- Instruções de finalização (como preencher o log, como abrir PR, como avisar Eduardo)

**Para quem serve:** dev tem um roteiro de execução — sabe exatamente o que
fazer em cada etapa e em qual ordem.

---

## Onde salvar

Os três documentos ficam **dentro da própria pasta da demanda** em `06_ANDAMENTO/DEMANDAS/`:

```
DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/
└── YYYYMMDD-HHMM_DEM-NNN_TITULO_DA_DEMANDA/
    ├── README.md                    ← ANDAMENTO_DEMANDA (log, status, metadados)
    ├── 01_ESPECIFICACAO_FUNCIONAL.md
    ├── 02_ESPECIFICACAO_TECNICA.md
    └── 03_PLANO_IMPLEMENTACAO.md
```

Toda a documentação da demanda fica junta — independente de quantos módulos
ela toque. A spec técnica referencia os módulos afetados internamente.

---

## Nomenclatura

```
01_ESPECIFICACAO_FUNCIONAL.md
02_ESPECIFICACAO_TECNICA.md
03_PLANO_IMPLEMENTACAO.md
```

Numerados para manter a ordem de leitura natural. O `README.md` é o ANDAMENTO_DEMANDA.

---

## Quem cria

**Claude + Eduardo** criam os três documentos antes de repassar ao dev.

O dev **não altera** a spec funcional nem a spec técnica após recebê-las.
Se identificar algo incorreto ou conflitante durante a implementação, deve:
1. Parar
2. Documentar a dúvida/conflito
3. Avisar Eduardo
4. Aguardar atualização da spec antes de prosseguir

---

## Quando criar

```
Eduardo detecta necessidade
    ↓
Claude + Eduardo definem escopo (conversa no chat)
    ↓
Claude cria os 3 documentos de spec
    ↓
Eduardo valida e aprova
    ↓
Claude atualiza ANDAMENTO_DEMANDA com links para os 3 docs
    ↓
Dev recebe: ANDAMENTO_DEMANDA + 3 docs de spec
    ↓
Dev lê, confirma entendimento ou formaliza dúvidas
    ↓
Dev inicia desenvolvimento
```

---

## Demandas já implementadas nesta norma

| Demanda | Módulos | Spec Funcional | Spec Técnica | Plano |
|---|---|---|---|---|
| DEM-004 | intellicare-admin | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1600_DEM-004_ADMIN_MODULE_TEST_CONSOLE/01_ESPECIFICACAO_FUNCIONAL.md) | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1600_DEM-004_ADMIN_MODULE_TEST_CONSOLE/02_ESPECIFICACAO_TECNICA.md) | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1600_DEM-004_ADMIN_MODULE_TEST_CONSOLE/03_PLANO_IMPLEMENTACAO.md) |
| DEM-005 | core · grahame · wanda · auth | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP/01_ESPECIFICACAO_FUNCIONAL.md) | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP/02_ESPECIFICACAO_TECNICA.md) | [✅](../06_ANDAMENTO/DEMANDAS/20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP/03_PLANO_IMPLEMENTACAO.md) |

> **Nota:** DEM-001, DEM-002 e DEM-003 foram criadas antes desta norma — têm
> o ANDAMENTO_DEMANDA como README.md mas não possuem os 3 docs separados
> (escopo simples ou demandas já concluídas). DEM-004 em diante segue a norma completa.

---

## Template de cada documento

### Template — ESPECIFICACAO_FUNCIONAL

```markdown
# DEM-NNN — [Título]: Especificação Funcional

**Demanda:** DEM-NNN
**Módulo:** intellicare-xxx
**Dev:** devN
**Referência:** `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/YYYYMMDD-HHMM_DEM-NNN_*.md`

---

## O que é
[Descrição em 2-3 linhas do que será construído]

## Problema que resolve
[Por que esta feature existe]

## [Seções por funcionalidade ou área]
[Uma seção por funcionalidade principal]

## O que NÃO faz
[Out-of-scope explícito]

## Fluxo de uso típico
[Passo a passo do ponto de vista do usuário]
```

### Template — ESPECIFICACAO_TECNICA

```markdown
# DEM-NNN — [Título]: Especificação Técnica

**Demanda:** DEM-NNN
**Módulo:** intellicare-xxx
**Dev:** devN

---

## Premissas e contexto técnico
[O que já existe, o que pode reaproveitar, restrições]

## Novos arquivos
[Árvore de diretórios com os novos arquivos]

## [Arquivo 1] — path/completo/arquivo.py
[Código completo ou referência]

## [Arquivo 2] — path/completo/arquivo.py
[Código completo ou referência]

## Registro em app.py / index.tsx
[Como conectar os novos componentes]

## Variáveis de ambiente necessárias
[Se houver]

## Pontos de atenção
[Timeouts, concorrência, autenticação, limites]
```

### Template — PLANO_IMPLEMENTACAO

```markdown
# DEM-NNN — [Título]: Plano de Implementação

**Demanda:** DEM-NNN
**Dev:** devN
**Branch:** feature/xxx-yyy

---

## Antes de começar
[Comandos de setup, o que ler, pré-requisitos]

## Sprint 1 — [Objetivo] (N dias)
### Passo 1 — [nome]
[Instruções detalhadas com comandos]
### Passo 2 — [nome]
[...]
### Entrega do Sprint 1
- [ ] Item verificável
- [ ] Item verificável

## Sprint 2 — [Objetivo] (N dias)
[...]

## FAQ
**P: [Dúvida comum]**
R: [Resposta]

## Checklist de entrega final
### Backend
- [ ] ...
### Frontend (se houver)
- [ ] ...
### Qualidade
- [ ] make lint passando
- [ ] make typecheck passando

## Ao terminar
[Como preencher log, como abrir PR, como avisar Eduardo]
```

---

## Referência rápida

| Documento | Responde | Audiência |
|---|---|---|
| `ESPECIFICACAO_FUNCIONAL` | *O que* e *por quê* | Dev + Eduardo + PM |
| `ESPECIFICACAO_TECNICA` | *Como* (arquitetura + código) | Dev |
| `PLANO_IMPLEMENTACAO` | *Quando* e *em qual ordem* | Dev |
| `ANDAMENTO_DEMANDA` | *O que foi feito* (log) | Eduardo + Claude |
