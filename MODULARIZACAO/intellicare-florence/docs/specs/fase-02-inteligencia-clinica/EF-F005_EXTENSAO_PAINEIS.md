# EF-F005 — Extensao de Paineis e Exames

> Expandir de 27 para 50+ exames laboratoriais, adicionando paineis de cardiologia, coagulacao, marcadores tumorais basicos, urina rotina e suporte a valores gender-specific e age-specific.

## 1. Objetivo

Ampliar a cobertura da Florence para exames clinicamente relevantes que hoje nao sao interpretados:
- Painel cardiologico: troponina I/T, BNP, CK-MB, mioglobina
- Painel de coagulacao: TTPA, fibrinogenio, D-dimero, tempo de protrombina
- Marcadores de ferro: ferritina, ferro serico, transferrina, TIBC
- Vitaminas e minerais: vitamina B12, vitamina D (25-OH), folato, magnesio, zinco, fosforo
- Painel urinario: creatinina urinaria, albumina urinaria, razao albumina/creatinina (ACR)
- Suporte a valores gender-specific (Hb F vs M, creatinina pediatrica, TSH gravidez)

## 2. Justificativa

- Oswaldo calcula ACR (albumina/creatinina) para estadiamento de CKD — Florence precisa interpretar
- Troponina e BNP sao os exames mais solicitados em emergencia — nao suportados
- D-dimero e TTPA sao fundamentais para avaliacao de coagulacao
- Ferritina e essencial para diagnostico de anemia por deficiencia de ferro
- Vitamina D deficiencia e endemica no Brasil — sem interpretacao hoje

## 3. Escopo

### 3.1 Novos Paineis YAML

```yaml
# florence/engine/reference_ranges/data/cardiac_panel.yaml

panel_id: cardiac
panel_name: "Painel Cardiologico"
specialty: "cardiologia"
labs:
  troponin_i:
    name: "Troponina I"
    loinc_code: "10839-9"
    unit: "ng/mL"
    normal_max: 0.04
    critical_high: 0.5         # Infarto confirmado
    panic_high: 2.0
    gender_specific: false
    note: "Elevacao > 0.04 requer ECG e avaliacao cardiologica"

  troponin_t:
    name: "Troponina T (hs-TnT)"
    loinc_code: "6598-7"
    unit: "ng/L"
    normal_max: 14.0           # hsTnT — alta sensibilidade
    critical_high: 52.0
    panic_high: 200.0

  bnp:
    name: "BNP (Peptideo Natriuretico)"
    loinc_code: "30449-7"
    unit: "pg/mL"
    normal_max: 100.0
    high_max: 400.0            # Insuficiencia cardiaca provavel
    critical_high: 900.0       # IC descompensada grave

  nt_probnp:
    name: "NT-proBNP"
    loinc_code: "33762-6"
    unit: "pg/mL"
    # Valores por faixa etaria (age-specific)
    age_ranges:
      - age_min: 0
        age_max: 75
        normal_max: 125.0
        critical_high: 5000.0
      - age_min: 75
        age_max: 999
        normal_max: 450.0     # Idosos tem valores mais altos fisiologicamente
        critical_high: 5000.0

  ck_mb:
    name: "CK-MB"
    loinc_code: "13969-1"
    unit: "U/L"
    normal_max: 25.0
    critical_high: 150.0

  myoglobin:
    name: "Mioglobina"
    loinc_code: "2155-0"
    unit: "mcg/L"
    normal_max: 80.0
    critical_high: 1000.0
```

```yaml
# florence/engine/reference_ranges/data/coagulation_panel.yaml

panel_id: coagulation
panel_name: "Painel de Coagulacao"
specialty: "hematologia"
labs:
  aptt:
    name: "TTPA (Tempo de Tromboplastina Parcial Ativada)"
    loinc_code: "3173-2"
    unit: "s"
    normal_min: 25.0
    normal_max: 35.0
    critical_high: 100.0       # Risco de sangramento grave

  fibrinogen:
    name: "Fibrinogenio"
    loinc_code: "3255-7"
    unit: "mg/dL"
    normal_min: 200.0
    normal_max: 400.0
    critical_low: 100.0        # Risco de coagulacao intravascular disseminada (CIVD)

  d_dimer:
    name: "D-Dimero"
    loinc_code: "71427-9"
    unit: "mcg/mL FEU"
    normal_max: 0.5
    high_max: 2.0              # TEV provavel
    critical_high: 5.0         # CIVD ou TEV extenso

  pt_activity:
    name: "Atividade de Protrombina (%)"
    loinc_code: "5902-2"
    unit: "%"
    normal_min: 70.0
    normal_max: 130.0
    critical_low: 30.0
    # INR ja existe no painel hematologico
```

