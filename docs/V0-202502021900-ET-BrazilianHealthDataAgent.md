# Especificação Técnica - Brazilian Health Data Agent
**Projeto:** IntelliCare - Portal de Agentes Inteligentes em Saúde Pública  
**Versão:** 1.0  
**Data:** 2025-02-02  
**Autor:** Equipe Técnica IntelliCare  
**Status:** 📋 Em Planejamento

---

## 1. ARQUITETURA GERAL

### 1.1 Visão Arquitetural

```
┌─────────────────────────────────────────────────────────────┐
│              IntelliCare/WANDA ORCHESTRATOR                  │
│                  (Multi-Agent System)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          BrazilianHealthDataAgent (BaseTool)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Action Router (run method)                          │   │
│  │  - get_health_units_types                            │   │
│  │  - search_establishments                             │   │
│  │  - search_municipalities                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┼────────────────────────────────┐  │
│  │                      ▼                                 │  │
│  │         API Client Layer (httpx/aiohttp)              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │  │
│  │  │ CNES Client  │  │ Municipios   │  │ Retry Logic │ │  │
│  │  │              │  │ Client       │  │ + Timeout   │ │  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │  │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────┼────────────────────────────────┐  │
│  │                      ▼                                 │  │
│  │              Cache Layer (Redis)                      │  │
│  │  - TTL: 24h (static) / 1h (dynamic)                   │  │
│  │  - Key pattern: health:cnes:{action}:{hash(params)}   │  │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         External APIs (Ministério da Saúde)                 │
│  - https://apidadosabertos.saude.gov.br/cnes/tipounidades   │
│  - https://apidadosabertos.saude.gov.br/cnes/estabelecimentos│
│  - https://apidadosabertos.saude.gov.br/macrorregiao-e-...  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Padrão de Integração com IntelliCare

O agente segue o padrão **BaseTool** do sistema IntelliCare/WANDA:

```python
from core.base_tool import BaseTool

class BrazilianHealthDataAgent(BaseTool):
    NAME = "br_health_data_agent"
    DESCRIPTION = "..."
    
    def __init__(self):
        super().__init__(self.NAME, self.DESCRIPTION)
    
    def get_definition(self) -> Dict[str, Any]:
        """Schema para o Maestro"""
        return {...}
    
    def run(self, input_text: str) -> str:
        """Execução principal"""
        pass
```

---

## 2. ESTRUTURA DE CÓDIGO

### 2.1 Estrutura de Diretórios

```
INTELLICAREREPO/agentes/tools/
├── brazilian_health_data_agent.py      # Agente principal (já existe)
├── health_api_client.py                # Cliente HTTP para APIs (NOVO)
├── health_cache_manager.py             # Gerenciador de cache (NOVO)
├── health_data_models.py               # Modelos Pydantic (NOVO)
└── tests/
    ├── test_health_agent.py            # Testes unitários
    ├── test_health_api_client.py       # Testes de integração
    └── fixtures/
        └── mock_responses.json         # Respostas mockadas
```

### 2.2 Dependências (pyproject.toml ou requirements.txt)

```toml
[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"
httpx = "^0.27.0"           # Cliente HTTP assíncrono
redis = "^5.0.0"            # Cache
pydantic = "^2.5.0"         # Validação de dados
tenacity = "^8.2.0"         # Retry logic
python-dotenv = "^1.0.0"    # Configuração
```

---

## 3. IMPLEMENTAÇÃO DETALHADA

### 3.1 Modelos de Dados (health_data_models.py)

```python
"""
Modelos Pydantic para validação de dados das APIs de Saúde
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class HealthUnitType(BaseModel):
    """Tipo de Unidade de Saúde (CNES)"""
    codigo_tipo_unidade: int = Field(..., description="Código do tipo")
    descricao_tipo_unidade: str = Field(..., description="Descrição")


class HealthEstablishment(BaseModel):
    """Estabelecimento de Saúde (CNES)"""
    codigo_cnes: str = Field(..., description="Código CNES")
    numero_cnpj_entidade: Optional[str] = Field(None, description="CNPJ")
    nome_razao_social: str = Field(..., description="Nome/Razão Social")
    nome_fantasia: Optional[str] = Field(None, description="Nome Fantasia")
    codigo_tipo_unidade: int
    descricao_tipo_unidade: str
    codigo_uf: int
    uf: str
    codigo_municipio: int
    descricao_municipio: str
    endereco_estabelecimento: Optional[str] = None
    numero_estabelecimento: Optional[str] = None
    bairro_estabelecimento: Optional[str] = None
    numero_telefone_estabelecimento: Optional[str] = None
    latitude_estabelecimento_decimo_grau: Optional[float] = None
    longitude_estabelecimento_decimo_grau: Optional[float] = None
    estabelecimento_possui_centro_cirurgico: Optional[int] = None
    estabelecimento_possui_centro_obstetrico: Optional[int] = None
    estabelecimento_possui_centro_neonatal: Optional[int] = None
    estabelecimento_possui_atendimento_hospitalar: Optional[int] = None
    estabelecimento_possui_servico_apoio: Optional[int] = None
    estabelecimento_possui_atendimento_ambulatorial: Optional[int] = None


class Municipality(BaseModel):
    """Município com Regiões de Saúde"""
    codigo_uf: int
    uf: str
    regiao: str
    codigo_macrorregiao_saude: str
    macrorregiao_saude: str
    codigo_regiao_saude: str
    regiao_saude: str
    codigo_municipio: str
    municipio: str
    populacao_estimada_ibge_2022: int
    
    @validator('populacao_estimada_ibge_2022', pre=True)
    def parse_population(cls, v):
        """Converte população para int"""
        if isinstance(v, str):
            return int(v.replace(',', '').replace('.', ''))
        return v


class APIResponse(BaseModel):
    """Resposta padrão da API"""
    success: bool = True
    data: dict
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None
```

### 3.2 Cliente HTTP (health_api_client.py)

```python
"""
Cliente HTTP para APIs do Ministério da Saúde
Implementa retry logic, timeout e tratamento de erros
"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from health_data_models import (
    HealthUnitType,
    HealthEstablishment,
    Municipality,
    APIResponse
)

