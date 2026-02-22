# 📋 PADRÃO DE NOMENCLATURA - DOCUMENTAÇÃO DEV1

## 📌 Objetivo
Definir padrão consistente e visual para nomenclatura de documentos técnicos no processo DEV1, facilitando organização, localização e compreensão da documentação.

---

## 🎯 PADRÃO GERAL

### Formato
```
SEQUENCIA_NOME_DOCUMENTO_TIPO
```

### Componentes

#### 1. SEQUENCIA (2 dígitos)
- **Formato**: `00`, `01`, `02`, `03`, etc.
- **Propósito**: Agrupar documentos por projeto/iniciativa
- **Regras**:
  - `00`: Documentos de processo/governança
  - `01-99`: Projetos específicos (ordem cronológica ou prioridade)

#### 2. NOME_DOCUMENTO (snake_case)
- **Formato**: `PALAVRAS_SEPARADAS_POR_UNDERSCORE`
- **Propósito**: Identificar o projeto/iniciativa
- **Regras**:
  - Usar MAIÚSCULAS
  - Máximo 3-4 palavras
  - Descritivo e conciso
  - Sem acentos ou caracteres especiais

#### 3. TIPO (palavra única)
- **Formato**: `PALAVRA_MAIUSCULA`
- **Propósito**: Identificar o tipo de documento
- **Valores permitidos**:
  - `FUNCIONAL` - Especificação Funcional (O QUE fazer)
  - `TECNICA` - Especificação Técnica (COMO fazer)
  - `PLANO` - Plano de Implementação (QUANDO/QUEM fazer)
  - `APROVACAO` - Documento de Aprovação
  - `IMPLEMENTACAO` - Relatório de Implementação
  - `TESTE` - Plano ou Relatório de Testes
  - `DEPLOY` - Plano de Deploy
  - `ROLLBACK` - Plano de Rollback
  - `MONITORAMENTO` - Plano de Monitoramento
  - `MANUTENCAO` - Guia de Manutenção

---

## 📚 EXEMPLOS

### Documentos de Processo (00)
```
00_PROCESSO_DEV1.md
00_PADRAO_NOMENCLATURA.md
00_TEMPLATE_FUNCIONAL.md
00_TEMPLATE_TECNICA.md
00_CHECKLIST_APROVACAO.md
```

### Projeto 01 - Florence Integração
```
01_FLORENCE_ESPECIFICACAO_FUNCIONAL.md
01_FLORENCE_ESPECIFICACAO_TECNICA.md
01_FLORENCE_ESPECIFICACAO_PLANO.md
01_FLORENCE_ESPECIFICACAO_TESTE.md
01_FLORENCE_ESPECIFICACAO_DEPLOY.md
01_FLORENCE_ESPECIFICACAO_APROVACAO.md
```

### Projeto 02 - Oswaldo Integracao
```
02_OSWALDO_ESPECIFICACAO_FUNCIONAL.md
02_OSWALDO_ESPECIFICACAO_TECNICA.md
02_OSWALDO_ESPECIFICACAO_PLANO.md
02_OSWALDO_ESPECIFICACAO_TESTE.md
02_OSWALDO_ESPECIFICACAO_DEPLOY.md
02_OSWALDO_ESPECIFICACAO_ROLLBACK.md
```

### Projeto 03 - Exemplo Futuro
```
03_NOME_PROJETO_FUNCIONAL.md
03_NOME_PROJETO_TECNICA.md
03_NOME_PROJETO_PLANO.md
```

---

## 🔄 CICLO DE VIDA DE UM PROJETO

### Ordem Recomendada de Criação

```
1. SEQUENCIA_NOME_FUNCIONAL.md
   ↓ (PO/Stakeholder define O QUE)
   
2. SEQUENCIA_NOME_TECNICA.md
   ↓ (DEV1 define COMO)
   
3. SEQUENCIA_NOME_PLANO.md
   ↓ (DEV1 define QUANDO/QUEM)
   
4. SEQUENCIA_NOME_APROVACAO.md
   ↓ (Aprovações formais)
   
5. SEQUENCIA_NOME_IMPLEMENTACAO.md
   ↓ (Durante implementação)
   
6. SEQUENCIA_NOME_TESTE.md
   ↓ (Testes e validação)
   
7. SEQUENCIA_NOME_DEPLOY.md
   ↓ (Deploy em produção)
   
8. SEQUENCIA_NOME_MANUTENCAO.md
   ↓ (Pós go-live)
```

---

## ✅ BENEFÍCIOS DO PADRÃO

