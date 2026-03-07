---
projeto: intellicare
tags: [fhir, medplum, auth]
status: draft
---
# Controle de Acesso e IAM

## Introdução
Este documento detalha o controle de acesso usando Medplum e Keycloak para a plataforma IntelliCare.

## Arquitetura
A arquitetura baseia-se no padrão OAuth2 e SMART-on-FHIR 2.0.

### Componentes
- **Keycloak:** Identity Provider para Single Sign-On.
- **Medplum:** FHIR Server que armazena os recursos e os Access Policies.

## Medplum Access Policies
As Access Policies do Medplum permitem granularidade de recursos.
Exemplo: Um paciente só pode ler seus próprios recursos (Observações, Medicações).

### Como funciona
1. O usuário loga no Keycloak.
2. O Token JWT é repassado ao Medplum.
3. O Medplum lê as Access Policies associadas ao `ProjectMembership`.