logger = logging.getLogger(__name__)


class HealthAPIClient:
    """Cliente para APIs de Dados Abertos do Ministério da Saúde"""
    
    BASE_URL = "https://apidadosabertos.saude.gov.br"
    TIMEOUT = 10.0  # segundos
    MAX_RETRIES = 3
    
    def __init__(self, cache_manager=None):
        self.cache = cache_manager
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=self.TIMEOUT,
            headers={
                "User-Agent": "IntelliCare-HealthAgent/1.0",
                "Accept": "application/json"
            }
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição HTTP com retry automático
        
        Args:
            endpoint: Caminho do endpoint (ex: /cnes/tipounidades)
            params: Query parameters
            
        Returns:
            Resposta JSON da API
            
        Raises:
            httpx.HTTPStatusError: Erro HTTP (4xx, 5xx)
            httpx.TimeoutException: Timeout
        """
        try:
            logger.info(f"Requesting {endpoint} with params: {params}")
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout requesting {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    def get_health_unit_types(self) -> List[HealthUnitType]:
        """
        Obtém todos os tipos de unidades de saúde
        
        Returns:
            Lista de tipos de unidade
        """
        # Verifica cache primeiro
        cache_key = "health:cnes:unit_types"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("Returning cached unit types")
                return [HealthUnitType(**item) for item in cached]
        
        # Consulta API
        data = self._make_request("/cnes/tipounidades")
        
        # Valida com Pydantic
        unit_types = [HealthUnitType(**item) for item in data]
        
        # Salva no cache (7 dias)
        if self.cache:
            self.cache.set(cache_key, data, ttl=604800)
        
        return unit_types
```

---

## 4. GERENCIAMENTO DE CACHE

### 4.1 Cache Manager (health_cache_manager.py)

```python
"""
Gerenciador de cache Redis para dados de saúde
"""
import redis
import json
import hashlib
import logging
from typing import Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


class HealthCacheManager:
    """Gerenciador de cache com Redis"""

    # TTLs padrão (em segundos)
    TTL_STATIC = 604800   # 7 dias (tipos de unidade, municípios - dados estáticos)
    TTL_DYNAMIC = 3600    # 1 hora (estabelecimentos - dados dinâmicos)
    TTL_DEFAULT = 86400   # 24 horas (fallback)
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Inicializa conexão com Redis
        
        Args:
            host: Host do Redis
            port: Porta do Redis
            db: Número do database
            password: Senha (opcional)
        """
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Testa conexão
            self.redis.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    def _generate_key(self, prefix: str, params: dict) -> str:
        """
        Gera chave de cache baseada em parâmetros
        
        Args:
            prefix: Prefixo da chave (ex: health:cnes:establishments)
            params: Parâmetros da consulta
            
        Returns:
            Chave única
        """
        # Ordena params para garantir consistência
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor deserializado ou None
        """
        if not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = TTL_DEFAULT
    ) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos
            
        Returns:
            True se sucesso
        """
        if not self.redis:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(self, pattern: str) -> int:
        """
        Invalida chaves que correspondem ao padrão
        
        Args:
            pattern: Padrão de chave (ex: health:cnes:*)
            
        Returns:
            Número de chaves deletadas
        """
        if not self.redis:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return 0
