# Guia Rápido — Carga de Dados

## Pré-requisitos

- Python 3.11+
- Keycloak rodando (realm `bemcuidar` configurado)
- GRAHAME rodando (porta 8012)
- Arquivos `data/REG-brasilia.csv` e `data/REG-montesClaros.csv`

## Passo 1: Gerar dados FHIR

```bash
# Carga completa (todos os pacientes)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK

# Volume reduzido (500 por cidade)
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK --limit 500

# Apenas um tipo
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK --only patients
```

**Saída:** `data/V2.0.0-KEYCLOAK/fhir/` com 15 tipos de recursos.

## Passo 2: Carregar usuários no Keycloak

```bash
python scripts/seed_keycloak_staging.py --admin-pass SUA_SENHA_ADMIN
# Ou: export KEYCLOAK_ADMIN_PASSWORD=xxx && python scripts/seed_keycloak_staging.py
```

**Cria:** 1 PLATFORM_ADMIN, 4 TENANT_GESTOR, 5 profissionais (MEDICO/ENFERMEIRO).  
**Senha padrão:** `Staging@2026!` (temporária)

## Passo 3: Carregar FHIR no GRAHAME

```bash
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir
# Carga paralela (mais rápida para base completa):
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --workers 20
```

## Carga completa (um comando)

```powershell
# Windows PowerShell — executa os 3 passos em sequência
.\scripts\carga_completa.ps1 -KeycloakAdminPass "sua_senha_admin"
# Ou com variável de ambiente:
$env:KEYCLOAK_ADMIN_PASSWORD = "sua_senha"; .\scripts\carga_completa.ps1
# Pular Keycloak (se não estiver rodando):
.\scripts\carga_completa.ps1 -SkipKeycloak -Workers 20
```

## Ordem recomendada

1. Subir Keycloak e GRAHAME
2. Executar `seed_staging_data.py` (ou `carga_completa.ps1`)
3. Executar `seed_keycloak_staging.py` (ou via `carga_completa.ps1`)
4. Executar `load_fhir_bundle.py` (ou via `carga_completa.ps1`)