### 1. Organização Visual
```
Listagem de diretório:
00_PADRAO_NOMENCLATURA.md
00_PROCESSO_DEV1.md
01_FLORENCE_ESPECIFICACAO_FUNCIONAL.md
01_FLORENCE_ESPECIFICACAO_PLANO.md
01_FLORENCE_ESPECIFICACAO_TECNICA.md
02_OSWALDO_ESPECIFICACAO_FUNCIONAL.md
02_OSWALDO_ESPECIFICACAO_PLANO.md
02_OSWALDO_ESPECIFICACAO_TECNICA.md
```
✅ Agrupamento automático por projeto
✅ Ordenação alfabética natural
✅ Fácil identificação visual

### 2. Busca Facilitada
```bash
# Todos os documentos do Projeto 01
ls 01_*

# Todas as especificações técnicas
ls *_TECNICA.md

# Todos os planos de implementação
ls *_PLANO.md
```

### 3. Consistência
- Todos seguem o mesmo padrão
- Fácil de ensinar para novos membros
- Reduz ambiguidade

### 4. Escalabilidade
- Suporta 99 projetos (01-99)
- Múltiplos tipos de documentos por projeto
- Fácil adicionar novos tipos

---

## 📏 REGRAS DE NOMENCLATURA

### ✅ FAZER

1. **Usar MAIÚSCULAS**
   ```
   ✅ 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
   ❌ 01_FLORENCE_integracao_funcional.md
   ```

2. **Usar underscore (_) como separador**
   ```
   ✅ 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
   ❌ 01-FLORENCE-INTEGRACAO-FUNCIONAL.md
   ❌ 01.FLORENCE.INTEGRACAO.FUNCIONAL.md
   ```

3. **Usar 2 dígitos para sequência**
   ```
   ✅ 01_PROJETO_FUNCIONAL.md
   ❌ 1_PROJETO_FUNCIONAL.md
   ```

4. **Ser descritivo mas conciso**
   ```
   ✅ 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
   ❌ 01_INTEGRACAO_COMPLETA_DO_FLORENCE_COM_TODOS_OS_MODULOS_FUNCIONAL.md
   ```

5. **Usar extensão .md (Markdown)**
   ```
   ✅ 01_PROJETO_FUNCIONAL.md
   ❌ 01_PROJETO_FUNCIONAL.txt
   ❌ 01_PROJETO_FUNCIONAL.docx
   ```

### ❌ NÃO FAZER

1. **Não usar espaços**
   ```
   ❌ 01 FLORENCE INTEGRACAO FUNCIONAL.md
   ```

2. **Não usar acentos ou caracteres especiais**
   ```
   ❌ 01_INTEGRAÇÃO_FLORENCE_FUNCIONAL.md
   ❌ 01_FLORENCE_INTEGRAÇÃO_FUNCIONAL.md
   ```

3. **Não usar minúsculas**
   ```
   ❌ 01_FLORENCE_integracao_funcional.md
   ```

4. **Não usar abreviações não padronizadas**
   ```
   ❌ 01_KC_INT_FUNC.md
   ✅ 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
   ```

5. **Não omitir a sequência**
   ```
   ❌ FLORENCE_INTEGRACAO_FUNCIONAL.md
   ✅ 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
   ```

---

## 🎨 TIPOS DE DOCUMENTOS DETALHADOS

### 1. FUNCIONAL
- **Propósito**: Definir O QUE será feito
- **Autor**: Product Owner / Stakeholder
- **Conteúdo**: Requisitos, casos de uso, critérios de aceite
- **Exemplo**: `01_FLORENCE_INTEGRACAO_FUNCIONAL.md`

### 2. TECNICA
- **Propósito**: Definir COMO será feito
- **Autor**: DEV1 / Arquiteto
- **Conteúdo**: Arquitetura, tecnologias, design patterns, código
- **Exemplo**: `01_FLORENCE_INTEGRACAO_TECNICA.md`

### 3. PLANO
- **Propósito**: Definir QUANDO e QUEM fará
- **Autor**: DEV1 / Gerente de Projeto
- **Conteúdo**: Cronograma, recursos, riscos, marcos
- **Exemplo**: `01_FLORENCE_INTEGRACAO_PLANO.md`

### 4. APROVACAO
- **Propósito**: Registrar aprovações formais
- **Autor**: DEV1
- **Conteúdo**: Assinaturas, datas, comentários
- **Exemplo**: `01_FLORENCE_INTEGRACAO_APROVACAO.md`

### 5. IMPLEMENTACAO
- **Propósito**: Documentar o que foi implementado
- **Autor**: DEV1
- **Conteúdo**: Código criado, decisões tomadas, problemas resolvidos
- **Exemplo**: `01_FLORENCE_INTEGRACAO_IMPLEMENTACAO.md`