```

---

## 5. AGENTE PRINCIPAL (brazilian_health_data_agent.py)

### 5.1 Estrutura Atualizada

O arquivo já existe, mas precisa ser **refatorado** para incluir as novas ações:

```python
# Adicionar ao enum de actions no get_definition():
"action": {
    "type": "string",
    "enum": [
        # ... ações existentes ...
        "get_health_units_types",      # NOVO
        "search_establishments",        # NOVO
        "search_municipalities"         # NOVO
    ],
    "description": "..."
}
```

### 5.2 Implementação dos Novos Métodos

```python
def run(self, input_text: str) -> str:
    """Execução principal do agente"""
    try:
        data = json.loads(input_text)
        action = data.get("action")
        params = data.get("params", {})
        
        # ... ações existentes ...
        
        # NOVAS AÇÕES
        elif action == "get_health_units_types":
            return self._get_health_units_types()
        
        elif action == "search_establishments":
            return self._search_establishments(params)
        
        elif action == "search_municipalities":
            return self._search_municipalities(params)
        
        else:
            return "Ação não reconhecida."
    
    except Exception as e:
        logger.error(f"Erro: {e}")
        return f"Erro: {str(e)}"


def _get_health_units_types(self) -> str:
    """
    Obtém todos os tipos de unidades de saúde
    
    Returns:
        String formatada com lista de tipos
    """
    try:
        with HealthAPIClient(cache_manager=self.cache) as client:
            unit_types = client.get_health_unit_types()
        
        # Formata resposta
        lines = ["🏥 **Tipos de Unidades de Saúde (CNES):**\n"]
        for ut in unit_types[:20]:  # Limita a 20 para não lotar
            lines.append(
                f"• **{ut.codigo_tipo_unidade}**: {ut.descricao_tipo_unidade}"
            )
        
        lines.append(f"\n✅ Total: {len(unit_types)} tipos")
        lines.append("Fonte: Ministério da Saúde (CNES)")
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.error(f"Erro ao buscar tipos de unidade: {e}")
        return f"Erro ao consultar tipos de unidade: {str(e)}"


def _search_establishments(self, params: dict) -> str:
    """
    Busca estabelecimentos de saúde com filtros

    Args:
        params: Filtros de busca
            - codigo_uf: int (opcional)
            - codigo_municipio: int (opcional)
            - codigo_tipo_unidade: int (opcional)
            - status: int (opcional, 1=ativo)
            - estabelecimento_possui_centro_cirurgico: int (opcional)
            - estabelecimento_possui_centro_obstetrico: int (opcional)
            - limit: int (padrão 20, max 100)
            - offset: int (padrão 0)

    Returns:
        String formatada com lista de estabelecimentos
    """
    try:
        # Validação e sanitização de parâmetros
        limit = min(max(int(params.get("limit", 20)), 1), 100)  # Entre 1 e 100
        offset = max(int(params.get("offset", 0)), 0)  # >= 0

        # Validação de código UF (11-53, códigos IBGE válidos)
        if "codigo_uf" in params:
            codigo_uf = int(params["codigo_uf"])
            if not (11 <= codigo_uf <= 53):
                return "Erro: código_uf inválido. Deve estar entre 11 e 53."

        # Validação de status (0 ou 1)
        if "status" in params:
            status = int(params["status"])
            if status not in [0, 1]:
                return "Erro: status deve ser 0 (inativo) ou 1 (ativo)."

        # Monta query parameters
        query_params = {
            "limit": limit,
            "offset": offset
        }

        # Adiciona filtros opcionais
        optional_filters = [
            "codigo_uf", "codigo_municipio", "codigo_tipo_unidade",
            "status", "estabelecimento_possui_centro_cirurgico",
            "estabelecimento_possui_centro_obstetrico"
        ]

        for filter_name in optional_filters:
            if filter_name in params:
                query_params[filter_name] = params[filter_name]

        # Consulta API
        with HealthAPIClient(cache_manager=self.cache) as client:
            establishments = client.search_establishments(query_params)

        if not establishments:
            return "Nenhum estabelecimento encontrado com os filtros especificados."

        # Formata resposta
        lines = ["🏥 **Estabelecimentos de Saúde Encontrados:**\n"]

        for est in establishments[:10]:  # Mostra top 10
            lines.append(f"**{est.nome_razao_social}**")
            lines.append(f"  • CNES: {est.codigo_cnes}")
            lines.append(f"  • Tipo: {est.descricao_tipo_unidade}")
            lines.append(f"  • Município: {est.descricao_municipio} - {est.uf}")
            if est.endereco_estabelecimento:
                lines.append(f"  • Endereço: {est.endereco_estabelecimento}, {est.numero_estabelecimento}")
            if est.numero_telefone_estabelecimento:
                lines.append(f"  • Telefone: {est.numero_telefone_estabelecimento}")
            lines.append("")

        lines.append(f"✅ Total encontrado: {len(establishments)}")
        lines.append(f"📄 Mostrando {min(10, len(establishments))} de {len(establishments)}")
        lines.append("Fonte: Ministério da Saúde (CNES)")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Erro ao buscar estabelecimentos: {e}")
        return f"Erro ao buscar estabelecimentos: {str(e)}"


