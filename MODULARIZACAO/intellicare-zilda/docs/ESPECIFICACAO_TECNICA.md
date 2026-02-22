# intellicare-zilda — Especificacao Tecnica

## 1. Estrutura

```
intellicare-zilda/
├── zilda/
│   ├── __init__.py
│   ├── config.py
│   ├── api/
│   │   ├── app.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── cnes.py          # Consultas CNES
│   │       ├── territory.py     # Contexto territorial
│   │       └── indicators.py    # Indicadores regionais
│   ├── engine/
│   │   ├── cnes_client.py       # Cliente API CNES
│   │   ├── datasus_client.py    # Cliente APIs DATASUS
│   │   ├── esus_client.py       # Cliente e-SUS APS
│   │   ├── territorial.py       # Analise territorial
│   │   └── cache.py             # Cache local (Redis/SQLite)
│   ├── ui/
│   │   └── main.py
│   └── subagent/
│       └── zilda_subagent.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 2. Maturidade Atual: 1/10

- Skeleton do subagent (50 linhas)
- Especificacao detalhada das APIs (23k linhas de documentacao)
- Implementacao real: novo desenvolvimento

## 3. APIs Externas

### CNES API
- Base URL: `https://apidadosabertos.saude.gov.br/cnes/`
- Endpoints: estabelecimentos, profissionais, leitos, servicos

### DATASUS APIs
- Dados abertos do Ministerio da Saude
- Tabuladores (TABNET via scraping ou API quando disponivel)
