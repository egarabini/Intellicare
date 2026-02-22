# EF-D008 — Integracao Zilda (Indicadores Territoriais Auto-Alimentados)

> Consumir dados da Zilda para alimentar automaticamente indicadores de qualidade baseados em cobertura ESF, internacoes evitaveis (ICSAP), vazios assistenciais e mortalidade — dimensao de equidade e resultado populacionais.

## 1. Objetivo

Implementar `ZildaIndicatorBridge` que traduz os dados territoriais da Zilda em medicoes automaticas de indicadores de qualidade do Donabedian:

- "% de cobertura ESF no municipio" (pilar Equidade / dimensao Estrutura)
- "Taxa de internacoes evitaveis (ICSAP) por 10.000 hab" (pilar Efetividade / dimensao Resultado)
- "% da populacao com acesso adequado a dialise" (pilar Equidade / dimensao Estrutura)
- "Taxa de mortalidade infantil por 1.000 nascidos vivos" (pilar Efetividade / dimensao Resultado)
- "Score de balanco oferta x demanda do territorio" (pilar Otimidade / dimensao Estrutura)

## 2. Justificativa

- Donabedian avalia qualidade do servico de saude, mas sem contexto territorial ignora dimensao populacional
- Equidade (pilar mais fraco do Donabedian) nao pode ser medida sem dados de acesso real da Zilda
- ICSAP e o indicador de desfecho mais poderoso — se ha muitas internacoes evitaveis, o sistema esta falhando na APS
- Sem integracao com Zilda, o pilar Equidade continua em 4/10 (apenas conceitual)
- Zilda ja tem todos esses dados agregados — aproveitamento direto via API

## 3. Escopo

### 3.1 Mapeamento Zilda → Indicadores Donabedian

```python
# Os indicadores abaixo devem existir no seed do Donabedian (ou ser criados automaticamente)
# e ser alimentados via Zilda periodicamente (cron semanal — dados DATASUS tem baixa frequencia)

ZILDA_TO_INDICATOR_MAP = [
    ZildaIndicatorMapping(
        indicator_name="Cobertura ESF no Municipio",
        indicator_description="% da populacao coberta por equipes de Saude da Familia",
        triad_dimension="structure",
        pillar="equidade",
        zilda_capability="esf_coverage",
        zilda_query={
            "capability": "esf_coverage",
            "context": {
                "include_regional_comparison": True,
            },
        },
        value_extractor="coverage_data.coverage_percentage",
        calculation="coverage_percentage",
        target_value=60.0,               # Meta federal Previne Brasil
        target_operator=">=",
        unit="%",
        period_type="monthly",
    ),
    ZildaIndicatorMapping(
        indicator_name="Taxa de Internacoes Evitaveis (ICSAP)",
        indicator_description="Internacoes Sensiveis a APS por 10.000 habitantes no municipio",
        triad_dimension="outcome",
        pillar="efetividade",
        zilda_capability="hospitalization_data",
        zilda_query={
            "capability": "hospitalization_data",
            "context": {
                "metric": "icsap_rate",
                "period_months": 12,
            },
        },
        value_extractor="icsap_rate_per_10k",
        calculation="avoidable_admissions / population * 10_000",
        target_value=40.0,               # Meta: < 40 ICSAP/10k hab (referencia CONASS)
        target_operator="<=",
        unit="por 10k hab",
        period_type="yearly",
    ),
    ZildaIndicatorMapping(
        indicator_name="Acesso a Dialise para Pacientes CKD G4-G5",
        indicator_description="% da populacao CKD G4+ com acesso adequado a servico de dialise (< 50km)",
        triad_dimension="structure",
        pillar="equidade",
        zilda_capability="void_analysis",
        zilda_query={
            "capability": "void_analysis",
            "context": {
                "service_code": "117",       # CNES: Servico de Dialise
                "max_distance_km": 50,
                "metric": "population_coverage_pct",
            },
        },
        value_extractor="coverage_percentage",
        calculation="population_within_50km_of_dialysis / total_population * 100",
        target_value=80.0,               # Meta: 80% com acesso
        target_operator=">=",
        unit="%",
        period_type="quarterly",
    ),
    ZildaIndicatorMapping(
        indicator_name="Taxa de Mortalidade Infantil",
        indicator_description="Obitos de criancas < 1 ano por 1.000 nascidos vivos",
        triad_dimension="outcome",
        pillar="efetividade",
        zilda_capability="vital_indicators",
        zilda_query={
            "capability": "vital_indicators",
            "context": {
                "metric": "infant_mortality_rate",
                "period_years": 1,
            },
        },
        value_extractor="infant_mortality_rate",
        calculation="deaths_under_1 / live_births * 1_000",
        target_value=10.0,               # Meta ODS: < 12/1000 (BR atual ~12.4)
        target_operator="<=",
        unit="por 1000 NV",
        period_type="yearly",
    ),
    ZildaIndicatorMapping(
        indicator_name="Balanco de Oferta x Demanda em APS",
        indicator_description="Score de balanco entre oferta de servicos APS e demanda populacional (0-100)",
        triad_dimension="structure",
        pillar="otimidade",
        zilda_capability="supply_demand_analysis",
        zilda_query={
            "capability": "supply_demand_analysis",
            "context": {
                "service_type": "APS",
                "metric": "balance_score",
            },
        },
        value_extractor="balance_score",
        calculation="balance_score",     # Ja vem calculado pela Zilda (0-100)
        target_value=60.0,               # Meta: score >= 60 (Equilibrado ou Superavit)
        target_operator=">=",
        unit="score",
        period_type="quarterly",
    ),
]
```

