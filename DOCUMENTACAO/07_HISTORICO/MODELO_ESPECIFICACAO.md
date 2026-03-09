# Modelo de Especificações e Fluxo de Trabalho

**Data:** 2026-02-19  
**Papéis:** ARQUITETO | PLANEJADOR | Agentes Desenvolvedores

---

## 1. Visão Geral do Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│  ARQUITETO + PLANEJADOR                                          │
│  • Definir escopo e prioridades                                  │
│  • Elaborar ESPECIFICACAO_FUNCIONAL (versionada)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENTES DESENVOLVEDORES                                         │
│  • Receber ESPECIFICACAO_FUNCIONAL                               │
│  • Produzir ESPECIFICACAO_TECNICA                                │
│  • Produzir PLANO_IMPLEMENTACAO                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  APROVAÇÃO (ARQUITETO + PLANEJADOR)                              │
│  • Revisar alinhamento com arquitetura e requisitos              │
│  • Aprovar OU registrar RESSALVAS                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │  APROVADO        │          │  RESSALVAS      │
     │  → Implementação │          │  → Ajustes      │
     └─────────────────┘          │  → Nova revisão  │
                                  └─────────────────┘
```

---

## 2. ESPECIFICACAO_FUNCIONAL

Documento elaborado por **ARQUITETO + PLANEJADOR** e entregue aos agentes desenvolvedores.

### 2.1 Estrutura Recomendada

```markdown
# ESPECIFICACAO_FUNCIONAL — [Nome da Feature/Módulo]

**Versão:** X.Y  
**Data:** YYYY-MM-DD  
**Status:** Rascunho | Em revisão | Aprovada

## 1. Contexto e Objetivo
- Por que esta feature existe
- Problema que resolve

## 2. Escopo
- O que está dentro
- O que está fora (explicitamente)

## 3. Requisitos Funcionais
- RF-001: [descrição]
- RF-002: [descrição]
- ...

## 4. Requisitos Não Funcionais
- RNF-001: Performance, segurança, etc.
- ...

## 5. Critérios de Aceite
- CA-001: Dado X, quando Y, então Z
- CA-002: ...
- ...

## 6. Cenários de Uso
- Cenário 1: [fluxo]
- Cenário 2: ...

## 7. Restrições e Premissas
- Tecnologias obrigatórias
- Integrações existentes
- Premissas de negócio
- **Python:** Sempre executar em ambiente virtual (venv, poetry, conda) — evita conflitos de versão de bibliotecas

## 8. Referências
- Documentos, APIs, diagramas
```

### 2.2 Versionamento

- **X.Y** — X = versão maior (mudanças de escopo), Y = versão menor (ajustes)
- Histórico de alterações no final do documento

---

## 3. ESPECIFICACAO_TECNICA

Documento produzido pelos **Agentes Desenvolvedores** em resposta à ESPECIFICACAO_FUNCIONAL.

### 3.1 Conteúdo Esperado

- Arquitetura técnica da solução
- Modelo de dados (entidades, relacionamentos)
- APIs (endpoints, contratos)
- Integrações com outros módulos
- Tecnologias e bibliotecas escolhidas
- Justificativas de decisões técnicas
- Diagramas (quando aplicável)

### 3.2 Premissas Obrigatórias (Python)

- **Ambiente virtual:** Todo código Python deve ser executado em ambiente virtual (venv, poetry, conda). Evitar conflitos de versão de bibliotecas entre módulos.

### 3.3 Critérios de Aprovação

- Alinhamento com ESPECIFICACAO_FUNCIONAL
- Conformidade com arquitetura do projeto (padrões, stack)
- Viabilidade e riscos identificados
- Clareza suficiente para implementação

---

## 4. PLANO_IMPLEMENTACAO

Documento produzido pelos **Agentes Desenvolvedores** em conjunto com a ESPECIFICACAO_TECNICA.

### 4.1 Conteúdo Esperado

- Tarefas ordenadas (fases/sprints)
- Dependências entre tarefas
- Estimativas (opcional)
- Ordem de implementação (backend, frontend, testes, etc.)
- Checklist de entrega

### 4.2 Critérios de Aprovação

- Sequência lógica e sem bloqueios desnecessários
- Cobertura dos requisitos da ESPECIFICACAO_FUNCIONAL
- Testes incluídos
- Documentação incluída

---

## 5. RESSALVAS

Documento ou seção produzido por **ARQUITETO + PLANEJADOR** quando a ESPECIFICACAO_TECNICA ou o PLANO_IMPLEMENTACAO não são aprovados integralmente.

### 5.1 Estrutura

```markdown
# RESSALVAS — [Nome da Feature] — Revisão YYYY-MM-DD

## R1: [Título]
- **Onde:** [seção/trecho da especificação técnica ou plano]
- **Problema:** [descrição]
- **Ação esperada:** [o que o desenvolvedor deve ajustar]

## R2: ...
```

### 5.2 Fluxo após RESSALVAS

1. Agentes ajustam ESPECIFICACAO_TECNICA e/ou PLANO_IMPLEMENTACAO
2. Submetem nova versão
3. ARQUITETO + PLANEJADOR revisam novamente
4. Repetir até aprovação

---

## 6. Localização dos Documentos

Cada fase ou feature possui um diretório próprio, concentrando todos os artefatos:

```
docs/PLANNER-CURSOR/especificacoes/
├── Fase1/                                    # Fase 1 — Estabilização
│   ├── ESPECIFICACAO_FUNCIONAL_..._v1.0.md
│   ├── ESPECIFICACAO_TECNICA_..._v1.0.md     # produzido pelo dev
│   ├── PLANO_IMPLEMENTACAO_..._v1.0.md       # produzido pelo dev
│   └── RESSALVAS_..._YYYY-MM-DD.md           # se houver
├── Fase2/                                    # Fase 2 — Git
│   └── ...
└── [Feature]/
    └── ...
```

| Tipo | Pasta |
|------|-------|
| ESPECIFICACAO_FUNCIONAL | `docs/PLANNER-CURSOR/especificacoes/[Fase ou Feature]/` |
| ESPECIFICACAO_TECNICA | Mesmo diretório da fase/feature |
| PLANO_IMPLEMENTACAO | Mesmo diretório da fase/feature |
| RESSALVAS | Mesmo diretório da fase/feature |

**Benefício:** Controle de cada ação bem documentada em um único lugar por fase/feature.

---

## 7. Convenção de Nomenclatura

- `ESPECIFICACAO_FUNCIONAL_[FEATURE]_vX.Y.md`
- `ESPECIFICACAO_TECNICA_[FEATURE]_vX.Y.md`
- `PLANO_IMPLEMENTACAO_[FEATURE]_vX.Y.md`
- `RESSALVAS_[FEATURE]_YYYY-MM-DD.md`

Exemplo: `ESPECIFICACAO_FUNCIONAL_UNIFICACAO_OPENAPI_v1.0.md`
