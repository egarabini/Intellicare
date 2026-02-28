# W11-B — Terminology ($lookup, $validate-code) — Especificação Funcional

**Workstream:** W11-B
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (Terminology)
**Status:** Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Implementar operações FHIR de terminologia conforme Medplum e FHIR R4:
- **CodeSystem/$lookup** — obter propriedades de um código
- **CodeSystem/$validate-code** — validar se código pertence ao sistema

---

## 2. Contexto de Negócio

### Problema Atual
- Terminology Service (W5-C) pode não expor $lookup e $validate-code
- Sistemas precisam validar códigos antes de salvar
- Lookup necessário para obter display e propriedades

### Solução Proposta
- Operações padrão FHIR
- Integração com CodeSystem e ValueSet existentes
- Suporte a CID-10, LOINC, SNOMED (conforme disponível)

### Benefícios
- Validação de códigos em formulários
- Lookup para autocomplete e exibição
- Interoperabilidade FHIR

---

## 3. Requisitos Funcionais

### RF-001 — CodeSystem/$lookup
- **Endpoint:** `POST /fhir/CodeSystem/$lookup` ou `POST /fhir/CodeSystem/{id}/$lookup`
- **Input:** Parameters com code, system, version (opcional)
- **Output:** Parameters com display, designations, properties
- **Regras:** Buscar no CodeSystem; retornar propriedades do código

### RF-002 — CodeSystem/$validate-code
- **Endpoint:** `POST /fhir/CodeSystem/$validate-code` ou `POST /fhir/CodeSystem/{id}/$validate-code`
- **Input:** Parameters com code, system, display (opcional), version (opcional)
- **Output:** Parameters com result (boolean), display (opcional)
- **Regras:** Verificar se código existe no CodeSystem ou ValueSet

### RF-003 — Parâmetros $lookup
- code (required)
- system (required para CodeSystem/$lookup sem id)
- version (optional)

### RF-004 — Parâmetros $validate-code
- code (required)
- system (required)
- display (optional) — validar display também
- version (optional)

### RF-005 — ValueSet/$validate-code
- Validar código contra ValueSet (expandido)
- Input: code, system, url (ValueSet)

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- $lookup: menor que 100ms
- $validate-code: menor que 200ms (com expand de ValueSet)

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | $lookup sucesso | code=A09, system=ICD-10 | display, properties |
| 2 | $lookup não encontrado | code=XXX | OperationOutcome |
| 3 | $validate-code válido | code=A09, system=ICD-10 | result=true |
| 4 | $validate-code inválido | code=XXX | result=false |
| 5 | ValueSet/$validate-code | code, url=ValueSet | result conforme membership |
