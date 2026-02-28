# 📋 W4-B — Especificação: SMART-on-FHIR Launch

## 1. Objetivo
Implementar o protocolo SMART-on-FHIR App Launch Framework, permitindo que aplicações de terceiros se autentiquem e acessem dados FHIR do IntelliCare de forma padronizada.

## 2. Funcionalidades

### 2.1 EHR Launch
- App lançado de dentro do IntelliCare (contexto do paciente/encontro)
- URL: `{app_url}?iss={fhir_server}&launch={launch_token}`
- Launch context inclui: patient, encounter, practitioner

### 2.2 Standalone Launch
- App acessa IntelliCare externamente
- Seleção de paciente dentro do app
- Token exchange OAuth2 com extensões SMART

### 2.3 SMART Scopes
- `patient/*.read` — Leitura de todos os recursos do paciente
- `user/Observation.write` — Escrita de Observations como usuário
- `launch/patient` — Contexto de paciente no launch
- `openid fhirUser` — Identidade do usuário

### 2.4 Well-Known Endpoint
```json
GET /.well-known/smart-configuration
{
  "authorization_endpoint": "https://auth.intellicare/realms/tenant/protocol/openid-connect/auth",
  "token_endpoint": "https://auth.intellicare/realms/tenant/protocol/openid-connect/token",
  "capabilities": ["launch-ehr", "launch-standalone", "client-public", "sso-openid-connect"],
  "scopes_supported": ["openid", "fhirUser", "launch", "launch/patient", "patient/*.*", "user/*.*"]
}
```

## 3. Integração com Keycloak
- Keycloak como Authorization Server
- Custom Protocol Mapper para SMART scopes
- Launch context (patient, encounter) serializado no token
- Client Registration para apps SMART

## 4. Referência Medplum
- `fhir/smart.ts` (8KB) — Scope-to-AccessPolicy translation
- `oauth/token.ts` (22KB) — Full OAuth2/OIDC token endpoint

## 5. Plano: 10 dias (Dev 4)
- Dia 1-2: Well-known endpoint + FHIR CapabilityStatement
- Dia 3-4: Keycloak custom mapper para SMART scopes
- Dia 5-6: EHR Launch flow
- Dia 7-8: Standalone Launch flow
- Dia 9-10: Testes com SMART Health IT test suite

## 6. Critérios de Aceite
1. ✅ Well-known endpoint retorna JSON válido
2. ✅ EHR Launch funcional (contexto patient propagado)
3. ✅ Standalone Launch funcional (seleção de paciente)
4. ✅ SMART scopes limitam AccessPolicy efetiva
5. ✅ Compatível com SMART Health IT test suite
