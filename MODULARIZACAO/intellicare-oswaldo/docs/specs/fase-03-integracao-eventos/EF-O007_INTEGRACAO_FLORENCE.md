# EF-O007 — Integracao Florence (Exames e RAG Clinico)

> Integrar o Oswaldo com a Florence para enriquecimento com resultados laboratoriais detalhados, interpretacao RAG de exames e contexto clinico expandido.

## 1. Objetivo

Implementar o `FlorenceClient` no Oswaldo para consumir dados da Florence quando disponivel:

- Buscar resultados laboratoriais completos (nao apenas os registrados no FHIR local)
- Solicitar interpretacao RAG de exames para o contexto especifico do paciente
- Enriquecer o estadiamento com dados que Florence tem mas Oswaldo nao armazena localmente
- Florence pode ter exames de outras fontes (laboratorio externo, integracao HIS)

## 2. Justificativa

- Oswaldo atualmente so usa observacoes do seu proprio FHIRDataStore
- Florence tem RAG de protocolos clinicos e pode contextualizar resultados anormais
- Florence pode ter exames mais recentes se integrada ao HIS/LIS
- Separacao de responsabilidades: Florence interpreta, Oswaldo estadeia e monitora

## 3. Escopo

### 3.1 FlorenceClient

```python
class FlorenceClient:
    """
    Cliente HTTP para integracao com Florence (8002).

    Usa o contrato padrao Wanda: POST /api/v1/analyze com capability especifica.
    Graceful degradation: se Florence indisponivel, Oswaldo usa apenas dados locais.

    Cache: 15 min por patient_id (Florence e computacionalmente cara).
    """

    BASE_URL: str  # Configurado via env: INTELLICARE_FLORENCE_URL

    def __init__(
        self,
        http_client,
        cache_manager,
    ):
        ...

    async def get_recent_labs(
        self,
        patient_id: str,
        days: int = 90,
        lab_codes: Optional[list[str]] = None,  # LOINC codes
    ) -> Optional[dict]:
        """
        Busca resultados laboratoriais recentes na Florence.

        Chama: POST /api/v1/analyze
        {
            "query": "Resultados laboratoriais recentes",
            "patient_id": patient_id,
            "capability": "lab_results",
            "context": {"requesting_agent": "oswaldo", "days": days}
        }

        Retorna dict com observacoes no formato FHIR Observation, ou None se indisponivel.
        Cache: 15 min.
        """

    async def get_lab_interpretation(
        self,
        patient_id: str,
        lab_code: str,
        lab_value: float,
        context: dict,
    ) -> Optional[str]:
        """
        Solicita interpretacao RAG de um resultado especifico.

        Util para resultados ambiguos:
        "eGFR 48 com clearance de creatinina 52 — qual usar para dosagem?"

        Retorna string com interpretacao clinica ou None.
        Cache: 30 min.
        """

    async def get_clinical_context(
        self,
        patient_id: str,
    ) -> Optional[dict]:
        """
        Contexto clinico ampliado: IPS enriquecido da Florence.

        Retorna:
        {
            "conditions": [...],         # Condicoes do IPS
            "medications": [...],        # Medicamentos atuais
            "allergies": [...],
            "recent_encounters": [...],
            "florence_enrichment": {...} # Dados extras da Florence (RAG, LLM)
        }

        Cache: 30 min.
        """

    async def is_available(self) -> bool:
        """
        Verifica disponibilidade da Florence (GET /api/v1/health).
        Nao lanca excecao — retorna False se indisponivel.
        """
```

### 3.2 FlorenceEnricher

```python
class FlorenceEnricher:
    """
    Enriquece o estadiamento do Oswaldo com dados da Florence.

    Estrategia:
    1. Tenta buscar labs recentes da Florence
    2. Mescla com observacoes locais (Florence tem prioridade se mais recente)
    3. Se Florence indisponivel: usa apenas dados locais (graceful degradation)
    4. Registra no metadata se Florence foi usada
    """

    async def enrich_observations(
        self,
        patient_id: str,
        local_observations: dict,
        disease_id: str,
    ) -> tuple[dict, dict]:
        """
        Retorna: (enriched_observations, enrichment_metadata)

        enriched_observations: local_observations com dados da Florence sobrepostos
        enrichment_metadata: {
            "florence_available": True,
            "florence_labs_found": 3,
            "labs_updated_from_florence": ["egfr", "acr"],
            "labs_only_local": ["potassium"],
        }
        """

    async def get_enriched_context(
        self,
        patient_id: str,
        staging_result: StagingResult,
    ) -> Optional[str]:
        """
        Contexto clinico adicional da Florence para incluir no summary.

        Exemplo de retorno:
        "Florence: HbA1c em queda nos ultimos 3 testes (9.3% → 8.8% → 8.1%).
         Relatorio de endocrinologia recente menciona inicio de insulina basica."
        """
```

### 3.3 Modificacoes no ChronicDiseaseEngine

```python
# Em get_patient_summary() e calculate_staging():
# Antes de calcular, tenta enriquecer observacoes via FlorenceEnricher
# Se Florence indisponivel: continua com dados locais sem interrupcao

async def get_patient_summary(
    self,
    patient_id: str,
    disease_ids: list[str],
    use_florence: bool = True,      # NOVO: flag para controlar enriquecimento
) -> OswaldoPatientSummary:
    """
    Agora com enrichment opcional da Florence.
    Metadata indica se Florence foi usada e quais dados foram atualizados.
    """
```

### 3.4 Configuracao

```env
INTELLICARE_FLORENCE_URL=http://florence:8002
INTELLICARE_FLORENCE_TIMEOUT=10
INTELLICARE_FLORENCE_ENABLED=true
INTELLICARE_FLORENCE_CACHE_TTL=900   # 15 min
```

### 3.5 Arquitetura de Arquivos

```
oswaldo/
  integrations/
    __init__.py
    florence.py          # FlorenceClient + FlorenceEnricher
```

## 4. Testes

- FlorenceClient: get_labs, is_available, Florence indisponivel (4 testes)
- FlorenceEnricher: dados mesclados, prioridade Florence, Florence ausente (4 testes)
- ChronicDiseaseEngine com Florence: enriquece antes de calcular (3 testes)
- Cache: dados da Florence em cache (2 testes)
- **Total**: 13+ testes novos

## 5. Criterios de Aceitacao

- [ ] `FlorenceClient` com 4 metodos e graceful degradation
- [ ] `FlorenceEnricher` mescla dados priorizando Florence quando mais recente
- [ ] `ChronicDiseaseEngine` tenta enriquecer antes de calcular
- [ ] Metadata indica se Florence foi usada e quais campos foram atualizados
- [ ] Florence indisponivel = Oswaldo continua funcionando normalmente
- [ ] 98 testes v1.0 continuam passando
- [ ] 13+ testes novos
- [ ] Cobertura >= 83%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `integrations/florence.py`
- **Arquivos modificados**: `engine/core_logic.py`, `config.py`
- **Linhas estimadas**: ~250
- **Testes novos**: ~13
