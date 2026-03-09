# Dados IntelliCare

Pasta central de dados para staging, testes e cargas iniciais.

## Estrutura

```
data/
├── README.md                    # Este arquivo
├── REG-brasilia.csv             # Pessoas (Brasília) — fonte para pacientes
├── REG-montesClaros.csv         # Pessoas (Montes Claros) — fonte para pacientes
├── estabelecimentos/            # Estabelecimentos de saúde (CNES)
│   └── README.md
└── V2.0.0-KEYCLOAK/            # Abordagem Keycloak (realm bemcuidar)
    ├── README.md
    ├── establishments/          # Organizações (hospitais, UBS, secretarias)
    ├── conditions_anon/        # Condições anonimizadas (DRC, etc.)
    ├── fhir/                   # Recursos FHIR gerados (patients, conditions, ...)
    └── source/                 # Referências aos dados fonte
```

## Abordagens

Cada abordagem de autenticação/autorização tem sua pasta em `data/`:

| Pasta | Descrição |
|-------|-----------|
| `V2.0.0-KEYCLOAK` | Realm `bemcuidar`, tenants (secretarias, hospitais), multi-tenant |

## Como gerar dados

```bash
# Gerar carga completa (V2.0.0-KEYCLOAK)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK

# Volume reduzido (500 pacientes por cidade)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK --limit 500

# Apenas pacientes
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK --only patients
```

## Carregar no FHIR Server

```bash
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir
```

## Documentação completa

Ver **`docs/CARGA_DADOS/`** para guia detalhado, estrutura de dados, carga Keycloak e FHIR.
