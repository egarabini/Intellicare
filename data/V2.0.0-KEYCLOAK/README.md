# V2.0.0-KEYCLOAK — Carga de Dados para Staging

Dados consistentes com a abordagem Keycloak (realm `bemcuidar`), preparados para gravação no servidor FHIR do IntelliCare.

## Estrutura

```
data/V2.0.0-KEYCLOAK/
├── README.md
├── establishments/           # Organizações (hospitais, UBS, secretarias)
├── practitioners/            # Profissionais (médicos, enfermeiros)
├── conditions_anon/         # Condições e alergias anonimizadas
├── fhir/                     # Recursos FHIR (14 tipos)
│   ├── patients/ │ practitioners/ │ practitionerroles/
│   ├── conditions/ │ observations/ │ encounters/ │ medications/
│   ├── allergies/ │ goals/ │ careplans/ │ procedures/
│   ├── diagnosticreports/ │ relatedpersons/
│   └── organizations/
```

## Recursos FHIR — demonstra todo o potencial do IntelliCare

| Recurso | Módulo | Uso |
|---------|--------|-----|
| Organization | GRAHAME, Zilda | Hospitais, UBS, secretarias |
| Patient | Todos | Pacientes (REG Brasília/Montes Claros) |
| Practitioner | Comunicação, Gestor | Médicos, enfermeiros |
| PractitionerRole | Encounters | Vínculo profissional–organização |
| Condition | Oswaldo, IPS | DRC, DM2, HAS |
| Observation | AlertHub, IPS | Creatinina, eGFR, PA (incl. valores críticos) |
| Encounter | Donabedian | Atendimentos |
| MedicationRequest | IPS, Geralda | Prescrições |
| AllergyIntolerance | IPS, CDS Hooks | Alergias |
| CarePlan + Goal | Geralda | Planos de cuidado |
| Procedure | IPS | Diálise, consultas |
| DiagnosticReport | Bulk Export | Relatórios |
| RelatedPerson | Comunicação | Contatos de emergência |

## Tenants (Keycloak)

| tenant_id | Descrição | Estabelecimentos |
|-----------|-----------|-----------------|
| `secretaria-brasilia` | SES-DF | Secretaria de Estado de Saúde do DF |
| `secretaria-montesclaros` | SMS Montes Claros | Secretaria Municipal de Saúde |
| `hospital-brasilia` | Hospital Regional Asa Norte | HRAN, HBDF |
| `hospital-montesclaros` | Santa Casa Montes Claros | Santa Casa, Hospital Universitário |

## Estrutura: Gestores, Unidades e Profissionais

| Tenant | Gestor (Keycloak) | Unidades | Profissionais |
|--------|-------------------|----------|---------------|
| secretaria-brasilia | gestor.sesdf@saude.df.gov.br | Sede SES-DF, UBS Asa Sul | Enf. Maria do Carmo |
| secretaria-montesclaros | gestor.sms@montesclaros.mg.gov.br | Sede SMS, UBS Centro | Enf. Paulo Henrique |
| hospital-brasilia | gestor.hran@saude.df.gov.br | HRAN, HBDF | Dr. Carlos, Dra. Ana, Dr. Roberto, Dra. Fernanda, Dr. André |
| hospital-montesclaros | gestor.santacasa@santacasa-mc.org.br | Santa Casa MC | Dr. João, Dra. Luciana, Dra. Beatriz |

## Como gerar a carga

```bash
# Gerar todos os dados (FHIR + Locations + PractitionerRoles com unidades)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK

# Volume reduzido (100 pacientes por cidade)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK --limit 100
```

## Carga no Keycloak (realm bemcuidar)

```bash
# Com senha do admin
python scripts/seed_keycloak_staging.py --admin-pass SUA_SENHA_ADMIN

# Ou: export KEYCLOAK_ADMIN_PASSWORD=xxx && python scripts/seed_keycloak_staging.py
```

Cria: 1 PLATFORM_ADMIN, 4 TENANT_GESTOR, profissionais (MEDICO/ENFERMEIRO) com tenant_id.

## Gravação no FHIR Server

Com o GRAHAME rodando (porta 8012):

```bash
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir
# Ou com URL customizada:
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --base-url http://localhost:8012
```

> **Nota:** O GRAHAME pode exigir autenticação. Use `--token <JWT>` se necessário.

## Documentação

Ver **`docs/CARGA_DADOS/`** para documentação completa do processo de carga.
