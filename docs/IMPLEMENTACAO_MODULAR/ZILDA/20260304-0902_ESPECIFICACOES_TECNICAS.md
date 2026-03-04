# ZILDA — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-zilda (porta 8007)

---

## 1. Stack Tecnologica

| Componente | Tecnologia | Versao |
|-----------|-----------|--------|
| Runtime | Python | 3.11 |
| Framework | FastAPI | >= 0.110 |
| HTTP Client | httpx | async |
| Cache | Redis (via intellicare-core) | 7.x |
| Testes | pytest + pytest-asyncio | latest |
| Lint/Format | ruff | latest |
| Deploy | Docker + docker-compose | - |

---

## 2. Estrutura de Diretorios

```
intellicare-zilda/
├── zilda/
│   ├── api/
│   │   ├── app.py            # FastAPI app + lifespan
│   │   └── routes/
│   │       ├── health.py     # GET /api/v1/health
│   │       ├── info.py       # GET /api/v1/info
│   │       ├── analyze.py    # POST /api/v1/analyze (BaseAgent)
│   │       ├── cnes.py       # GET /api/v1/cnes/{codigo}
│   │       ├── establishments.py # GET /api/v1/establishments
│   │       └── territory.py  # GET /api/v1/territory/{municipio}
│   ├── services/
│   │   ├── cnes_service.py   # Logica de busca e validacao CNES
│   │   ├── datasus_client.py # Client HTTP para APIs DATASUS
│   │   └── territory_service.py # Analise territorial
│   ├── models/
│   │   ├── cnes.py           # Pydantic models CNES
│   │   └── territory.py      # Pydantic models territoriais
│   └── config.py             # Settings (pydantic-settings)
├── tests/
│   ├── conftest.py
│   ├── test_cnes_service.py
│   ├── test_territory_service.py
│   └── test_routes.py
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## 3. Endpoints da API

### 3.1 Endpoints Padrao (BaseAgent)

```
GET  /api/v1/health          → HealthCheck
GET  /api/v1/info            → ModuleInfo
POST /api/v1/analyze         → AnalysisResponse
```

### 3.2 Endpoints Especializados

```
GET  /api/v1/cnes/{codigo}           → DadosCNES
     Query params: none
     Response: {cnes, nome, tipo, municipio, uf, cnes_valido}

GET  /api/v1/establishments          → List[Estabelecimento]
     Query params: uf, municipio, tipo_unidade, limit=50
     Response: lista paginada de estabelecimentos

GET  /api/v1/unit-types              → List[TipoUnidade]
     Response: lista de tipos cadastrados

GET  /api/v1/territory/{uf}/{municipio} → PerfilTerritorial
     Response: {populacao, regiao_saude, macrorregio, ubs_count, esf_coverage}

GET  /api/v1/territory/region/{codigo_regiao} → RegiaoSaude
     Response: dados da regiao de saude
```

---

## 4. Modelos Pydantic

```python
class DadosCNES(BaseModel):
    cnes: str                    # 7 digitos
    nome_fantasia: str
    razao_social: str
    tipo_unidade: str
    tipo_unidade_codigo: str
    municipio: str
    uf: str
    cep: Optional[str]
    telefone: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    ativo: bool

class PerfilTerritorial(BaseModel):
    municipio: str
    uf: str
    codigo_ibge: str
    populacao_estimada: int
    regiao_saude: str
    codigo_regiao: str
    macrorregiao: str
    area_km2: Optional[float]
    ubs_count: int
    hospitais_count: int
    esf_equipes: int
    esf_cobertura_pct: Optional[float]

class Estabelecimento(BaseModel):
    cnes: str
    nome: str
    tipo: str
    municipio: str
    uf: str
    latitude: Optional[float]
    longitude: Optional[float]
```

---

## 5. Integracao com Fontes de Dados

### 5.1 CNES (Cadastro Nacional de Estabelecimentos de Saude)
- **URL Base:** `https://apidadosabertos.saude.gov.br/cnes/`
- **Endpoints usados:**
  - `GET /estabelecimentos?coEstado={uf}&coMunicipio={cod}&tpUnidade={tipo}`
  - `GET /estabelecimentos/{cnes}`
- **Auth:** Nenhuma (dados publicos)
- **Rate limit:** ~10 req/s (usar cache Redis)

### 5.2 IBGE (Populacao e Municipios)
- **URL Base:** `https://servicodados.ibge.gov.br/api/v1/`
- **Endpoints usados:**
  - `GET /localidades/municipios/{cod_ibge}`
  - `GET /localidades/estados/{uf}/municipios`
- **Cache TTL:** 7 dias (dados raramente mudam)

### 5.3 Cache Redis
```python
# Estrategia de cache
KEY_PATTERN = "zilda:{tipo}:{parametros_hash}"
TTL_CNES = 86400       # 24h — dados CNES mudam raramente
TTL_TERRITORIO = 604800 # 7 dias — populacao IBGE e anual
TTL_MUNICIPIOS = 604800 # 7 dias — lista de municipios
```

---

## 6. Configuracao (environment)

```env
# Obrigatorio
REDIS_URL=redis://localhost:6379/0

# Opcional (defaults fornecidos)
CNES_API_BASE_URL=https://apidadosabertos.saude.gov.br/cnes
IBGE_API_BASE_URL=https://servicodados.ibge.gov.br/api/v1
ZILDA_CACHE_TTL_CNES=86400
ZILDA_CACHE_TTL_TERRITORY=604800
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
LOG_LEVEL=INFO
PORT=8000
```

---

## 7. Tratamento de Erros

| Cenario | Status HTTP | Mensagem |
|---------|-------------|---------|
| CNES invalido (formato) | 400 | "CNES deve ter 7 digitos numericos" |
| CNES nao encontrado | 404 | "Estabelecimento CNES {x} nao encontrado" |
| DATASUS indisponivel | 503 | "Servico DATASUS temporariamente indisponivel" |
| Municipio invalido | 404 | "Municipio nao encontrado para UF {uf}" |
| Timeout externo | 504 | "Timeout na consulta de dados externos" |

Para DATASUS indisponivel, o servico tenta retornar cache Redis se disponivel.
Se nao houver cache, retorna 503 com `"cached": false`.

---

## 8. Testes

### 8.1 Estrategia
- Servicos testados com httpx mocking (respx)
- Rotas testadas com FastAPI TestClient
- Sem dependencias externas nos testes unitarios

### 8.2 Cobertura Minima
- `cnes_service.py`: 90%
- `territory_service.py`: 85%
- `routes/`: 80%

### 8.3 Testes Obrigatorios
```python
# test_cnes_service.py
test_validar_cnes_formato_correto()
test_validar_cnes_formato_incorreto_letras()
test_validar_cnes_formato_incorreto_comprimento()
test_buscar_estabelecimento_por_cnes_sucesso()
test_buscar_estabelecimento_cnes_nao_encontrado()
test_buscar_estabelecimento_datasus_offline_usa_cache()
test_listar_por_municipio_retorna_lista()
test_listar_por_tipo_filtra_corretamente()

# test_territory_service.py
test_perfil_territorial_municipio_valido()
test_perfil_territorial_municipio_nao_encontrado()
test_regioes_saude_uf_valida()
```

---

## 9. Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dev]" --no-cache-dir
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:${PORT:-8000}/api/v1/health || exit 1
CMD ["uvicorn", "zilda.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

*ZILDA v2.0 — Especificacoes Tecnicas — 2026-03-04*
