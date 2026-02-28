# W10-A — Custom Operations Framework — Especificação Funcional

**Workstream:** W10-A
**Responsável:** DEV0
**Módulo:** `intellicare-grahame` + `intellicare-core`
**Status:** Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Permitir que tenants registrem operações FHIR customizadas (instance-level e system-level), sem alterar código do core. Cada tenant pode criar operações como `Patient/$exames-laboratoriais` ou `$relatorio-consolidado`.

---

## 2. Contexto de Negócio

### Problema Atual
- Operações FHIR são fixas no código
- Cada hospital/clínica tem necessidades específicas
- Customização exige deploy de código novo

### Solução Proposta
- Registry de operações por tenant
- Operações definidas via Admin API ou UI
- Execução em sandbox (segurança)

### Benefícios
- Flexibilidade para tenants
- Sem deploy para novas operações
- Alinhado a Medplum v5.0.13+

---

## 3. Requisitos Funcionais

### RF-001 — Instance-level Custom Op
- **Endpoint:** `POST /fhir/{ResourceType}/{id}/$custom-op`
- **Exemplo:** `POST /fhir/Patient/123/$exames-laboratoriais`
- **Input:** Parameters (opcional)
- **Output:** Parameters ou recurso FHIR
- **Regras:** Operação deve estar registrada para o tenant

### RF-002 — System-level Custom Op
- **Endpoint:** `POST /fhir/$custom-op`
- **Exemplo:** `POST /fhir/$relatorio-consolidado`
- **Input:** Parameters (opcional)
- **Output:** Parameters ou recurso FHIR
- **Regras:** Operação deve estar registrada para o tenant

### RF-003 — Registry de Operações
- CRUD de operações customizadas por tenant
- Campos: name, type (instance|system), resourceType, handler (URL ou bot ID)
- Handler pode ser: URL externa, Bot ID, ou código inline (sandbox)

### RF-004 — Execução em Sandbox
- Operações executadas em ambiente isolado
- Timeout configurável (default 30s)
- Sem acesso direto a filesystem ou rede arbitrária

### RF-005 — Validação
- Nome da operação: [a-z][a-z0-9-]* (ex: exames-laboratoriais)
- Não conflitar com operações nativas FHIR
- ResourceType obrigatório para instance-level

### RF-006 — Auditoria
- Log de todas as execuções (tenant, op, user, resultado)
- Métricas de uso por operação

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- Resolução de operação: menor que 50ms
- Execução: depende do handler (timeout 30s default)

### RNF-002 — Segurança
- Isolamento por tenant
- Handler validado antes de registro
- Rate limit por operação (configurável)

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | Instance op | POST /fhir/Patient/123/$exames-laboratoriais | Parameters com lista de exames |
| 2 | System op | POST /fhir/$relatorio-consolidado | Parameters com relatório |
| 3 | Op não registrada | POST /fhir/Patient/123/$op-inexistente | 404 Not Found |
| 4 | Nome inválido | Registrar $validate | 400 (conflito com nativo) |
| 5 | Timeout | Handler demora 60s | 504 Gateway Timeout |

---

## 6. Referências

- FHIR Operations: https://www.hl7.org/fhir/operations.html
- Medplum Custom Ops v5.0.13+
- Parameters: https://www.hl7.org/fhir/parameters.html
