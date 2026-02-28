# EF-O006 — Extensao de Doencas Cronicas (DPOC, ICC, Dislipidemia)

> Adicionar 3 novas doencas cronicas ao motor Oswaldo via YAML, aproveitando a arquitetura extensivel ja existente: DPOC (GOLD), ICC (NYHA/AHA) e Dislipidemia (SBC).

## 1. Objetivo

Expandir o motor Oswaldo de 3 para 6 doencas cronicas, sem modificar codigo Python — apenas criando novos arquivos YAML de perfil e validando que a factory e o engine processam corretamente:

- **DPOC**: Classificacao GOLD 2023 (A/B/E por espirometria e sintomas)
- **ICC**: Classificacao NYHA I-IV + estadiamento AHA A-D
- **Dislipidemia**: Estratificacao LDL/HDL/Triglicerideos por risco CV (SBC 2017)

## 2. Justificativa

- A arquitetura YAML do Oswaldo foi projetada exatamente para esta extensibilidade
- `DiseaseProfileRegistry` carrega qualquer `.yaml` do diretorio sem mudanca de codigo
- `StagingStrategyFactory` suporta `generic_range` para novas doencas
- DPOC, ICC e Dislipidemia sao comuns em pacientes com CKD/DM2/HAS (comorbidades)
- Oswaldo so suporta monitoramento de doencas ja diagnosticadas — estas sao frequentes

## 3. Escopo

### 3.1 DPOC — Perfil YAML (GOLD 2023)

```yaml
# oswaldo/profiles/diseases/dpoc.yaml
id: "dpoc"
name: "Doenca Pulmonar Obstrutiva Cronica"
version: "1.0.0"
guideline: "GOLD 2023"
guideline_url: "https://goldcopd.org"
snomed_code: "13645005"

observations:
  - id: "fev1_percent"
    name: "VEF1 (% previsto)"
    loinc_code: "19926-5"
    unit: "%"
    required: true
    reference_ranges:
      normal: {min: 80.0}
      borderline: {min: 50.0, max: 79.9}
      critical: {max: 49.9}

  - id: "fev1_fvc_ratio"
    name: "Relacao VEF1/CVF"
    loinc_code: "19927-3"
    unit: "ratio"
    required: true  # Obrigatorio para confirmacao obstrutiva

  - id: "cat_score"
    name: "CAT Score (sintomas)"
    loinc_code: "89744-0"
    unit: "points"
    reference_ranges:
      low: {max: 9}
      medium: {min: 10, max: 19}
      high: {min: 20}

  - id: "exacerbations_last_year"
    name: "Exacerbacoes moderadas/graves no ultimo ano"
    unit: "count"
    reference_ranges:
      low_risk: {max: 1}
      high_risk: {min: 2}

staging:
  strategy: "gold_2023"               # Estrategia especifica necessaria
  description: "Classificacao GOLD ABCD → ABE (2023)"
  axes:
    - id: "obstruction"
      name: "Grau de obstrucao"
      observation: "fev1_percent"
      stages:
        - {name: "GOLD1", label: "Leve", min: 80.0, severity: info}
        - {name: "GOLD2", label: "Moderado", min: 50.0, max: 79.9, severity: warning}
        - {name: "GOLD3", label: "Grave", min: 30.0, max: 49.9, severity: warning}
        - {name: "GOLD4", label: "Muito Grave", max: 29.9, severity: critical}

  # Grupos ABE (GOLD 2023 - substitui ABCD)
  risk_groups:
    A:
      description: "Baixo risco, poucos sintomas"
      criteria: "exacerbacoes <= 1 E cat < 10"
      severity: info
    B:
      description: "Baixo risco, mais sintomas"
      criteria: "exacerbacoes <= 1 E cat >= 10"
      severity: warning
    E:
      description: "Alto risco de exacerbacoes"
      criteria: "exacerbacoes >= 2"
      severity: critical

alerts:
  - id: "dpoc_severe_obstruction"
    type: threshold
    observation: "fev1_percent"
    condition: lt
    threshold: 30.0
    severity: critical
    message: "VEF1 < 30% — DPOC muito grave. Avaliar suporte ventilatório."

  - id: "dpoc_frequent_exacerbations"
    type: threshold
    observation: "exacerbations_last_year"
    condition: gte
    threshold: 2
    severity: warning
    message: "2+ exacerbações no último ano — Grupo E. Revisar tratamento de manutencao."

recommendations:
  - id: "dpoc_group_e_lama_laba"
    trigger:
      risk_group: "E"
    category: "medicamento"
    title: "LAMA + LABA (broncodilatadores duplos)"
    description: "Grupo E: LAMA + LABA recomendados como primeiro passo"
    guideline: "GOLD-2023"
    evidence_level: "A"
    urgency: "media"
    monitoring: ["spirometria_anual", "cat_score_3meses"]
```

### 3.2 ICC — Perfil YAML (NYHA + AHA)

