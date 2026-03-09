# W11-C — Display language overrides (i18n) — Especificação Funcional

**Workstream:** W11-C
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (Terminology)
**Status:** Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Permitir override de display em conceitos codificados conforme idioma preferido do cliente (Accept-Language), suportando internacionalização de terminologias.

---

## 2. Contexto de Negócio

### Problema Atual
- Códigos retornam display em um único idioma (ex: inglês)
- Sistemas multilíngues precisam de traduções
- CodeSystem.concept.designation contém múltiplos idiomas

### Solução Proposta
- Respeitar header Accept-Language nas operações de terminologia
- Retornar designation no idioma preferido quando disponível
- Fallback para idioma padrão (ex: pt-BR, en)

### Benefícios
- Portal em português exibe códigos em português
- Suporte a múltiplos idiomas
- Alinhado a Medplum v5.0.11+

---

## 3. Requisitos Funcionais

### RF-001 — Accept-Language
- Operações $lookup, $validate-code, $expand, $translate respeitam Accept-Language
- Formato: `Accept-Language: pt-BR, pt;q=0.9, en;q=0.8`
- Ordem de preferência por q-value

### RF-002 — Designation por idioma
- CodeSystem.concept.designation com use e language
- Buscar designation onde language matches Accept-Language
- Se não houver: fallback para designation sem language ou primeiro disponível

### RF-003 — ValueSet $expand
- Retornar display no idioma preferido nos conceitos expandidos
- ConceptMap $translate: match.display no idioma preferido

### RF-004 — Recursos FHIR com Coding
- Ao serializar recursos (Patient, Observation, etc.): opcionalmente resolver display de Coding conforme Accept-Language
- Configurável (pode ser opt-in por endpoint)

### RF-005 — Idiomas suportados
- Depende dos dados no CodeSystem (designations)
- Comum: pt-BR, en, es
- Sem designation: usar display padrão do conceito

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- Lookup de designation por idioma: índice por (code, language)
- Impacto mínimo no tempo de resposta

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | $lookup pt-BR | Accept-Language: pt-BR | display em português |
| 2 | $lookup en | Accept-Language: en | display em inglês |
| 3 | $lookup sem designation pt | Accept-Language: pt-BR | fallback para en ou default |
| 4 | $expand com Accept-Language | ValueSet $expand | conceitos com display no idioma |
| 5 | Múltiplos idiomas (q-values) | pt-BR, pt;q=0.9, en;q=0.8 | primeiro disponível na ordem |
