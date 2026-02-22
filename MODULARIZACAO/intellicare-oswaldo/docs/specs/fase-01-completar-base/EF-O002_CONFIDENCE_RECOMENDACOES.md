# EF-O002 — Confidence Score e Recomendacoes Clinicas Estruturadas

> Preencher o confidence score com algoritmo baseado em qualidade dos dados e adicionar recomendacoes clinicas estruturadas baseadas em guidelines brasileiras (PCDT/SBC/SBN/SBD).

## 1. Objetivo

Transformar os alertas textuais atuais em **recomendacoes clinicas estruturadas** com referencia de guideline, nivel de evidencia e contexto do paciente:

- Ao inves de: `"HbA1c acima de 9% — risco muito alto"`
- Entregar: `{"recommendation": "Intensificar terapia hipoglicemiante", "guideline": "PCDT-DM2-2022", "evidence_level": "A", "urgency": "alta", "detail": "HbA1c 9.3% indica controle muito inadequado (meta < 7% para maioria dos adultos). Considerar adicao de insulina basal ou troca de esquema oral."}`

## 2. Justificativa

- Alertas atuais sao textos simples sem contexto clinico acionavel
- Florence e Wanda precisam de recomendacoes estruturadas para gerar orientacoes ao paciente
- Geralda precisa converter recomendacoes em linguagem acessivel para o paciente
- Donabedian avalia se recomendacoes seguem guidelines — precisa da referencia

## 3. Escopo

### 3.1 Modelo de Recomendacao Clinica

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class EvidenceLevel(str, Enum):
    A = "A"    # Meta-analise / ECR multiplos
    B = "B"    # ECR unico / estudo coorte
    C = "C"    # Consenso de especialistas / relatos
    D = "D"    # Opiniao de especialistas


class RecommendationUrgency(str, Enum):
    IMMEDIATE = "imediata"     # < 24h — emergencia
    HIGH = "alta"              # < 7 dias — urgente
    MEDIUM = "media"           # < 30 dias — eletivo urgente
    LOW = "baixa"              # Proximo retorno programado
    ROUTINE = "rotina"         # Sem urgencia


@dataclass
class ClinicalRecommendation:
    """
    Recomendacao clinica estruturada com referencia de guideline.
    """
    rec_id: str                          # UUID
    patient_id: str
    disease_id: str                      # "ckd", "dm2", "has"
    alert_id: Optional[str]             # Alert que gerou esta recomendacao (se aplicavel)

    # Recomendacao
    category: str                        # "medicamento", "exame", "encaminhamento", "estilo_vida", "monitoramento"
    title: str                           # Titulo curto (ex: "Iniciar IECA")
    description: str                     # Descricao completa e contextualizada
    rationale: str                       # Por que esta recomendacao para ESTE paciente

    # Guideline
    guideline_id: str                    # "PCDT-DM2-2022", "KDIGO-2024", "SBC-HAS-2020"
    guideline_url: Optional[str]
    evidence_level: EvidenceLevel
    recommendation_grade: str            # "Forte", "Fraca", "Condicional"

    # Urgencia
    urgency: RecommendationUrgency

    # Dados de suporte
    trigger_values: dict                 # {"hba1c": 9.3, "threshold": 9.0}
    contraindications: list[str]         # Contraindicacoes conhecidas (do perfil)
    monitoring_required: list[str]       # Exames de monitoramento (ex: "K+ em 7 dias")

    # Metadados
    generated_at: str                    # ISO timestamp
    applicable_for_stage: str           # Estadio para o qual se aplica
