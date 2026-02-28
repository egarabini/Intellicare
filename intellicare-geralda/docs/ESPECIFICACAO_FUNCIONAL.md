# intellicare-geralda — Especificacao Funcional

> Homenagem a Geralda Lopes da Silva, enfermeira brasileira dedicada ao cuidado e a educacao em saude.

## 1. Proposito

O intellicare-geralda sustenta a **continuidade do cuidado e o vinculo com o paciente**. Traduz orientacoes clinicas em acoes praticas, organiza o cuidado diario e fortalece a adesao terapeutica.

## 2. Valor de Negocio

- Melhoria na adesao ao tratamento
- Reducao de faltas em consultas e exames
- Empoderamento do paciente no autocuidado
- Fortalecimento do vinculo equipe-paciente

## 3. Funcionalidades

### 3.1 Gestao do Cuidado Diario
- Organizacao de atividades de cuidado por paciente
- Checklist de tarefas diarias (medicamentos, exercicios, dieta)
- Acompanhamento de cumprimento

### 3.2 Sistema de Lembretes
- Lembretes personalizados para medicamentos
- Alertas de consultas e exames agendados
- Notificacoes configuráveis (frequencia, canal)

### 3.3 Preparacao para Consultas
- Checklist pre-consulta
- Resumo do historico recente para o paciente levar
- Orientacoes sobre exames preparatorios

### 3.4 Educacao em Saude
- Materiais educativos personalizados por condicao
- Linguagem acessivel (adequada ao nivel de letramento)
- Formatos variados (texto, infografico, audio)

### 3.5 Comunicacao Equipe-Paciente
- Canal de mensagens entre equipe e paciente
- Respostas automatizadas para duvidas frequentes
- Escalonamento para profissional quando necessario

## 4. Origem do Codigo

- **Novo desenvolvimento** — conceito definido, sem codigo existente
- Usa FHIR CarePlan como base do plano de cuidado

## 5. Integracao

- Roda sozinho: Interface para paciente + painel para equipe
- Integrado: Wanda encaminha orientacoes para Geralda executar
- Consome: CarePlan FHIR, dados de medicamentos, agendas
