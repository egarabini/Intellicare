# 🏥 ALGORITMOS CLÍNICOS - Oswaldo

Documentação técnica dos algoritmos de classificação clínica implementados no Oswaldo.

---

## 1. CLASSIFICAÇÃO DE DIABETES MELLITUS (ADA 2024)

### Referência
- **American Diabetes Association (ADA)**
- **Standards of Care in Diabetes 2024**
- https://diabetesjournals.org/care/pages/standards-of-care/

### Parâmetros Monitorados

| Parâmetro | Unidade | Prioridade | Referência Normal |
|-----------|---------|-----------|------------------|
| HbA1c | % | 1️⃣ (Preferencial) | < 5.7% |
| Glicemia de Jejum | mg/dL | 2️⃣ | 70-100 |
| Glicemia Casual/Acaso | mg/dL | 3️⃣ | < 140 |

### Lógica de Classificação

```python
def classificar_diabetes(hba1c=None, glicemia_jejum=None, glicemia_acaso=None):
    """
    Classifica controle glicêmico conforme ADA 2024.
    Ordem de prioridade: HbA1c > Glicemia de Jejum > Glicemia Casual
    """
    
    # OPÇÃO 1: HbA1c (Preferencial)
    if hba1c is not None:
        if hba1c < 5.7:
            return 'BEM_CONTROLADO' (A0)
        elif hba1c < 7.0:
            return 'BEM_CONTROLADO' (A0)  # Meta padrão
        elif hba1c < 8.0:
            return 'MODERADO' (A1)
        elif hba1c < 9.0:
            return 'MAL_CONTROLADO' (A2)
        else:
            return 'CRITICO' (A3)
    
    # OPÇÃO 2: Glicemia de Jejum
    elif glicemia_jejum is not None:
        if glicemia_jejum < 100:
            return 'BEM_CONTROLADO'
        elif glicemia_jejum < 126:
            return 'MODERADO'        # Pré-diabetes
        elif glicemia_jejum < 160:
            return 'MAL_CONTROLADO'
        else:
            return 'CRITICO'
    
    # OPÇÃO 3: Glicemia Casual
    elif glicemia_acaso is not None:
        if glicemia_acaso < 140:
            return 'BEM_CONTROLADO'
        elif glicemia_acaso < 200:
            return 'MODERADO'
        else:
            return 'MAL_CONTROLADO'
```

### Tabela de Decisão Completa

| HbA1c | Estado | Ação Clínica |
|-------|--------|-------------|
| < 5.7% | Normal/Pré-diabetes | Prevenção |
| 5.7 → 6.4% | Pré-diabetes | Intensificar lifestyle |
| 6.5% | Diagnóstico DM2 | Iniciar tratamento |
| < 7.0% | **META PADRÃO** | Manutenção ✅ |
| 7.0 → 8.0% | Moderadamente elevado | Revisar medicações |
| 8.0 → 9.0% | Elevado | **Intensificar** ⚠️ |
| ≥ 9.0% | **CRÍTICO** | **Avaliação urgente** 🔴 |

### Casos Especiais

#### 1. Diabetes Gestacional
- Meta HbA1c: < 6.5%
- (Não implementado em v0.6.0)

#### 2. Diabetes em Idosos (≥65 anos)
- Meta HbA1c: < 8.0% (flexível)
- Considerar funcionalidade e comorbidades

#### 3. Diabetes com Complicações Vasculares
- Meta HbA1c: < 6.5% (mais rigorosa)
- Monitorar proteinúria, creatinina

---

## 2. CLASSIFICAÇÃO DE HIPERTENSÃO (SBC 2023)

### Referência
- **Sociedade Brasileira de Cardiologia (SBC)**
- **Diretrizes de Hipertensão 2023**
- https://www.sbh.org.br/

### Parâmetros Monitorados

| Parâmetro | Unidade | Categoria | Valor |
|-----------|---------|-----------|-------|
| Pressão Sistólica | mmHg | Principal | ≥ 140 (diagnóstico) |
| Pressão Diastólica | mmHg | Secundária | ≥ 90 |

