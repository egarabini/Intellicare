# EF-F006 — Validacao Clinica e Delta Check

> Ativar validacao de qualidade dos dados de entrada antes da interpretacao, detectando valores fisiologicamente imposssiveis, variacao abrupta suspeita de erro (delta check) e inconsistencias entre exames.

## 1. Objetivo

Garantir que a Florence interpreta apenas dados validos e alertar quando um resultado parece ser erro de coleta ou transcricao — evitando que erros de laboratorio gerem interpretacoes incorretas.

Tipos de validacao:
- **Valores imposssiveis**: creatinina 0.001 ou 50.0 — fisiologicamente impossivel
- **Delta check**: creatinina 1.2 na semana passada, 3.8 hoje — variacao de 217% suspeita de troca de amostra
- **Inconsistencias cruzadas**: HbA1c 4.0% com glicose de jejum 350 mg/dL (matematicamente impossivel)
- **Valores de unidade errada**: creatinina 120 quando deveria ser 1.2 (confusao mg/dL vs umol/L)

## 2. Justificativa

- Regras criadas em `src/florence/services/` (legacy) mas nao ativas no pipeline atual
- Delta check e procedimento padrao em laboratorios (SBPC/ML)
- Sem validacao, erro de laboratorio gera alerta "critico" que nao existe clinicamente
- LGPD e boas praticas: dados incorretos geram recomendacoes incorretas

## 3. Escopo

### 3.1 ClinicalValidator

```python
class ClinicalValidator:
    """
    Valida dados de entrada antes da interpretacao clinica.

    Executado automaticamente no inicio de ClinicalAnalyzer.analyze_labs().
    Resultado: ValidationReport com flags e warnings — a analise prossegue mesmo
    com warnings (nao bloqueia), mas flags sao incluidas no resultado.
    """

    async def validate(
        self,
        lab_results: dict,
        patient_id: Optional[str] = None,
        patient_context: Optional[dict] = None,   # {age, sex, known_conditions}
    ) -> ValidationReport:
        """
        Executa todas as validacoes em paralelo.
        Retorna ValidationReport com lista de issues.
        """

    def check_physiological_limits(
        self,
        lab_id: str,
        value: float,
    ) -> Optional[ValidationIssue]:
        """
        Verifica se o valor e fisiologicamente possivel.

        PHYSIOLOGICAL_LIMITS = {
            "creatinine":       (0.1, 30.0),    # mg/dL — impossivel < 0.1 ou > 30
            "egfr":             (1.0, 150.0),   # mL/min/1.73m²
            "potassium":        (1.5, 9.0),     # mEq/L — > 9 = cadaver
            "sodium":           (100.0, 175.0), # mEq/L
            "glucose_fasting":  (20.0, 1500.0), # mg/dL
            "hba1c":            (3.0, 20.0),    # %
            "hemoglobin":       (2.0, 25.0),    # g/dL
            "tsh":              (0.001, 500.0), # mUI/L
            "inr":              (0.5, 20.0),    # razao
            "troponin_i":       (0.0, 1000.0),  # ng/mL
            "bnp":              (0.0, 35000.0), # pg/mL
            ...
        }
        """

    async def check_delta(
        self,
        lab_id: str,
        current_value: float,
        patient_id: str,
    ) -> Optional[ValidationIssue]:
        """
        Compara com ultima medicao do banco (requer EF-F002).
        Calcula delta% = abs(atual - anterior) / anterior * 100

        DELTA_THRESHOLDS = {
            # lab_id: (delta_pct, periodo_horas) — suspeito se variou mais que X% em Y horas
            "creatinine":    (100, 24),  # dobrar em 24h e possivel mas > 200% suspeito
            "potassium":     (50, 12),   # K varia rapidamente mas > 50% em 12h e suspeito
            "hemoglobin":    (30, 24),   # Hb nao cai 30% em 24h sem hemorragia masssiva
            "tsh":           (500, 24),  # TSH pode variar muito mas > 500% suspeito
            "troponin_i":    (1000, 4),  # Pode subir muito rapido — threshold alto
            "sodium":        (10, 12),   # Variacao > 10 mEq/L em 12h e perigosa E suspeita
            "hba1c":         (30, 720),  # HbA1c muda lentamente — > 30% em 30 dias suspeito
        }

        Se patient_id invalido ou sem historico: retorna None (nao bloqueia).
        """

    def check_cross_consistency(
        self,
        lab_results: dict,
    ) -> list[ValidationIssue]:
        """
        Verifica inconsistencias entre exames.

        CONSISTENCY_RULES = [
            # HbA1c e glicose sao matematicamente relacionados
            ConsistencyRule(
                name="hba1c_glucose_consistency",
                condition=lambda r: "hba1c" in r and "glucose_fasting" in r,
                check=lambda r: not (r["hba1c"] < 5.0 and r["glucose_fasting"] > 200),
                message="HbA1c < 5% incompativel com glicemia > 200 mg/dL — suspeito",
            ),
            # eGFR e creatinina sao inversamente relacionados
            ConsistencyRule(
                name="egfr_creatinine_consistency",
                condition=lambda r: "egfr" in r and "creatinine" in r,
                check=lambda r: not (r["egfr"] > 90 and r["creatinine"] > 2.0),
                message="TFG > 90 e creatinina > 2.0 sao matematicamente incompativeis — verificar calculo",
            ),
            # INR alto com fibrinogenio normal pode ser OK mas merece flag
            ConsistencyRule(
                name="coagulation_consistency",
                condition=lambda r: "inr" in r and "fibrinogen" in r,
                check=lambda r: not (r["inr"] > 3.0 and r["fibrinogen"] < 100),
                message="INR > 3 com fibrinogenio baixo — suspeito de CIVD ou erro",
            ),
        ]
        """

    def check_unit_confusion(
        self,
        lab_id: str,
        value: float,
    ) -> Optional[ValidationIssue]:
        """
        Detecta possiveis confusoes de unidade.

        UNIT_CONFUSION_HINTS = {
            "creatinine": {
                "suspicious_range": (50, 1000),  # Provavelmente em umol/L (multiplicar por 0.0113)
                "hint": "Valor suspeito de estar em umol/L. Para converter: valor_mgdL = valor_umolL * 0.0113",
            },
            "glucose_fasting": {
                "suspicious_range": (0.5, 20),   # Provavelmente em mmol/L (multiplicar por 18)
                "hint": "Valor suspeito de estar em mmol/L. Para converter: mg/dL = mmol/L * 18",
            },
        }
        """
```