```yaml
# florence/engine/reference_ranges/data/iron_panel.yaml

panel_id: iron
panel_name: "Painel de Ferro e Anemia"
specialty: "hematologia"
labs:
  ferritin:
    name: "Ferritina"
    loinc_code: "2276-4"
    unit: "ng/mL"
    gender_specific: true
    male:
      normal_min: 30.0
      normal_max: 400.0
      critical_low: 10.0
    female:
      normal_min: 13.0
      normal_max: 150.0
      critical_low: 7.0

  serum_iron:
    name: "Ferro Serico"
    loinc_code: "2498-4"
    unit: "mcg/dL"
    gender_specific: true
    male:
      normal_min: 65.0
      normal_max: 175.0
    female:
      normal_min: 50.0
      normal_max: 170.0

  tibc:
    name: "TIBC (Capacidade de Ligacao de Ferro)"
    loinc_code: "2500-7"
    unit: "mcg/dL"
    normal_min: 250.0
    normal_max: 370.0

  transferrin_saturation:
    name: "Saturacao de Transferrina"
    loinc_code: "2502-3"
    unit: "%"
    normal_min: 20.0
    normal_max: 50.0
    critical_low: 10.0         # Deficiencia de ferro confirmada
    critical_high: 70.0        # Hemocromatose
```

```yaml
# florence/engine/reference_ranges/data/vitamins_panel.yaml

panel_id: vitamins
panel_name: "Vitaminas e Minerais"
specialty: "medicina_geral"
labs:
  vitamin_b12:
    name: "Vitamina B12 (Cobalamina)"
    loinc_code: "2132-9"
    unit: "pg/mL"
    normal_min: 200.0
    normal_max: 900.0
    critical_low: 100.0        # Deficiencia grave — risco neurologico

  vitamin_d:
    name: "Vitamina D (25-OH)"
    loinc_code: "1989-3"
    unit: "ng/mL"
    normal_min: 30.0
    normal_max: 100.0
    low_min: 20.0              # Insuficiencia
    critical_low: 10.0         # Deficiencia grave

  folate:
    name: "Folato Serico"
    loinc_code: "2284-8"
    unit: "ng/mL"
    normal_min: 3.0
    normal_max: 20.0
    critical_low: 2.0

  magnesium:
    name: "Magnesio"
    loinc_code: "19123-9"
    unit: "mg/dL"
    normal_min: 1.7
    normal_max: 2.4
    critical_low: 1.0          # Risco de arritmia
    critical_high: 4.0

  phosphorus:
    name: "Fosforo"
    loinc_code: "2777-1"
    unit: "mg/dL"
    normal_min: 2.5
    normal_max: 4.5
    critical_low: 1.0
    critical_high: 8.0         # Hiperfosfatemia grave (DRC)
```

```yaml
# florence/engine/reference_ranges/data/urine_panel.yaml

panel_id: urine
panel_name: "Painel Urinario"
specialty: "nefrologia"
labs:
  urine_creatinine:
    name: "Creatinina Urinaria"
    loinc_code: "2161-8"
    unit: "mg/dL"
    note: "Valor isolado interpretado em conjunto com ACR"

  urine_albumin:
    name: "Albumina Urinaria"
    loinc_code: "1754-1"
    unit: "mg/L"
    normal_max: 20.0

  albumin_creatinine_ratio:
    name: "Razao Albumina/Creatinina (ACR)"
    loinc_code: "32294-1"
    unit: "mg/g"
    # KDIGO 2024 — classificacao proteinuria DRC
    normal_max: 30.0           # A1: normal a levemente elevado
    high_max: 300.0            # A2: moderadamente elevado
    critical_high: 300.0       # A3: muito elevado (proteinuria nefrotica)
    note: "KDIGO: A1 < 30, A2 30-300, A3 > 300 mg/g"
```

### 3.2 Suporte a Gender-Specific e Age-Specific

