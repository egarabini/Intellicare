# intellicare-florence — Especificacao Funcional

> Homenagem a Florence Nightingale, fundadora da enfermagem moderna e pioneira no uso de dados para melhorar a saude.

## 1. Proposito

O intellicare-florence e um agente de **inteligencia clinica profunda**. Ele aprofunda a analise clinica alem do que o estadiamento de cronicos oferece — interpreta exames laboratoriais no contexto do paciente, identifica tendencias clinicas sutis e fornece apoio a decisao medica baseado em evidencias.

## 2. Valor de Negocio

- Reducao de erros de interpretacao laboratorial
- Deteccao precoce de deterioracao clinica
- Visao longitudinal do paciente com tendencias
- Apoio objetivo a decisao medica com RAG sobre protocolos

## 3. Funcionalidades

### 3.1 Analise de Exames Laboratoriais
- Interpretacao contextualizada (nao apenas "acima/abaixo da referencia")
- Correlacao entre exames (ex: creatinina + potassio + hemoglobina = perfil renal)
- Evolucao temporal com graficos

### 3.2 Inteligencia Clinica (RAG)
- Retrieval-Augmented Generation sobre protocolos clinicos
- Base de conhecimento indexada (diretrizes SUS, protocolos MS, NICE, UpToDate)
- Respostas com citacao de fontes

### 3.3 Deteccao de Tendencias
- Analise de series temporais de biomarcadores
- Deteccao de padroes de deterioracao
- Alertas de sinais clinicos sutis

### 3.4 Apoio Diagnostico
- Cruzamento de dados para sugestoes diagnosticas
- Diagnosticos diferenciais baseados no quadro clinico
- Score de probabilidade

### 3.5 IPS (International Patient Summary)
- Geracao e interpretacao de IPS Brasil
- Resumo clinico consolidado para transferencia de cuidado

## 4. Diferenca entre Florence e Oswaldo

| Aspecto | Oswaldo | Florence |
|---------|---------|----------|
| Foco | Doencas cronicas especificas | Quadro clinico geral |
| Profundidade | Estadiamento por doenca | Analise clinica holistica |
| Metodo | Disease Profiles + Strategy Pattern | RAG + NLP + Reasoning |
| Saida | Estagio + alertas + tendencias | Interpretacao + apoio diagnostico |
| Quando usar | Acompanhamento de cronicos | Avaliacao clinica geral |

## 5. Origem do Codigo

- `agentes/wanda/subagents/patient_iq.py` — skeleton do subagent
- `agentes/subagents/patient_iq/` — conceito inicial
- Maior parte e **novo desenvolvimento**

## 6. Integracao

- Roda sozinho: Streamlit + API REST
- Integrado: Wanda chama Florence para analise clinica profunda
- Consome: FHIR Server (via intellicare-core FHIRClient)
