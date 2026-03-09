# Carga de Dados — IntelliCare Staging

Documentação completa do processo de carga de dados para ambiente de staging do IntelliCare, demonstrando todo o potencial da plataforma.

## Índice

| Documento | Conteúdo |
|----------|----------|
| [01_GUIA_RAPIDO.md](./01_GUIA_RAPIDO.md) | Passo a passo para executar a carga completa |
| [02_ESTRUTURA_DADOS.md](./02_ESTRUTURA_DADOS.md) | Estrutura de pastas, arquivos fonte e hierarquia |
| [03_RECURSOS_FHIR.md](./03_RECURSOS_FHIR.md) | Recursos FHIR gerados e módulos que os utilizam |
| [04_TENANTS_GESTORES.md](./04_TENANTS_GESTORES.md) | Tenants, gestores, unidades e profissionais |
| [05_CARGA_KEYCLOAK.md](./05_CARGA_KEYCLOAK.md) | Carga de usuários no Keycloak (realm bemcuidar) |
| [06_CARGA_FHIR.md](./06_CARGA_FHIR.md) | Carga de recursos FHIR no GRAHAME |

## Visão geral

A carga de dados cobre:

- **Organizações** — Secretarias (SES-DF, SMS Montes Claros), hospitais (HRAN, HBDF, Santa Casa), UBS
- **Locations** — Unidades físicas de cada estabelecimento
- **Pacientes** — Dados reais de REG (Brasília e Montes Claros)
- **Profissionais** — Médicos e enfermeiros vinculados a organizações e unidades
- **Gestores** — Um TENANT_GESTOR por secretaria/estabelecimento
- **Dados clínicos** — Conditions, Observations (incl. críticas), Encounters, Medications, Allergies
- **Planos de cuidado** — CarePlan, Goal (GERALDA)
- **Procedimentos e relatórios** — Procedure, DiagnosticReport
- **Contatos** — RelatedPerson

## Fluxo de execução

```
1. seed_staging_data.py    → Gera JSON em data/V2.0.0-KEYCLOAK/fhir/
2. seed_keycloak_staging.py → Cria usuários no Keycloak (realm bemcuidar)
3. load_fhir_bundle.py     → Envia recursos FHIR ao GRAHAME
```

**Carga completa (um comando):**

```powershell
.\scripts\carga_completa.ps1 -KeycloakAdminPass "sua_senha"
# Ou sem Keycloak: .\scripts\carga_completa.ps1 -SkipKeycloak -Workers 20
```

## Referências

- Dados fonte: `data/REG-brasilia.csv`, `data/REG-montesClaros.csv`
- Especificação Keycloak: `docs/V2.0.0-KEYCLOAK/`
- Scripts: `scripts/seed_staging_data.py`, `scripts/seed_keycloak_staging.py`, `scripts/load_fhir_bundle.py`
