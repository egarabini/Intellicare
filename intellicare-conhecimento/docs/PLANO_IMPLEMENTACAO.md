# intellicare-conhecimento - Plano de Implementacao

## Status Atual
- MVP funcional entregue para o GAP 1.
- Camada de conhecimento formal operacional via API e dados seed.

## Fase 1 (Concluida)
- [x] Modelagem de protocolos, terminologias e templates
- [x] Persistencia em arquivos YAML/JSON
- [x] Versionamento e historico de protocolos
- [x] Workflow de aprovacao/publicacao
- [x] RAG MVP (indexacao + retrieval)
- [x] Endpoints REST principais
- [x] Testes de servicos e API

## Fase 2 (Proxima)
- [ ] Persistir metadados em PostgreSQL
- [ ] Substituir retriever MVP por pgvector/embedding provider oficial
- [ ] Controle de acesso por papel (autor/revisor/aprovador)
- [ ] Auditoria detalhada de mudancas por usuario
- [ ] Cliente SDK para consumo por Florence, Oswaldo e Pierre

## Fase 3 (Producao)
- [ ] Workflow com SLA e filas de aprovacao
- [ ] RAG hibrido (semantico + keyword + filtros clinicos)
- [ ] Integracao FHIR (Library/PlanDefinition/ValueSet)
- [ ] Politica de backup e retention de historico

## Criterios de Conclusao do GAP 1
- [x] Protocolos versionados
- [x] Pathways e linhas de cuidado estruturados
- [x] Terminologias CID-10/LOINC/SNOMED
- [x] Templates de CarePlan por condicao
- [x] RAG consumivel via API
- [x] Workflow de aprovacao/publicacao

