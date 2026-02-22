# PLANO DE IMPLEMENTAÇÃO: MÓDULO NISE - TREINAMENTO ASSISTIDO

## ID: DEV1-NISE-PLAN-001
## Versão: 1.0
## Data: 26/02/2026
## Responsável: DEV1
## Status: AGUARDANDO APROVAÇÃO

---

## 1. VISÃO GERAL

### 1.1. Objetivo
Implementar o **Módulo NISE** em **8 semanas** (~60 horas), dividido em 2 fases:
- **Fase 1 (MVP)**: Infraestrutura + APIs FHIR básicas (4 semanas)
- **Fase 2 (Avançado)**: Sistema de treinamento + Integrações (4 semanas)

### 1.2. Equipe
- **DEV1**: Documentação, coordenação, validações
- **DEV2**: Implementação técnica (FastAPI, PostgreSQL, geradores)
- **Stakeholders**: Validação de cenários clínicos

### 1.3. Cronograma
- **Início**: 03/03/2026 (Segunda-feira)
- **Término**: 25/04/2026 (Sexta-feira)
- **Duração**: 8 semanas (40 dias úteis)

---

## 2. FASE 1 - MVP (SEMANAS 1-4)

### SEMANA 1: Infraestrutura Básica (03/03 - 07/03)

#### Dia 1 - Segunda, 03/03/2026 (4 horas)
**Objetivo**: Setup inicial e schema PostgreSQL

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar schema `nise_training` | DEV2 | SQL executado |
| 10:00-11:00 | Criar tabelas (patients, observations) | DEV2 | Tabelas criadas |
| 11:00-12:00 | Criar índices e constraints | DEV2 | Índices criados |
| 14:00-15:00 | Instalar pgvector extension | DEV2 | Extension instalada |

**Entregas**: Schema PostgreSQL completo

#### Dia 2 - Terça, 04/03/2026 (4 horas)
**Objetivo**: Estrutura do projeto FastAPI

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar estrutura de diretórios | DEV2 | Estrutura criada |
| 10:00-11:00 | Setup FastAPI + dependencies | DEV2 | `main.py` funcionando |
| 11:00-12:00 | Configurar conexão PostgreSQL | DEV2 | Connection pool |
| 14:00-15:00 | Criar modelos SQLAlchemy | DEV2 | `models.py` |

**Entregas**: Projeto FastAPI estruturado

#### Dia 3 - Quarta, 05/03/2026 (4 horas)
**Objetivo**: Geradores de dados sintéticos - Pacientes

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Implementar validador CPF/CNS | DEV2 | `validators.py` |
| 10:00-11:00 | Criar gerador de pacientes | DEV2 | `patients.py` |
| 11:00-12:00 | Gerar 5.000 pacientes sintéticos | DEV2 | Dados inseridos |
| 14:00-15:00 | Validar dados gerados | DEV1 + DEV2 | Relatório validação |

**Entregas**: 5.000 pacientes sintéticos no banco

#### Dia 4 - Quinta, 06/03/2026 (4 horas)
**Objetivo**: Geradores de dados sintéticos - Observações

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar gerador de observações | DEV2 | `observations.py` |
| 10:00-11:00 | Gerar 20.000 observações | DEV2 | Dados inseridos |
| 11:00-12:00 | Validar códigos LOINC | DEV1 + DEV2 | Códigos validados |
| 14:00-15:00 | Documentar geradores | DEV1 | README geradores |

**Entregas**: 20.000 observações sintéticas no banco

#### Dia 5 - Sexta, 07/03/2026 (4 horas)
**Objetivo**: Retrospectiva Semana 1

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Revisar entregas da semana | DEV1 + DEV2 | Checklist |
| 10:00-11:00 | Testar queries de performance | DEV2 | Relatório performance |
| 11:00-12:00 | Documentar progresso | DEV1 | Status atualizado |
| 14:00-15:00 | Planejar Semana 2 | DEV1 + DEV2 | Plano Semana 2 |

**Entregas**: Retrospectiva Semana 1

---

### SEMANA 2: Infraestrutura Avançada (10/03 - 14/03)

#### Dia 6 - Segunda, 10/03/2026 (4 horas)
**Objetivo**: Geradores - Profissionais e Consultas

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar gerador de profissionais | DEV2 | `practitioners.py` |
| 10:00-11:00 | Gerar 1.000 profissionais | DEV2 | Dados inseridos |
| 11:00-12:00 | Criar gerador de consultas | DEV2 | `encounters.py` |
| 14:00-15:00 | Gerar 500 consultas | DEV2 | Dados inseridos |

**Entregas**: Profissionais e consultas no banco

#### Dia 7 - Terça, 11/03/2026 (4 horas)
**Objetivo**: Flowise + Ollama Setup

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Instalar Ollama + modelo Llama2-7B | DEV2 | Ollama funcionando |
| 10:00-11:00 | Instalar Flowise (Docker) | DEV2 | Flowise rodando |
| 11:00-12:00 | Configurar Flowise ↔ Ollama | DEV2 | Integração testada |
| 14:00-15:00 | Documentar setup Flowise/Ollama | DEV1 | README Flowise |