### 3.2 ZildaClient (no Donabedian)

```python
class ZildaClient:
    """
    Cliente HTTP para integracao com Zilda (8003).
    Usa o contrato padrao: POST /api/v1/analyze

    Cache: 72h por consulta (dados DATASUS tem frequencia semanal/mensal)
    Graceful degradation: se Zilda indisponivel, indicadores ficam
    sem medicao para o periodo.

    Timeout: 30s (Zilda pode consultar DATASUS on-demand — latencia maior)
    """

    async def get_esf_coverage(
        self,
        municipio_ibge: Optional[str] = None,
    ) -> dict:
        """
        Cobertura ESF no municipio ou regiao.
        Ex: {"coverage_percentage": 68.4, "teams_count": 142, "population_covered": 184_200}
        """

    async def get_icsap_rate(
        self,
        period_months: int = 12,
        municipio_ibge: Optional[str] = None,
    ) -> dict:
        """
        Taxa de internacoes sensiveis a APS.
        Ex: {"icsap_rate_per_10k": 38.7, "avoidable_admissions": 1_240, "total_population": 320_000}
        """

    async def get_service_void_coverage(
        self,
        service_code: str,
        max_distance_km: float = 50.0,
    ) -> dict:
        """
        Cobertura populacional para servico especifico.
        Ex: {"coverage_percentage": 74.2, "population_within_distance": 196_000, "voids_identified": 3}
        """

    async def get_vital_indicators(
        self,
        period_years: int = 1,
    ) -> dict:
        """
        Indicadores vitais do municipio.
        Ex: {"infant_mortality_rate": 11.2, "maternal_mortality_rate": 45.0, "live_births": 8_420}
        """

    async def get_supply_demand_balance(
        self,
        service_type: str = "APS",
    ) -> dict:
        """
        Balanco oferta x demanda.
        Ex: {"balance_score": 58.0, "balance_status": "EQUILIBRADO", "deficit_services": ["CEME"]}
        """

    async def is_available(self) -> bool:
        """Verifica disponibilidade da Zilda."""
```

### 3.3 ZildaIndicatorBridge

```python
@dataclass
class ZildaIndicatorMapping:
    indicator_name: str
    indicator_description: str
    triad_dimension: str            # "structure" | "process" | "outcome"
    pillar: str                     # "equidade" | "efetividade" | "otimidade" ...
    zilda_capability: str           # Nome da capability da Zilda
    zilda_query: dict               # Payload para /api/v1/analyze da Zilda
    value_extractor: str            # Dot-notation para extrair valor do response
    calculation: str                # Documentacao da formula (apenas descritivo)
    target_value: float
    target_operator: str            # ">=" | "<="
    unit: str
    period_type: str                # "monthly" | "quarterly" | "yearly"
    # Municipio IBGE (opcional — Donabedian pode ser configurado por municipio)
    municipio_ibge: Optional[str] = None


class ZildaIndicatorBridge:
    """
    Traduz dados da Zilda em medicoes para o Donabedian.

    Executado:
    1. Via job schedulado (cron semanal as domingos 03:00)
       Frequencia semanal: dados DATASUS mudam mensalmente, mais do que suficiente
    2. Via endpoint manual: POST /api/v1/sync/zilda
    3. Configuravel por municipio IBGE (INTELLICARE_MUNICIPIO_IBGE)

    Diferenca vs Oswaldo:
    - Oswaldo: dados por paciente, cron DIARIO
    - Zilda: dados territoriais/populacionais, cron SEMANAL
    """

    async def sync_all_indicators(self) -> SyncResult:
        """
        Sincroniza todos os indicadores territoriais mapeados.

        Para cada mapeamento:
        1. Chama Zilda via POST /api/v1/analyze com capability correta
        2. Extrai valor usando value_extractor (dot-notation)
        3. Verifica se ja existe medicao para o periodo (skip se sim)
        4. Cria nova Measurement via DAO do Donabedian
        5. Associa ao pilar e dimensao corretos
        6. Log do resultado

        Retorna: SyncResult com contagem de criados, ignorados, erros.
        """

    async def sync_indicator(
        self,
        mapping: ZildaIndicatorMapping,
    ) -> Optional[dict]:
        """Sincroniza um indicador especifico."""

    def _extract_value(
        self,
        response: dict,
        extractor: str,
    ) -> Optional[float]:
        """
        Extrai valor do response usando dot-notation.
        Ex: "coverage_data.coverage_percentage" → response["coverage_data"]["coverage_percentage"]
        """

    def _calculate_period_dates(
        self,
        period_type: str,
    ) -> tuple[str, str]:
        """
        Calcula period_start e period_end para o tipo de periodo.
        monthly: mes atual
        quarterly: trimestre atual
        yearly: ano atual (ou ano anterior se dados SIM/SINASC nao disponiveis ainda)
        """
```

