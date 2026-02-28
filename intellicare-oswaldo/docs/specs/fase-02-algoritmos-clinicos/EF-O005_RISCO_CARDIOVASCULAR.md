# EF-O005 — Calculadora de Risco Cardiovascular

> Implementar o modulo de risco cardiovascular usando Escore de Framingham (Brasil) e CKD-EPI para pacientes com IRC, com estratificacao de risco e metas terapeuticas derivadas.

## 1. Objetivo

Implementar a `CVRiskCalculator` — que foi especificada mas nunca construida (flag `enable_cv_risk_calculator` existe sem implementacao) — calculando:

- Risco cardiovascular em 10 anos (Escore de Framingham validado para populacao brasileira)
- Risco especifico para CKD (IRC aumenta risco CV independente de Framingham)
- Estratificacao de risco: Baixo / Intermediario / Alto / Muito Alto
- Metas terapeuticas derivadas do risco (meta LDL por categoria)
- Impacto de cada fator de risco modificavel

## 2. Justificativa

- Doenca cardiovascular e a principal causa de morte em pacientes com IRC e DM2
- Framingham e o padrao-ouro validado para populacao brasileira (SBC 2020)
- Metas de LDL, PA e HbA1c dependem da categoria de risco
- Donabedian avalia calculo e documentacao de risco CV como indicador de qualidade
- Wanda precisa desta informacao para priorizar urgencia de encaminhamentos

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CVRiskCategory(str, Enum):
    LOW = "baixo"                    # < 5% em 10 anos
    INTERMEDIATE = "intermediario"   # 5-19% em 10 anos
    HIGH = "alto"                    # 20-29% em 10 anos
    VERY_HIGH = "muito_alto"         # >= 30% em 10 anos
    EXTREME = "extremo"              # CKD G4-G5 / DM2 com complicacoes / AVC previo


@dataclass
class CVRiskFactors:
    """
    Fatores de risco coletados para calculo de Framingham.
    """
    # Obrigatorios
    age: int
    sex: str                         # "M" / "F"
    systolic_bp: float
    is_on_hypertension_treatment: bool
    total_cholesterol: Optional[float]  # mg/dL
    hdl_cholesterol: Optional[float]   # mg/dL

    # Importantes
    smoking: bool = False
    diabetes: bool = False

    # CKD-especifico
    egfr: Optional[float] = None
    has_ckd: bool = False
    ckd_stage: Optional[str] = None    # "G3a", "G4", etc.
    has_proteinuria: bool = False       # ACR > 30

    # Historico clinico (elevam automaticamente para muito alto)
    previous_cardiovascular_event: bool = False  # IAM, AVC, revascularizacao
    heart_failure: bool = False
    peripheral_arterial_disease: bool = False


@dataclass
class CVRiskResult:
    """
    Resultado do calculo de risco cardiovascular.
    """
    patient_id: str

    # Fatores usados
    risk_factors: CVRiskFactors
    data_completeness: float           # % de fatores disponiveis

    # Resultado Framingham
    framingham_score_pct: Optional[float]  # % em 10 anos
    framingham_category: Optional[CVRiskCategory]

    # Ajuste CKD
    ckd_risk_adjustment: Optional[str]  # "CKD G3+ dobra risco CV"
    final_category: CVRiskCategory     # Categoria final (ajustada por CKD/comorbidades)
    final_score_pct: Optional[float]

    # Metas terapeuticas derivadas
    ldl_target_mg_dl: float           # Meta de LDL baseada no risco
    bp_target_mmhg: str               # Meta PA (ex: "< 130/80 mmHg")
    hba1c_target_pct: Optional[float] # Meta HbA1c (se DM)

    # Fatores modificaveis
    modifiable_risk_factors: list[str]  # ["tabagismo", "hbp_nao_controlada"]
    risk_reduction_potential: str       # "alto" / "medio" / "baixo"

    # Recomendacoes derivadas
    statin_recommendation: str         # "Alta intensidade", "Moderada", "Nao indicada"
    aspirin_recommendation: str        # "Indicada" / "Nao indicada" / "Discutir"

    # Calculo
    calculation_method: str           # "framingham_brasil_2020" + "kdigo_ckd_adjustment"
    guideline_references: list[str]
    calculated_at: str