### Lógica de Classificação

```python
def classificar_has(pressao_sistolica, pressao_diastolica):
    """
    Classifica HAS conforme SBC 2023.
    REGRA: Sistólica >= Diastólica (coerência física)
    """
    
    # Validação de coerência
    if sistolica < diastolica:
        return ERROR: "Pressão incoerente"
    
    # Classificação
    if sistolica < 120 and diastolica < 80:
        return 'CONTROLADO' (Ótimo)
    
    elif sistolica <= 139 or diastolica <= 89:
        return 'PRE_HIPERTENSAO' (Elevado)
    
    elif sistolica <= 159 or diastolica <= 99:
        return 'ESTAGIO_1'
    
    elif sistolica <= 179 or diastolica <= 109:
        return 'ESTAGIO_2'
    
    elif sistolica >= 180 or diastolica >= 110:
        return 'CRISE_HIPERTENSIVA' (CRÍTICO 🔴)
```

### Tabela de Decisão Completa

| Sistólica (mmHg) | Diastólica (mmHg) | Classificação | Ação |
|------------------|------------------|---------------|------|
| < 120 | < 80 | ✅ CONTROLADO | Manutenção |
| 120-139 | 80-89 | Elevado | Lifestyle |
| 140-159 | 90-99 | Estágio 1 | Iniciar medic. |
| 160-179 | 100-109 | Estágio 2 | **Intensificar** ⚠️ |
| ≥ 180 | ≥ 110 | **CRISE** | **Emergência** 🔴 |

### Casos Especiais

#### 1. Hipertensão de Consultório (White Coat)
- PA elevada no consultório, normal em casa
- Confirmar com monitorização ambulatorial (MAPA)

#### 2. Hipertensão Mascarada
- PA normal no consultório, elevada em casa
- Requer MAPA para diagnóstico

#### 3. Pacientes Idosos (≥65 anos)
- Meta PA: < 140/90 mmHg (SBC 2023)
- Más tolerância a hipotensão

---

## 3. CLASSIFICAÇÃO DE DOENÇA RENAL CRÔNICA (KDIGO 2021)

### Referência
- **Kidney Disease: Improving Global Outcomes (KDIGO)**
- **2021 Clinical Practice Guideline**
- https://kdigo.org/

### Parâmetros Monitorados

| Parâmetro | Unidade | Cálculo | Fonte |
|-----------|---------|--------|-------|
| TFG (Taxa Filtração Glomerular) | mL/min/1.73m² | CKD-EPI eq. | Creatinina sérica |
| Creatinina | mg/dL | Medida direta | Lab |
| Relação Albumina/Creatinina (RAC) | mg/g | Urina amostra | Lab |

### Cálculo de TFG (CKD-EPI Equation 2021)

```python
def calcular_tfg(creatinina_mg_dl, edad_anos, genero, etnia='nao_negra'):
    """
    Calcula TFG conforme equação CKD-EPI 2021.
    
    NOTA: A creatinina DEVE estar calibrada (creatinina de laboratório padrão)
    """
    
    # Fator de ajuste por gênero
    kappa = 0.7 if genero == 'feminino' else 0.9
    alfa = -0.302 if genero == 'feminino' else -0.241
    
    # Ajuste por etnia (se aplicável - opcional em v0.6.0)
    multiplicador_etnia = 1.0  # Sem fator de etnia em versão atual
    
    # Cálculo
    tfg = 142 * (creatinina / kappa) ** alfa * (0.9938 ** edad) * multiplicador_etnia
    
    return round(tfg, 1)

# Exemplo
tfg = calcular_tfg(creatinina_mg_dl=1.8, edad_anos=68, genero='masculino')
# tfg ≈ 38 mL/min/1.73m² → G3b
```

### Lógica de Classificação (Estágios KDIGO)

