# EF-O004 — Conselheiro de Medicamentos (MedicationAdvisor)

> Implementar o modulo de recomendacoes farmacologicas baseadas em PCDT do Ministerio da Saude, SBN, SBD e SBC, ajustadas para o estadio e funcao renal do paciente.

## 1. Objetivo

Implementar o `MedicationAdvisor` — que foi especificado mas nunca construido (flag `enable_medication_advisor` existe sem implementacao) — gerando recomendacoes farmacologicas contextualizadas:

- "Para CKD G3b com DM2 SUBOPTIMAL, o paciente pode usar metformina?"
- "Qual anti-hipertensivo e preferencial para paciente com IRC + proteinuria?"
- "Dose de insulina precisa de ajuste por funcao renal?"
- "Quais medicamentos do paciente precisam de ajuste ou suspensao dado o eGFR atual?"

## 2. Justificativa

- Flag `enable_medication_advisor` foi criada antecipando esta funcionalidade
- Ajuste de dose por funcao renal e critico na pratica clinica — erro comum e evitavel
- Florence precisa desta informacao para revisao do IPS farmacologico
- PCDT e legislacao publica — a Zilda pode referenciar sem problemas de copyright

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class MedicationStatus(str, Enum):
    RECOMMENDED = "recomendado"
    ACCEPTABLE = "aceitavel"
    USE_WITH_CAUTION = "usar_com_cautela"
    DOSE_ADJUST = "ajuste_de_dose"
    AVOID = "evitar"
    CONTRAINDICATED = "contraindicado"


@dataclass
class MedicationRecommendation:
    """
    Recomendacao para um medicamento especifico.
    """
    drug_name: str                       # Nome generico
    drug_class: str                      # Classe farmacologica
    atc_code: Optional[str]              # Codigo ATC (WHO)
    pcdt_code: Optional[str]             # Codigo PCDT-MS

    status: MedicationStatus
    status_rationale: str                # Por que este status

    # Dose
    standard_dose: Optional[str]         # Dose padrao (sem restricao)
    adjusted_dose: Optional[str]         # Dose ajustada para funcao renal
    dose_adjustment_rule: Optional[str]  # Regra: "reduzir 50% se eGFR 15-29"

    # Restricoes por funcao renal
    egfr_thresholds: Optional[dict]      # {"avoid_below": 30, "adjust_below": 60}
    renal_considerations: str

    # Guideline
    guideline_id: str
    evidence_level: str                  # A/B/C
    monitoring_required: list[str]       # Ex: ["creatinina", "potassio"]

    # Alertas especificos
    drug_interactions: list[str]         # Interacoes importantes
    contraindicated_with: list[str]      # Condicoes que contraindicam


@dataclass
class MedicationAdvisorResult:
    """
    Resultado completo do MedicationAdvisor para um paciente.
    """
    patient_id: str
    current_egfr: Optional[float]
    current_hba1c: Optional[float]
    current_bp: Optional[tuple]

    # Recomendacoes por doenca
    ckd_recommendations: list[MedicationRecommendation]
    dm2_recommendations: list[MedicationRecommendation]
    has_recommendations: list[MedicationRecommendation]

    # Alertas criticos de medicamento
    critical_interactions: list[dict]
    contraindicated_drugs: list[dict]   # Se paciente usa medicamento contraindicado
    dose_adjustments_needed: list[dict]

    # Medicamentos do paciente (do IPS)
    patient_current_medications: list[str]
    medications_to_review: list[str]    # Medicamentos do paciente que precisam revisao
