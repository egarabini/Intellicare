# EF-W002 — IPS-First Aprimorado

> Cache inteligente do IPS, validacao e enriquecimento para garantir contexto clinico sempre disponivel.

## 1. Objetivo

Aprimorar a regra **IPS-First** da Wanda para:
- Cache do IPS por paciente com TTL configuravel
- Validacao de integridade do IPS (campos obrigatorios)
- Enriquecimento com dados de agentes especializados
- Estrategia graceful quando Florence indisponivel
- Propagacao do IPS para todos os agentes da consulta

## 2. Justificativa

- **Performance**: Cada consulta nao deve buscar IPS de novo
- **Disponibilidade**: Cache garante IPS mesmo se Florence cair
- **Completude**: IPS pode estar incompleto, precisa enriquecimento
- **Seguranca**: Toda consulta com patient_id DEVE ter IPS
- **Rastreabilidade**: Saber se IPS veio do cache ou foi buscado

## 3. Escopo

### 3.1 Regra IPS-First v2.0

A regra atual (v1.0) simplesmente bloqueia requisicoes sem IPS.

A v2.0 adiciona:
1. **Cache Redis**: IPS armazenado com TTL (padrão 1 hora)
2. **Busca automatica**: Se nao tem IPS, busca Florence automaticamente
3. **Fallback gracioso**: Se Florence indisponivel, usa dados basicos
4. **Enriquecimento**: Complementa IPS com dados de Oswaldo/Geralda
5. **Invalidacao**: Invalida cache quando Florence emite evento de update

### 3.2 IPSManager

```python
class IPSManager:
    """
    Gerencia o IPS (International Patient Summary) de forma inteligente.

    IPS = International Patient Summary
    Formato: FHIR Bundle com:
    - Patient (demograficos)
    - Conditions (diagnosticos ativos)
    - MedicationStatements (medicamentos em uso)
    - AllergyIntolerances (alergias)
    - Observations recentes (exames, sinais vitais)
    - Immunizations (vacinas)
    """

    def __init__(
        self,
        florence_client,
        redis_client,
        oswaldo_client,
        ips_ttl: int = 3600,       # 1 hora padrao
        stale_ttl: int = 86400,    # 24 horas para stale
    ):
        ...

    async def get(
        self,
        patient_id: str,
        force_refresh: bool = False,
    ) -> IPSBundle:
        """
        Retorna IPS do paciente.

        Estrategia:
        1. Verificar Redis cache
           a. Existe e nao expirou → retornar cache (TTL)
           b. Existe mas expirou → retornar stale + buscar async
           c. Nao existe → buscar Florence sincronamente

        2. Buscar Florence:
           GET {florence_url}/api/v1/ips/{patient_id}
           Se erro → usar stale (se disponivel) ou IPS minimo

        3. Enriquecer:
           - Adicionar estagiamento de doencas (Oswaldo)
           - Adicionar dados de cuidado (Geralda)

        4. Atualizar cache

        Returns:
            IPSBundle com metadados (source, age, freshness)
        """

    async def get_batch(
        self,
        patient_ids: list[str],
    ) -> dict[str, IPSBundle]:
        """Busca IPS de multiplos pacientes (paralelo)."""

    async def invalidate(self, patient_id: str) -> None:
        """
        Invalida cache de um paciente.

        Chamado quando Florence emite evento de atualizacao
        ou quando exame relevante e registrado.
        """

    async def validate(
        self,
        ips: IPSBundle,
    ) -> ValidationResult:
        """
        Valida integridade do IPS.

        Campos obrigatorios:
        - patient_id
        - conditions (pelo menos uma)
        - medications (pode ser vazio)
        - allergies (pode ser vazio)

        Alertas (nao bloqueantes):
        - IPS mais antigo que 90 dias
        - Sem exames laboratoriais recentes
        - Sem medicamentos registrados
        """
```

### 3.3 Enriquecimento do IPS

```python
class IPSEnricher:
    """Enriquece IPS com dados de agentes especializados."""

    async def enrich(
        self,
        ips: IPSBundle,
        modules_available: list[str],
    ) -> EnrichedIPS:
        """
        Adiciona contexto especializado ao IPS base.

        Se Oswaldo disponivel:
        - Estagiamento de DRC (G1-G5, A1-A3)
        - Score de risco cardiovascular
        - Controle de DM2 (HbA1c)
        - Controle de HAS (PA media)

        Se Geralda disponivel:
        - Macroestado da jornada (E0-E7)
        - Score de adesao atual
        - Planos de cuidado ativos
        - Nivel de risco Geralda

        Returns:
            EnrichedIPS com secoes adicionais:
            - staging: {chronic_conditions: [...]}
            - care: {macrostate, adherence_score, risk_level}
        """
```