```python
def classificar_drc(tfg, albuminuria=None):
    """
    Classifica DRC conforme KDIGO estágios G (GFR) e A (Albuminúria)
    """
    
    # Estágios de TFG
    if tfg >= 90:
        estagio_gfr = 'G1'  # Normal/Alta
    elif tfg >= 60:
        estagio_gfr = 'G2'  # Levemente reduzida
    elif tfg >= 45:
        estagio_gfr = 'G3a'  # Moderadamente reduzida
    elif tfg >= 30:
        estagio_gfr = 'G3b'  # Moderadamente reduzida
    elif tfg >= 15:
        estagio_gfr = 'G4'   # Severamente reduzida
    else:
        estagio_gfr = 'G5'   # Falência renal
    
    # Estágios de Albuminúria (se disponível)
    if albuminuria is not None:
        if albuminuria < 10:
            estagio_albumin = 'A1'  # Normal
        elif albuminuria < 30:
            estagio_albumin = 'A2'  # Aumentada
        else:
            estagio_albumin = 'A3'  # Muito aumentada
    else:
        estagio_albumin = None
    
    # Resultado final: G3a_A2 (exemplo)
    resultado = f"{estagio_gfr}"
    if estagio_albumin:
        resultado += f"_{estagio_albumin}"
    
    return resultado
```

### Tabela de Decisão (TFG)

| TFG (mL/min) | Estágio | Descrição | Ação |
|--------------|---------|-----------|------|
| ≥ 90 | G1 | Normal/Alto | Monitorar |
| 60-89 | G2 | Levemente ↓ | Monitorar |
| 45-59 | **G3a** | Moderadamente ↓ | **Intensificar** ⚠️ |
| 30-44 | **G3b** | Moderadamente ↓ | **Intensificar** ⚠️ |
| 15-29 | **G4** | Severamente ↓ | **Avaliação urologia** 🔴 |
| < 15 | **G5** | Falência | **Diálise iminente** 🔴 |

### Tabela de Albuminúria (RAC)

| RAC (mg/g) | Estágio | Descrição |
|------------|---------|-----------|
| < 10 | A1 | Normal |
| 10-29 | A2 | Levemente elevada |
| ≥ 30 | A3 | Muito elevada (proteinúria) |

### Exemplo Clínico

```
Paciente: J.S., 68 anos, masculino
Creatinina: 1.8 mg/dL
RAC: 45 mg/g

TFG = 38 mL/min/1.73m² → G3b
RAC = 45 mg/g → A3

CLASSIFICAÇÃO FINAL: G3b_A3 (DRC Moderado-Severo com proteinúria)
AÇÃO: Referência a nefrologia, investigar causa, previne de progressão
```

---

## 4. DETECÇÃO DE PIORA PROGRESSIVA

### Definição
Deterioração clínica quando **2 ou mais estágios pioram em período curto** (≤ 90 dias).

### Algoritmo

```python
def detectar_piora_progressiva(ultima_classificacao, nova_classificacao,
                               dias_desde_ultima=30):
    """
    Detecta piora clínica grave = múltiplos estágios em curto período.
    """
    
    # Mapa de severidade (exemplo para DM)
    mapa_severidade = {
        'BEM_CONTROLADO': 1,
        'MODERADO': 2,
        'MAL_CONTROLADO': 3,
        'CRITICO': 4
    }
    
    severidade_anterior = mapa_severidade[ultima_classificacao]
    severidade_novo = mapa_severidade[nova_classificacao]
    
    piora_em_estágios = severidade_novo - severidade_anterior
    
    # Critério: piora >= 2 estágios EM < 90 dias
    if piora_em_estágios >= 2 and dias_desde_ultima <= 90:
        return {
            'piora_detectada': True,
            'severidade_piora': piora_em_estágios,
            'dias_decurso': dias_desde_ultima,
            'alerta': 'PIORA_PROGRESSIVA_CRÍTICA'
        }
    
    return {'piora_detectada': False}
```

### Exemplos