**Entregas**: Flowise + Ollama funcionais

#### Dia 8 - Quarta, 12/03/2026 (4 horas)
**Objetivo**: Validação Parcial - Dashboard Conformidade LGPD

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Preparar demo dashboard | DEV2 | Dashboard pronto |
| 10:00-10:30 | Validação com Dra. Maria Santos | DEV1 + DEV2 | Aprovação final |
| 10:30-11:00 | Coletar feedback | DEV1 | Feedback documentado |
| 11:00-12:00 | Ajustes finais dashboard | DEV2 | Dashboard ajustado |
| 14:00-15:00 | Gerar ata da validação | DEV1 | Ata distribuída |

**Entregas**: Dashboard LGPD aprovado (Projeto 03 finalizado)

#### Dia 9 - Quinta, 13/03/2026 (4 horas)
**Objetivo**: Testes automatizados + Dagger Setup

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar testes de geradores | DEV2 | `test_generators.py` |
| 10:00-11:00 | Criar testes de validadores | DEV2 | `test_validators.py` |
| 11:00-12:00 | Executar suite de testes | DEV2 | Relatório testes |
| 14:00-15:00 | Setup Dagger básico | DEV2 | Dagger configurado |

**Entregas**: Suite de testes + Dagger inicial

#### Dia 10 - Sexta, 14/03/2026 (4 horas)
**Objetivo**: Retrospectiva Semana 2

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Revisar entregas da semana | DEV1 + DEV2 | Checklist |
| 10:00-11:00 | Validar dados sintéticos | DEV1 + DEV2 | Relatório validação |
| 11:00-12:00 | Documentar progresso | DEV1 | Status atualizado |
| 14:00-15:00 | Planejar Semana 3 | DEV1 + DEV2 | Plano Semana 3 |

**Entregas**: Retrospectiva Semana 2

---

### SEMANA 3: APIs FHIR Core (17/03 - 21/03)

#### Dia 11 - Segunda, 17/03/2026 (4 horas)
**Objetivo**: Endpoints FHIR Patient

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Implementar GET /fhir/Patient | DEV2 | Endpoint funcionando |
| 10:00-11:00 | Implementar GET /fhir/Patient/{id} | DEV2 | Endpoint funcionando |
| 11:00-12:00 | Implementar POST /fhir/Patient | DEV2 | Endpoint funcionando |
| 14:00-15:00 | Testar endpoints com Postman | DEV1 + DEV2 | Testes documentados |

**Entregas**: Endpoints FHIR Patient

#### Dia 12 - Terça, 18/03/2026 (4 horas)
**Objetivo**: Endpoints FHIR Observation

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Implementar GET /fhir/Observation | DEV2 | Endpoint funcionando |
| 10:00-11:00 | Implementar GET /fhir/Observation/{id} | DEV2 | Endpoint funcionando |
| 11:00-12:00 | Implementar POST /fhir/Observation | DEV2 | Endpoint funcionando |
| 14:00-15:00 | Testar endpoints com Postman | DEV1 + DEV2 | Testes documentados |

**Entregas**: Endpoints FHIR Observation

#### Dia 13 - Quarta, 19/03/2026 (4 horas)
**Objetivo**: Endpoints FHIR Practitioner e Encounter

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Implementar endpoints Practitioner | DEV2 | Endpoints funcionando |
| 10:00-11:00 | Implementar endpoints Encounter | DEV2 | Endpoints funcionando |
| 11:00-12:00 | Validar conformidade FHIR R4 | DEV1 + DEV2 | Relatório conformidade |
| 14:00-15:00 | Documentar API (OpenAPI) | DEV1 | Documentação OpenAPI |

**Entregas**: Todos endpoints FHIR básicos

#### Dia 14 - Quinta, 20/03/2026 (4 horas)
**Objetivo**: Testes de integração FHIR

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar testes de API | DEV2 | `test_api.py` |
| 10:00-11:00 | Testar performance (<100ms P99) | DEV2 | Relatório performance |
| 11:00-12:00 | Testar validação FHIR | DEV2 | Relatório validação |
| 14:00-15:00 | Ajustes e otimizações | DEV2 | APIs otimizadas |

**Entregas**: APIs FHIR testadas e validadas

#### Dia 15 - Sexta, 21/03/2026 (4 horas)
**Objetivo**: Retrospectiva Semana 3

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Revisar entregas da semana | DEV1 + DEV2 | Checklist |
| 10:00-11:00 | Testar APIs end-to-end | DEV1 + DEV2 | Relatório testes |
| 11:00-12:00 | Documentar progresso | DEV1 | Status atualizado |
| 14:00-15:00 | Planejar Semana 4 | DEV1 + DEV2 | Plano Semana 4 |

**Entregas**: Retrospectiva Semana 3

---

### SEMANA 4: Integração Básica e Validação MVP (24/03 - 28/03)