### 3.4 Configuracao de Municipio

```python
# O Donabedian pode ser configurado para um municipio especifico
# Isso permite que indicadores territoriais sejam corretos para o municipio do hospital

# config.py
@dataclass
class DonabedianConfig:
    # ... configuracoes existentes ...

    # Configuracao territorial (para integracao Zilda)
    municipio_ibge: Optional[str] = None        # Ex: "3550308" (Sao Paulo)
    municipio_name: Optional[str] = None         # Ex: "Sao Paulo"
    zilda_url: str = "http://zilda:8003"
    zilda_enabled: bool = True
    zilda_sync_cron: str = "0 3 * * 0"          # Domingos 03:00
    zilda_cache_hours: int = 72                  # 3 dias de cache
    zilda_timeout_seconds: int = 30              # Zilda pode ser lenta (DATASUS)
```

### 3.5 Endpoints REST Novos

```python
# POST /api/v1/sync/zilda
# Dispara sincronizacao manual com Zilda
# Retorna: SyncResult

# GET /api/v1/sync/zilda/status
# Retorna: ultima sincronizacao (data, resultado, indicadores atualizados)

# GET /api/v1/sync/mappings/zilda
# Retorna: lista de mapeamentos Zilda → Indicadores Donabedian

# GET /api/v1/sync/status
# Retorna: status de TODAS as fontes (oswaldo + zilda) em um unico endpoint
# {
#   "sources": {
#     "oswaldo": {"last_sync": "...", "status": "ok", "indicators_synced": 5},
#     "zilda": {"last_sync": "...", "status": "ok", "indicators_synced": 5}
#   },
#   "total_auto_indicators": 10
# }
```

### 3.6 Configuracao ENV

```env
INTELLICARE_ZILDA_URL=http://zilda:8003
INTELLICARE_ZILDA_ENABLED=true
INTELLICARE_DONABEDIAN_SYNC_ZILDA_ENABLED=true
INTELLICARE_DONABEDIAN_SYNC_ZILDA_CRON="0 3 * * 0"    # Domingos 03:00
INTELLICARE_MUNICIPIO_IBGE=3550308                      # Codigo IBGE do municipio
INTELLICARE_MUNICIPIO_NAME="Sao Paulo"
```

## 4. Testes

- ZildaClient: get_esf_coverage, get_icsap_rate, get_service_void_coverage, Zilda indisponivel (5 testes)
- ZildaIndicatorBridge.sync_all_indicators: dados disponiveis, Zilda down, extrator invalido (4 testes)
- _extract_value: dot-notation simples, aninhado, campo inexistente (3 testes)
- Mapeamentos: valor extraido correto de response simulado para cada indicador (5 testes)
- Endpoints: sync, status, mappings, status geral (4 testes)
- **Total**: 21+ testes novos

## 5. Criterios de Aceitacao

- [ ] 5 indicadores territoriais mapeados para dados da Zilda
- [ ] `ZildaIndicatorBridge` com sync automatico (semanal) e manual
- [ ] Graceful degradation: Zilda down = indicadores sem medicao (nao erro)
- [ ] Deduplicacao: nao cria medicao duplicada para o mesmo periodo
- [ ] Configuravel por municipio IBGE via variavel de ambiente
- [ ] Endpoint `/api/v1/sync/status` consolida Oswaldo + Zilda
- [ ] Job schedulado configurado no docker-compose (cron semanal)
- [ ] 363 testes v1.0 continuam passando
- [ ] 21+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `integrations/zilda.py`, `sync/zilda_bridge.py` (+ refatorar `sync/oswaldo_bridge.py` para base compartilhada `sync/base_bridge.py`)
- **Arquivos modificados**: `api/routes/sync.py` (adicionar endpoints Zilda + status unificado), `config.py`, `docker-compose.yml`
- **Linhas estimadas**: ~350 (+ ~50 de refatoracao da base compartilhada)
- **Testes novos**: ~21

## 7. Nota de Arquitetura — Base Compartilhada

```python
# sync/base_bridge.py — extrair logica comum de Oswaldo e Zilda

class BaseIndicatorBridge:
    """
    Base para bridges de sincronizacao de indicadores externos.
    Oswaldo e Zilda herdam desta classe.
    """

    async def _get_or_create_indicator(
        self,
        name: str,
        description: str,
        pillar: str,
        triad_dimension: str,
        unit: str,
        target_value: float,
        target_operator: str,
        period_type: str,
    ) -> str:
        """
        Retorna ID de indicador existente ou cria novo.
        Evita duplicacao de indicadores auto-criados entre syncs.
        """

    async def _create_measurement_if_not_exists(
        self,
        indicator_id: str,
        period_start: str,
        period_end: str,
        value: float,
        source: str,    # "oswaldo" | "zilda"
        notes: str,
    ) -> bool:
        """
        Cria medicao apenas se nao existe para o periodo.
        Retorna True se criou, False se ja existia (duplicata ignorada).
        """
```
