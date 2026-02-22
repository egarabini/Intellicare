# EF-O008 — Integracao Zilda (Disponibilidade de Servicos por Territorio)

> Integrar o Oswaldo com a Zilda para verificar disponibilidade de servicos (dialise, UTI, ambulatorio renal) no territorio do paciente, enriquecendo recomendacoes de encaminhamento com informacao de acesso real.

## 1. Objetivo

Implementar o `ZildaClient` no Oswaldo para que recomendacoes de encaminhamento sejam baseadas no contexto territorial real:

- Antes: "Encaminhar a nefrologia" (sem saber se existe servico acessivel)
- Depois: "Encaminhar a nefrologia — Hospital Estadual de Campinas (47km) tem 3 nefrologistas SUS. Sessoes de dialise disponiveis em 2 estabelecimentos no municipio."

## 2. Justificativa

- Recomendacao de encaminhamento sem verificar disponibilidade e inutil na pratica
- Oswaldo sabe O QUE o paciente precisa; Zilda sabe ONDE esta disponivel
- Para pacientes com CKD G4-G5: verificar se ha dialise SUS acessivel e urgente
- Reduce re-encaminhamentos desnecessarios quando servico nao esta disponivel na regiao

## 3. Escopo

### 3.1 ZildaClient

```python
class ZildaClient:
    """
    Cliente HTTP para integracao com Zilda (8003).

    Usa o contrato padrao Wanda: POST /api/v1/analyze com capability especifica.
    Graceful degradation: se Zilda indisponivel, recomendacoes sao geradas sem
    informacao territorial (com aviso explicito).

    Cache: 1h por patient_city + service_code (dados territoriais mudam pouco).
    """

    async def check_service_access(
        self,
        municipality_code: str,
        service_codes: list[str],       # ["117"] para dialise, ["100"] para UTI
    ) -> Optional[dict]:
        """
        Verifica acesso a servicos especificos no municipio.

        Chama: POST /api/v1/analyze
        {
            "query": f"Disponibilidade de servicos no municipio {municipality_code}",
            "capability": "cnes_search",
            "context": {
                "requesting_agent": "oswaldo",
                "municipality_code": municipality_code,
                "service_codes": service_codes,
            }
        }

        Retorna:
        {
            "municipality_code": "350950",
            "services": {
                "117": {
                    "name": "Hemodialise",
                    "has_local": True,
                    "sus_available": True,
                    "establishments_count": 2,
                    "nearest": {"name": "Hospital X", "cnes": "1234567"}
                },
                "100": {
                    "name": "UTI",
                    "has_local": False,
                    "nearest": {"name": "Hospital Y", "city": "Campinas", "km": 47}
                }
            }
        }

        Cache: 1h.
        """

    async def get_patient_location(
        self,
        patient_id: str,
        patient_ips: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Extrai codigo IBGE do municipio do paciente a partir do IPS ou dados FHIR.

        Busca em ordem:
        1. IPS.patient.address.city (do IPS passado)
        2. FHIR Patient resource no FHIRDataStore local
        3. Retorna None se nao disponivel
        """

    async def is_available(self) -> bool:
        """
        Verifica disponibilidade da Zilda (GET /api/v1/health).
        """
```

### 3.2 ServicesForDisease

```python
# Mapeamento: doenca → servicos necessarios (codigos CNES)
DISEASE_SERVICE_MAP = {
    "ckd": {
        "G4": ["117", "100"],        # Dialise + UTI para CKD grave
        "G5": ["117", "100"],
        "G3a": [],                    # Apenas ambulatorio renal (nao tem codigo especifico)
        "G3b": ["117"],              # Verificar disponibilidade de dialise futura
    },
    "icc": {
        "HFrEF": ["100"],            # UTI para IC grave
        "AHA_D": ["100"],
    },
    "dpoc": {
        "GOLD3": ["ventilacao_nao_invasiva"],
        "GOLD4": ["100"],
    },
}

def get_services_for_staging(
    disease_id: str,
    stage: str,
) -> list[str]:
    """
    Retorna lista de codigos de servico CNES relevantes para o estadio.
    """
```

