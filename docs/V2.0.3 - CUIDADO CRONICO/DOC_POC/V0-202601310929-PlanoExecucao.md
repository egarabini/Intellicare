# Plano de Execucao - Painel DRC (Prototipo)

**Documento:** V0-202601310929-PlanoExecucao.md
**Projeto:** Painel DRC (Prototipo)
**Versao:** 1.0
**Data:** 31 de Janeiro de 2026
**Autor:** Desenvolvedor (Codex)
**Base:** V0-202601310733-Especificacao Tecnica - Painel DRC (Prototipo).md

## 1. Objetivo

Entregar o prototipo do Painel DRC em Streamlit com mock FHIR em JSON, persistencia PostgreSQL e cache LMDB, cobrindo o escopo funcional completo definido pelo Arquiteto e Planejador.

## 2. Premissas e Decisoes Confirmadas

- Servidor FHIR: Mock simples em JSON + facade Python (FHIRDataStore).
- Persistencia: PostgreSQL como source of truth + LMDB para cache por ID.
- Dataset: sintetico, criado do zero para demonstrar longitudinalidade.
- Escopo UI: eGFR, PA, ACR, K+, meds, pendencias, metas e 4 formularios rapidos.
- Credenciais: sempre via .env (nada hardcoded).

## 3. Plano de Execucao (Passo a Passo)

### 3.1. Preparacao do Repositorio
1. Criar e ativar ambiente virtual do projeto e registrar o comando padrao no README interno do projeto.
2. Mapear a estrutura atual do repo e criar a estrutura minima (src/api, src/core, src/ui, data/seed, tests/).
3. Revisar `DRCFHIRREPO/requirements.txt` e alinhar dependencias minimas (streamlit, fhir.resources, psycopg2/SQLAlchemy, lmdb, pydantic, python-dotenv, pandas, plotly/altair).
4. Criar `.env.example` com variaveis de conexao PostgreSQL e paths do LMDB.
5. Registrar no ANDAMENTO a abertura do ciclo e o inicio do plano.

### 3.2. Camada de Dados (FHIRDataStore)
5. Implementar conexao PostgreSQL e criar o esquema minimo (tabela unica de recursos FHIR com JSONB e indices).
6. Implementar LMDB com chaves `[resource_type]:[resource_id]` e cache por ID.
7. Implementar `get_resource`, `save_resource` e `search_resources` no `FHIRDataStore`.
8. Implementar validacao FHIR com `fhir.resources` antes de persistir.
9. Implementar criacao automatica de Provenance para recursos clinicos criados/atualizados.

### 3.3. Camada de Logica (DRCCoreLogic)
10. Implementar `get_patient_summary` agregando dados para o Resumo DRC.
11. Implementar funcoes de registro rapido: adicionar PA, exame (eGFR/ACR/K+), nota/conduta, pendencia/meta.
12. Implementar calculo de estagio DRC (G/A) a partir das Observations mais recentes.

### 3.4. Dataset Sintetico
13. Definir casos clinicos com series temporais (eGFR, PA, ACR, K+), meds e pendencias.
14. Gerar recursos FHIR JSON (Patient, Observation, Condition, MedicationStatement/Request, CarePlan, Goal, Provenance).
15. Criar rotina de carga do dataset no PostgreSQL e cachear IDs no LMDB.

### 3.5. UI Streamlit
16. Montar layout do Resumo DRC (identificacao, status, tendencias, meds, condicoes, pendencias, metas).
17. Implementar graficos de tendencia (eGFR, PA, ACR, K+).
18. Implementar formularios rapidos e salvar via `DRCCoreLogic`.
19. Implementar feedback de sucesso/erro e atualizacao dos blocos.

### 3.6. Testes e Validacao
20. Criar testes basicos de unidade para `FHIRDataStore` e `DRCCoreLogic`.
21. Validar integracao completa: carga do dataset -> renderizacao -> registro rapido -> persistencia.
22. Ajustar performance basica (cache LMDB e queries PostgreSQL).

### 3.7. Finalizacao e Registro
23. Atualizar o ANDAMENTO com o que foi entregue e pendencias.
24. Versionar conforme orientacao do Arquiteto (tag/nota do ciclo).
25. Solicitar homologacao do Arquiteto.

## 4. Entregaveis

- Estrutura de codigo com `src/api`, `src/core`, `src/ui` e `data/seed`.
- `FHIRDataStore` e `DRCCoreLogic` implementados.
- Dataset sintetico carregavel.
- App Streamlit funcional com o Resumo DRC e formularios rapidos.
- Testes basicos e registro de andamento.

## 5. Riscos e Mitigacoes

- Risco: escopo visual grande para prototipo rapido. Mitigacao: entregar primeiro os blocos essenciais e adicionar os demais em iteracoes curtas.
- Risco: dados sinteticos pouco realistas. Mitigacao: casos clinicos com series e tendencias clinicamente plausiveis.
- Risco: complexidade de persistencia. Mitigacao: tabela unica JSONB e indices minimos.

## 6. Criterios de Pronto (DoD)

- Resumo DRC exibe dados longitudinalmente para pelo menos 3 pacientes sinteticos.
- Formularios rapidos gravam recursos e geram Provenance.
- Graficos de eGFR e PA exibem historico consistente.
- Credenciais isoladas em `.env`.
- ANDAMENTO atualizado e ciclo pronto para homologacao.
