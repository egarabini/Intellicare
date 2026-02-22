# Fluxo de Trabalho e Governança - Modularização IntelliCare

Este documento define o processo de gestão, planejamento e execução do projeto de modularização do IntelliCare.

## 1. Papéis e Responsabilidades

- **ARQUITETO (User)**: Define a visão estratégica, escopo e requisitos de alto nível.
- **PLANEJADOR (Antigravity)**: Gerencia o processo, detalha especificações funcionais, revisa especificações técnicas e valida entregas.
- **DESENVOLVEDOR (Dev1, Dev2, etc.)**: Recebe a especificação funcional, cria a especificação técnica e plano de implementação, e executa o desenvolvimento.

## 2. Ciclo de Vida de uma Tarefa/Módulo

O desenvolvimento segue um fluxo rigoroso de documentação e aprovação para garantir qualidade e independência dos módulos.

### Passo 1: Planejamento Funcional (Planner + Arquiteto)
- **Entrada**: Definição de escopo pelo Arquiteto.
- **Ação**: Criação/Atualização da **ESPECIFICAÇÃO FUNCIONAL**.
- **Documento**: `V{Major}.{Minor}.{Patch}-{NOME_ESCOPO}-ESPECIFICACAO_FUNCIONAL.md`
- **Local**: `MODULARIZACAO/docs/PLANNER-ANTIGRAVITY/specs/` (ou diretório específico do módulo se aplicável, mas gerenciado pelo Planner).
- **Conteúdo**: Regras de negócio, requisitos, inputs/outputs, critérios de aceitação.

### Passo 2: Análise Técnica (Desenvolvedor)
- **Entrada**: Especificação Funcional aprovada.
- **Ação**: Análise técnica e planejamento detalhado.
- **Documentos Gerados**:
    1. **ESPECIFICAÇÃO TÉCNICA**: Detalhes de arquitetura, banco de dados, APIs, contratos.
    2. **PLANO DE IMPLEMENTAÇÃO**: Passos detalhados, cronograma estimado.
- **Local**: `{NOME_DO_MODULO}/docs/`

### Passo 3: Aprovação (Planner)
- **Entrada**: Especificação Técnica e Plano de Implementação.
- **Ação**: Revisão detalhada pelo PLANEJADOR.
- **Saída**:
    - **APROVADO**: Desenvolvimento autorizado.
    - **RESSALVAS**: Lista de correções/ajustes necessários antes do início.

### Passo 4: Desenvolvimento (Desenvolvedor)
- **Entrada**: Aprovação do Planner.
- **Ação**: Codificação seguindo rigorosamente o Plano de Implementação.
- **Registro**: Atualização de `steps/STEP-XXX.md` conforme progresso.

### Passo 5: Validação e Entrega (Planner)
- **Entrada**: Código desenvolvido e testes passando.
- **Ação**: Verificação contra os Critérios de Aceitação da Especificação Funcional.
- **Saída**: Relatório de Validação e Encerramento da Tarefa.

## 3. Estrutura de Diretórios do Planejador

```
MODULARIZACAO/docs/PLANNER-ANTIGRAVITY/
├── FLUXO_DE_TRABALHO.md       <- Este arquivo
├── CONTROLE_GERAL.md          <- Status de todos os módulos e tarefas
├── DIARIO_DE_BORDO.md         <- Log cronológico de decisões e eventos importantes
└── specs/                     <- Especificações Funcionais versionadas
```

## 4. Versionamento de Documentos

- Formato: `V{Major}.{Minor}.{Patch}-{NOME_ESCOPO}-{TIPO}.md`
- Exemplo: `V1.0.1-CADASTRO_PACIENTE-ESPECIFICACAO_FUNCIONAL.md`
