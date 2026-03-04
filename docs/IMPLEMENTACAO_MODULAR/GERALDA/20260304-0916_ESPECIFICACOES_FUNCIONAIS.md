# GERALDA — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 2.0.0
**Modulo:** intellicare-geralda (porta 8006)
**Homenagem:** Geralda Lopes da Silva — enfermeira pioneira na saude comunitaria brasileira

---

## 1. Proposito

A GERALDA e o agente de acompanhamento longitudinal do paciente cronico.
Ela cria e gerencia planos de cuidado personalizados, garantindo que medicos,
enfermeiros e pacientes estejam alinhados no processo terapeutico.

---

## 2. Funcionalidades Implementadas (v1.0 — in-memory)

### 2.1 Planos de Cuidado
- Criar plano personalizado por paciente com metas e condicoes alvo
- Listar planos por paciente
- Ativar/desativar planos

### 2.2 Tarefas Diarias
- Criar tarefas: medicamentos, exercicios, dieta, exames, monitoramento
- Marcar tarefas como concluidas ou puladas
- Listar tarefas por status (pendente, concluida, vencida)
- Calcular taxa de adesao ao plano

### 2.3 Lembretes
- Agendar lembretes com frequencia (unico, diario, semanal, mensal)
- Listar lembretes pendentes
- Integrar com COMUNICACAO para envio automatico

### 2.4 Educacao em Saude
- Materiais educativos pre-cadastrados para DRC, Diabetes e Hipertensao
- Vincular material ao plano de cuidado do paciente
- Busca por condicao clinica

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 Persistencia PostgreSQL (PRIORITARIO)
- Migrar estruturas in-memory para modelos SQLAlchemy
- Dados persistem apos restart do container
- Indices otimizados para busca por patient_id

### 3.2 Integracao FHIR CarePlan
- Sincronizar plano de cuidado com GRAHAME como FHIR CarePlan R4
- Graceful degradation: funciona sem GRAHAME online
- Mapper bidirecional Geralda <-> FHIR CarePlan

### 3.3 Motor de Linguagem Acessivel
- Converter linguagem clinica para linguagem de paciente via Ollama
- Ex: "Insuficiencia renal cronica estadio 3" -> "Seu rim funciona a ~40% do normal"
- Parametro `?simplify=true` nos endpoints

### 3.4 Motor de Eventos
- Regras configuráveis baseadas em eventos do plano:
  - Tarefa vencida ha > 3 dias -> alerta WANDA
  - Meta nao atingida em 30 dias -> notificar responsavel via COMUNICACAO
  - Nova condicao ICD-10 -> sugerir tarefas automaticamente
- Integrar com Kestra para execucao periodica

### 3.5 Integracao com ZILDA
- Ao criar plano, consultar ZILDA para mapear UBS de referencia
- Incluir estabelecimento de referencia no plano de cuidado

---

## 4. Casos de Uso Principais

### UC-01: Criar Plano para Paciente Diabetico
**Ator:** Enfermeiro na UBS
**Fluxo:** Novo paciente DM2 -> Geralda cria plano com tarefas diarias (glicemia, medicamento) e lembretes semanais -> Sincroniza FHIR CarePlan com GRAHAME

### UC-02: Adesao Terapeutica
**Ator:** Medico acompanhando evolucao
**Fluxo:** GET /care-plans/{id}/adherence -> Geralda calcula taxa de adesao por periodo -> Identifica tarefas mais negligenciadas

### UC-03: Alerta de Baixa Adesao
**Ator:** Motor de eventos (Kestra) automatico
**Fluxo:** Job verifica adesao diaria -> Paciente com < 50% em 7 dias -> Geralda dispara alerta WANDA -> WANDA roteia para enfermeiro responsavel via RC

---

## 5. Criterios de Aceite

- [ ] Dados persistem apos docker restart
- [ ] GET /care-plans?patient={id} retorna planos do banco
- [ ] Taxa de adesao calculada corretamente
- [ ] Sincronizacao FHIR CarePlan com GRAHAME
- [ ] Motor de eventos gera alertas para tarefas vencidas
- [ ] Cobertura de testes >= 80%

---

*GERALDA v2.0 — Especificacoes Funcionais — 2026-03-04*