### 3.3 TerritorialRecommendationEnricher

```python
class TerritorialRecommendationEnricher:
    """
    Enriquece recomendacoes clinicas com informacao territorial da Zilda.

    Transforma:
    "Encaminhar a Nefrologia — CKD G4 (KDIGO-2024, Evidencia A)"

    Em:
    "Encaminhar a Nefrologia — CKD G4 (KDIGO-2024, Evidencia A)
     [Servicos disponiveis no municipio: 2 estabelecimentos com hemodialise SUS.
      Nefrologista SUS mais proximo: Hospital Estadual de Campinas (47 km)]"
    """

    async def enrich_recommendations(
        self,
        patient_id: str,
        recommendations: list[ClinicalRecommendation],
        municipality_code: Optional[str],
    ) -> list[ClinicalRecommendation]:
        """
        Adiciona contexto territorial as recomendacoes de encaminhamento.

        Apenas para recomendacoes do tipo "encaminhamento".
        Se Zilda indisponivel: retorna recomendacoes sem alteracao.
        """

    async def check_dialysis_access(
        self,
        municipality_code: str,
        ckd_stage: str,
    ) -> dict:
        """
        Verificacao especifica de acesso a dialise para pacientes CKD G4-G5.

        Retorna:
        {
            "has_dialysis_in_municipality": True,
            "sus_dialysis_available": True,
            "dialysis_establishments": 2,
            "nearest_if_absent": None,
            "planning_recommendation": None  # Se ausente: "Iniciar planejamento de acesso..."
        }
        """
```

### 3.4 Configuracao

```env
INTELLICARE_ZILDA_URL=http://zilda:8003
INTELLICARE_ZILDA_TIMEOUT=10
INTELLICARE_ZILDA_ENABLED=true
INTELLICARE_ZILDA_CACHE_TTL=3600   # 1h
```

### 3.5 Modificacoes no RecommendationEngine

```python
# Em generate_recommendations():
# Apos gerar lista de recomendacoes, chama TerritorialRecommendationEnricher
# se tipo == "encaminhamento" e municipality_code disponivel
```

### 3.6 Exemplo de Resposta Enriquecida

```json
{
    "rec_id": "...",
    "category": "encaminhamento",
    "title": "Encaminhar a Nefrologia",
    "description": "CKD G4 — KDIGO recomenda acompanhamento nefrologico para planejamento de TRS",
    "territorial_context": {
        "municipality_code": "350950",
        "municipality_name": "Campinas",
        "dialysis_sus_available": true,
        "dialysis_establishments_local": 2,
        "nearest_nephrology": {
            "name": "AME Campinas",
            "sus": true,
            "distance_km": 3.2
        },
        "zilda_data_date": "2026-02-16"
    },
    "full_description": "CKD G4 — encaminhamento a nefrologia urgente. "
                        "AME Campinas (3.2km) oferece consultas SUS com nefrologista. "
                        "2 centros de hemodialise SUS disponíveis no municipio."
}
```

## 4. Testes

- ZildaClient: check_service_access, Zilda indisponivel (4 testes)
- TerritorialRecommendationEnricher: enriquece encaminhamento, sem municipio (3 testes)
- check_dialysis_access: disponivel, ausente (2 testes)
- DISEASE_SERVICE_MAP: mapeamento correto por estadio (2 testes)
- **Total**: 11+ testes novos

## 5. Criterios de Aceitacao

- [ ] `ZildaClient` com graceful degradation quando Zilda indisponivel
- [ ] Recomendacoes de encaminhamento enriquecidas com informacao territorial
- [ ] Verificacao especifica de dialise para CKD G4-G5
- [ ] `DISEASE_SERVICE_MAP` mapeando doencas e estadios para servicos CNES
- [ ] Informacao territorial no response do /api/v1/analyze (quando disponivel)
- [ ] 98 testes v1.0 continuam passando
- [ ] 11+ testes novos
- [ ] Cobertura >= 83%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `integrations/zilda.py`
- **Arquivos modificados**: `engine/recommendations.py` (enriquecimento), `engine/models.py`, `config.py`
- **Linhas estimadas**: ~250
- **Testes novos**: ~11
