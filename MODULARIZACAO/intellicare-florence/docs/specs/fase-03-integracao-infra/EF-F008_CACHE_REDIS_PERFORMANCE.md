# EF-F008 — Cache Redis e Otimizacao de Performance

> Ativar o Redis (ja instalado como dependencia) para cache de interpretacoes de exames, queries RAG e contexto Oswaldo — reduzindo latencia em requests repetidos e aliviando carga no ChromaDB.

## 1. Objetivo

Reduzir latencia e CPU em casos de uso repetitivos:
- Interpretacao do mesmo exame com o mesmo valor: cache de 1h (resultado deterministico)
- Query RAG identica: cache de 6h (ChromaDB e relativamente lento)
- Contexto Oswaldo por patient_id: cache de 30min (ja especificado em EF-F007, centralizar aqui)
- Analise completa identica (mesmo patient_id + mesmo lab_results): cache de 15min

## 2. Justificativa

- Redis esta em `pyproject.toml` mas com zero uso no codigo
- ChromaDB pode levar 200-500ms por query semantica — totalmente evitavel se query e identica
- Em contexto de uso clinico, o mesmo paciente tem os mesmos labs consultados multiplas vezes na mesma sessao (Wanda + Oswaldo + Florence todos consultando)
- Analise deterministica: mesmos inputs → sempre mesmo output, portanto cacheable

## 3. Escopo

### 3.1 FlorenceCache

```python
class FlorenceCache:
    """
    Interface de cache para a Florence usando Redis.

    Fallback: se Redis indisponivel, opera sem cache (nao quebra).
    Serialization: JSON para todos os dados (Pydantic models → dict).

    Prefixos de chave:
    - "florence:lab:{lab_id}:{value}:{gender}:{age_group}" → LabInterpretation (TTL 1h)
    - "florence:rag:{query_hash}" → list[ProtocolChunk] (TTL 6h)
    - "florence:oswaldo:{patient_id}" → OswaldoContext (TTL 30min)
    - "florence:analysis:{hash}" → ClinicalAnalysis (TTL 15min)
    """

    async def get_lab_interpretation(
        self,
        lab_id: str,
        value: float,
        gender: Optional[str] = None,
        age_group: Optional[str] = None,   # "pediatric" | "adult" | "elderly"
    ) -> Optional[LabInterpretation]:
        """
        Cache de interpretacao de exame individual.
        Chave deterministicca: nao depende de patient_id (mesmo resultado para qualquer paciente).
        """

    async def set_lab_interpretation(
        self,
        lab_id: str,
        value: float,
        interpretation: LabInterpretation,
        gender: Optional[str] = None,
        age_group: Optional[str] = None,
        ttl: int = 3600,                   # 1 hora
    ) -> None: ...

    async def get_rag_result(
        self,
        query: str,
        top_k: int = 3,
    ) -> Optional[list[dict]]:
        """
        Cache de resultado RAG.
        Chave: hash SHA256 da query normalizada + top_k.
        """

    async def set_rag_result(
        self,
        query: str,
        result: list[dict],
        top_k: int = 3,
        ttl: int = 21600,                  # 6 horas
    ) -> None: ...

    async def get_oswaldo_context(
        self,
        patient_id: str,
    ) -> Optional[dict]:
        """Cache de contexto Oswaldo por patient_id."""

    async def set_oswaldo_context(
        self,
        patient_id: str,
        context: dict,
        ttl: int = 1800,                   # 30 minutos
    ) -> None: ...

    async def invalidate_patient(
        self,
        patient_id: str,
    ) -> int:
        """
        Invalida todo o cache relacionado a um patient_id.
        Retorna: numero de chaves removidas.
        Chamado quando nova analise e salva (EF-F002).
        """

    async def is_available(self) -> bool:
        """Verifica disponibilidade do Redis (PING)."""

    async def get_stats(self) -> dict:
        """
        Retorna estatisticas de uso do cache.
        {hit_rate, total_keys, memory_used_mb}
        Util para monitoramento (EF-F009).
        """
```

### 3.2 Integracao nos Componentes