```

### 3.2 Mapa de Recomendacoes por Guideline

As recomendacoes sao definidas nos **arquivos YAML de perfil de doenca**, nao em codigo:

```yaml
# Adicionar secao "recommendations" em ckd.yaml:
recommendations:
  - id: "ckd_egfr_below_60_ieca"
    trigger:
      observation: "egfr"
      condition: "lt"
      threshold: 60
    category: "medicamento"
    title: "Manter ou iniciar IECA/BRA"
    description: "Para CKD G3+ com proteinuria, IECA/BRA reduzem progressao renal"
    guideline: "KDIGO-2024"
    evidence_level: "A"
    urgency: "media"
    monitoring: ["creatinina", "potassio"]
    contraindications: ["gravidez", "estenose_bilateral_arteria_renal"]

  - id: "ckd_egfr_below_30_nefrologista"
    trigger:
      stage: ["G4", "G5"]
    category: "encaminhamento"
    title: "Encaminhar a Nefrologia"
    description: "CKD G4-G5 requer acompanhamento nefrologico para planejamento de TRS"
    guideline: "KDIGO-2024"
    evidence_level: "A"
    urgency: "alta"

  - id: "ckd_dialise_acesso"
    trigger:
      stage: ["G4"]
      time_to_progression: "<24m"  # Zilda verifica disponibilidade
    category: "encaminhamento"
    title: "Planejamento de acesso para TRS"
    description: "Avaliar criacao de fistula arteriovenosa ou selecao de modalidade de TRS"
    guideline: "KDIGO-2024"
    evidence_level: "A"
    urgency: "alta"
```

### 3.3 RecommendationEngine

```python
class RecommendationEngine:
    """
    Gera recomendacoes clinicas estruturadas a partir do estadiamento
    e dos dados clinicos do paciente.

    Estrategia:
    1. Carrega recomendacoes do perfil YAML da doenca
    2. Para cada recomendacao: avalia se trigger se aplica
    3. Contextualiza: preenche trigger_values com dados reais
    4. Filtra contraindicacoes (dados do perfil do paciente)
    5. Ordena por urgencia (IMMEDIATE > HIGH > MEDIUM > LOW > ROUTINE)
    """

    def __init__(
        self,
        profile_registry: DiseaseProfileRegistry,
    ):
        self._registry = profile_registry

    def generate_recommendations(
        self,
        patient_id: str,
        disease_id: str,
        staging: StagingResult,
        observations: dict,
        patient_context: Optional[dict] = None,  # Alergias, contraindicacoes conhecidas
    ) -> list[ClinicalRecommendation]:
        """
        Gera recomendacoes para um estadiamento especifico.

        Exemplos:
        - CKD G3a com eGFR 47 → ["IECA/BRA", "Restricao proteica", "Avaliar anemia"]
        - DM2 HbA1c 9.3% → ["Intensificar terapia", "Educacao alimentar", "Automonitoramento"]
        - HAS Grau2 → ["Modificar doses", "ECG em 30 dias", "Avaliar dano de orgao-alvo"]
        """

    def _evaluate_trigger(
        self,
        trigger: dict,
        staging: StagingResult,
        observations: dict,
    ) -> bool:
        """
        Avalia se um trigger de recomendacao e verdadeiro.
        Suporta triggers por: observation_value, stage, stage_axis, time_to_progression.
        """
```

### 3.4 Atualizacao nos Modelos

```python
# Adicionar ao OswaldoPatientSummary:
@dataclass
class OswaldoPatientSummary:
    # ... campos existentes ...
    recommendations: list[ClinicalRecommendation] = field(default_factory=list)  # NOVO
    recommendations_by_disease: dict = field(default_factory=dict)               # NOVO
    total_recommendations: int = 0                                                 # NOVO
    urgent_recommendations: int = 0                                                # NOVO
