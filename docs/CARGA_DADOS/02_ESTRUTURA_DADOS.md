# Estrutura de Dados

## Pasta data/

```
data/
├── README.md
├── REG-brasilia.csv             # Fonte: pessoas Brasília (~2.600)
├── REG-montesClaros.csv         # Fonte: pessoas Montes Claros (~9.400)
├── estabelecimentos/            # Estabelecimentos (CNES)
└── V2.0.0-KEYCLOAK/            # Abordagem Keycloak
    ├── README.md
    ├── establishments/          # Organizações e Locations
    │   ├── organizacoes.json    # FHIR Organization (7)
    │   ├── locations.json       # FHIR Location (7 unidades)
    │   ├── lista_estabelecimentos.csv
    │   └── estrutura_tenant_unidades.json
    ├── practitioners/           # Profissionais
    │   └── profissionais.json   # 10 profissionais (org, location, tenant_id)
    ├── conditions_anon/         # Condições anonimizadas
    │   ├── drc_estagios.json
    │   ├── condicoes_comuns.json
    │   └── alergias_comuns.json
    ├── keycloak/                # Usuários Keycloak
    │   └── usuarios_staging.json
    └── fhir/                    # Recursos FHIR gerados
        ├── organizations/
        ├── locations/
        ├── patients/
        ├── practitioners/
        ├── practitionerroles/
        ├── conditions/
        ├── observations/
        ├── encounters/
        ├── medications/
        ├── allergies/
        ├── goals/
        ├── careplans/
        ├── procedures/
        ├── diagnosticreports/
        └── relatedpersons/
```

## Hierarquia Organization

- **SES-DF** (secretaria-brasilia)
  - `partOf`: —
  - Unidades: Sede SES-DF, UBS Asa Sul (`partOf` → SES-DF)
- **SMS Montes Claros** (secretaria-montesclaros)
  - Unidades: Sede SMS, UBS Centro MC (`partOf` → SMS)
- **HRAN, HBDF** (hospital-brasilia) — estabelecimentos
- **Santa Casa MC** (hospital-montesclaros)

## Arquivos fonte

| Arquivo | Colunas principais |
|--------|---------------------|
| REG-brasilia.csv | NOME_COMPLETO, CPF, DATA_NASCIMENTO, SEXO, CEP, TELEFONE, EMAIL |
| REG-montesClaros.csv | Idem |