def _search_municipalities(self, params: dict) -> str:
    """
    Busca municípios com informações de regiões de saúde

    Args:
        params: Filtros de busca
            - municipio: str (nome do município)
            - uf: str (sigla do estado)
            - codigo_regiao_saude: str (opcional)
            - limit: int (padrão 20)
            - offset: int (padrão 0)

    Returns:
        String formatada com dados dos municípios
    """
    try:
        # Validação
        limit = min(params.get("limit", 20), 100)
        offset = max(params.get("offset", 0), 0)

        query_params = {
            "limit": limit,
            "offset": offset
        }

        # Filtros opcionais
        if "municipio" in params:
            query_params["municipio"] = params["municipio"]
        if "uf" in params:
            query_params["uf"] = params["uf"].upper()
        if "codigo_regiao_saude" in params:
            query_params["codigo_regiao_saude"] = params["codigo_regiao_saude"]

        # Consulta API
        with HealthAPIClient(cache_manager=self.cache) as client:
            municipalities = client.search_municipalities(query_params)

        if not municipalities:
            return "Nenhum município encontrado com os filtros especificados."

        # Formata resposta
        lines = ["🏙️ **Municípios Encontrados:**\n"]

        for mun in municipalities[:10]:
            lines.append(f"**{mun.municipio} - {mun.uf}**")
            lines.append(f"  • Código IBGE: {mun.codigo_municipio}")
            lines.append(f"  • Região: {mun.regiao}")
            lines.append(f"  • Macrorregião de Saúde: {mun.macrorregiao_saude} ({mun.codigo_macrorregiao_saude})")
            lines.append(f"  • Região de Saúde: {mun.regiao_saude} ({mun.codigo_regiao_saude})")
            lines.append(f"  • População (IBGE 2022): {mun.populacao_estimada_ibge_2022:,}")
            lines.append("")

        lines.append(f"✅ Total encontrado: {len(municipalities)}")
        lines.append("Fonte: Ministério da Saúde")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Erro ao buscar municípios: {e}")
        return f"Erro ao buscar municípios: {str(e)}"
```

---

## 6. CONFIGURAÇÃO E VARIÁVEIS DE AMBIENTE

### 6.1 Arquivo .env

```bash
# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API Settings
HEALTH_API_BASE_URL=https://apidadosabertos.saude.gov.br
HEALTH_API_TIMEOUT=10
HEALTH_API_MAX_RETRIES=3

# Cache TTLs (segundos)
CACHE_TTL_STATIC=604800    # 7 dias
CACHE_TTL_DYNAMIC=3600     # 1 hora
CACHE_TTL_DEFAULT=86400    # 24 horas

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 6.2 Arquivo de Configuração (config.py)

```python
"""
Configurações do Brazilian Health Data Agent
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações do agente"""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # API
    health_api_base_url: str = "https://apidadosabertos.saude.gov.br"
    health_api_timeout: int = 10
    health_api_max_retries: int = 3

    # Cache
    cache_ttl_static: int = 604800   # 7 dias
    cache_ttl_dynamic: int = 3600    # 1 hora
    cache_ttl_default: int = 86400   # 24 horas

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
settings = Settings()
```

---

## 7. TESTES

### 7.1 Testes Unitários (test_health_agent.py)

```python
"""
Testes unitários para Brazilian Health Data Agent
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from brazilian_health_data_agent import BrazilianHealthDataAgent
from health_data_models import HealthUnitType, HealthEstablishment


class TestBrazilianHealthDataAgent:
    """Suite de testes para o agente"""

    @pytest.fixture
    def agent(self):
        """Fixture do agente"""
        return BrazilianHealthDataAgent()

    @pytest.fixture
    def mock_cache(self):
        """Mock do cache manager"""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = True
        return cache

    def test_get_definition(self, agent):
        """Testa schema de definição"""
        definition = agent.get_definition()

        assert definition["name"] == "br_health_data_agent"
        assert "description" in definition
        assert "input_schema" in definition

        # Verifica ações
        actions = definition["input_schema"]["properties"]["action"]["enum"]
        assert "get_health_units_types" in actions
        assert "search_establishments" in actions
        assert "search_municipalities" in actions

    @patch('brazilian_health_data_agent.HealthAPIClient')
    def test_get_health_units_types_success(self, mock_client, agent):
        """Testa busca de tipos de unidade com sucesso"""
        # Mock da resposta
        mock_types = [
            HealthUnitType(codigo_tipo_unidade=1, descricao_tipo_unidade="POSTO DE SAUDE"),
            HealthUnitType(codigo_tipo_unidade=2, descricao_tipo_unidade="CENTRO DE SAUDE")
        ]
        mock_client.return_value.__enter__.return_value.get_health_unit_types.return_value = mock_types

        # Executa
        input_data = json.dumps({"action": "get_health_units_types", "params": {}})
        result = agent.run(input_data)

        # Valida
        assert "POSTO DE SAUDE" in result
        assert "CENTRO DE SAUDE" in result
        assert "Fonte: Ministério da Saúde" in result

    @patch('brazilian_health_data_agent.HealthAPIClient')
    def test_search_establishments_with_filters(self, mock_client, agent):
        """Testa busca de estabelecimentos com filtros"""
        # Mock
        mock_est = HealthEstablishment(
            codigo_cnes="1234567",
            nome_razao_social="Hospital Teste",
            codigo_tipo_unidade=1,
            descricao_tipo_unidade="HOSPITAL GERAL",
            codigo_uf=27,
            uf="AL",
            codigo_municipio=270850,
            descricao_municipio="MACEIO"
        )
        mock_client.return_value.__enter__.return_value.search_establishments.return_value = [mock_est]

        # Executa
        input_data = json.dumps({
            "action": "search_establishments",
            "params": {
                "codigo_uf": 27,
                "status": 1,
                "limit": 10
            }
        })
        result = agent.run(input_data)

        # Valida
        assert "Hospital Teste" in result
        assert "CNES: 1234567" in result
        assert "MACEIO - AL" in result

    def test_invalid_action(self, agent):
        """Testa ação inválida"""
        input_data = json.dumps({"action": "invalid_action", "params": {}})
        result = agent.run(input_data)

        assert "não reconhecida" in result.lower()

    def test_invalid_json(self, agent):
        """Testa JSON inválido"""
        result = agent.run("invalid json")

        assert "erro" in result.lower()


### 7.2 Testes de Integração (test_health_api_client.py)

```python
"""
Testes de integração com APIs reais
"""
import pytest
from health_api_client import HealthAPIClient
from health_cache_manager import HealthCacheManager


