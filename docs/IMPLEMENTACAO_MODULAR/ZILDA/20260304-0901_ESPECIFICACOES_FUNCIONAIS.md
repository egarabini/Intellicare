# ZILDA — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-zilda (porta 8007)
**Homenagem:** Zilda Arns (1934-2010), medica pediatra e sanitarista brasileira

---

## 1. Proposito

O ZILDA e o agente de dados de saude publica brasileira do IntelliCare.
Ele contextualize o cuidado clinico com informacoes territoriais e populacionais,
respondendo perguntas como:
- "Quais UBS existem no municipio X?"
- "Qual a cobertura de ESF na regiao Y?"
- "O CNES codigo 1234567 e valido?"

---

## 2. Funcionalidades Atuais (v1.0 — Implementadas)

### 2.1 Consulta CNES
- Buscar estabelecimentos por estado (UF), municipio e tipo de unidade
- Validar formato e existencia de codigos CNES (7 digitos numericos)
- Listar tipos de unidade de saude (hospital, UBS, clinica, CAPS, etc.)

### 2.2 Contexto Territorial
- Consultar regioes e macrorregioes de saude com dados populacionais
- Analisar o perfil de saude de um municipio/estado (resumo territorial)
- Identificar regiao de saude, municipios vizinhos e populacao estimada

### 2.3 API de Analise
- `POST /api/v1/analyze` — endpoint padrao BaseAgent para consultas via WANDA

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 Integracao DATASUS Real
- Conectar a API publica do DATASUS (TabNet) para dados atualizados
- Puxar indicadores do SIAB/e-SUS: cobertura ESF, equipes NASF, ACS
- Cache Redis com TTL de 24h para dados estaticos

### 3.2 Indicadores Populacionais
- Mortalidade infantil por municipio
- Cobertura vacinal por faixa etaria
- Internacoes por CID-10 (SIHSUS)
- Prevalencia de cronicas (Hipertensao, Diabetes) por regiao

### 3.3 Mapa de Rede Assistencial
- Dado um paciente com CEP, identificar os estabelecimentos mais proximos
- Calcular distancia media ate UBS de referencia
- Identificar vazios assistenciais na regiao

### 3.4 Integracao com GERALDA
- Ao criar plano de cuidado, GERALDA consulta ZILDA para mapear
  UBS de referencia do paciente
- ZILDA responde com codigo CNES + dados do estabelecimento

---

## 4. Casos de Uso Principais

### UC-01: Validacao de CNES
**Ator:** Profissional de saude cadastrando estabelecimento
**Fluxo:** Informa codigo CNES → ZILDA valida formato e verifica na base → Retorna dados do estabelecimento

### UC-02: Contexto Territorial do Paciente
**Ator:** WANDA orquestrando analise clinica
**Fluxo:** WANDA envia CEP do paciente → ZILDA retorna regiao de saude, UBS proximas e perfil epidemiologico

### UC-03: Relatorio de Rede Assistencial
**Ator:** Gestor de saude
**Fluxo:** Informa municipio → ZILDA retorna mapa completo de estabelecimentos, coberturas e indicadores

---

## 5. Criterios de Aceite

- [ ] Health check responde 200 com `{"status": "healthy", "module": "zilda"}`
- [ ] Busca por municipio retorna lista de estabelecimentos CNES valida
- [ ] Validacao CNES retorna erro claro para codigo invalido
- [ ] Smoke test incluido no `scripts/smoke_tests.py`
- [ ] Cobertura de testes >= 80%

---

## 6. Fora de Escopo (v2.0)

- Integracao com geolocationgPS (sera modulo futuro)
- Dados de planos privados (somente SUS)
- Historico de mudancas cadastrais do CNES

---

*ZILDA v2.0 — Especificacoes Funcionais — 2026-03-04*