#### Dia 16 - Segunda, 24/03/2026 (4 horas)
**Objetivo**: Integração com Florence (Exames)

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Estudar API Florence | DEV1 + DEV2 | Documentação lida |
| 10:00-11:00 | Implementar integração básica | DEV2 | Integração funcionando |
| 11:00-12:00 | Testar fluxo completo | DEV1 + DEV2 | Fluxo testado |
| 14:00-15:00 | Documentar integração | DEV1 | Documentação criada |

**Entregas**: Integração Florence funcionando

#### Dia 17 - Terça, 25/03/2026 (4 horas)
**Objetivo**: Documentação completa MVP

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar guia de instalação | DEV1 | README.md |
| 10:00-11:00 | Criar referência de API | DEV1 | api_reference.md |
| 11:00-12:00 | Criar guia de uso | DEV1 | user_guide.md |
| 14:00-15:00 | Revisar documentação | DEV1 + DEV2 | Documentação revisada |

**Entregas**: Documentação completa do MVP

#### Dia 18 - Quarta, 26/03/2026 (4 horas)
**Objetivo**: Preparação para validação MVP

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Criar apresentação MVP | DEV1 | Slides prontos |
| 10:00-11:00 | Preparar demo ambiente | DEV2 | Ambiente demo |
| 11:00-12:00 | Simular apresentação | DEV1 + DEV2 | Simulação realizada |
| 14:00-15:00 | Ajustes finais | DEV1 + DEV2 | MVP pronto |

**Entregas**: MVP pronto para validação

#### Dia 19 - Quinta, 27/03/2026 (4 horas)
**Objetivo**: Validação MVP com stakeholders

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Preparação final | DEV1 + DEV2 | Ambiente pronto |
| 10:00-12:00 | Validação MVP (2h) | DEV1 + Stakeholders | Feedback coletado |
| 14:00-15:00 | Consolidar feedback | DEV1 | Feedback documentado |

**Entregas**: MVP validado

#### Dia 20 - Sexta, 28/03/2026 (4 horas)
**Objetivo**: Retrospectiva Fase 1 (MVP)

| Horário | Tarefa | Responsável | Entregável |
|---------|--------|-------------|------------|
| 09:00-10:00 | Revisar todas as entregas | DEV1 + DEV2 | Checklist completo |
| 10:00-11:00 | Gerar ata da validação | DEV1 | Ata distribuída |
| 11:00-12:00 | Criar retrospectiva Fase 1 | DEV1 | Retrospectiva completa |
| 14:00-15:00 | Planejar Fase 2 | DEV1 + DEV2 | Plano Fase 2 |

**Entregas**: Retrospectiva Fase 1 completa

---

## 3. FASE 2 - TREINAMENTO ASSISTIDO (SEMANAS 5-8)

### SEMANA 5: Sistema de Cenários (31/03 - 04/04)

**Entregas principais**:
- Gerador de cenários clínicos (100 cenários)
- Tabela `scenarios` populada
- Classificação por dificuldade e módulo
- Embeddings para RAG
- **NOVO**: Ingestão guidelines clínicas no Flowise (SBC, KDIGO, ADA)
- **NOVO**: Configuração Flowise knowledge bases

---

### SEMANA 6: Sistema de Sessões (07/04 - 11/04)

**Entregas principais**:
- Endpoints de treinamento
- Sistema de avaliação automática
- Feedback estruturado
- Dashboard de progresso
- **NOVO**: Integração Flowise chatbot "Dr. Nise"
- **NOVO**: LLM evaluation workflows no Flowise

---

### SEMANA 7: Integrações Avançadas (14/04 - 18/04)

**Entregas principais**:
- Integração Flowise (RAG + Chatbots)
- Integração Ollama (LLM Engine)
- Integração todos os módulos INTELLICARE
- Testes end-to-end
- **NOVO**: Monitoramento Flowise + Ollama

---

### SEMANA 8: Finalização e Validação Final (21/04 - 25/04)

**Entregas principais**:
- Sistema de certificação
- Documentação pedagógica completa
- Validação final com stakeholders
- Retrospectiva Projeto 04 completo
- **NOVO**: Dagger CI/CD pipelines completos
- **NOVO**: Deployment automation

---

## 4. MÉTRICAS DE SUCESSO

### 4.1. Fase 1 (MVP)
- ✅ Schema PostgreSQL criado
- ✅ 5.000 pacientes sintéticos
- ✅ 20.000 observações sintéticas
- ✅ APIs FHIR funcionando (<100ms P99)
- ✅ Integração básica com Florence
- ✅ Documentação completa
- ✅ MVP validado por stakeholders

### 4.2. Fase 2 (Completo)
- ✅ 100 cenários clínicos criados
- ✅ Sistema de treinamento funcionando
- ✅ Feedback automático implementado
- ✅ Integrações com Ollama e n8n
- ✅ Certificação implementada
- ✅ Projeto validado e aprovado

---

**Documento criado por**: DEV1  
**Data**: 26/02/2026  
**Versão**: 1.0  
**Status**: ✅ AGUARDANDO APROVAÇÃO  
**Próximo passo**: Aguardar aprovação para iniciar implementação

