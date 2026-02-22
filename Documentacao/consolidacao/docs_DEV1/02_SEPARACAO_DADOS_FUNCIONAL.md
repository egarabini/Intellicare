# ESPECIFICAÇÃO FUNCIONAL: SEPARAÇÃO OPERACIONAL/ANALÍTICO

## 📌 ID: DEV1-FUNC-002
## 🎯 Objetivo: Implementar separação clara entre dados operacionais e analíticos
## 📅 Data: 12/02/2026
## 👤 Responsável: Product Owner/Arquiteto
## 👨‍💻 Responsável Técnico: DEV1
## ⚠️ Prioridade: ALTA
## ⏱️ Estimativa PO: 30 horas

## 1. CONTEXTO
Atualmente os módulos INTELLICARE acessam dados sem distinção entre operacionais (transacionais, vivos) e analíticos (históricos, agregados). Esta especificação implementa o princípio fundamental da arquitetura da outra equipe: "operacional → analítico (nunca o contrário)".

## 2. REQUISITOS FUNCIONAIS

### RF-001: Definição Clara de Domínios
**Descrição**: Classificação explícita de cada tabela/coleção como operacional ou analítico.
**Critérios de Aceite**:
- [ ] Documentação de cada tabela com classificação
- [ ] Metadados no banco indicando domínio
- [ ] Validação em tempo de desenvolvimento
- [ ] Alertas para classificações ambíguas

### RF-002: Bancos de Dados Separados
**Descrição**: Dados operacionais e analíticos em bancos físicos diferentes.
**Critérios de Aceite**:
- [ ] PostgreSQL operacional: dados transacionais
- [ ] PostgreSQL analítico: dados históricos/agregados
- [ ] Conexões separadas por domínio
- [ ] Backup/restore independentes

### RF-003: Pipeline Operacional → Analítico
**Descrição**: Fluxo unidirecional de dados do operacional para o analítico.
**Critérios de Aceite**:
- [ ] ETL/ELT diário (incremental)
- [ ] Anonimização/pseudonimização no pipeline
- [ ] Garantia de idempotência
- [ ] Logs de transformação

### RF-004: Política de Acesso por Domínio
**Descrição**: Controle de acesso baseado no domínio dos dados.
**Critérios de Aceite**:
- [ ] Aplicações operacionais: acesso apenas a operacional
- [ ] Aplicações analíticas: acesso apenas a analítico
- [ ] Exceções documentadas e auditadas
- [ ] Bloqueio de acesso cruzado

### RF-005: Validação em Runtime
**Descrição**: Verificação em tempo de execução do domínio acessado.
**Critérios de Aceite**:
- [ ] Middleware que valida domínio do query
- [ ] Logs de violações de política
- [ ] Alertas em tempo real
- [ ] Métricas de compliance

## 3. REQUISITOS NÃO FUNCIONAIS

### RNF-001: Isolamento
**Descrição**: Dados operacionais protegidos de queries analíticas pesadas.
**Métrica**:
- Zero queries analíticas no banco operacional
- Latência operacional mantida < 100ms
- SLA operacional: 99.9%

### RNF-002: Performance Analítica
**Descrição**: Banco analítico otimizado para queries complexas.
**Métrica**:
- Índices otimizados para agregações
- Particionamento por tempo
- Query response < 5s para 1 bilhão de registros

### RNF-003: Qualidade de Dados
**Descrição**: Dados analíticos com qualidade garantida.
**Métrica**:
- Completeness: > 99%
- Accuracy: > 99%
- Timeliness: dados com no máximo 24h de atraso
- Consistency: entre fontes > 95%

### RNF-004: Segurança
**Descrição**: Proteção de dados sensíveis no pipeline.
**Métrica**:
- Dados anonimizados: 100% no analítico
- Auditoria completa do pipeline
- Compliance LGPD/HIPAA

## 4. REGRAS DE NEGÓCIO

### RN-001: Direção Única
- Dados fluem apenas: operacional → analítico
- Nunca: analítico → operacional
- Nunca: operacional ←→ analítico

### RN-002: Granularidade Temporal
- Operacional: dados em tempo real
- Analítico: dados diários (batch nightly)
- Exceção: near-real-time para casos críticos (max 1h delay)

### RN-003: Retenção
- Operacional: 7 anos (conforme LGPD)
- Analítico: indefinido (dados anonimizados)
- Archive: após 7 anos, move para cold storage

