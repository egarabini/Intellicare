# W9-C — On-behalf-of Header — Especificação Funcional

**Workstream:** W9-C
**Responsável:** DEV0
**Módulo:** `intellicare-auth` + `intellicare-core`
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Suportar header **`X-On-Behalf-Of`** para delegação de acesso: usuário A (ex: coordenador) age em nome do usuário B (ex: médico), permitindo operações como "médico A visualiza agenda do médico B" ou "secretária agenda para o paciente em nome do médico".

---

## 2. Contexto de Negócio

### Problema Atual
Sem delegação, cada usuário só acessa seus próprios dados. Cenários comuns:
- Coordenador precisa acessar dados de vários médicos
- Secretária agenda consultas em nome do médico
- Supervisor revisa ações de residentes

### Solução Proposta
Header `X-On-Behalf-Of: {user_id}` indica que o usuário autenticado está agindo em nome de outro. O sistema valida permissão de delegação e usa o contexto do usuário delegado para autorização.

### Benefícios
- **Delegação explícita** — auditoria clara (quem fez, em nome de quem)
- **Flexibilidade** — suporta workflows hospitalares
- **Compliance** — rastreabilidade total

---

## 3. Requisitos Funcionais

### RF-001 — Header X-On-Behalf-Of
- **Formato:** `X-On-Behalf-Of: {user_id}` ou `X-On-Behalf-Of: Practitioner/{id}`
- **Opcional:** Se ausente, comportamento atual (sem delegação)

### RF-002 — Validação de Permissão
- Verificar se usuário autenticado tem permissão para agir em nome do delegado
- Regras: mesmo tenant; role com `on_behalf_of` ou relação hierárquica
- Se não autorizado: HTTP 403

### RF-003 — Contexto de Autorização
- Com header válido: usar `on_behalf_of_user` para checagem de permissões
- Ex: "Pode ver Patient X?" → verificar permissões do médico delegado

### RF-004 — Auditoria
- Todas as ações com On-behalf-of devem registrar:
  - `actor`: usuário autenticado (quem fez)
  - `on_behalf_of`: usuário delegado (em nome de quem)
- Formato: AuditEvent ou log estruturado

### RF-005 — Escopo
- Aplicar a endpoints FHIR e API protegidos
- Não aplicar a endpoints de autenticação

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Segurança
- Não permitir delegação para usuário de outro tenant
- Rate limit em tentativas de delegação inválida

### RNF-002 — Performance
- Overhead < 10ms por request

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída |
|---|---------|---------|-------|
| 1 | Delegação válida | Token + X-On-Behalf-Of: user_B | Acesso como user_B |
| 2 | Delegação inválida | Token + X-On-Behalf-Of: user_outro_tenant | 403 |
| 3 | Sem permissão | User sem role on_behalf_of | 403 |
| 4 | Sem header | Token apenas | Comportamento atual |
| 5 | Auditoria | Request com On-behalf-of | Log com actor + on_behalf_of |

---

## 6. Referências

- Medplum On-behalf-of: v5.0.12+
- OAuth2 On-Behalf-Of: RFC 8693 (conceito similar)