```

### 3.2 MedicationAdvisor

```python
class MedicationAdvisor:
    """
    Conselheiro de medicamentos baseado em estadiamento e funcao renal.

    Estrategia:
    - Nao prescribe: INFORMA sobre guidelines e contraindicacoes
    - Sempre referencia a guideline fonte
    - Ajustes de dose baseados em eGFR (Cockcroft-Gault para dose, CKD-EPI para estadiamento)
    - Interacoes criticas sinalizadas (nao e um sistema completo de interacoes)
    """

    def generate_advice(
        self,
        patient_id: str,
        staging: dict,                   # {ckd: StagingResult, dm2: ..., has: ...}
        observations: dict,              # Valores atuais
        current_medications: list[str],  # Medicamentos em uso (do IPS)
    ) -> MedicationAdvisorResult:
        """
        Gera orientacoes farmacologicas para o perfil do paciente.
        """

    def check_renal_dosing(
        self,
        drug_name: str,
        egfr: float,
    ) -> MedicationRecommendation:
        """
        Verifica se medicamento precisa de ajuste de dose ou esta contraindicado.

        Base de dados: tabela interna baseada em PCDT + Micromedex livres + SBN.
        Cobre: metformina, IECA/BRA, diureticos, antidiabeticos, antibioticos comuns.
        """

    def check_patient_medications(
        self,
        current_medications: list[str],
        egfr: float,
    ) -> list[dict]:
        """
        Verifica lista de medicamentos atuais do paciente contra funcao renal.

        Retorna lista de medicamentos que precisam:
        - Ajuste de dose
        - Suspensao
        - Monitoramento adicional
        """
```

### 3.3 Base de Dados de Medicamentos (Renal Dosing)

```python
# medication_database.py
# Baseado em PCDT-MS + SBN + SBD + SBC

RENAL_DOSING_DATABASE = {
    # Antidiabeticos
    "metformina": {
        "class": "Biguanida",
        "atc": "A10BA02",
        "egfr_rules": [
            {"condition": ">=60", "status": "recomendado", "dose": "padrao"},
            {"condition": "45-59", "status": "usar_com_cautela", "dose": "reduzir 50%"},
            {"condition": "30-44", "status": "evitar", "dose": "contraindicado apos internacao"},
            {"condition": "<30", "status": "contraindicado", "dose": "suspender"},
        ],
        "guideline": "PCDT-DM2-2022",
        "evidence_level": "A",
        "rationale": "Risco de acidose lactica em insuficiencia renal",
        "monitoring": ["creatinina_trimestral"],
    },
    "empagliflozina": {
        "class": "SGLT-2",
        "atc": "A10BK03",
        "egfr_rules": [
            {"condition": ">=45", "status": "recomendado", "dose": "10mg/dia"},
            {"condition": "20-44", "status": "dose_ajuste",
             "dose": "Beneficio renal documentado - usar conforme CREDENCE/DAPA-CKD"},
            {"condition": "<20", "status": "evitar", "dose": "eficacia reduzida"},
        ],
        "guideline": "KDIGO-2024",
        "evidence_level": "A",
        "rationale": "SGLT-2 com beneficio cardiovascular e renal documentado na CKD",
        "monitoring": ["egfr_mensal_inicio", "itru"],
        "special_note": "Continuar mesmo com progressao renal pelo beneficio em mortalidade CV",
    },
    # IECA/BRA
    "enalapril": {
        "class": "IECA",
        "atc": "C09AA02",
        "egfr_rules": [
            {"condition": ">=30", "status": "recomendado",
             "dose": "inicio 5mg/dia, titular", "note": "Protetor renal com proteinuria"},
            {"condition": "15-29", "status": "usar_com_cautela",
             "dose": "inicio 2.5mg/dia", "note": "Monitorar K+ e creatinina"},
            {"condition": "<15", "status": "usar_com_cautela",
             "dose": "avaliar individualmente"},
        ],
        "guideline": "KDIGO-2024",
        "evidence_level": "A",
        "monitoring": ["potassio_7dias_inicio", "creatinina_7dias_inicio"],
        "contraindicated_with": ["estenose_bilateral_arteria_renal", "gravidez"],
    },
    # Diureticos
    "espironolactona": {
        "class": "Diuretico poupador de potassio",
        "atc": "C03DA01",
        "egfr_rules": [
            {"condition": ">=45", "status": "aceitavel", "dose": "25-50mg/dia"},
            {"condition": "30-44", "status": "usar_com_cautela",
             "dose": "baixas doses, monitorar K+"},
            {"condition": "<30", "status": "evitar",
             "dose": "risco de hiperpotassemia grave"},
        ],
        "guideline": "SBC-HAS-2020",
        "evidence_level": "B",
        "monitoring": ["potassio_semanal_inicio", "creatinina"],
    },
    # Analgésicos (nefrotoxicos)
    "ibuprofeno": {
        "class": "AINE",
        "atc": "M01AE01",
        "egfr_rules": [
            {"condition": ">=60", "status": "usar_com_cautela",
             "dose": "evitar uso cronico"},
            {"condition": "<60", "status": "contraindicado",
             "dose": "AINEs contraindicados em CKD G3+"},
        ],
        "guideline": "KDIGO-2024",
        "evidence_level": "A",
        "rationale": "AINEs causam vasoconstricao renal e progressao de CKD",
    },
}
```

### 3.4 Configuracao

```env
INTELLICARE_OSWALDO_MEDICATION_ADVISOR_ENABLED=true
INTELLICARE_OSWALDO_MEDICATION_DB_PATH=oswaldo/data/renal_dosing.yaml
```

### 3.5 Integracao com /api/v1/analyze

```python
# Adicionar ao OswaldoAnalysis e resposta do /analyze:
{
    "medication_advice": {
        "critical_alerts": [
            {
                "drug": "metformina",
                "current_egfr": 27.0,
                "status": "contraindicado",
                "action": "Suspender imediatamente — eGFR < 30",
                "guideline": "PCDT-DM2-2022"
            }
        ],
        "dose_adjustments": [
            {
                "drug": "enalapril",
                "current_egfr": 27.0,
                "adjustment": "Reduzir para 2.5mg/dia — monitorar K+ em 7 dias"
            }
        ],
        "recommendations": [
            {
                "drug": "empagliflozina",
                "recommendation": "Considerar SGLT-2 para beneficio renal/CV documentado",
                "guideline": "KDIGO-2024",
                "evidence": "A"
            }
        ],
    }
}
```

### 3.6 Arquitetura de Arquivos

```
oswaldo/
  medication/
    __init__.py
    advisor.py             # MedicationAdvisor
    database.py            # RENAL_DOSING_DATABASE
    models.py              # MedicationRecommendation, MedicationAdvisorResult
  data/
    renal_dosing.yaml      # Base de dados de medicamentos (YAML editavel)