#### Exemplo 1: Piora Rápida em DM
```
Consulta 1 (30/jan): HbA1c 7.2% → MODERADO (A1)
Consulta 2 (28/fev): HbA1c 9.5% → CRITICO (A3)
Período: 29 dias
Piora: A1 → A3 (2 estágios em < 30 dias)
RESULTADO: ✅ PIORA_PROGRESSIVA detectada
```

#### Exemplo 2: Sem Piora Progressiva
```
Estadiamento 1 (01/jan): TFG 52 → G3a
Estadiamento 2 (15/mar): TFG 48 → G3a
Período: 73 dias
Piora: 0 estágios (permaneceu em G3a)
RESULTADO: ❌ Sem piora progressiva (apenas piora leve)
```

---

## 5. GERAÇÃO DE ALERTAS

### Critérios de Alerta

| Tipo | Severidade | Trigger | Ação |
|------|-----------|---------|------|
| **PIORA_PROGRESSIVA** | CRÍTICO 🔴 | 2+ estágios em ≤90 dias | Contatar médico |
| **DESCONTROLE** | ALTO ⚠️ | Novo estágio MAL_CONTROLADO/CRÍTICO | Ajustar terapia |
| **MONITORAMENTO** | MÉDIO | Mudança de estagio (sem piora) | Seguimento |
| **PREVENTIVO** | BAIXO | Risco de descontrole identificado | Reforçar lifestyle |

### Exemplos de Severidade

```python
def determinar_severidade_alerta(desvio_percentual):
    """
    Quanto maior o desvio do objetivo, maior a severidade.
    """
    if desvio_percentual <= 10:
        return 'BAJO'      # Verde: aceitável
    elif desvio_percentual <= 25:
        return 'MEDIO'     # Amarelo: atenção
    elif desvio_percentual <= 50:
        return 'ALTO'      # Laranja: avalie
    else:
        return 'CRITICO'   # Vermelho: emergência
```

---

## 6. RESPOSTAS CLÍNICAS RECOMENDADAS

### Por Severidade e Tipo de Condição

#### HAS em Estágio 2
```
PA = 170/105 mmHg (Estágio 2)
RESPOSTA OSWALDO:
├─ Alerta: DESCONTROLE, SEVERIDADE=ALTO
├─ Recomendação: Intensificar anti-hipertensivo
├─ Frequência acompanhamento: 7-14 dias
└─ Encaminhamento: Cardiologia se refratária
```

#### DM com HbA1c CRÍTICA
```
HbA1c = 11.2% (CRÍTICO)
RESPOSTA OSWALDO:
├─ Alerta: DESCONTROLE, SEVERIDADE=CRÍTICO
├─ Recomendação: Avaliar urgentemente, risco de DKA
├─ Frequência: 3-7 dias
└─ Encaminhamento: Endocrinologia urgente
```

#### DRC em Estágio G4
```
TFG = 22 mL/min (G4, Severamente reduzida)
RESPOSTA OSWALDO:
├─ Alerta: Monitoramento rigoroso
├─ Recomendação de: Dieta renal, ajustar medicações
├─ Frequência: Mensal
└─ Encaminhamento: Nefrologia para planejamento dialítico
```

---

## Notas Técnicas

### Limitações em v0.6.0

- ⚠️ Não inclui cálculos de risco cardiovascular total (Framingham, SCORE)
- ⚠️ Não estratifica idosos com multiple comorbidades
- ⚠️ Não inclui algoritmos de otimização de polifarmácia
- ⚠️ Não integra genética (APOE para dislipidemia, genes DM)

### Próximas Versões

- 📌 v0.7: Risco cardiovascular integrado
- 📌 v0.8: Suporte para Asma e DPOC
- 📌 v0.9: Machine Learning para predição de descompensação

---

**Referências Clínicas**:
- ADA Standards of Care 2024
- SBC Diretrizes HAS 2023
- KDIGO Clinical Practice Guideline 2021
- ESC Guidelines on Prevention 2021

**Data de Atualização**: FEV 2026  
**Versão da Documentação**: 0.6.0
