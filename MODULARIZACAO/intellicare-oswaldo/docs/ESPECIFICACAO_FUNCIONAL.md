# intellicare-oswaldo — Especificacao Funcional

> Homenagem a Oswaldo Cruz, medico sanitarista que revolucionou a saude publica no Brasil.

## 1. Proposito

O intellicare-oswaldo e um **motor generico de monitoramento de doencas cronicas**. Ele analisa dados clinicos de pacientes, realiza estadiamento conforme guidelines internacionais, detecta tendencias de progressao e gera alertas acionaveis.

## 2. Valor de Negocio

### Para a UBS/Hospital:
- Monitoramento continuo de pacientes cronicos sem esforco manual
- Alertas precoces de deterioracao clinica
- Estadiamento padronizado conforme protocolos internacionais
- Reducao de internacoes evitaveis

### Para o Gestor:
- Visao consolidada da populacao de cronicos
- Indicadores de progressao por doenca
- Priorizacao automatica de pacientes em risco

### Diferencial: Extensibilidade
Novas doencas cronicas entram via configuracao YAML — nao requer codigo novo.

## 3. Doencas Suportadas (v1.0)

### 3.1 Doenca Renal Cronica (CKD)
- **Guideline:** KDIGO 2024
- **Estadiamento:** G1-G5 (por eGFR) + A1-A3 (por albuminuria)
- **Biomarcadores:** Creatinina, eGFR (CKD-EPI), Albuminuria (ACR), Ureia, Potassio, Hemoglobina
- **Alertas:** eGFR < 15 (emergencia), queda rapida de eGFR, hipercalemia

### 3.2 Diabetes Mellitus Tipo 2 (DM2)
- **Guideline:** ADA Standards of Care 2024
- **Estadiamento:** Pre-diabetes / Controlado / Nao-controlado / Complicacoes
- **Biomarcadores:** HbA1c, Glicemia de jejum, Glicemia pos-prandial, Perfil lipidico
- **Alertas:** HbA1c > 9% (descontrole grave), hipoglicemia, complicacoes microvasculares

### 3.3 Hipertensao Arterial Sistemica (HAS)
- **Guideline:** ESC/ESH 2023
- **Estadiamento:** Normal / Elevada / Estagio 1 / Estagio 2 / Crise
- **Biomarcadores:** PA sistolica, PA diastolica, Frequencia cardiaca
- **Alertas:** PA > 180/120 (crise), hipertensao resistente, lesao de orgao-alvo

### 3.4 Extensibilidade
Para adicionar nova doenca (ex: Insuficiencia Cardiaca):
1. Criar arquivo YAML em `profiles/diseases/ic.yaml`
2. Implementar estrategia de estadiamento em `engine/staging/ic_staging.py`
3. Registrar no factory
4. Pronto — sem mexer no core

## 4. Funcionalidades

### 4.1 Estadiamento Clinico
- Classificacao automatica baseada em biomarcadores
- Multi-parametro (ex: eGFR + albuminuria para CKD)
- Confidence score baseado em volume e qualidade dos dados
- Historico de estadiamento com timeline

### 4.2 Analise de Tendencias
- Calculo de velocidade de progressao (ex: queda de eGFR ml/min/ano)
- Deteccao de aceleracao ou desaceleracao
- Projecao de tempo ate proximo estagio
- Graficos temporais

### 4.3 Alertas Inteligentes
- **Threshold alerts:** valores fora da faixa de referencia
- **Trend alerts:** progressao acelerada detectada
- Severidade: informacional / atencao / urgente / emergencia
- Recomendacoes clinicas associadas a cada alerta

### 4.4 Recomendacoes de Medicamentos
- Sugestoes baseadas em estagio e perfil do paciente
- Ajustes por funcao renal (DRC)
- Contraindicacoes

### 4.5 Risco Cardiovascular
- Calculo de risco CV integrado
- Fatores de risco: idade, sexo, tabagismo, diabetes, colesterol

### 4.6 Dashboard (Streamlit)
- Visao do paciente individual
- Timeline de biomarcadores com graficos
- Estadiamento visual
- Alertas ativos
- Painel de populacao (lista de pacientes por risco)

### 4.7 API REST
- Endpoints padrao IntelliCare (/health, /info, /analyze)
- Endpoint de estadiamento por paciente
- Endpoint de alertas ativos
- Endpoint de tendencias

## 5. Perfis de Usuario

| Perfil | Acesso | Funcionalidades |
|--------|--------|-----------------|
| Medico | Completo | Todos os dados clinicos, estadiamento, alertas, recomendacoes |
| Enfermeiro | Parcial | Alertas, tendencias, orientacoes de cuidado |
| Gestor | Agregado | Indicadores populacionais, sem dados individuais identificaveis |

## 6. Integracao

### Roda Sozinho:
- Streamlit em http://localhost:8501
- API REST em http://localhost:8000
- PostgreSQL local (ou SQLite para desenvolvimento)

### Integrado com IntelliCare:
- Wanda chama Oswaldo como subagent via LangGraph
- Portal exibe dashboard do Oswaldo
- Eventos de alerta publicados em Redis Stream

## 7. Requisitos Nao-Funcionais

- Tempo de resposta de estadiamento: < 2 segundos
- Suporte a 10.000+ pacientes simultaneos
- Dados clinicos NUNCA saem do ambiente do cliente
- Logs auditaveis de todas as analises
- Funciona offline (sem internet) apos carga inicial de dados