@pytest.mark.integration
class TestHealthAPIClientIntegration:
    """Testes de integração (requerem conexão com APIs)"""

    @pytest.fixture
    def client(self):
        """Cliente sem cache"""
        return HealthAPIClient()

    def test_get_health_unit_types_real_api(self, client):
        """Testa consulta real de tipos de unidade"""
        with client:
            unit_types = client.get_health_unit_types()

        assert len(unit_types) > 0
        assert all(hasattr(ut, 'codigo_tipo_unidade') for ut in unit_types)
        assert all(hasattr(ut, 'descricao_tipo_unidade') for ut in unit_types)

    def test_search_establishments_real_api(self, client):
        """Testa busca real de estabelecimentos"""
        with client:
            establishments = client.search_establishments({
                "codigo_uf": 27,  # Alagoas
                "limit": 5
            })

        assert len(establishments) > 0
        assert all(hasattr(e, 'codigo_cnes') for e in establishments)

    @pytest.mark.slow
    def test_api_timeout_handling(self, client):
        """Testa tratamento de timeout"""
        # Força timeout muito baixo
        client.client.timeout = 0.001

        with pytest.raises(Exception):
            with client:
                client.get_health_unit_types()


@pytest.mark.integration
class TestCacheIntegration:
    """Testes de integração com Redis"""

    @pytest.fixture
    def cache(self):
        """Cache manager"""
        return HealthCacheManager()

    def test_cache_set_get(self, cache):
        """Testa set e get no cache"""
        key = "test:key"
        value = {"test": "data"}

        # Set
        success = cache.set(key, value, ttl=60)
        assert success

        # Get
        retrieved = cache.get(key)
        assert retrieved == value

        # Cleanup
        cache.redis.delete(key)

    def test_cache_invalidate(self, cache):
        """Testa invalidação de cache"""
        # Cria múltiplas chaves
        cache.set("test:key1", {"data": 1}, ttl=60)
        cache.set("test:key2", {"data": 2}, ttl=60)

        # Invalida
        deleted = cache.invalidate("test:*")
        assert deleted == 2
```

---

## 8. LOGGING E MONITORAMENTO

### 8.1 Configuração de Logs

```python
"""
Configuração de logging estruturado
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formatter para logs em JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Adiciona exceção se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Adiciona campos extras
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO", format_type: str = "json"):
    """
    Configura logging para o agente

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        format_type: Formato (json ou text)
    """
    logger = logging.getLogger("brazilian_health_data_agent")
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler()

    if format_type == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

    logger.addHandler(handler)
    return logger
```

### 8.2 Métricas e Observabilidade

```python
"""
Métricas para monitoramento
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import time


@dataclass
class AgentMetrics:
    """Métricas do agente"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    def record_request(self, success: bool, response_time: float, error_type: str = None):
        """Registra uma requisição"""
        self.total_requests += 1
        self.response_times.append(response_time)

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        # Atualiza média
        self.avg_response_time = sum(self.response_times) / len(self.response_times)

    def record_cache(self, hit: bool):
        """Registra acesso ao cache"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        total = self.total_requests or 1
        return {
            "total_requests": self.total_requests,
            "success_rate": (self.successful_requests / total) * 100,
            "failure_rate": (self.failed_requests / total) * 100,
            "cache_hit_rate": (self.cache_hits / (self.cache_hits + self.cache_misses or 1)) * 100,
            "avg_response_time_ms": self.avg_response_time * 1000,
            "errors_by_type": self.errors_by_type
        }