```

### 3.2 FraminghamBrazilCalculator

```python
class FraminghamBrazilCalculator:
    """
    Escore de Framingham validado para a populacao brasileira.

    Base: Diretriz SBC de Prevencao Cardiovascular 2020
    (Andrade et al., Arq Bras Cardiol 2018 — tabela de pontuacao)

    Faixas de risco:
    - Baixo: < 5%
    - Intermediario: 5-19%
    - Alto: 20-29%
    - Muito Alto: >= 30%

    Nota: CKD G3+ automaticamente elevada para categoria superior.
    """

    # Tabela de pontuacao por sexo (masculino)
    # [faixa etaria, colesterol total, hdl, pa sistolica, pa tratada, tabagismo, diabetes]
    SCORING_TABLE_MALE = {
        "age": {
            (30, 34): 0,
            (35, 39): 2,
            (40, 44): 5,
            (45, 49): 7,
            (50, 54): 8,
            (55, 59): 10,
            (60, 64): 11,
            (65, 69): 12,
            (70, 74): 13,
            (75, None): 14,
        },
        # ... tabela completa do Framingham
    }

    def calculate(
        self,
        risk_factors: CVRiskFactors,
    ) -> tuple[float, CVRiskCategory]:
        """
        Calcula Escore de Framingham (versao brasileira).

        Retorna: (score_pct_10anos, categoria_risco)
        """

    def _apply_ckd_adjustment(
        self,
        base_category: CVRiskCategory,
        ckd_stage: str,
        has_proteinuria: bool,
    ) -> CVRiskCategory:
        """
        Ajusta categoria de risco pela presenca e estadio de CKD.

        Regras (baseadas em KDIGO 2020 Cardiovascular Risk):
        - CKD G3a sem proteinuria: elevada um nível
        - CKD G3b ou proteinuria A2: elevada um nivel
        - CKD G4: automaticamente Muito Alto
        - CKD G5: automaticamente Extremo

        Fonte: KDIGO 2020 Clinical Practice Guideline on Diabetes
                Management in Chronic Kidney Disease
        """

    def get_ldl_target(
        self,
        category: CVRiskCategory,
    ) -> float:
        """
        Meta de LDL por categoria de risco (SBC 2017 / ESC 2019).

        - Baixo: < 130 mg/dL
        - Intermediario: < 100 mg/dL
        - Alto: < 70 mg/dL
        - Muito Alto: < 50 mg/dL
        - Extremo: < 50 mg/dL (com estatina maxima + ezetimibe)
        """

    def get_statin_recommendation(
        self,
        category: CVRiskCategory,
        current_ldl: Optional[float],
    ) -> str:
        """
        Indicacao e intensidade de estatina.

        - Baixo: apenas se LDL > 190
        - Intermediario: estatina moderada intensidade
        - Alto: estatina alta intensidade
        - Muito Alto / Extremo: estatina alta intensidade + ezetimibe se necessario
        """