```yaml
# oswaldo/profiles/diseases/icc.yaml
id: "icc"
name: "Insuficiencia Cardiaca Cronica"
version: "1.0.0"
guideline: "AHA/ACC 2022 + SBC 2021"
snomed_code: "84114007"

observations:
  - id: "feve_percent"
    name: "Fracao de Ejecao VE (%)"
    loinc_code: "10230-1"
    unit: "%"
    required: true
    reference_ranges:
      preserved: {min: 50.0}      # HFpEF
      mildly_reduced: {min: 40.0, max: 49.9}  # HFmrEF
      reduced: {max: 39.9}        # HFrEF

  - id: "nt_pro_bnp"
    name: "NT-proBNP"
    loinc_code: "33762-6"
    unit: "pg/mL"
    reference_ranges:
      normal: {max: 125}
      elevated: {min: 125, max: 900}
      markedly_elevated: {min: 900}

  - id: "nyha_class"
    name: "Classe Funcional NYHA"
    unit: "class"
    reference_ranges:
      i: {value: 1}
      ii: {value: 2}
      iii: {value: 3}
      iv: {value: 4}

  - id: "6mwt_meters"
    name: "Teste de Caminhada 6 minutos (metros)"
    loinc_code: "59516-4"
    unit: "m"
    reference_ranges:
      preserved: {min: 450}
      reduced: {min: 300, max: 449}
      critically_reduced: {max: 299}

staging:
  strategy: "generic_range"
  description: "Estadiamento AHA A-D + Funcional NYHA I-IV"
  axes:
    - id: "aha_stage"
      name: "Estadio AHA"
      stages:
        - {name: "AHA_A", label: "Risco de ICC (sem doenca)", severity: info}
        - {name: "AHA_B", label: "Doenca estrutural sem sintomas", severity: info}
        - {name: "AHA_C", label: "ICC sintomatica", severity: warning}
        - {name: "AHA_D", label: "ICC refrataria/avancada", severity: critical}

    - id: "feve_class"
      name: "Classe por FE"
      observation: "feve_percent"
      stages:
        - {name: "HFpEF", label: "FE preservada (>= 50%)", min: 50.0, severity: info}
        - {name: "HFmrEF", label: "FE levemente reduzida (40-49%)", min: 40.0, max: 49.9, severity: warning}
        - {name: "HFrEF", label: "FE reduzida (< 40%)", max: 39.9, severity: critical}

alerts:
  - id: "icc_hfrfe"
    type: threshold
    observation: "feve_percent"
    condition: lt
    threshold: 40.0
    severity: critical
    message: "FE < 40% (HFrEF) — Indicacao de IECA/BRA + BB + ARM. Encaminhamento a Cardiologia."

  - id: "icc_bnp_critical"
    type: threshold
    observation: "nt_pro_bnp"
    condition: gt
    threshold: 900
    severity: critical
    message: "NT-proBNP > 900 pg/mL — ICC descompensada. Avaliar internacao."

recommendations:
  - id: "icc_hfref_ieca_bb"
    trigger:
      stage_axis: {feve_class: "HFrEF"}
    category: "medicamento"
    title: "IECA/BRA + Beta-bloqueador + Diuretico"
    description: "HFrEF: cornerstone terapeutico — IECA (ou ARNI), BB e ARM"
    guideline: "AHA-ACC-2022"
    evidence_level: "A"
    urgency: "alta"
```

### 3.3 Dislipidemia — Perfil YAML (SBC 2017)

```yaml
# oswaldo/profiles/diseases/dislipidemia.yaml
id: "dislipidemia"
name: "Dislipidemia"
version: "1.0.0"
guideline: "V Diretriz Brasileira de Dislipidemias - SBC 2017"
snomed_code: "55822004"

observations:
  - id: "ldl_cholesterol"
    name: "LDL Colesterol"
    loinc_code: "2089-1"
    unit: "mg/dL"
    required: true

  - id: "hdl_cholesterol"
    name: "HDL Colesterol"
    loinc_code: "2085-9"
    unit: "mg/dL"

  - id: "triglycerides"
    name: "Triglicerideos"
    loinc_code: "2571-8"
    unit: "mg/dL"

  - id: "non_hdl_cholesterol"
    name: "Colesterol nao-HDL"
    unit: "mg/dL"                # Calculado: CT - HDL

staging:
  strategy: "generic_range"
  description: "Classificacao por valores de LDL/HDL/TG (SBC 2017)"
  axes:
    - id: "ldl_class"
      name: "Classificacao LDL"
      observation: "ldl_cholesterol"
      stages:
        - {name: "OPTIMAL", label: "Otimo (< 100)", max: 99.9, severity: info}
        - {name: "DESIRABLE", label: "Desejavel (100-129)", min: 100.0, max: 129.9, severity: info}
        - {name: "BORDERLINE", label: "Limítrofe (130-159)", min: 130.0, max: 159.9, severity: warning}
        - {name: "HIGH", label: "Alto (160-189)", min: 160.0, max: 189.9, severity: warning}
        - {name: "VERY_HIGH", label: "Muito Alto (>= 190)", min: 190.0, severity: critical}

    - id: "hdl_class"
      observation: "hdl_cholesterol"
      stages:
        - {name: "LOW", label: "Baixo (< 40M / < 50F)", max: 39.9, severity: warning}
        - {name: "DESIRABLE", label: "Desejavel (>= 60)", min: 60.0, severity: info}

    - id: "tg_class"
      observation: "triglycerides"
      stages:
        - {name: "DESIRABLE", label: "Desejavel (< 150)", max: 149.9, severity: info}
        - {name: "BORDERLINE", label: "Limítrofe (150-199)", min: 150.0, max: 199.9, severity: info}
        - {name: "HIGH", label: "Alto (200-499)", min: 200.0, max: 499.9, severity: warning}
        - {name: "VERY_HIGH", label: "Muito Alto (>= 500)", min: 500.0, severity: critical}

alerts:
  - id: "ldl_very_high"
    type: threshold
    observation: "ldl_cholesterol"
    condition: gte
    threshold: 190.0
    severity: critical
    message: "LDL >= 190 mg/dL — investigar hipercolesterolemia familiar. Estatina alta intensidade."

  - id: "tg_very_high"
    type: threshold
    observation: "triglycerides"
    condition: gte
    threshold: 500.0
    severity: critical
    message: "TG >= 500 mg/dL — risco de pancreatite. Fibratos emergencialmente."
```

