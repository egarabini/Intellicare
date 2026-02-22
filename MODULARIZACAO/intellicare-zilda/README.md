# intellicare-zilda

Agente de dados de saude publica brasileira do IntelliCare.

Homenagem a **Zilda Arns** (1934-2010), medica pediatra e sanitarista brasileira, fundadora da Pastoral da Crianca.

## O que faz

O Zilda consulta e contextualiza dados de saude publica do Brasil, integrando informacoes do CNES (Cadastro Nacional de Estabelecimentos de Saude):

- **Consulta CNES**: Busca estabelecimentos de saude por estado, municipio e tipo
- **Validacao CNES**: Verifica formato e existencia de codigos CNES
- **Tipos de unidade**: Lista tipos de unidade de saude (hospitais, UBS, clinicas, etc.)
- **Regioes de saude**: Consulta regioes e macrorregioes com dados populacionais
- **Analise territorial**: Resume contexto de saude de um municipio/estado
- **Contexto regional**: Identifica regiao de saude, municipios vizinhos e populacao

## API REST

```bash
uvicorn zilda.api.app:create_app --factory --port 8003
```

### Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/info` | Informacoes do modulo |
| GET | `/api/v1/unit-types` | Lista tipos de unidade CNES |
| GET | `/api/v1/establishments` | Busca estabelecimentos (filtros: state_code, city_code, unit_type_code) |
| GET | `/api/v1/establishment/{cnes_code}` | Busca por codigo CNES |
| POST | `/api/v1/validate` | Valida codigo CNES (formato + existencia) |
| GET | `/api/v1/regions` | Lista regioes de saude |
| GET | `/api/v1/territorial-summary` | Resumo territorial de um municipio/estado |
| GET | `/api/v1/region-context/{city_code}` | Contexto da regiao de saude |

### Exemplo GET /api/v1/establishments?state_code=35&limit=5

```json
[
  {
    "cnes_code": "2077485",
    "legal_name": "Hospital Municipal de Exemplo",
    "fantasy_name": "Hospital Exemplo",
    "unit_type_description": "HOSPITAL GERAL",
    "city_name": "SAO PAULO",
    "has_surgical_center": true,
    "active": true
  }
]
```

### Exemplo POST /api/v1/validate

```json
{
  "cnes_code": "2077485"
}
```

Resposta:
```json
{
  "cnes_code": "2077485",
  "valid_format": true,
  "found": true,
  "establishment": { ... },
  "message": "CNES 2077485 encontrado: Hospital Exemplo"
}
```

## Instalacao

```bash
pip install -e ".[dev]"
```

## Docker

```bash
docker compose up -d
```

## Testes

```bash
pytest tests/ -v
pytest tests/ --cov=zilda --cov-report=term-missing
```

## Estrutura

```
zilda/
├── api/
│   └── app.py              # FastAPI (9 endpoints)
├── config.py               # ZildaConfig
├── engine/
│   ├── cache.py            # SimpleCache com TTL
│   ├── cnes_client.py      # Cliente CNES API (httpx)
│   ├── models.py           # Modelos de dados
│   └── territorial.py      # Motor de analise territorial
```

## Fonte de dados

| Fonte | URL | Dados |
|-------|-----|-------|
| CNES/MS | `apidadosabertos.saude.gov.br` | Estabelecimentos, tipos, regioes |

## Diferenca entre Zilda e outros agentes

| Aspecto | Zilda | Oswaldo | Florence |
|---------|-------|---------|----------|
| Foco | Dados publicos de saude | Doencas cronicas | Exames laboratoriais |
| Fonte | APIs CNES/DATASUS | Obs FHIR do paciente | Resultados de lab |
| Saida | Contexto territorial | Estadiamento | Interpretacao clinica |

## Metricas

- **68 testes** | **95% cobertura**
- 9 endpoints REST
- Cache com TTL (estatico 7d, dinamico 1h)
- Cliente CNES com retry e error handling
