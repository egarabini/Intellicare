# 📋 W2-B — Especificação Funcional: FHIR Access Policies

## 1. Objetivo

Implementar **Access Policies FHIR** no IntelliCare, substituindo o RBAC básico do Keycloak por um sistema de **controle de acesso baseado em atributos (ABAC)** granular, inspirado no Medplum. Isso permite controlar acesso por recurso, campo, compartment e critérios dinâmicos.

---

## 2. Conceito

Uma **Access Policy** define:
- **Quais recursos** um usuário pode acessar (por ResourceType)
- **Quais campos** são visíveis/editáveis/ocultos
- **Qual compartment** limita o escopo (ex: só pacientes da minha unidade)
- **Quais interações** são permitidas (search, read, create, update, delete)
- **Critérios dinâmicos** via FHIR Search (ex: só Encounters do meu setor)

---

## 3. Funcionalidades

### 3.1 Definição de Access Policies
```json
{
  "resourceType": "AccessPolicy",
  "name": "Enfermeiro - Setor A",
  "resource": [
    {
      "resourceType": "Patient",
      "interaction": ["search", "read"],
      "criteria": "Patient?general-practitioner=Practitioner/%profile.id"
    },
    {
      "resourceType": "Observation",
      "interaction": ["search", "read", "create"],
      "readonlyFields": ["status", "category"],
      "hiddenFields": ["meta"]
    },
    {
      "resourceType": "MedicationRequest",
      "readonly": true
    }
  ],
  "compartment": {
    "reference": "Organization/setor-a"
  }
}
```

### 3.2 Tipos de Controle

| Controle | Descrição | Exemplo |
|---|---|---|
| **ResourceType** | Acesso por tipo de recurso | "Enfermeiro pode ver Patient mas não Bot" |
| **Interaction** | Tipo de operação permitida | "search, read" (sem create/update/delete) |
| **Criteria** | Filtro FHIR dinâmico | "Só Patients do meu Practitioner" |
| **readonlyFields** | Campos não-editáveis | "status e category são read-only" |
| **hiddenFields** | Campos invisíveis | "meta é oculto para enfermeiros" |
| **readonly** | Recurso inteiro read-only | "MedicationRequest só leitura" |
| **Compartment** | Escopo organizacional | "Só dados da Organization/setor-a" |
| **IP Access Rules** | Restrição por IP | "Admin só de IP interno" |

### 3.3 Atribuição de Policies
- Uma policy é atribuída via **ProjectMembership** (no nosso caso, TenantMembership)
- Um usuário pode ter múltiplas policies (compostas)
- Policies são parametrizáveis (`%profile`, `%patient` → substituídos por referências do usuário)

### 3.4 Integração com Keycloak
- **Manter Keycloak para autenticação** (login, MFA, SSO)
- **Access Policies para autorização** (o que pode fazer)
- JWT do Keycloak contém `membership_id` → resolve para policies
- Keycloak roles mapeiam para groups de policies

### 3.5 SMART-on-FHIR Scopes (Preview)
- Suporte básico a SMART scopes: `patient/*.read`, `user/Observation.write`
- Scopes do JWT limitam a AccessPolicy efetiva
- Preparação para Onda 4 (SMART Launch)

---

## 4. Casos de Uso

| Persona | Policy | Resultado |
|---|---|---|
| Médico | Full access ao compartment dos seus pacientes | Vê e edita tudo dos seus pacientes |
| Enfermeiro | Read Patient + Create Observation no setor | Cria observações, não edita medicações |
| Recepcionista | Read/Create Encounter + Patient (nome, contato) | Agenda consultas, não vê dados clínicos |
| Admin local | Gestão de users e roles do tenant | Não vê dados clínicos |
| Sistema externo | Read-only em Observation, DiagnosticReport | Integração sem risco de escrita |

---

## 5. Referência Medplum

| Componente | Arquivo | Nota |
|---|---|---|
| Access Policy Builder | `fhir/accesspolicy.ts` | 318 linhas — parameterized compound policies |
| SMART Scopes | `fhir/smart.ts` | 8KB — scope-to-policy translation |
| Test Suite | `fhir/accesspolicy.test.ts` | 102KB — testes exaustivos |