```

---

## 9. DEPLOYMENT E INFRAESTRUTURA

### 9.1 Dockerfile

```dockerfile
# Dockerfile para Brazilian Health Data Agent
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY agentes/tools/ ./agentes/tools/
COPY core/ ./core/

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import redis; r = redis.Redis(host='${REDIS_HOST}', port=${REDIS_PORT}); r.ping()"

# Comando padrão (se for standalone)
CMD ["python", "-m", "agentes.tools.brazilian_health_data_agent"]
```

### 9.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: health_agent_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  health_agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: brazilian_health_agent
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LOG_LEVEL=INFO
      - HEALTH_API_TIMEOUT=10
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  redis_data:
```

### 9.3 Requirements.txt

```txt
# Core dependencies
requests==2.31.0
httpx==0.27.0
redis==5.0.1
pydantic==2.5.3
pydantic-settings==2.1.0
tenacity==8.2.3
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx-mock==0.7.0

# Logging
python-json-logger==2.0.7

# Development
black==23.12.1
flake8==7.0.0
mypy==1.8.0
```

---

## 10. GUIA DE IMPLEMENTAÇÃO PASSO A PASSO

### Fase 0: Validação de APIs (Pré-requisito)

**0.1 Validar Endpoints do Ministério da Saúde**

```bash
# Testa endpoint de tipos de unidades
curl -I https://apidadosabertos.saude.gov.br/cnes/tipounidades

# Testa endpoint de estabelecimentos
curl -I https://apidadosabertos.saude.gov.br/cnes/estabelecimentos

# Testa endpoint de municípios
curl -I https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio

# Verifica resposta JSON
curl https://apidadosabertos.saude.gov.br/cnes/tipounidades | jq .
```

**Critérios de Validação:**
- ✅ Status HTTP 200
- ✅ Content-Type: application/json
- ✅ Resposta com dados válidos
- ✅ Sem necessidade de autenticação

**Se alguma API estiver indisponível:**
- Documentar endpoint alternativo
- Contatar Ministério da Saúde
- Considerar usar dados mockados temporariamente

---

### Fase 1: Preparação (Dia 1)

**1.1 Setup do Ambiente**
```bash
# Clone o repositório
cd INTELLICAREREPO/agentes/tools

# Cria ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instala dependências
pip install -r requirements.txt

# Configura Redis (Docker)
docker run -d -p 6379:6379 --name health_redis redis:7-alpine
```

**1.2 Configuração**
```bash
# Cria arquivo .env
cp .env.example .env

# Edita configurações
nano .env
```

### Fase 2: Desenvolvimento Core (Dias 2-4)

**2.1 Criar Modelos de Dados**
```bash
# Cria arquivo health_data_models.py
touch health_data_models.py

# Implementa classes Pydantic (ver seção 3.1)
# - HealthUnitType
# - HealthEstablishment
# - Municipality
# - APIResponse
```

**2.2 Implementar Cache Manager**
```bash
# Cria arquivo health_cache_manager.py
touch health_cache_manager.py

# Implementa HealthCacheManager (ver seção 4.1)
# Testa conexão com Redis
python -c "from health_cache_manager import HealthCacheManager; c = HealthCacheManager(); print(c.redis.ping())"
```

**2.3 Implementar API Client**
```bash
# Cria arquivo health_api_client.py
touch health_api_client.py

# Implementa HealthAPIClient (ver seção 3.2)
# Testa consulta real
python -c "from health_api_client import HealthAPIClient; c = HealthAPIClient(); print(len(c.get_health_unit_types()))"
```

### Fase 3: Integração com Agente (Dia 5)

**3.1 Refatorar brazilian_health_data_agent.py**
```python
# Adiciona imports
from health_api_client import HealthAPIClient
from health_cache_manager import HealthCacheManager
from health_data_models import *

# Atualiza __init__
def __init__(self):
    super().__init__(self.NAME, self.DESCRIPTION)
    self.cache = HealthCacheManager()

# Adiciona novos métodos (ver seção 5.2)
```

**3.2 Atualizar get_definition()**
```python
# Adiciona novas ações ao enum
"enum": [
    # ... ações existentes ...
    "get_health_units_types",
    "search_establishments",
    "search_municipalities"
]
```

### Fase 4: Testes (Dias 6-7)

**4.1 Testes Unitários**
```bash
# Cria diretório de testes
mkdir -p tests/fixtures

# Cria arquivos de teste
touch tests/test_health_agent.py
touch tests/test_health_api_client.py
touch tests/test_cache_manager.py

# Executa testes
pytest tests/ -v --cov=agentes/tools --cov-report=html
```

**4.2 Testes de Integração**
```bash
# Testes com APIs reais (requer conexão)
pytest tests/ -v -m integration

# Testes de performance
pytest tests/ -v -m slow --durations=10
```