### 3.4 Fallback e Graceful Degradation

```python
class IPSFallbackStrategy:
    """Estrategia de fallback quando Florence nao esta disponivel."""

    async def get_minimal_ips(
        self,
        patient_id: str,
    ) -> IPSBundle:
        """
        Constroi IPS minimo sem Florence.

        Fontes alternativas:
        1. Cache stale (expirado mas disponivel)
        2. Dados basicos do Oswaldo (se disponivel)
        3. Dados basicos da Geralda (se disponivel)
        4. IPS vazio estruturado (ultima opcao)

        Marca IPS como "degraded" para que agentes
        saibam que dados podem estar incompletos.
        """

    def build_empty_ips(self, patient_id: str) -> IPSBundle:
        """
        IPS estruturado vazio.

        Usado quando todas as fontes falharam.
        Permite consulta continuar com aviso.
        """
```

### 3.5 Propagacao para Agentes

```python
class WandaOrchestrator:
    """Como o IPS e propagado para os agentes."""

    async def execute_with_ips(
        self,
        patient_id: str,
        query: str,
        target_agents: list[str],
    ) -> OrchestratedResponse:
        """
        Carrega IPS e propaga para todos os agentes da consulta.

        Fluxo:
        1. ips = await ips_manager.get(patient_id)
        2. ips_enriched = await ips_enricher.enrich(ips, available_modules)
        3. validation = await ips_manager.validate(ips_enriched)
        4. Para cada agente:
           POST {agent_url}/api/v1/analyze
           {
               "query": query,
               "patient_id": patient_id,
               "ips": ips_enriched,        # <- IPS completo
               "context": {...}
           }
        5. Agregar respostas
        """
```

### 3.6 Metricas e Cache

```python
# Metricas de IPS
ips_cache_hits = Counter("wanda_ips_cache_hits_total", "Cache hits", ["freshness"])
ips_cache_misses = Counter("wanda_ips_cache_misses_total", "Cache misses")
ips_enrichments = Counter("wanda_ips_enrichments_total", "IPS enriquecidos", ["added_sources"])
ips_fallbacks = Counter("wanda_ips_fallbacks_total", "Fallbacks usados", ["reason"])

# Histograma
ips_load_time = Histogram("wanda_ips_load_seconds", "Tempo de carregamento do IPS")
ips_age = Histogram("wanda_ips_age_hours", "Idade do IPS usado")
```

### 3.7 Tabela de Cache (Redis keys)

```
# Cache de IPS
wanda:ips:{patient_id}               TTL = 3600s (1h)
wanda:ips:stale:{patient_id}         TTL = 86400s (24h)
wanda:ips:enriched:{patient_id}      TTL = 1800s (30min)

# Invalids
HDEL wanda:ips:{patient_id}          # Ao invalidar
PUBLISH wanda:ips:invalidated {pid}  # Notifica subscribed workers
```

### 3.8 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| GET | `/api/v1/ips/{patient_id}` | Busca IPS (com cache) |
| DELETE | `/api/v1/ips/{patient_id}/cache` | Invalida cache do IPS |
| GET | `/api/v1/ips/{patient_id}/validate` | Valida IPS atual |
| GET | `/api/v1/ips/stats` | Metricas de cache |

## 4. Testes

- IPSManager: cache hit, cache miss, stale, force_refresh (8 testes)
- IPSEnricher: com Oswaldo, com Geralda, ambos, nenhum (5 testes)
- IPSFallbackStrategy: florence down, stale available, empty (4 testes)
- Validacao: IPS completo, faltando campos, antigo (4 testes)
- Propagacao: IPS chegando a todos os agentes (3 testes)
- Metricas: hits, misses, enrichments (2 testes)
- Endpoints (4 testes)
- **Total**: 30+ testes

## 5. Criterios de Aceitacao

- [ ] Cache Redis funcional com TTL de 1 hora
- [ ] Busca automatica de IPS quando ausente
- [ ] Stale-while-revalidate (retorna stale, busca em background)
- [ ] Enriquecimento com Oswaldo (staging) e Geralda (jornada)
- [ ] Fallback gracioso quando Florence indisponivel
- [ ] IPS propagado para todos os agentes da consulta
- [ ] Invalidacao por evento ou manual
- [ ] Metricas Prometheus
- [ ] 4 novos endpoints
- [ ] 30+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~6
- **Arquivos modificados**: ~4 (orchestrator, safety_rules, api, config)
- **Linhas estimadas**: ~1.000
- **Testes novos**: ~30
