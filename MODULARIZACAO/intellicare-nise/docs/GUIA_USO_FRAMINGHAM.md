# 🩺 Guia de Uso - Framingham Risk Score

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [O que é Framingham?](#o-que-é-framingham)
3. [Como Usar](#como-usar)
4. [Interpretação de Resultados](#interpretação-de-resultados)
5. [Integração com Oswaldo](#integração-com-oswaldo)
6. [Workflows Automatizados](#workflows-automatizados)
7. [Exemplos Práticos](#exemplos-práticos)
8. [Perguntas Frequentes](#perguntas-frequentes)

---

## 🎯 VISÃO GERAL

O **Framingham Risk Score** é uma ferramenta validada cientificamente para calcular o risco de desenvolver doença cardiovascular em 10 anos.

**Implementação NISE**:
- ✅ Algoritmo Framingham completo (D'Agostino et al., 2008)
- ✅ Cálculo automático a partir de dados do Oswaldo
- ✅ Recomendações clínicas personalizadas
- ✅ Integração com workflows Kestra
- ✅ API REST simples e rápida

---

## 📚 O QUE É FRAMINGHAM?

### História

O **Framingham Heart Study** é um dos estudos epidemiológicos mais importantes da história da medicina, iniciado em 1948 na cidade de Framingham, Massachusetts (EUA).

**Objetivo**: Identificar fatores de risco para doenças cardiovasculares.

**Resultado**: Desenvolvimento de um modelo preditivo validado mundialmente.

### Fatores de Risco Avaliados

O algoritmo considera **7 fatores de risco**:

1. **Idade** (30-74 anos)
2. **Sexo** (Masculino/Feminino)
3. **Colesterol Total** (mg/dL)
4. **HDL Colesterol** (mg/dL) - fator protetor
5. **Pressão Arterial Sistólica** (mmHg)
6. **Tabagismo** (Sim/Não)
7. **Diabetes** (Sim/Não)

### Classificação de Risco

| Risco | Percentual | Ação Recomendada |
|-------|-----------|------------------|
| **Baixo** | < 10% | Manter estilo de vida saudável |
| **Intermediário** | 10-20% | Estatina moderada + acompanhamento |
| **Alto** | > 20% | Estatina alta intensidade + AAS + acompanhamento intensivo |

---

## 🚀 COMO USAR

### Método 1: Cálculo Direto (API)

Use quando você tem todos os dados do paciente.

**Endpoint**: `POST /api/v1/framingham/calcular`

**Exemplo**:
```bash
curl -X POST "http://localhost:8000/api/v1/framingham/calcular" \
  -H "Content-Type: application/json" \
  -d '{
    "sexo": "M",
    "idade": 55,
    "colesterol_total": 220,
    "hdl": 45,
    "pa_sistolica": 140,
    "tabagismo": true,
    "diabetes": false
  }'
```

**Response**:
```json
{
  "risco_10_anos": 18.5,
  "classificacao": "intermediario",
  "pontos_totais": 12,
  "recomendacoes": [
    "⚠️ RISCO INTERMEDIÁRIO: Acompanhamento intensivo recomendado",
    "Estatina de intensidade moderada (Atorvastatina 10-20mg)",
    "Meta LDL < 100 mg/dL",
    "🩺 Controle rigoroso da pressão arterial (meta < 130/80 mmHg)",
    "🚭 CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano",
    "🏃 Atividade física regular: 150 min/semana de exercício moderado",
    "🥗 Dieta mediterrânea ou DASH",
    "⚖️ Manter peso saudável (IMC 18.5-24.9)"
  ],
  "pontos_idade": 4,
  "pontos_colesterol": 1,
  "pontos_hdl": 1,
  "pontos_pa": 2,
  "pontos_tabagismo": 2,
  "pontos_diabetes": 0
}
```

---

### Método 2: Integração com Oswaldo (Automático)

Use quando o paciente já está cadastrado no Oswaldo.

**Endpoint**: `GET /api/v1/framingham/paciente/{paciente_id}`

**Exemplo**:
```bash
curl -X GET "http://localhost:8000/api/v1/framingham/paciente/PAC001"
```

**O que acontece**:
1. NISE busca dados do paciente no Oswaldo
2. Extrai automaticamente:
   - Sexo e idade (dados demográficos)
   - Última PA sistólica
   - Último lipidograma (colesterol total, HDL)
   - Histórico de tabagismo
   - Diagnóstico de diabetes
3. Calcula risco Framingham
4. Retorna resultado completo

**Vantagens**:
- ✅ Sem necessidade de digitar dados manualmente
- ✅ Sempre usa dados mais recentes
- ✅ Integração automática com prontuário
- ✅ Histórico de avaliações

---

### Método 3: Via Chatbot Dr. Nise

Use para interação conversacional.

**Exemplo de Conversa**:
```
Usuário: "Qual o risco cardiovascular do paciente PAC001?"

Dr. Nise: "Vou calcular o risco cardiovascular do paciente PAC001 usando o 
algoritmo Framingham...

📊 Resultado da Avaliação:
- Risco em 10 anos: 18.5%
- Classificação: INTERMEDIÁRIO
- Pontos totais: 12

⚠️ Recomendações:
1. Estatina de intensidade moderada (Atorvastatina 10-20mg)
2. Meta LDL < 100 mg/dL
3. Controle rigoroso da pressão arterial (meta < 130/80 mmHg)
4. CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano
5. Atividade física regular: 150 min/semana

Deseja que eu agende uma consulta de cardiologia?"
```

---

## 📊 INTERPRETAÇÃO DE RESULTADOS

### Risco Baixo (< 10%)

**Significado**: Baixa probabilidade de evento cardiovascular em 10 anos.

**Recomendações**:
- ✅ Manter estilo de vida saudável
- ✅ Reavaliação anual
- ✅ Exercício regular (150 min/semana)
- ✅ Dieta balanceada
- ✅ Controle de peso

**Exemplo de Paciente**:
- Mulher, 35 anos
- Colesterol total: 170 mg/dL
- HDL: 60 mg/dL
- PA: 110/70 mmHg
- Não fumante, sem diabetes

---

### Risco Intermediário (10-20%)

**Significado**: Risco moderado - requer acompanhamento e intervenção.

**Recomendações**:
- ⚠️ Estatina de intensidade moderada
  - Atorvastatina 10-20mg/dia
  - Meta LDL < 100 mg/dL
- ⚠️ Controle de PA (meta < 130/80 mmHg)
- ⚠️ Cessação do tabagismo (se fumante)
- ⚠️ Controle glicêmico (se diabético)
- ⚠️ Acompanhamento semestral

**Exemplo de Paciente**:
- Homem, 55 anos
- Colesterol total: 220 mg/dL
- HDL: 45 mg/dL
- PA: 140/90 mmHg
- Fumante, sem diabetes

---

### Risco Alto (> 20%)

**Significado**: Alto risco - intervenção urgente necessária.

**Recomendações**:
- 🚨 **URGENTE**: Estatina de alta intensidade
  - Atorvastatina 40-80mg/dia OU
  - Rosuvastatina 20-40mg/dia
  - Meta LDL < 70 mg/dL
- 🚨 Considerar AAS 100mg/dia (prevenção primária)
- 🚨 Controle rigoroso de PA (meta < 130/80 mmHg)
- 🚨 Cessação do tabagismo URGENTE
- 🚨 Controle glicêmico rigoroso (HbA1c < 7%)
- 🚨 Acompanhamento mensal
- 🚨 Encaminhamento para cardiologia

**Exemplo de Paciente**:
- Homem, 70 anos
- Colesterol total: 280 mg/dL
- HDL: 30 mg/dL
- PA: 165/95 mmHg
- Fumante, diabético

---

## 🔗 INTEGRAÇÃO COM OSWALDO

### Dados Necessários

Para cálculo automático, o paciente deve ter no Oswaldo:

| Dado | Localização | Obrigatório |
|------|-------------|-------------|
| Sexo | Dados demográficos | ✅ Sim |
| Idade | Dados demográficos | ✅ Sim |
| PA Sistólica | Última medição | ✅ Sim |
| Colesterol Total | Último lipidograma | ✅ Sim |
| HDL | Último lipidograma | ✅ Sim |
| Tabagismo | Histórico | ✅ Sim |
| Diabetes | Diagnósticos | ✅ Sim |

### Fluxo de Integração

```
┌─────────────┐
│   NISE API  │
└──────┬──────┘
       │
       │ GET /framingham/paciente/{id}
       │
       ▼
┌─────────────────────────────────────┐
│  1. Buscar dados do paciente        │
│     GET /oswaldo/paciente/{id}      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  2. Extrair dados necessários       │
│     - Sexo, idade                   │
│     - Última PA sistólica           │
│     - Último lipidograma            │
│     - Tabagismo, diabetes           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  3. Calcular risco Framingham       │
│     - Pontuação por fator           │
│     - Conversão para risco %        │
│     - Classificação                 │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  4. Gerar recomendações             │
│     - Baseadas em risco             │
│     - Personalizadas por fator      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  5. Retornar resultado completo     │
└─────────────────────────────────────┘
```

---

## ⚙️ WORKFLOWS AUTOMATIZADOS

### Workflow: Avaliação de Risco Cardiovascular

**Arquivo**: `kestra/avaliacao-risco-cardiovascular.yml`

**Trigger**: Manual ou agendado (mensal)

**Fluxo**:
1. Recebe ID do paciente
2. Busca dados no Oswaldo
3. Calcula risco Framingham
4. Classifica risco
5. Aciona ações baseadas no risco:
   - **Alto**: Dispara alerta crítico + notificação urgente
   - **Intermediário**: Agenda consulta de cardiologia
   - **Baixo**: Registra avaliação
6. Atualiza plano de cuidado
7. Notifica paciente

**Como Executar**:
```bash
# Via API Kestra
curl -X POST "http://localhost:8080/api/v1/executions/intellicare.nise/avaliacao-risco-cardiovascular" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": "PAC001",
    "avaliacao_periodica": true
  }'
```

---

## 💡 EXEMPLOS PRÁTICOS

### Exemplo 1: Paciente de Baixo Risco

**Cenário**: Mulher jovem, sem fatores de risco

**Input**:
```json
{
  "sexo": "F",
  "idade": 35,
  "colesterol_total": 170,
  "hdl": 60,
  "pa_sistolica": 110,
  "tabagismo": false,
  "diabetes": false
}
```

**Output**:
```json
{
  "risco_10_anos": 2.3,
  "classificacao": "baixo",
  "pontos_totais": -2,
  "recomendacoes": [
    "✅ RISCO BAIXO: Manter estilo de vida saudável",
    "Reavaliação anual do risco cardiovascular",
    "🏃 Atividade física regular: 150 min/semana",
    "🥗 Dieta mediterrânea ou DASH",
    "⚖️ Manter peso saudável (IMC 18.5-24.9)"
  ]
}
```

**Ação**: Manter estilo de vida, reavaliação anual.

---

### Exemplo 2: Paciente de Risco Intermediário

**Cenário**: Homem meia-idade, fumante, PA elevada

**Input**:
```json
{
  "sexo": "M",
  "idade": 60,
  "colesterol_total": 240,
  "hdl": 40,
  "pa_sistolica": 150,
  "tabagismo": true,
  "diabetes": false
}
```

**Output**:
```json
{
  "risco_10_anos": 15.6,
  "classificacao": "intermediario",
  "pontos_totais": 11,
  "recomendacoes": [
    "⚠️ RISCO INTERMEDIÁRIO: Acompanhamento intensivo recomendado",
    "Estatina de intensidade moderada (Atorvastatina 10-20mg)",
    "Meta LDL < 100 mg/dL",
    "🩺 Controle rigoroso da pressão arterial (meta < 130/80 mmHg)",
    "Considerar anti-hipertensivo (IECA ou BRA)",
    "🚭 CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano",
    "Encaminhar para programa de cessação tabágica",
    "📊 Colesterol total elevado - dieta DASH + estatina",
    "🏃 Atividade física regular: 150 min/semana"
  ]
}
```

**Ação**: Iniciar estatina, controlar PA, cessar tabagismo, acompanhamento semestral.

---

### Exemplo 3: Paciente de Alto Risco

**Cenário**: Homem idoso, múltiplos fatores de risco

**Input**:
```json
{
  "sexo": "M",
  "idade": 70,
  "colesterol_total": 280,
  "hdl": 30,
  "pa_sistolica": 165,
  "tabagismo": true,
  "diabetes": true
}
```

**Output**:
```json
{
  "risco_10_anos": 28.7,
  "classificacao": "alto",
  "pontos_totais": 16,
  "recomendacoes": [
    "⚠️ RISCO ALTO: Prevenção primária urgente necessária",
    "Estatina de alta intensidade (Atorvastatina 40-80mg ou Rosuvastatina 20-40mg)",
    "Meta LDL < 70 mg/dL",
    "Considerar AAS 100mg/dia para prevenção primária",
    "🩺 Controle rigoroso da pressão arterial (meta < 130/80 mmHg)",
    "Considerar anti-hipertensivo (IECA ou BRA)",
    "🚭 CESSAÇÃO DO TABAGISMO URGENTE - reduz risco em 50% em 1 ano",
    "💉 Controle glicêmico rigoroso (HbA1c < 7%)",
    "Considerar Metformina + SGLT2i ou GLP-1 RA (proteção cardiovascular)",
    "📊 HDL muito baixo - aumentar atividade física (150 min/semana)",
    "👴 Idade avançada - rastreamento anual de doença cardiovascular"
  ]
}
```

**Ação**: Intervenção urgente, estatina alta intensidade, controle rigoroso de todos os fatores, encaminhamento para cardiologia.

---

## ❓ PERGUNTAS FREQUENTES

### 1. Por que a idade é limitada a 30-74 anos?

O algoritmo Framingham foi validado apenas para essa faixa etária. Fora dela, a precisão do cálculo não é garantida.

### 2. O que fazer se o paciente tem < 30 ou > 74 anos?

Use outras ferramentas de avaliação de risco (ex: ASCVD Risk Calculator para > 75 anos).

### 3. Com que frequência devo reavaliar o risco?

- **Risco baixo**: Anualmente
- **Risco intermediário**: Semestralmente
- **Risco alto**: Mensalmente (ou conforme orientação médica)

### 4. O Framingham substitui a avaliação médica?

**NÃO**. O Framingham é uma ferramenta de apoio à decisão clínica, não substitui a avaliação médica completa.

### 5. Posso usar para pacientes com doença cardiovascular prévia?

**NÃO**. O Framingham é para **prevenção primária** (pacientes sem doença cardiovascular). Para prevenção secundária, use outras ferramentas.

### 6. Como o tabagismo impacta o risco?

Fumantes têm:
- **Homens**: +2 pontos
- **Mulheres**: +3 pontos

Cessar o tabagismo reduz o risco em **50% em 1 ano**.

### 7. E se faltar algum dado do paciente?

O endpoint `/paciente/{id}` retorna erro 400 indicando quais dados estão faltando. Complete o prontuário no Oswaldo antes de calcular.

### 8. Os resultados são salvos?

Sim, quando integrado com workflows Kestra, os resultados são salvos no plano de cuidado do Oswaldo.

---

**Versão**: 1.0.0  
**Última atualização**: 15/02/2026  
**Referência**: D'Agostino RB Sr, et al. General cardiovascular risk profile for use in primary care: the Framingham Heart Study. Circulation. 2008;117(6):743-53.

