# Estabelecimentos de Saúde

Pasta para armazenar dados de estabelecimentos de saúde (CNES) e sua relação com profissionais.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `estabelecimentos_brasilia_montesclaros.csv` | Gerado por `list_profissionais_estabelecimentos.py` — estabelecimentos via API |
| `estabelecimentos_staging.csv` | Lista para staging (Brasília + Montes Claros + secretarias) |

## Estabelecimentos para Staging

A lista completa para simulação está em `data/V2.0.0-KEYCLOAK/establishments/`:

- **Secretarias:** SES-DF, SMS Montes Claros
- **Hospitais:** HRAN, HBDF (Brasília), Santa Casa (Montes Claros)
- **UBS:** UBS Asa Sul (Brasília), UBS Centro (Montes Claros)

## Como gerar (via API)

```bash
python scripts/list_profissionais_estabelecimentos.py
```

## Profissionais de saúde

Portal CNES: https://cnes.datasus.gov.br/pages/profissionais/extracao.jsp