### 6. TESTE
- **Propósito**: Plano e resultados de testes
- **Autor**: DEV1 / QA
- **Conteúdo**: Casos de teste, resultados, bugs encontrados
- **Exemplo**: `01_FLORENCE_INTEGRACAO_TESTE.md`

### 7. DEPLOY
- **Propósito**: Plano de deploy em produção
- **Autor**: DEV1 / DevOps
- **Conteúdo**: Passos, checklist, validações
- **Exemplo**: `01_FLORENCE_INTEGRACAO_DEPLOY.md`

### 8. ROLLBACK
- **Propósito**: Plano de rollback em caso de problemas
- **Autor**: DEV1 / DevOps
- **Conteúdo**: Passos para reverter, critérios, responsáveis
- **Exemplo**: `01_FLORENCE_INTEGRACAO_ROLLBACK.md`

### 9. MONITORAMENTO
- **Propósito**: Como monitorar o sistema
- **Autor**: DEV1 / SRE
- **Conteúdo**: Métricas, alertas, dashboards
- **Exemplo**: `01_FLORENCE_INTEGRACAO_MONITORAMENTO.md`

### 10. MANUTENCAO
- **Propósito**: Guia de manutenção pós go-live
- **Autor**: DEV1
- **Conteúdo**: Troubleshooting, FAQs, procedimentos
- **Exemplo**: `01_FLORENCE_INTEGRACAO_MANUTENCAO.md`

---

## 📂 ESTRUTURA DE DIRETÓRIOS

### Recomendação
```
Documentacao/
└── consolidacao/
    └── docs_DEV1/
        ├── 00_PROCESSO_DEV1.md
        ├── 00_PADRAO_NOMENCLATURA.md
        ├── 00_TEMPLATE_FUNCIONAL.md
        ├── 00_TEMPLATE_TECNICA.md
        │
        ├── 01_FLORENCE_INTEGRACAO_FUNCIONAL.md
        ├── 01_FLORENCE_INTEGRACAO_TECNICA.md
        ├── 01_FLORENCE_INTEGRACAO_PLANO.md
        ├── 01_FLORENCE_INTEGRACAO_TESTE.md
        │
        ├── 02_OSWALDO_ESPECIFICACAO_FUNCIONAL.md
        ├── 02_OSWALDO_ESPECIFICACAO_TECNICA.md
        ├── 02_OSWALDO_ESPECIFICACAO_PLANO.md
        │
        └── README.md
```

---

## 🔍 EXEMPLOS DE USO

### Criar Novo Projeto (Sequência 03)

**Passo 1**: Criar Especificação Funcional
```bash
touch 03_NOVO_PROJETO_FUNCIONAL.md
```

**Passo 2**: Criar Especificação Técnica
```bash
touch 03_NOVO_PROJETO_TECNICA.md
```

**Passo 3**: Criar Plano de Implementação
```bash
touch 03_NOVO_PROJETO_PLANO.md
```

### Buscar Documentos

**Todos os documentos do Projeto 02**:
```bash
ls 02_*
```

**Todas as especificações técnicas**:
```bash
ls *_TECNICA.md
```

**Todos os planos de implementação**:
```bash
ls *_PLANO.md
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de criar um documento, verifique:

- [ ] Sequência está correta (2 dígitos: 00-99)
- [ ] Nome do documento é descritivo (3-4 palavras)
- [ ] Tipo está na lista de valores permitidos
- [ ] Tudo em MAIÚSCULAS
- [ ] Separadores são underscores (_)
- [ ] Sem espaços, acentos ou caracteres especiais
- [ ] Extensão é .md
- [ ] Segue o padrão: `SEQUENCIA_NOME_DOCUMENTO_TIPO.md`

---

## 📊 RESUMO VISUAL

```
┌─────────────────────────────────────────────────────┐
│  PADRÃO: SEQUENCIA_NOME_DOCUMENTO_TIPO.md          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  SEQUENCIA:        00-99 (2 dígitos)               │
│  NOME_DOCUMENTO:   PALAVRAS_SEPARADAS              │
│  TIPO:             FUNCIONAL | TECNICA | PLANO...  │
│                                                     │
│  Exemplo:                                           │
│  01_FLORENCE_INTEGRACAO_FUNCIONAL.md               │
│  └┬┘ └──────┬──────────┘ └────┬────┘              │
│   │         │                  │                    │
│   │         │                  └─ Tipo              │
│   │         └──────────────────── Nome              │
│   └────────────────────────────── Sequência         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Versão**: 1.0  
**Data**: 12/02/2026  
**Autor**: DEV1  
**Status**: ✅ APROVADO