```python
# LabInterpreter — cache de interpretacoes individuais
class LabInterpreter:
    async def interpret(self, lab_id, value, gender=None, age_years=None):
        # 1. Tentar cache
        cached = await self._cache.get_lab_interpretation(lab_id, value, gender, age_group)
        if cached:
            return cached

        # 2. Calcular (logica existente)
        result = self._do_interpret(lab_id, value)

        # 3. Salvar no cache
        await self._cache.set_lab_interpretation(lab_id, value, result, gender, age_group)
        return result


# ProtocolRetriever — cache de queries RAG
class ProtocolRetriever:
    async def retrieve(self, query, top_k=3):
        # 1. Tentar cache
        cached = await self._cache.get_rag_result(query, top_k)
        if cached:
            return [ProtocolChunk(**c) for c in cached]

        # 2. Query ChromaDB (logica existente)
        result = self._do_retrieve(query, top_k)

        # 3. Salvar no cache
        await self._cache.set_rag_result(query, [c.dict() for c in result], top_k)
        return result
```

### 3.3 Metricas de Cache (para EF-F009)

```python
class CacheMetrics:
    """
    Coleta metricas de hit/miss para monitoramento.
    Armazenado no proprio Redis (contadores atomicos).
    """

    METRICS_KEYS = {
        "florence:metrics:lab:hits": "Cache hits em interpretacoes de exames",
        "florence:metrics:lab:misses": "Cache misses em interpretacoes de exames",
        "florence:metrics:rag:hits": "Cache hits em queries RAG",
        "florence:metrics:rag:misses": "Cache misses em queries RAG",
    }
```

### 3.4 Endpoint de Status

```python
# GET /api/v1/cache/stats
# Retorna: status do cache e metricas
{
    "redis_available": True,
    "total_keys": 1247,
    "memory_used_mb": 8.4,
    "hit_rates": {
        "lab_interpretation": 0.73,    # 73% das interpretacoes servidas do cache
        "rag_queries": 0.51,           # 51% das queries RAG servidas do cache
        "oswaldo_context": 0.88,       # 88% dos contextos Oswaldo do cache
    },
    "ttls": {
        "lab_interpretation": 3600,
        "rag_queries": 21600,
        "oswaldo_context": 1800,
    }
}

# DELETE /api/v1/cache
# Limpa todo o cache da Florence (operacao administrativa)
# Requer header Authorization

# DELETE /api/v1/cache/patient/{patient_id}
# Invalida cache de um paciente especifico
```

### 3.5 Configuracao

```env
FLORENCE_REDIS_URL=redis://redis:6379/0
FLORENCE_REDIS_PASSWORD=                       # Opcional
FLORENCE_CACHE_ENABLED=true
FLORENCE_CACHE_LAB_TTL=3600                   # 1h
FLORENCE_CACHE_RAG_TTL=21600                  # 6h
FLORENCE_CACHE_OSWALDO_TTL=1800               # 30min
FLORENCE_CACHE_ANALYSIS_TTL=900               # 15min
```

### 3.6 Impacto de Performance Esperado

| Operacao | Antes (sem cache) | Depois (cache hit) | Ganho |
|----------|------------------|--------------------|-------|
| Interpretar exame | ~2ms | < 1ms | 2x |
| Query RAG ChromaDB | ~300ms | < 1ms | 300x |
| Contexto Oswaldo | ~200ms | < 1ms | 200x |
| Analise completa (5 exames + RAG) | ~600ms | ~50ms | 12x |

## 4. Testes

- FlorenceCache: get/set lab interpretation (cache hit e miss), Redis down fallback (3 testes)
- FlorenceCache: get/set RAG result, hash deterministico de query (2 testes)
- FlorenceCache: invalidate_patient remove chaves corretas (1 teste)
- LabInterpreter com cache: hit evita calculo, miss calcula e armazena (2 testes)
- ProtocolRetriever com cache: hit evita ChromaDB, miss consulta e armazena (2 testes)
- /api/v1/cache/stats: retorna metricas (1 teste)
- **Total**: 11+ testes novos

## 5. Criterios de Aceitacao

- [ ] `FlorenceCache` com graceful fallback (sem Redis: opera sem cache)
- [ ] `LabInterpreter` usa cache para interpretacoes individuais (TTL 1h)
- [ ] `ProtocolRetriever` usa cache para queries RAG (TTL 6h)
- [ ] `OswaldoClient` usa cache para contexto Oswaldo (TTL 30min)
- [ ] Invalidacao por patient_id quando nova analise e salva
- [ ] /api/v1/cache/stats com hit rates por tipo
- [ ] 198 testes existentes continuam passando
- [ ] 11+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/cache/redis_cache.py`, `florence/cache/__init__.py`
- **Arquivos modificados**: `florence/engine/lab_interpreter.py` (integrar cache), `florence/engine/rag/retriever.py` (integrar cache), `florence/integrations/oswaldo.py` (integrar cache), `florence/api/app.py` (endpoints de cache), `florence/config.py`
- **Linhas estimadas**: ~280
- **Testes novos**: ~11
