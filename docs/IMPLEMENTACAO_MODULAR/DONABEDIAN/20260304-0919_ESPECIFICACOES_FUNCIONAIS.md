# DONABEDIAN — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 2.0.0
**Modulo:** intellicare-donabedian (porta 8003)
**Homenagem:** Avedis Donabedian (1919-2000) — medico e pesquisador, criador do modelo Estrutura-Processo-Resultado para avaliacao da qualidade em saude

---

## 1. Proposito

O DONABEDIAN e o agente de qualidade e indicadores do IntelliCare.
Ele calcula, consolida e reporta indicadores de qualidade assistencial
baseados no modelo Donabedian (Estrutura, Processo, Resultado),
auxiliando gestores na tomada de decisao e na acreditacao hospitalar.

---

## 2. Funcionalidades Implementadas (v1.0 — piloto)

### 2.1 Motor de Indicadores
- Calculo de indicadores de processo (ex: % pacientes DM com HbA1c < 7%)
- Calculo de indicadores de resultado (ex: taxa de reinternacao em 30 dias)
- Calculo de indicadores de estrutura (ex: proporcao medico/paciente)

### 2.2 Consolidacao de Dados
- Batch processing de dados clinicos periodico
- Agregacao por periodo (mensal, trimestral, anual)
- Segmentacao por patologia, UBS, equipe, faixa etaria

### 2.3 Dashboard de Indicadores
- API de dados para o portal frontend
- Comparacao com benchmarks nacionais (PMAQ-AB, ONA)
- Semaforizacao: verde/amarelo/vermelho

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 API REST Exposta
- Atualmente sem API FastAPI. Precisa criar a camada REST.
- Endpoints para: listar indicadores, calcular sob demanda, obter historico

### 3.2 Integracao com GRAHAME
- Consumir dados FHIR para calculo de indicadores
- Observation para indicadores clinicos
- Condition para prevalencia de doencas
- Encounter para volume assistencial

### 3.3 Relatorios PDF
- Gerar relatorio de indicadores mensais via MINERVA/PDF skill
- Formato: painel de controle com graficos e semaforizacao
- Exportacao para ONA/PMAQ-AB

### 3.4 Alertas de Qualidade
- Enviar alertas para gestores quando indicador piora
- Limites configuráveis por indicador
- Integracao com WANDA AlertHub

### 3.5 Acreditacao ONA
- Mapa de requisitos ONA vs indicadores coletados
- Checklist automatizado de conformidade
- Evidencias vinculadas a cada requisito

---

## 4. Indicadores Prioritarios (v2.0)

### Atencao Primaria (PMAQ-AB)
- Cobertura de pre-natal no primeiro trimestre
- % DM2 com HbA1c < 7% no periodo
- % HAS com PA < 140/90 em acompanhamento
- Taxa de hospitalizacao por condicoes sensiveis a APS (CSAP)

### Qualidade do Cuidado Cronico
- Taxa de adesao terapeutica (via GERALDA)
- Frequencia de consultas por paciente cronico
- Taxa de completude do plano de cuidado

### Seguranca do Paciente
- Taxa de incidentes notificados
- Taxa de reinternacao hospitalar em 30 dias
- Eventos adversos a medicamentos

---

## 5. Criterios de Aceite

- [ ] Health check responde 200
- [ ] GET /indicators retorna lista de indicadores calculados
- [ ] POST /indicators/calculate dispara calculo sob demanda
- [ ] Dados de indicadores persistidos no PostgreSQL
- [ ] Semaforizacao correta (verde/amarelo/vermelho)
- [ ] Cobertura de testes >= 75%

---

*DONABEDIAN v2.0 — Especificacoes Funcionais — 2026-03-04*
