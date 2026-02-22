# intellicare-zilda — Especificacao Funcional

> Homenagem a Zilda Arns, medica pediatra e sanitarista fundadora da Pastoral da Crianca.

## 1. Proposito

O intellicare-zilda e o agente especialista em **contexto territorial e dados de saude brasileira**. Ele consulta e valida dados do CNES, DATASUS, e-SUS e fontes regionais, fornecendo contexto realista da rede assistencial para decisoes mais fundamentadas.

## 2. Valor de Negocio

- Decisoes conectadas ao contexto real da rede de saude
- Validacao automatica de unidades e profissionais
- Mapeamento de capacidade instalada por territorio
- Identificacao de vazios assistenciais

## 3. Funcionalidades

### 3.1 Cliente CNES
- Consulta de unidades de saude por municipio, tipo, especialidade
- Validacao de codigos CNES
- Enriquecimento de dados (leitos, profissionais, servicos)
- Cache local para performance

### 3.2 Cliente DATASUS
- Consulta a APIs publicas do Ministerio da Saude
- Dados de producao (SIH, SIA, SIM, SINASC)
- Indicadores epidemiologicos

### 3.3 Contexto Territorial
- Mapeamento de rede assistencial por regiao de saude
- Cobertura de equipes de Saude da Familia
- Distancias e acessibilidade
- Populacao por area de abrangencia

### 3.4 Planejamento Assistencial
- Analise de oferta vs demanda por regiao
- Identificacao de vazios assistenciais
- Sugestao de encaminhamentos baseada em capacidade real

## 4. Fontes de Dados

| Fonte | Tipo | Uso |
|-------|------|-----|
| CNES | API REST | Unidades, profissionais, leitos |
| DATASUS | API REST | Producao, indicadores |
| e-SUS APS | API REST | Atencao primaria |
| IBGE | API REST | Populacao, geografia |
| Secretarias | Variavel | Dados regionais |

## 5. Origem do Codigo

- `agentes/tools/zilda_health_data_agent.py` — skeleton (50 linhas)
- `agentes/tools/brazilian_public_data_agent.py` — specs detalhadas (23k linhas)
- As specs do brazilian_public_data_agent sao a base para implementacao
