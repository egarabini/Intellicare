# Carga no FHIR Server (GRAHAME)

## Script

```bash
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| fhir_dir | (obrigatório) | Diretório com subpastas de recursos |
| --base-url | http://localhost:8012 | URL do GRAHAME |
| --token | — | JWT Bearer (se autenticação exigida) |

## Ordem de carga

O script carrega na ordem de dependências:

1. Organization
2. Location
3. Patient
4. Practitioner
5. PractitionerRole
6. Condition
7. Observation
8. Encounter
9. MedicationRequest
10. AllergyIntolerance
11. Goal
12. CarePlan
13. Procedure
14. DiagnosticReport
15. RelatedPerson

## Pré-requisito

Executar `seed_staging_data.py` antes para gerar os arquivos em `data/V2.0.0-KEYCLOAK/fhir/`.

## Autenticação

Se o GRAHAME exigir autenticação:

```bash
# Obter token (exemplo com Keycloak)
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/bemcuidar/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=intellicare-portal" \
  -d "username=admin@intellicare.ia.br" -d "password=Staging@2026!" \
  | jq -r '.access_token')

python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --token "$TOKEN"
```