### 3.2 Modelos de Validacao

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ValidationSeverity(str, Enum):
    ERROR = "error"        # Valor impossivel — interpretacao nao deve prosseguir
    WARNING = "warning"    # Delta check ou inconsistencia — interpretacao prossegue com flag
    INFO = "info"          # Informativo — nao afeta interpretacao


@dataclass
class ValidationIssue:
    lab_id: str
    issue_type: str             # "physiological_limit" | "delta_check" | "cross_consistency" | "unit_confusion"
    severity: ValidationSeverity
    current_value: float
    message: str                # Mensagem para medico/usuario
    suggestion: Optional[str]   # O que fazer (ex: "Verificar identificacao da amostra")
    previous_value: Optional[float] = None    # Para delta check
    delta_percent: Optional[float] = None


@dataclass
class ValidationReport:
    is_valid: bool                           # True se sem ERRORs
    has_warnings: bool
    issues: list[ValidationIssue]
    validated_at: str
    labs_validated: int

    # Contagem por severidade
    error_count: int
    warning_count: int
    info_count: int
```

### 3.3 Integracao no ClinicalAnalyzer

```python
class ClinicalAnalyzer:
    """
    Versao com validacao na entrada.
    """

    async def analyze_labs(
        self,
        patient_id: str,
        lab_results: dict,
        skip_validation: bool = False,    # Para testes ou integracao interna
        ...
    ) -> ClinicalAnalysis:
        """
        1. Validacao (a menos que skip_validation=True)
        2. Se ha ERRORs: retorna ClinicalAnalysis com is_valid=False e lista de erros
        3. Se ha apenas WARNINGs: prossegue com analise, inclui warnings no resultado
        4. Analise normal (comportamento existente)
        """
```

### 3.4 Endpoint Atualizado

```python
# POST /api/v1/validate (existente)
# ATUALIZADO: agora inclui delta_check e cross_consistency alem dos ranges
# Response:
{
    "is_valid": True,
    "has_warnings": True,
    "issues": [
        {
            "lab_id": "creatinine",
            "issue_type": "delta_check",
            "severity": "warning",
            "current_value": 3.8,
            "previous_value": 1.2,
            "delta_percent": 217.0,
            "message": "Creatinina aumentou 217% em 18h — variacao suspeita de troca de amostra",
            "suggestion": "Verificar identificacao da amostra e repetir coleta se clinicamente inconsistente",
        }
    ],
    "labs_validated": 4,
    "error_count": 0,
    "warning_count": 1,
}

# NOVO endpoint:
# POST /api/v1/validate/delta/{patient_id}
# Body: {lab_results} — valida delta especificamente para um paciente (requer historico)
# Retorna: ValidationReport focado em delta checks
```

### 3.5 Configuracao

```env
FLORENCE_VALIDATION_ENABLED=true
FLORENCE_DELTA_CHECK_ENABLED=true          # Requer EF-F002 (persistencia)
FLORENCE_VALIDATION_BLOCK_ON_ERROR=false   # false = warning mas prossegue; true = rejeita
```

## 4. Testes

- check_physiological_limits: creatinina impossivel (0.001), valor normal, valor extremo mas possivel (3 testes)
- check_delta: variacao > threshold (warning), variacao normal, sem historico (3 testes)
- check_cross_consistency: HbA1c + glicose inconsistentes, eGFR + creatinina inconsistentes (2 testes)
- check_unit_confusion: creatinina em umol/L detectada (2 testes)
- Integracao ClinicalAnalyzer: com erro bloqueia, com warning prossegue (2 testes)
- /api/v1/validate atualizado: inclui delta e cross-consistency (2 testes)
- **Total**: 14+ testes novos

## 5. Criterios de Aceitacao

- [ ] `ClinicalValidator` com 4 tipos de validacao: physiological, delta, consistency, unit
- [ ] Delta check consultando historico do banco (requer EF-F002 ativo)
- [ ] Valores imposssiveis geram ERROR (interpretacao bloqueada com FLORENCE_VALIDATION_BLOCK_ON_ERROR=true)
- [ ] Inconsistencias cruzadas geram WARNING (analise prossegue com flag)
- [ ] Response da analise inclui campo `validation_report` quando ha issues
- [ ] /api/v1/validate atualizado com delta e cross-consistency
- [ ] 198 testes existentes continuam passando
- [ ] 14+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/engine/validator.py`, `florence/engine/validation_models.py`
- **Arquivos modificados**: `florence/engine/clinical_analyzer.py` (integrar validator), `florence/api/app.py` (endpoint /validate atualizado + /validate/delta)
- **Linhas estimadas**: ~400
- **Testes novos**: ~14
