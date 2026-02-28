# W10-B — ConceptMap Import + $translate — Especificação Funcional

**Workstream:** W10-B
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (Terminology)
**Status:** Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Importar ConceptMap e expor operação `ConceptMap/$translate` para mapeamento de códigos entre terminologias (ex: CID-10 para SNOMED, LOINC para código interno).

---

## 2. Contexto de Negócio

### Problema Atual
- Sistemas usam terminologias diferentes (CID-10, SNOMED, LOINC, códigos internos)
- Conversão manual ou scripts ad-hoc
- Sem operação FHIR padronizada

### Solução Proposta
- Importar ConceptMap (Bundle ou recurso)
- Operação ConceptMap/$translate conforme FHIR R4
- Mapeamento bidirecional quando aplicável

### Benefícios
- Interoperabilidade entre sistemas
- Padrão FHIR (Medplum v5.0.14+)
- Tenants importam seus mapeamentos

---

## 3. Requisitos Funcionais

### RF-001 — Import de ConceptMap
- **Endpoint:** `POST /fhir/ConceptMap` ou `POST /fhir` (Bundle)
- **Input:** ConceptMap ou Bundle com ConceptMap
- **Regras:** Validar estrutura FHIR; indexar grupos e elementos para $translate
- **Output:** ConceptMap criado/atualizado

### RF-002 — Operação $translate
- **Endpoint:** `POST /fhir/ConceptMap/{id}/$translate` ou `POST /fhir/ConceptMap/$translate`
- **Input:** Parameters com code, system, target (opcional), source (opcional)
- **Output:** Parameters com result (boolean), match (conceito equivalente)
- **Regras:** Buscar no ConceptMap; retornar equivalente ou no match

### RF-003 — Parâmetros de Entrada
- code (required): Código a traduzir
- system (optional): Sistema de origem (URL)
- source (optional): ConceptMap source (se múltiplos)
- target (optional): Sistema alvo desejado (URL)
- reverse (optional): Traduzir no sentido inverso

### RF-004 — Parâmetros de Saída
- result: boolean — encontrou equivalente?
- match: Coding — conceito equivalente (quando result=true)
- message: string — mensagem informativa (opcional)

### RF-005 — Múltiplos ConceptMaps
- Se ConceptMap/$translate (sem id): usar ConceptMap por URL ou escopo
- Se ConceptMap/{id}/$translate: usar ConceptMap específico

### RF-006 — Suporte a Grupos
- ConceptMap.group.element
- Mapeamento source para target
- Suportar equivalence (equal, equivalent, wider, narrower, etc.)

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- $translate: menor que 100ms para ConceptMap com até 10k mapeamentos
- Import: menor que 5s para ConceptMap com 10k elementos

### RNF-002 — Indexação
- Índice por (source system, source code) para lookup rápido
- Índice por (target system, target code) para reverse

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | Import ConceptMap | POST ConceptMap | 201 Created |
| 2 | $translate sucesso | code=A09, system=ICD-10 | match com SNOMED equivalente |
| 3 | $translate sem match | code=XXX, system=ICD-10 | result=false |
| 4 | $translate reverse | code=..., target=ICD-10 | match em CID-10 |
| 5 | Bundle com ConceptMaps | POST Bundle | Todos importados |

---

## 6. Referências

- FHIR ConceptMap: https://www.hl7.org/fhir/conceptmap.html
- FHIR $translate: https://www.hl7.org/fhir/conceptmap-operation-translate.html
- Medplum ConceptMap Import v5.0.14+