```

### 3.3 CVRiskCalculator (facade)

```python
class CVRiskCalculator:
    """
    Facade para calculo completo de risco cardiovascular.
    Usa FraminghamBrazilCalculator + ajustes clinicos.
    """

    def calculate(
        self,
        patient_id: str,
        observations: dict,           # Dados do FHIR
        staging: dict,                # Estadiamento atual
        patient_context: Optional[dict] = None,  # Historico clinico do IPS
    ) -> CVRiskResult:
        """
        Calculo completo de risco CV para o paciente.

        1. Extrai fatores de risco das observacoes FHIR
        2. Calcula Framingham Brasil
        3. Aplica ajuste CKD (se aplicavel)
        4. Verifica historia de evento CV (elevacao automatica)
        5. Gera metas terapeuticas e recomendacoes

        Cache: 4h (muda com novos exames).
        """

    def calculate_modifiable_impact(
        self,
        risk_factors: CVRiskFactors,
    ) -> list[dict]:
        """
        Calcula o impacto de cada fator de risco modificavel.

        Retorna lista ordenada pelo potencial de reducao:
        [
            {"factor": "tabagismo", "impact_pct": 15, "action": "Cessacao tabagica"},
            {"factor": "ldl_elevado", "impact_pct": 8, "action": "Estatina"},
            {"factor": "has_nao_controlada", "impact_pct": 6, "action": "Anti-hipertensivo"},
        ]
        """
```

### 3.4 Integracao com /api/v1/analyze

```python
# Resposta do /analyze inclui (quando enable_cv_risk_calculator=True):
{
    "cv_risk": {
        "framingham_score": 18.3,       # % em 10 anos
        "category": "intermediario",
        "final_category": "alto",        # Ajustado por CKD G3b
        "adjustment_reason": "CKD G3b eleva risco para categoria 'alto'",
        "ldl_target": 70,               # mg/dL
        "statin_recommendation": "Estatina alta intensidade (Rosuvastatina 20-40mg)",
        "bp_target": "< 130/80 mmHg",
        "modifiable_factors": [
            {"factor": "tabagismo", "impact": "alto", "action": "Cessacao tabagica"},
        ],
        "guideline": "SBC-Prevencao-CV-2020",
    }
}
```

### 3.5 Endpoint Novo

```python
# GET /api/v1/cv-risk/{patient_id}
# Retorna: CVRiskResult completo

# GET /api/v1/cv-risk/{patient_id}/factors
# Retorna: CVRiskFactors disponiveis + ausentes (com impacto na completude)
```

### 3.6 LangChain Tool adicional no OswaldoAgent

```python
Tool(
    name="calculate_cv_risk",
    description="Calcular risco cardiovascular em 10 anos (Framingham Brasil). "
                "Retorna categoria de risco, meta de LDL e recomendacao de estatina. "
                "Use para perguntas sobre risco cardiaco, prevencao secundaria, "
                "meta de colesterol ou indicacao de estatina.",
    func=self._tool_calculate_cv_risk,
),
```

### 3.7 Configuracao

```env
INTELLICARE_OSWALDO_CV_RISK_ENABLED=true
INTELLICARE_OSWALDO_CV_RISK_CACHE_TTL=14400  # 4h
```

## 4. Testes

- FraminghamBrazilCalculator: homem 45a tabagista HAS, mulher 60a DM (4 testes)
- Ajuste CKD: G3b eleva categoria, G4 muito alto, G5 extremo (3 testes)
- Metas LDL por categoria (4 testes)
- calculate_modifiable_impact: fatores ordenados corretamente (2 testes)
- Endpoints: cv-risk, factors (3 testes)
- LangChain Tool (2 testes)
- **Total**: 18+ testes novos

## 5. Criterios de Aceitacao

- [ ] Tabela Framingham Brasil completa (masculino + feminino)
- [ ] Ajuste automatico por CKD (G3b → alto, G4 → muito alto, G5 → extremo)
- [ ] Elevacao automatica para "muito alto" se evento CV previo
- [ ] Metas LDL derivadas da categoria de risco
- [ ] Recomendacao de estatina com intensidade e nome comercial
- [ ] Flag `enable_cv_risk_calculator` ativa o modulo
- [ ] 1 nova LangChain Tool no OswaldoAgent
- [ ] 98 testes v1.0 continuam passando
- [ ] 18+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `engine/cv_risk.py`, `engine/framingham.py`
- **Arquivos modificados**: `engine/models.py`, `api/app.py` (2 endpoints), `config.py`, `subagent/tools.py`
- **Linhas estimadas**: ~450
- **Testes novos**: ~18