### 3.4 GOLD Staging Strategy (Python)

Para DPOC, e necessario uma `GoldStagingStrategy` porque o algoritmo GOLD 2023 combina obstrutividade (VEF1%) + grupos de risco (ABE) de forma nao coberta pela `GenericRangeStagingStrategy`:

```python
# oswaldo/engine/staging/gold_staging.py
class GoldStagingStrategy(StagingStrategy):
    """
    Estrategia de estadiamento GOLD 2023 para DPOC.

    Combina:
    - Grau de obstrucao GOLD 1-4 (por VEF1%)
    - Grupo de risco ABE (por CAT score + exacerbacoes)

    Resultado: "GOLD3_E" significa obstrucao grave + grupo alto risco
    """

    def calculate_stage(
        self,
        observations: dict,
    ) -> StagingResult:
        """
        Calcula estadio GOLD 2023.
        Requer fev1_percent (obrigatorio) e cat_score + exacerbacoes (para grupo ABE).
        """
```

### 3.5 Modificacoes na StagingStrategyFactory

```python
# Registrar GoldStagingStrategy:
factory.register_strategy("gold_2023", GoldStagingStrategy)
```

### 3.6 /api/v1/diseases (resposta atualizada)

```json
[
    {"id": "ckd", "name": "Doenca Renal Cronica", "version": "1.0.0", "guideline": "KDIGO 2024"},
    {"id": "dm2", "name": "Diabetes Mellitus Tipo 2", "version": "1.0.0", "guideline": "ADA 2025"},
    {"id": "has", "name": "Hipertensao Arterial", "version": "1.0.0", "guideline": "ESC/ESH 2018"},
    {"id": "dpoc", "name": "DPOC", "version": "1.0.0", "guideline": "GOLD 2023"},
    {"id": "icc", "name": "Insuficiencia Cardiaca", "version": "1.0.0", "guideline": "AHA/ACC 2022"},
    {"id": "dislipidemia", "name": "Dislipidemia", "version": "1.0.0", "guideline": "SBC 2017"}
]
```

## 4. Testes

- dpoc.yaml: carregamento, GOLD 1-4, grupos ABE (4 testes)
- GoldStagingStrategy: GOLD1_B, GOLD3_E (3 testes)
- icc.yaml: HFrEF, HFpEF, alertas (3 testes)
- dislipidemia.yaml: LDL alto, TG muito alto (3 testes)
- registry.list_ids() retorna 6 doencas (1 teste)
- **Total**: 14+ testes novos

## 5. Criterios de Aceitacao

- [ ] 3 novos perfis YAML (dpoc, icc, dislipidemia) carregados pelo registry
- [ ] `GoldStagingStrategy` implementada e registrada
- [ ] DPOC: grupos ABE calculados corretamente
- [ ] ICC: HFrEF (<40%), HFmrEF (40-49%), HFpEF (>=50%) classificados
- [ ] Dislipidemia: LDL, HDL e TG classificados independentemente
- [ ] Alertas criticos por doenca (LDL>=190, TG>=500, FE<40%)
- [ ] /api/v1/diseases retorna 6 doencas
- [ ] 98 testes v1.0 continuam passando
- [ ] 14+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `profiles/diseases/dpoc.yaml`, `icc.yaml`, `dislipidemia.yaml`, `engine/staging/gold_staging.py`
- **Arquivos modificados**: `engine/staging/factory.py` (registrar GOLD)
- **Linhas estimadas**: ~350 (principalmente YAML + uma estrategia Python)
- **Testes novos**: ~14