```

### 3.5 Mapa de Guidelines Suportados

```python
SUPPORTED_GUIDELINES = {
    "KDIGO-2024": {
        "name": "KDIGO 2024 Clinical Practice Guideline for CKD",
        "url": "https://kdigo.org/guidelines/ckd-evaluation-and-management/",
        "diseases": ["ckd"],
    },
    "ADA-2025": {
        "name": "ADA Standards of Care in Diabetes 2025",
        "url": "https://diabetesjournals.org/care",
        "diseases": ["dm2"],
    },
    "SBC-HAS-2020": {
        "name": "7a Diretriz Brasileira de Hipertensao Arterial — SBC 2020",
        "url": "https://www.scielo.br/j/abc/a/ZMpJdqzRqZ3GKNqP7H7yCjm",
        "diseases": ["has"],
    },
    "PCDT-HAS-2022": {
        "name": "Protocolo Clinico e Diretrizes Terapeuticas HAS — MS 2022",
        "url": "https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos",
        "diseases": ["has"],
    },
    "PCDT-DM2-2022": {
        "name": "Protocolo Clinico e Diretrizes Terapeuticas DM2 — MS 2022",
        "url": "https://www.gov.br/saude/pt-br/assuntos/protocolos-clinicos",
        "diseases": ["dm2"],
    },
    "SBN-CKD-2023": {
        "name": "Diretrizes SBN para Doenca Renal Cronica",
        "url": "https://www.sbn.org.br",
        "diseases": ["ckd"],
    },
}
```

### 3.6 Modificacoes nos YAMLs de Perfil

Os 3 perfis existentes (`ckd.yaml`, `dm2.yaml`, `has.yaml`) recebem a secao `recommendations` com as recomendacoes guidelines-based. Cada doenca recebe no minimo 5 recomendacoes cobrindo:
- Farmacoterapia
- Encaminhamentos
- Monitoramento laboratorial
- Mudancas de estilo de vida
- Metas terapeuticas

### 3.7 Integracao com /api/v1/analyze

```python
# Resposta do /analyze passa a incluir:
{
    "patient_id": "P001",
    "staging": { ... },
    "alerts": [ ... ],
    "trends": { ... },
    "recommendations": [                     # NOVO
        {
            "rec_id": "...",
            "category": "encaminhamento",
            "title": "Encaminhar a Nefrologia",
            "description": "eGFR 27 mL/min/1.73m² indica CKD G4. ...",
            "guideline_id": "KDIGO-2024",
            "evidence_level": "A",
            "urgency": "alta",
            "trigger_values": {"egfr": 27.0}
        }
    ],
    "urgent_recommendations_count": 1,      # NOVO
}
```

## 4. Testes

- RecommendationEngine: generate por doenca, trigger avaliado (6 testes)
- Guidelines: referencia correta por doenca (3 testes)
- Urgencia: ordenacao por prioridade (2 testes)
- Contraindicacoes: filtro aplicado (2 testes)
- Endpoint /analyze com recomendacoes (2 testes)
- YAMLs: validacao de schema com novo campo (3 testes)
- Confidence score: formula completa (4 testes) — integrado de EF-O001
- **Total**: 22+ testes novos

## 5. Criterios de Aceitacao

- [ ] `RecommendationEngine` com avaliacao de triggers YAML
- [ ] Recomendacoes estruturadas com guideline, evidence_level e urgencia
- [ ] Minimo 5 recomendacoes por doenca nos YAMLs (ckd, dm2, has)
- [ ] Guidelines brasileiros incluidos (PCDT-DM2, PCDT-HAS, SBN, SBC)
- [ ] `/api/v1/analyze` retorna `recommendations` no response
- [ ] Recomendacoes ordenadas por urgencia (IMMEDIATE primeiro)
- [ ] Schema JSON do profile YAML atualizado para incluir `recommendations`
- [ ] 98 testes v1.0 continuam passando
- [ ] 22+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `engine/recommendations.py`, `engine/guidelines.py`
- **Arquivos modificados**: `profiles/models.py` (RecConfig), `profiles/schema.py`, `profiles/diseases/ckd.yaml`, `dm2.yaml`, `has.yaml`, `engine/models.py`, `api/app.py`
- **Linhas estimadas**: ~450
- **Testes novos**: ~22