### RN-004: Transformações Permitidas
```yaml
operacional_to_analitico:
  permitido:
    - anonimização
    - agregação
    - sumarização
    - enriquecimento com dados externos
  proibido:
    - junção com dados identificáveis
    - exportação de dados brutos
    - reidentificação
```

## 5. ARQUITETURA DE DADOS

### 5.1. Domínio Operacional
```sql
-- Banco: intellicare_operacional
-- Tables:
- pacientes (dados identificados)
- consultas (transações em tempo real)
- exames (resultados brutos)
- prescricoes (dados vivos)
- tarefas (workflow ativo)
```

### 5.2. Domínio Analítico
```sql
-- Banco: intellicare_analitico
-- Tables:
- pacientes_anon (dados anonimizados)
- metricas_diarias (agregados)
- tendencias (time series)
- kpis (indicadores)
- pesquisas (dados para estudos)
```

### 5.3. Pipeline ETL
```
[Operacional] → [Extração] → [Transformação] → [Carga] → [Analítico]
     ↓               ↓             ↓             ↓           ↓
   Raw data      Incremental   Anonimização   Upsert    Aggregated
   Live          Change Data   Aggregation    Merge     Historical
                 Capture       Enrichment
```

## 6. IMPLEMENTAÇÃO POR MÓDULO

### 6.1. Florence (Análise Clínica)
- Operacional: exames brutos, laudos
- Analítico: estatísticas por doença, tendências

### 6.2. Oswaldo (Doenças Crônicas)
- Operacional: evolução diária, medicamentos
- Analítico: progressão da doença, eficácia tratamentos

### 6.3. Wanda (Orquestração)
- Operacional: fluxos ativos, decisões em tempo real
- Analítico: métricas de orquestração, padrões

### 6.4. Geralda (Acompanhamento)
- Operacional: interações com pacientes
- Analítico: engajamento, adesão

## 7. RESTRIÇÕES

### Técnicas:
- Não pode impactar performance operacional
- Deve usar infraestrutura existente
- Compatível com PostgreSQL 15+

### Temporais:
- Pipeline deve rodar em < 4 horas
- Janela de manutenção: 2h-4h

### Regulatórias:
- Conformidade com LGPD
- Auditoria completa
- Não pode exportar dados identificáveis

## 8. ENTREGÁVEIS

### 8.1. Infraestrutura
- [ ] Bancos PostgreSQL separados
- [ ] Scripts de criação/migração
- [ ] Configuração de conexões
- [ ] Backup/restore procedures

### 8.2. Pipeline ETL
- [ ] Scripts de extração incremental
- [ ] Transformações de anonimização
- [ ] Carga com upsert/merge
- [ ] Monitoramento do pipeline

### 8.3. Controle de Acesso
- [ ] Middleware de validação de domínio
- [ ] Políticas de acesso por aplicação
- [ ] Logs de violações
- [ ] Dashboard de compliance

### 8.4. Documentação
- [ ] Mapa de dados (data lineage)
- [ ] Dicionário de dados
- [ ] Guia de desenvolvimento
- [ ] Runbooks de operação

## 9. MÉTRICAS DE SUCESSO

### Técnicas:
- ✅ Zero queries analíticas no banco operacional
- ✅ Pipeline roda em < 4 horas
- ✅ Dados analíticos com < 24h de atraso
- ✅ 100% dos dados anonimizados no analítico

### Operacionais:
- ✅ Performance operacional mantida
- ✅ Backup/restore funcionando
- ✅ Monitoramento em tempo real
- ✅ Alertas para violações

### Negócio:
- ✅ Conformidade com LGPD
- ✅ Dados prontos para análise/BI
- ✅ Base para machine learning
- ✅ Escalabilidade para big data

---

## 📋 APROVAÇÕES

- [ ] **Aprovação Técnica (DEV1)**: _________________ Data: __/__/____
- [ ] **Aprovação Product Owner**: _________________ Data: __/__/____
- [ ] **Aprovação DPO (LGPD)**: _________________ Data: __/__/____

## 🔄 PRÓXIMOS PASSOS

1. DEV1 analisa e cria especificação técnica
2. Revisão com arquiteto de dados
3. Validação com especialista LGPD
4. Implementação faseada por módulo
5. Testes e validação
6. Go-live com monitoramento

---

**STATUS**: 📄 ESPECIFICAÇÃO FUNCIONAL PRONTA PARA ANÁLISE TÉCNICA