```python
# Atualizar ReferenceRangeLoader para suportar gender_specific e age_ranges:

class ReferenceRangeLoader:
    """
    Versao atualizada com suporte a gender e age specific ranges.
    """

    def get_range(
        self,
        lab_id: str,
        gender: Optional[str] = None,      # "male" | "female"
        age_years: Optional[int] = None,   # Para NT-proBNP, creatinina pediatrica, etc.
    ) -> Optional[ReferenceRange]:
        """
        Retorna faixa de referencia ajustada por genero/idade.
        Se gender/age nao fornecidos: usa faixa padrao.
        """
```

### 3.3 Novos Padroes Clinicos (correlations/data/patterns.yaml)

```yaml
# Adicionar ao patterns.yaml existente:

  cardiac_injury:
    id: cardiac_injury
    name: "Lesao Miocardica Aguda"
    significance: critical
    conditions:
      - lab_id: troponin_i
        operator: ">"
        value: 0.04
    recommendation: "Lesao miocardica detectada — ECG e avaliacao cardiologica IMEDIATOS"

  heart_failure:
    id: heart_failure
    name: "Insuficiencia Cardiaca"
    significance: urgent
    conditions:
      - lab_id: bnp
        operator: ">"
        value: 400
    recommendation: "BNP elevado sugestivo de IC descompensada. Avaliar hidratacao, funcao renal e otimizar terapia"

  iron_deficiency:
    id: iron_deficiency
    name: "Deficiencia de Ferro"
    significance: attention
    conditions:
      - lab_id: ferritin
        operator: "<"
        value: 15
    recommendation: "Ferritina baixa — deficiencia de ferro. Investigar sangramento oculto"

  ckd_albuminuria:
    id: ckd_albuminuria
    name: "Albuminuria Significativa (DRC)"
    significance: urgent
    conditions:
      - lab_id: albumin_creatinine_ratio
        operator: ">"
        value: 30
    recommendation: "ACR > 30 indica proteinuria. KDIGO: considerar IECA/BRA e restricao proteica"

  vitamin_d_deficiency:
    id: vitamin_d_deficiency
    name: "Deficiencia de Vitamina D"
    significance: attention
    conditions:
      - lab_id: vitamin_d
        operator: "<"
        value: 20
    recommendation: "Vitamina D insuficiente. Considerar suplementacao 1000-4000 UI/dia"
```

### 3.4 Endpoints Atualizados

```python
# GET /api/v1/labs
# Retorna agora 50+ exames (antes 27)
# Response inclui painel de origem e se gender/age-specific:
{
    "labs": [
        {"id": "troponin_i", "panel": "cardiac", "gender_specific": false, "critical_threshold": 0.04},
        {"id": "ferritin", "panel": "iron", "gender_specific": true},
        {"id": "albumin_creatinine_ratio", "panel": "urine", "loinc": "32294-1"},
        ...
    ],
    "total": 52,
    "panels": ["renal", "metabolic", "hematologic", "hepatic", "thyroid", "inflammatory",
               "cardiac", "coagulation", "iron", "vitamins", "urine"]
}
```

## 4. Testes

- ReferenceRangeLoader gender-specific: ferritina masculino, feminino, sem genero (3 testes)
- ReferenceRangeLoader age-specific: NT-proBNP < 75 anos, > 75 anos (2 testes)
- LabInterpreter com novos exames: troponina elevada (critical), BNP alto, ACR A3 (4 testes)
- CorrelationDetector novos padroes: cardiac_injury, iron_deficiency, ckd_albuminuria (3 testes)
- /api/v1/labs: retorna 50+ exames com todos os paineis (2 testes)
- /api/v1/panels: retorna 11 paineis (1 teste)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] 5 novos paineis YAML: cardiac, coagulation, iron, vitamins, urine
- [ ] 25+ novos exames (total 52+)
- [ ] `ReferenceRangeLoader` suporta gender_specific e age_specific
- [ ] 5 novos padroes clinicos: cardiac_injury, heart_failure, iron_deficiency, ckd_albuminuria, vitamin_d_deficiency
- [ ] Troponina, BNP, D-dimero, ferritina, vitamina D, ACR com valores criticos corretos
- [ ] 198 testes existentes continuam passando (exames existentes intactos)
- [ ] 15+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: 5 paineis YAML (`cardiac_panel.yaml`, `coagulation_panel.yaml`, `iron_panel.yaml`, `vitamins_panel.yaml`, `urine_panel.yaml`)
- **Arquivos modificados**: `florence/engine/reference_ranges/loader.py` (gender/age support), `florence/engine/correlations/data/patterns.yaml` (5 padroes novos)
- **Linhas estimadas**: ~500 (maioria YAML)
- **Testes novos**: ~15