### Fase 5: Documentação (Dia 8)

**5.1 Docstrings**
```bash
# Valida docstrings
pydocstyle agentes/tools/

# Gera documentação
pdoc --html agentes/tools/ -o docs/api/
```

**5.2 README**
```markdown
# Brazilian Health Data Agent

## Instalação
...

## Uso
...

## Exemplos
...
```

### Fase 6: Deploy (Dias 9-10)

**6.1 Build Docker**
```bash
# Build da imagem
docker build -t brazilian-health-agent:1.0 .

# Testa localmente
docker-compose up -d

# Verifica logs
docker-compose logs -f health_agent
```

**6.2 Deploy em Produção**
```bash
# Tag para registry
docker tag brazilian-health-agent:1.0 registry.example.com/health-agent:1.0

# Push
docker push registry.example.com/health-agent:1.0

# Deploy (Kubernetes/Docker Swarm/etc)
kubectl apply -f k8s/deployment.yaml
```

### Fase 7: Validação (Dia 11)

**7.1 Testes End-to-End**
```python
# Testa integração completa com HERMES
from brazilian_health_data_agent import BrazilianHealthDataAgent
import json

agent = BrazilianHealthDataAgent()

# Teste 1: Tipos de unidade
result = agent.run(json.dumps({
    "action": "get_health_units_types",
    "params": {}
}))
print(result)

# Teste 2: Busca estabelecimentos
result = agent.run(json.dumps({
    "action": "search_establishments",
    "params": {
        "codigo_uf": 27,
        "status": 1,
        "limit": 10
    }
}))
print(result)

# Teste 3: Busca municípios
result = agent.run(json.dumps({
    "action": "search_municipalities",
    "params": {
        "municipio": "Serra",
        "uf": "ES"
    }
}))
print(result)
```

**7.2 Monitoramento**
```bash
# Verifica métricas
curl http://localhost:8000/metrics

# Verifica logs
tail -f logs/health_agent.log | jq .

# Verifica cache
redis-cli
> KEYS health:*
> TTL health:cnes:unit_types
```

---

## 11. EXEMPLOS DE USO

### 11.1 Exemplo 1: Listar Tipos de Unidades

**Input:**
```json
{
  "action": "get_health_units_types",
  "params": {}
}
```

**Output:**
```
🏥 **Tipos de Unidades de Saúde (CNES):**

• **1**: POSTO DE SAUDE
• **2**: CENTRO DE SAUDE/UNIDADE BASICA
• **4**: POLICLINICA
• **5**: HOSPITAL GERAL
• **7**: HOSPITAL ESPECIALIZADO
• **15**: UNIDADE MISTA
• **20**: PRONTO SOCORRO GERAL
• **21**: PRONTO SOCORRO ESPECIALIZADO
• **22**: CONSULTORIO ISOLADO
• **32**: UNIDADE MOVEL FLUVIAL
• **36**: CLINICA/CENTRO DE ESPECIALIDADE
• **39**: UNIDADE DE APOIO DIAGNOSE E TERAPIA (SADT ISOLADO)
• **40**: UNIDADE MOVEL TERRESTRE
• **42**: UNIDADE MOVEL DE NIVEL PRE-HOSPITALAR NA AREA DE URGENCIA
• **50**: UNIDADE DE VIGILANCIA EM SAUDE
• **60**: COOPERATIVA OU EMPRESA DE CESSAO DE TRABALHADORES NA SAUDE
• **61**: CENTRO DE PARTO NORMAL - ISOLADO
• **62**: HOSPITAL/DIA - ISOLADO
• **64**: CENTRAL DE REGULACAO DE SERVICOS DE SAUDE
• **67**: LABORATORIO CENTRAL DE SAUDE PUBLICA LACEN

✅ Total: 80 tipos
Fonte: Ministério da Saúde (CNES)
```

### 11.2 Exemplo 2: Buscar Hospitais com Centro Cirúrgico

**Input:**
```json
{
  "action": "search_establishments",
  "params": {
    "codigo_uf": 27,
    "codigo_tipo_unidade": 5,
    "status": 1,
    "estabelecimento_possui_centro_cirurgico": 1,
    "limit": 5
  }
}
```

**Output:**
```
🏥 **Estabelecimentos de Saúde Encontrados:**

**HOSPITAL GERAL DO ESTADO PROFESSOR OSVALDO BRANDAO VILELA**
  • CNES: 0000078
  • Tipo: HOSPITAL GERAL
  • Município: MACEIO - AL
  • Endereço: AVENIDA SIQUEIRA CAMPOS, 2095
  • Telefone: 8233156200

**HOSPITAL UNIVERSITARIO PROFESSOR ALBERTO ANTUNES**
  • CNES: 0000086
  • Tipo: HOSPITAL GERAL
  • Município: MACEIO - AL
  • Endereço: AVENIDA LOURIVAL MELO MOTA, S/N
  • Telefone: 8233261300

**SANTA CASA DE MISERICORDIA DE MACEIO**
  • CNES: 0000094
  • Tipo: HOSPITAL GERAL
  • Município: MACEIO - AL
  • Endereço: RUA BARAO DE ANADIA, 397
  • Telefone: 8232231744

✅ Total encontrado: 15
📄 Mostrando 3 de 15
Fonte: Ministério da Saúde (CNES)
```

