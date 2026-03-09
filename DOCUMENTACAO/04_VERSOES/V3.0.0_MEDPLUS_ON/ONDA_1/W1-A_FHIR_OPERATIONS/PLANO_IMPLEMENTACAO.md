# 📅 W1-A — Plano de Implementação: Operações FHIR

## Visão Geral
- **Duração estimada:** 10 dias úteis
- **Desenvolvedores:** 2 (Dev 1 + Dev 2)
- **Módulo:** `intellicare-grahame`

---

## Sprint 1 (Dias 1-5) — Fundação + $everything + $summary

### Dia 1-2: Fundação (Dev 1 + Dev 2 em pair)
- [ ] Criar package `grahame/fhir/operations/`
- [ ] Implementar `compartment.py` — definição do Patient Compartment
- [ ] Implementar `reference_resolver.py` — resolução recursiva de referências
- [ ] Implementar router `fhir_operations.py` com tratamento de erros padronizado (`OperationOutcome`)
- [ ] Criar helper `fhir_error()` para respostas de erro FHIR
- [ ] Adicionar dependências ao `pyproject.toml` (`fhir.resources>=7.0`)
- [ ] Setup de testes com fixtures FHIR

### Dia 2-3: `$everything` (Dev 1)
- [ ] Implementar `patient_everything.py`
- [ ] Query SQL compartmentalizada por tenant
- [ ] Suporte a `_since`, `_count`, `_offset`, `_type`, `start`, `end`
- [ ] Resolução recursiva de referências (Organization, Practitioner, etc.)
- [ ] Deduplicação de resultados
- [ ] Testes unitários (mínimo 8 cenários)
- [ ] Teste de integração com DB

### Dia 2-4: `$summary` (Dev 2)
- [ ] Implementar `ips_sections.py` — mapeamento LOINC para seções
- [ ] Implementar classificador automático de Observation (vital-signs, social-history, results)
- [ ] Implementar classificador de Condition (problem-list vs health-concerns)
- [ ] Builder de Composition com todas as 18 seções
- [ ] Geração de narrative text (HTML) para cada seção
- [ ] `patient_summary.py` — handler principal
- [ ] Testes unitários (mínimo 10 cenários)

### Dia 5: Integração + Review
- [ ] Code review cruzado (Dev 1 review $summary, Dev 2 review $everything)
- [ ] Testes end-to-end com dados realistas
- [ ] Documentação dos endpoints
- [ ] PR #1 — $everything + $summary

---

## Sprint 2 (Dias 6-10) — $expand + $validate + $evaluate-measure

### Dia 6-7: `$expand` (Dev 1)
- [ ] Criar migration para tabela `fhir_codesystem_concepts`
- [ ] Implementar carga de CodeSystems padrão (CID-10, LOINC, TUSS)
- [ ] Implementar `valueset_expand.py`
- [ ] Filtro por texto (case-insensitive, contains)
- [ ] Paginação
- [ ] Testes unitários

### Dia 6-7: `$validate` (Dev 2)
- [ ] Implementar `resource_validate.py`
- [ ] Validação estrutural via `fhir.resources` (Pydantic)
- [ ] Conversão de erros Pydantic → `OperationOutcome`
- [ ] Suporte a `mode` (create, update)
- [ ] Testes unitários

### Dia 8-9: `$evaluate-measure` (Dev 1 + Dev 2)
- [ ] Implementar `measure_evaluate.py`
- [ ] Parser de Measure groups (population, denominator, numerator)
- [ ] Avaliação de critérios FHIR Search contra dados do paciente
- [ ] Cálculo de scores
- [ ] Builder de MeasureReport
- [ ] Integração conceitual com Donabedian
- [ ] Testes unitários

### Dia 10: Finalização
- [ ] Testes de integração completos (todas as 5 operações)
- [ ] Testes de multi-tenancy (verificar isolamento)
- [ ] Atualização da documentação do módulo
- [ ] PR #2 — $expand + $validate + $evaluate-measure
- [ ] Merge final

---

## Critérios de Aceite

1. ✅ Todos os 5 endpoints retornam JSON FHIR R4 válido
2. ✅ Erros retornam `OperationOutcome` padronizado
3. ✅ Multi-tenancy funcional (dados isolados entre tenants)
4. ✅ Autenticação JWT obrigatória em todos os endpoints
5. ✅ Paginação funcional em `$everything` e `$expand`
6. ✅ `$summary` gera Composition com pelo menos 10 das 18 seções
7. ✅ Cobertura de testes ≥ 80%
8. ✅ Documentação OpenAPI atualizada

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Dados FHIR insuficientes no CDR para testar | Alto | Criar script de seed com dados realistas |
| Performance do $everything em pacientes com muitos dados | Médio | Limite padrão de 1000 recursos, paginação |
| Complexidade do $summary (18 seções) | Alto | Implementar 10 seções na v1, expandir depois |
| $evaluate-measure depende de Measures pré-cadastradas | Médio | Criar 3 Measures exemplo para testes |
