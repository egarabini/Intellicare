# GUIA DO SISTEMA INTELLICARE - DEV1

## 📚 Conhecimento Essencial para Comunicação

**Responsável**: DEV1  
**Data**: 25/02/2026  
**Versão**: 1.0

---

## 1. VISÃO GERAL DO SISTEMA

### O que é INTELLICARE?
Sistema de gestão da qualidade em saúde baseado no modelo Donabedian (Estrutura, Processo, Resultado).

### Objetivo:
Monitorar e melhorar a qualidade do atendimento em instituições de saúde através de indicadores e análises.

---

## 2. ARQUITETURA DO SISTEMA

### Modularização (9 Módulos):
1. **Donabedian** - Indicadores de qualidade
2. **Wanda** - Gestão de leitos
3. **LGPD** - Conformidade e privacidade
4. **Keycloak** - Autenticação e autorização ✅
5. **CQRS** - Separação operacional/analítico ✅
6. **Comunicação** - Gestão de stakeholders (em desenvolvimento)
7. **Módulo 7** - (a definir)
8. **Módulo 8** - (a definir)
9. **Módulo 9** - (a definir)

### Padrões Arquiteturais:
- **CQRS**: Separação de comandos (OLTP) e consultas (OLAP)
- **Event Sourcing**: Histórico completo de eventos
- **Microserviços**: Módulos independentes
- **API Gateway**: Keycloak como ponto central de autenticação

---

## 3. PROJETOS CONCLUÍDOS

### Projeto 01: Integração Keycloak ✅
- **Status**: 100% concluído
- **Funcionalidades**:
  - SSO (Single Sign-On)
  - Autenticação OAuth2/OIDC
  - Gestão de usuários e permissões
  - Integração com módulos existentes

### Projeto 02: Separação Operacional/Analítico ✅
- **Status**: 100% concluído
- **Funcionalidades**:
  - Banco OLTP (operacional) - PostgreSQL
  - Banco OLAP (analítico) - PostgreSQL
  - Pipeline ETL para Donabedian e Wanda
  - Anonimização LGPD (SHA-256)
  - Orquestração e monitoramento

---

## 4. MÓDULO DONABEDIAN

### Conceito:
Modelo de avaliação de qualidade em 3 dimensões:
- **Estrutura**: Recursos disponíveis (equipamentos, pessoal)
- **Processo**: Como o cuidado é prestado
- **Resultado**: Desfechos do cuidado

### Indicadores Principais:
- Taxa de ocupação de leitos
- Tempo médio de permanência
- Taxa de readmissão
- Satisfação do paciente
- Eventos adversos

### Dados Coletados:
- Admissões e altas
- Procedimentos realizados
- Resultados de exames
- Eventos clínicos

---

## 5. MÓDULO WANDA (GESTÃO DE LEITOS)

### Funcionalidades:
- Controle de ocupação de leitos
- Gestão de transferências
- Histórico de permanência
- Análise de utilização

### Dados Sensíveis (LGPD):
- ID do leito (anonimizado)
- ID do paciente (anonimizado)
- Datas de entrada/saída (generalizadas)
- Tipo de leito
- Setor/unidade

### Anonimização:
```python
# Exemplo de anonimização
leito_id_anonimizado = SHA256(leito_id + salt)
paciente_id_anonimizado = SHA256(paciente_id + salt)
data_generalizada = "2026-Q1"  # Trimestre ao invés de data exata
```

---

## 6. CONFORMIDADE LGPD

### Princípios Aplicados:
1. **Minimização**: Apenas dados necessários
2. **Anonimização**: Irreversível (SHA-256)
3. **Finalidade**: Uso apenas para análise de qualidade
4. **Transparência**: Documentação completa
5. **Segurança**: Acesso restrito ao OLAP

### Validações Necessárias:
- ✅ Irreversibilidade da anonimização
- ✅ Ausência de PII (Personally Identifiable Information)
- ✅ Generalização temporal adequada
- ✅ Controle de acesso (read-only)
- ✅ Auditoria de acessos

---

## 7. PIPELINE ETL

### Fluxo:
```
OLTP (Operacional)
    ↓
[Extração] → Dados brutos
    ↓
[Transformação] → Anonimização + Agregação
    ↓
[Carga] → OLAP (Analítico)
```