```

## 4. Testes

- MedicationAdvisor: metformina por faixa eGFR, IECA, SGLT-2 (6 testes)
- check_patient_medications: lista com drogas problematicas (3 testes)
- Base de dados: 20+ drogas validadas (2 testes)
- Integracao com /analyze (2 testes)
- YAML renal_dosing: carregamento e validacao (2 testes)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] `MedicationAdvisor` com 3 metodos principais
- [ ] Base de dados com 20+ medicamentos comuns em doencas cronicas
- [ ] Regras de ajuste renal por faixa de eGFR para cada medicamento
- [ ] Flag `enable_medication_advisor` ativa o modulo
- [ ] Alertas criticos para medicamentos contraindicados em uso
- [ ] Recomendacao de SGLT-2 para CKD G3-G4 (guideline KDIGO-2024)
- [ ] Monitoramento especificado para cada droga
- [ ] 98 testes v1.0 continuam passando
- [ ] 15+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `medication/advisor.py`, `medication/database.py`, `medication/models.py`, `data/renal_dosing.yaml`
- **Arquivos modificados**: `engine/core_logic.py`, `config.py`, `api/app.py`
- **Linhas estimadas**: ~500
- **Testes novos**: ~15

## 7. Nota de Responsabilidade

O MedicationAdvisor **nao e um sistema de prescricao**. Ele:
- Referencia guidelines publicas (PCDT, KDIGO, SBN)
- Sinaliza contraindicacoes e ajustes conhecidos
- Recomenda monitoramento
- **NAO substitui avaliacao clinica do medico assistente**

Toda resposta deve incluir o disclaimer:
> "Recomendacoes baseadas em guidelines publicas. A decisao final e responsabilidade do medico assistente."