### 11.3 Exemplo 3: Consultar Região de Saúde

**Input:**
```json
{
  "action": "search_municipalities",
  "params": {
    "municipio": "Serra",
    "uf": "ES"
  }
}
```

**Output:**
```
🏙️ **Municípios Encontrados:**

**ES - SERRA**
  • Código IBGE: 320500
  • Região: Sudeste
  • Macrorregião de Saúde: METROPOLITANA (3207)
  • Região de Saúde: METROPOLITANA (32002)
  • População (IBGE 2022): 520,653

✅ Total encontrado: 1
Fonte: Ministério da Saúde
```

---

## 12. TROUBLESHOOTING

### 12.1 Problemas Comuns

**Problema: Redis Connection Error**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solução:**
```bash
# Verifica se Redis está rodando
docker ps | grep redis

# Inicia Redis
docker start health_redis

# Ou via docker-compose
docker-compose up -d redis
```

---

**Problema: API Timeout**
```
httpx.TimeoutException: Request timeout
```

**Solução:**
```python
# Aumenta timeout no .env
HEALTH_API_TIMEOUT=30

# Ou no código
client = HealthAPIClient()
client.TIMEOUT = 30.0
```

---

**Problema: Cache não funciona**
```
Cache MISS sempre, nunca HIT
```

**Solução:**
```bash
# Verifica conexão Redis
redis-cli ping

# Verifica chaves
redis-cli KEYS health:*

# Verifica TTL
redis-cli TTL health:cnes:unit_types

# Limpa cache se necessário
redis-cli FLUSHDB
```

---

**Problema: Dados desatualizados**
```
Dados retornados estão antigos
```

**Solução:**
```python
# Invalida cache manualmente
from health_cache_manager import HealthCacheManager

cache = HealthCacheManager()
cache.invalidate("health:cnes:*")
```

---

## 13. MANUTENÇÃO E EVOLUÇÃO

### 13.1 Roadmap Futuro

**Versão 1.1 (Q2 2025)**
- [ ] Integração com DATASUS (SIH, SIA, SINAN)
- [ ] Suporte a queries complexas (JOIN de múltiplas fontes)
- [ ] Dashboard de visualização de dados
- [ ] Exportação de relatórios (PDF, Excel)

**Versão 1.2 (Q3 2025)**
- [ ] Análise preditiva com ML
- [ ] Alertas automáticos de anomalias
- [ ] API GraphQL
- [ ] Suporte a webhooks

**Versão 2.0 (Q4 2025)**
- [ ] Integração com HL7 FHIR
- [ ] Sincronização bidirecional
- [ ] Multi-tenancy
- [ ] Auditoria completa

### 13.2 Checklist de Manutenção Mensal

- [ ] Atualizar dependências (pip-audit, safety)
- [ ] Revisar logs de erro
- [ ] Verificar métricas de performance
- [ ] Validar integridade do cache
- [ ] Testar APIs externas
- [ ] Backup de configurações
- [ ] Revisar documentação

---

## 14. REFERÊNCIAS

### 14.1 APIs Oficiais

- **API Dados Abertos Saúde**: https://apidadosabertos.saude.gov.br
- **DATASUS**: https://datasus.saude.gov.br
- **IBGE Localidades**: https://servicodados.ibge.gov.br/api/docs/localidades

### 14.2 Documentação Técnica

- **CNES Manual**: http://cnes.datasus.gov.br/pages/downloads/documentacao.jsp
- **Pydantic Docs**: https://docs.pydantic.dev
- **HTTPX Docs**: https://www.python-httpx.org
- **Redis Docs**: https://redis.io/docs
- **Tenacity Docs**: https://tenacity.readthedocs.io

### 14.3 Padrões e Boas Práticas

- **PEP 8**: Style Guide for Python Code
- **PEP 484**: Type Hints
- **REST API Best Practices**: https://restfulapi.net
- **12-Factor App**: https://12factor.net

---

## 15. APROVAÇÕES E CONTROLE DE VERSÃO

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2025-02-02 | Equipe Técnica | Versão inicial |
| | | | |

### Aprovações

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Tech Lead | | | |
| Arquiteto de Software | | | |
| DevOps Lead | | | |
| QA Lead | | | |

---

**Documento Relacionado:** [V0-202502021900-EF-BrazilianHealthDataAgent.md](./V0-202502021900-EF-BrazilianHealthDataAgent.md)

**Status:** 📋 Pronto para Implementação