### Frequência:
- **Donabedian**: Diária (03:00)
- **Wanda**: Diária (04:00)
- **Monitoramento**: Contínuo

### Scripts:
- `07_etl_donabedian.py` - ETL Donabedian
- `08_etl_wanda.py` - ETL Wanda
- `09_etl_orchestrator.py` - Orquestrador
- `10_etl_monitor.py` - Monitor
- `11_validate_lgpd.py` - Validação LGPD

---

## 8. STAKEHOLDERS PRINCIPAIS

### 1. Dr. João Silva (STK-001)
- **Área**: Qualidade
- **Interesse**: Indicadores Donabedian
- **Nível técnico**: Médio
- **Comunicação**: Apresentações visuais

### 2. Dra. Maria Santos (STK-002)
- **Área**: Compliance/LGPD
- **Interesse**: Conformidade e privacidade
- **Nível técnico**: Alto (jurídico/técnico)
- **Comunicação**: Documentação detalhada

### 3. Enf. Carlos Oliveira (STK-003)
- **Área**: Operacional
- **Interesse**: Gestão de leitos (Wanda)
- **Nível técnico**: Baixo
- **Comunicação**: Demos práticas

### 4. Prof. Ana Costa (STK-004)
- **Área**: Tecnologia
- **Interesse**: Arquitetura e integração
- **Nível técnico**: Muito alto
- **Comunicação**: Discussões técnicas

### 5. Dr. Pedro Almeida (STK-005)
- **Área**: Gestão
- **Interesse**: ROI e resultados
- **Nível técnico**: Baixo
- **Comunicação**: Resumos executivos

---

## 9. PRIMEIRA VALIDAÇÃO: LGPD

### Data: 26/02/2026 - 10:00-12:00
### Especialista: Dra. Maria Santos (STK-002)

### Objetivo:
Validar conformidade LGPD da anonimização no pipeline ETL.

### Agenda:
1. **Contexto** (5 min): Explicar projeto e necessidade
2. **Demonstração** (30 min): Mostrar pipeline ETL
3. **Testes práticos** (45 min): Executar validações
4. **Discussão** (30 min): Feedback e ajustes
5. **Próximos passos** (10 min): Documentação e aprovação

### Materiais:
- Especificação técnica CQRS
- Scripts ETL
- Script de validação LGPD
- Exemplos de dados anonimizados

### Critérios de Aprovação:
- ✅ Anonimização irreversível
- ✅ Ausência de PII
- ✅ Generalização adequada
- ✅ Controle de acesso
- ✅ Documentação completa

---

## 10. PONTOS DE ATENÇÃO PARA COMUNICAÇÃO

### Ao Falar com Especialistas Técnicos:
- ✅ Usar terminologia correta
- ✅ Mostrar código quando relevante
- ✅ Explicar decisões arquiteturais
- ✅ Estar preparado para perguntas profundas

### Ao Falar com Gestores:
- ✅ Focar em resultados e benefícios
- ✅ Usar métricas e KPIs
- ✅ Evitar jargão técnico
- ✅ Mostrar ROI e impacto

### Ao Falar com Operacionais:
- ✅ Demonstrações práticas
- ✅ Casos de uso reais
- ✅ Interface amigável
- ✅ Suporte e treinamento

---

## 11. GLOSSÁRIO TÉCNICO

### Termos Essenciais:
- **OLTP**: Online Transaction Processing (operacional)
- **OLAP**: Online Analytical Processing (analítico)
- **ETL**: Extract, Transform, Load
- **CQRS**: Command Query Responsibility Segregation
- **PII**: Personally Identifiable Information
- **SHA-256**: Algoritmo de hash criptográfico
- **SSO**: Single Sign-On
- **OAuth2**: Protocolo de autorização
- **OIDC**: OpenID Connect

---

## 12. RECURSOS ÚTEIS

### Documentação:
- `/docs_DEV1/02_SEPARACAO_DADOS_ESPECIFICACAO_TECNICA.md`
- `/docs_DEV1/01_KEYCLOAK_ESPECIFICACAO_TECNICA.md`
- `/scripts/` - Todos os scripts implementados

### Contatos:
- **DEV2**: Desenvolvedor técnico principal
- **Stakeholders**: Ver `cadastro_stakeholders.json`

---

**Estudado por**: DEV1  
**Data**: 25/02/2026  
**Status**: ✅ Conhecimento adquirido

