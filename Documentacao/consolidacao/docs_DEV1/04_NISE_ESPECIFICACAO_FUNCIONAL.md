"# ESPECIFICAÇÃO FUNCIONAL: MÓDULO NISE - TREINAMENTO ASSISTIDO

## ID: DEV1-NISE-FUNC-001
## Domínio: Treinamento Assistido e Simulação FHIR
## Data: 15/02/2026
## Responsável: DEV1
## Prioridade: MÉDIA (Planejamento Futuro)
## Estimativa PO: 60 horas

## 1. CONTEXTO E JUSTIFICATIVA

### 1.1. Homenagem a Nise da Silveira
**Por que Nise?**
- Psiquiatra brasileira pioneira na terapia ocupacional
- Método \"aprender fazendo\" e desenvolvimento de habilidades
- Representa paciência, observação e método prático de ensino
- Alinhado com filosofia de treinamento assistido

### 1.2. Objetivo do Módulo
Criar um ambiente de **treinamento assistido** para:
1. **Simulação realista** do sistema INTELLICARE
2. **Treinamento de profissionais** de saúde
3. **Validação de integrações** FHIR
4. **Testes de cenários clínicos complexos**
5. **Capacitação em interoperabilidade** RNDS/SUS

## 2. ARQUITETURA TÉCNICA

### 2.1. Stack Tecnológica
```
┌─────────────────────────────────────────────┐
│           MÓDULO NISE (Treinamento)         │
├─────────────────────────────────────────────┤
│  FastAPI + fhir.resources + psycopg         │
│  PostgreSQL (schema dedicado)               │
│  pgvector para RAG no treinamento           │
│  Docker para isolamento                     │
│  Integração com Ollama/n8n                  │
└─────────────────────────────────────────────┘
```

### 2.2. Banco de Dados Dedicado
**Schema PostgreSQL exclusivo para treinamento**:
```sql
-- Schema separado para não interferir com produção
CREATE SCHEMA nise_training;

-- Tabelas FHIR normalizadas
CREATE TABLE nise_training.patients (
    id SERIAL PRIMARY KEY,
    fhir_id VARCHAR(64) UNIQUE,
    name_given VARCHAR(100),
    name_family VARCHAR(100),
    birth_date DATE,
    gender VARCHAR(20),
    cns VARCHAR(15),  -- Cartão Nacional de Saúde
    data JSONB        -- FHIR Patient completo
);
```

## 3. CASOS DE USO PRINCIPAIS

### 3.1. UC-NISE-001: Treinamento de Profissionais
**Objetivo**: Capacitar profissionais no uso do INTELLICARE
**Fluxo**:
1. Login no ambiente de treinamento
2. Selecionar cenário clínico
3. Executar fluxo completo
4. Receber feedback automático
5. Analisar desempenho
6. Obter certificação

### 3.2. UC-NISE-002: Simulação de Integração FHIR
**Objetivo**: Testar integrações com sistemas externos
**Fluxo**:
1. Sistema externo chama API FHIR
2. NISE responde com dados sintéticos
3. Valida conformidade com padrões
4. Registra logs para análise

### 3.3. UC-NISE-003: Cenários Clínicos Complexos
**Objetivo**: Treinar tomada de decisão em casos complexos
**Exemplos**:
- Paciente com HAS + Diabetes + DRC
- Interações medicamentosas complexas
- Emergências hipertensivas
- Descompensação diabética

## 4. DADOS DE TREINAMENTO

### 4.1. Fontes de Dados Sintéticos
```python
# Características:
- CPFs/CNS válidos (algoritmo módulo 11)
- Nomes brasileiros (Faker pt_BR)
- Municípios IBGE
- Códigos LOINC/SNOMED BR
- ValueSets oficiais RNDS
```

### 4.2. Volumes Iniciais
```
✅ 5.000 pacientes sintéticos
✅ 20.000 observações (RELs)
✅ 1.000 profissionais de saúde
✅ 500 consultas simuladas
✅ 100 cenários clínicos complexos
```

## 5. INTEGRAÇÕES

### 5.1. Com Módulos Existentes
```
Florence (Exames) → NISE (Treinamento exames)
Oswaldo (Doenças crônicas) → NISE (Treinamento gestão)
Geralda (Acompanhamento) → NISE (Treinamento follow-up)
Wanda (Orquestração) → NISE (Treinamento fluxos)
```

### 5.2. Com Ferramentas de IA
```
Ollama: RAG para suporte ao treinamento
n8n: Automação de fluxos de treinamento
pgvector: Busca semântica em cenários
```

## 6. FLUXOS DE TREINAMENTO

### 6.1. Fluxo Básico de Treinamento
```yaml
etapa_1_selecao:
  - Login no ambiente de treinamento
  - Selecionar perfil (médico, enfermeiro, técnico)
  - Escolher módulo (Florence, Oswaldo, etc)
  - Selecionar cenário clínico

etapa_2_execucao:
  - Executar fluxo clínico completo
  - Interagir com sistema simulado
  - Tomar decisões clínicas
  - Registrar ações

etapa_3_avaliacao:
  - Receber feedback automático
  - Analisar erros cometidos
  - Verificar conformidade com protocolos
  - Obter pontuação

etapa_4_certificacao:
  - Atingir pontuação mínima
  - Completar todos os cenários obrigatórios
  - Receber certificado de capacitação
```

## 7. CRONOGRAMA DE IMPLEMENTAÇÃO

### Fase 1: MVP (Mês 1)
```
✅ Semana 1-2: Infraestrutura básica
  - Schema PostgreSQL dedicado
  - FastAPI facade FHIR
  - Scripts de dados sintéticos básicos

✅ Semana 3-4: Funcionalidades core
  - Endpoints FHIR Patient/Observation
  - Geração dados RNDS
  - Integração básica com Florence
```

### Fase 2: Treinamento Assistido (Mês 2)
```
⏳ Semana 5-6: Sistema de treinamento
  - Cenários clínicos estruturados
  - Feedback automático
  - Dashboard de desempenho

⏳ Semana 7-8: Integrações avançadas
  - Todos os módulos INTELLICARE
  - Ollama para suporte RAG
  - n8n para automação fluxos
```

## 8. CRITÉRIOS DE ACEITAÇÃO

### Técnicos:
```
✅ Integração FHIR funcionando
✅ Performance: <100ms P99 para APIs
✅ Dados sintéticos realistas
✅ Conformidade RNDS/SUS
✅ Isolamento completo de produção
```

### Pedagógicos:
```
✅ Feedback útil e construtivo
✅ Progressão de dificuldade adequada
✅ Certificação com valor reconhecido
✅ Interface intuitiva
✅ Suporte durante o treinamento
```

### Operacionais:
```
✅ Escalável para múltiplos usuários
✅ Monitoramento de uso
✅ Relatórios de desempenho
✅ Backup/restore de dados
✅ Documentação completa
```

---
**STATUS**: ESPECIFICAÇÃO FUNCIONAL PRONTA PARA REVISÃO
**PRÓXIMO**: DEV1 CRIAR ESPECIFICAÇÃO TÉCNICA E PLANO
**PRAZO**: AVALIAÇÃO ATÉ 19/02, INÍCIO IMPLEMENTAÇÃO 22/02
**INTEGRAÇÃO**: USA INFRAESTRUTURA EXISTENTE (DEV1) + MÓDULOS (DEV2)
"