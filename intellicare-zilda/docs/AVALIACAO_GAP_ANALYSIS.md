# ZILDA — Avaliacao e Gap Analysis

> Status: v1.0.0 implementado | Avaliacao realizada em 2026-02-16 por DEV0

## Resumo Executivo

A Zilda v1.0.0 entregou a **fundacao do modulo** com excelente qualidade tecnica (95% cobertura, 68 testes), implementando com sucesso a integracao com a API CNES e o motor territorial basico.

**Porem, em relacao ao que foi especificado, o modulo cobre apenas ~30% das funcionalidades previstas.**

---

## Comparativo Especificado vs Implementado

### 3.1 Cliente CNES

| Funcionalidade | Especificada | Implementada | Observacao |
|----------------|:------------:|:------------:|-----------|
| Busca de estabelecimentos por municipio/tipo | ✅ | ✅ | Funcional via `/api/v1/establishments` |
| Validacao de codigos CNES | ✅ | ✅ | Funcional via `/api/v1/validate` |
| Cache local para performance | ✅ | ✅ | SimpleCache em memoria com TTL |
| Enriquecimento — **leitos** | ✅ | ❌ | Nao implementado — endpoint CNES existe |
| Enriquecimento — **profissionais** | ✅ | ❌ | Nao implementado — endpoint CNES existe |
| Enriquecimento — **servicos especializados** | ✅ | ❌ | Nao implementado — endpoint CNES existe |

**Observacao critica**: A API CNES publica (`apidadosabertos.saude.gov.br`) disponibiliza endpoints para `/cnes/profissionais`, `/cnes/leitos`, `/cnes/servicos`. O cliente atual so consulta `/cnes/estabelecimentos` e `/cnes/tipounidades`. Os dados de leitos e profissionais sao essenciais para analise de capacidade instalada.

---

### 3.2 Cliente DATASUS

| Funcionalidade | Especificada | Implementada | Observacao |
|----------------|:------------:|:------------:|-----------|
| Dados de producao — SIH (internacoes) | ✅ | ❌ | Apenas feature flag `enable_datasus=False` |
| Dados de producao — SIA (ambulatorial) | ✅ | ❌ | Nao implementado |
| Dados de producao — SIM (mortalidade) | ✅ | ❌ | Nao implementado |
| Dados de producao — SINASC (nascimentos) | ✅ | ❌ | Nao implementado |
| Indicadores epidemiologicos | ✅ | ❌ | Nao implementado |

**Impacto**: Sem DATASUS, a Zilda nao pode fornecer indicadores de saude da populacao — uma das principais propostas de valor do modulo. Wanda e outros agentes nao conseguem contextualizar dados epidemiologicos.

---

### 3.3 Contexto Territorial

| Funcionalidade | Especificada | Implementada | Observacao |
|----------------|:------------:|:------------:|-----------|
| Mapeamento de rede por regiao de saude | ✅ | ✅ | Parcial — via `territorial-summary` + `region-context` |
| Populacao por area de abrangencia | ✅ | ✅ | Dados IBGE 2022 via API de regioes |
| Cobertura de equipes Saude da Familia (ESF) | ✅ | ❌ | Nao implementado |
| Calculo de distancias e acessibilidade | ✅ | ❌ | Nao implementado |
| Identificacao de vazios assistenciais | ✅ | ❌ | Nao implementado |

---

### 3.4 Planejamento Assistencial

| Funcionalidade | Especificada | Implementada | Observacao |
|----------------|:------------:|:------------:|-----------|
| Analise oferta vs demanda por regiao | ✅ | ❌ | Nao implementado |
| Identificacao de vazios assistenciais | ✅ | ❌ | Nao implementado |
| Sugestao de encaminhamentos por capacidade | ✅ | ❌ | Nao implementado |

---

### Estrutura Tecnica (ET vs Real)

| Componente Planejado | Implementado | Observacao |
|----------------------|:------------:|-----------|
| `routes/cnes.py` | ✅ (em app.py) | Endpoints CNES funcionais |
| `routes/territory.py` | ✅ (em app.py) | Territorial basico |
| `routes/indicators.py` | ❌ | Nao existe — sem indicadores DATASUS |
| `engine/cnes_client.py` | ✅ | Implementado e testado |
| `engine/datasus_client.py` | ❌ | Nao existe |
| `engine/esus_client.py` | ❌ | Nao existe |
| `ui/main.py` (Streamlit) | ❌ | Dependencia instalada, sem codigo |
| `subagent/zilda_subagent.py` | ❌ | Nao implementado — importante para Wanda |
| Cache Redis | ❌ | SimpleCache em memoria (suficiente para v1) |
| Persistencia PostgreSQL | ❌ | Alembic configurado, sem uso |

---

## O Que Esta Funcionando Bem (Pontos Fortes)

1. **Base CNES solida**: Busca, validacao, tipos e regioes funcionam com cache e tratamento de erros
2. **Qualidade**: 95% de cobertura, 68 testes, sem TODOs ou debito tecnico
3. **Graceful degradation**: API externa indisponivel retorna lista vazia (nao crasha)
4. **Contrato IntelliCare**: `/api/v1/health` e `/api/v1/info` com capabilities declaradas
5. **Docker pronto**: Funciona standalone com `docker compose up`
6. **Feature flags corretas**: `enable_datasus` e `enable_esus` preparados para extensao

---

## Gaps Criticos (Bloqueiam Valor)

### GAP-001 — Ausencia de Cliente DATASUS (ALTA PRIORIDADE)
- **Impacto**: Sem dados de producao e indicadores, Zilda nao pode suportar decisoes de gestao
- **Complexidade**: Media — APIs do DataSUS sao abertas mas inconsistentes; requer scraping do TABNET ou uso de API alternativa
- **Sugestao**: Avaliar `datasus-python` como biblioteca alternativa ao acesso direto

### GAP-002 — Ausencia de Subagente LangChain (ALTA PRIORIDADE)
- **Impacto**: Wanda nao consegue usar a Zilda de forma conversacional — apenas via endpoints REST diretos
- **Complexidade**: Media — estrutura LangChain ja existe no monolito
- **Bloqueio para**: EF-W003 (Roteamento Wanda), EF-009 (Integracao Wanda/Geralda)

### GAP-003 — Enriquecimento CNES Incompleto (MEDIA PRIORIDADE)
- **Impacto**: Nao e possivel saber quantos leitos tem um hospital, quais medicos atendem
- **Complexidade**: Baixa — endpoints CNES ja existem, e apenas adicionar metodos ao `cnes_client.py`
- **Novos endpoints CNES**: `/cnes/profissionais`, `/cnes/leitos`, `/cnes/servicos`

### GAP-004 — Sem Analise de Vazios Assistenciais (MEDIA PRIORIDADE)
- **Impacto**: Nao e possivel identificar regioes sem cobertura adequada
- **Complexidade**: Media — requer cruzar dados de populacao com cobertura de estabelecimentos

### GAP-005 — Sem Cobertura ESF (BAIXA PRIORIDADE)
- **Impacto**: Nao sabe quantas equipes de Saude da Familia cobrem um municipio
- **Complexidade**: Media — dados via e-SUS APS

---

## Endpoint Atual vs Endpoint Planejado

### Endpoints EXISTENTES (v1.0.0)
```
GET /api/v1/health
GET /api/v1/info
GET /api/v1/unit-types
GET /api/v1/establishments       # Busca por municipio/tipo
GET /api/v1/establishment/{code} # Detalhe por CNES
POST /api/v1/validate            # Validacao de CNES
GET /api/v1/regions              # Regioes de saude
GET /api/v1/territorial-summary  # Resumo territorial
GET /api/v1/region-context/{city}# Contexto regional
```

### Endpoints PLANEJADOS (nao implementados)
```
GET /api/v1/establishment/{code}/beds         # Leitos
GET /api/v1/establishment/{code}/professionals # Profissionais
GET /api/v1/establishment/{code}/services     # Servicos especializados
GET /api/v1/indicators/{city_code}            # Indicadores DATASUS
GET /api/v1/indicators/mortality              # SIM - mortalidade
GET /api/v1/indicators/admissions             # SIH - internacoes
GET /api/v1/indicators/primary-care           # e-SUS APS
GET /api/v1/analyze                           # Endpoint padrao Wanda
GET /api/v1/coverage/esf/{city_code}          # Cobertura ESF
GET /api/v1/voids/{region_code}               # Vazios assistenciais
```

---

## Plano de Evolucao Sugerido (v1.1 a v1.3)

### v1.1.0 — Completar CNES + Subagente (URGENTE para integracao com Wanda)

**1. Enriquecimento CNES** (~200 linhas, ~15 testes)
- Adicionar ao `cnes_client.py`: `get_beds()`, `get_professionals()`, `get_services()`
- Endpoints: `/cnes/leitos`, `/cnes/profissionais`, `/cnes/servicos`
- Novos endpoints REST: `/establishment/{code}/beds`, `/establishment/{code}/professionals`

**2. Subagente Zilda** (~150 linhas, ~10 testes)
- Criar `zilda/subagent/zilda_subagent.py` com LangChain
- Tools: `search_establishments`, `validate_cnes`, `get_territory_context`, `find_nearby_units`
- Registrar como capability "territorial" no `/api/v1/info`
- Adicionar endpoint `/api/v1/analyze` (contrato Wanda)

### v1.2.0 — Cliente DATASUS

**3. DATASUS Client** (~400 linhas, ~25 testes)
- Criar `zilda/engine/datasus_client.py`
- Avaliar: API direta (`apidadosabertos.saude.gov.br`) vs `datasus-python` vs TabNet scraping
- Priorizar: SIH (internacoes) e SIM (mortalidade) — maior impacto clinico
- Novos endpoints: `/api/v1/indicators/{city_code}`

### v1.3.0 — Analise Avancada

**4. Vazios Assistenciais** (~200 linhas, ~15 testes)
- Motor de analise: populacao / capacidade instalada = cobertura
- Identificar regioes abaixo de limiar configuravel
- Novo endpoint: `/api/v1/voids/{region_code}`

**5. Cobertura ESF** (~150 linhas, ~10 testes)
- Integrar e-SUS APS para dados de equipes de saude da familia
- Calcular cobertura percentual por municipio

---

## Estimativa de Esforco para Completar a Especificacao

| Item | Complexidade | Linhas Estimadas | Testes Novos |
|------|:-----------:|:----------------:|:------------:|
| Enriquecimento CNES (leitos/prof/servicos) | Baixa | ~200 | ~15 |
| Subagente LangChain + endpoint /analyze | Media | ~200 | ~15 |
| Cliente DATASUS (SIH + SIM) | Media-Alta | ~500 | ~30 |
| Analise vazios assistenciais | Media | ~250 | ~15 |
| Cobertura ESF (e-SUS APS) | Media | ~200 | ~15 |
| **TOTAL** | — | **~1.350** | **~90** |

---

## Score de Maturidade

| Dimensao | Score | Notas |
|----------|:-----:|-------|
| Qualidade do codigo v1.0 | 9/10 | 95% cov, sem debito tecnico |
| Cobertura da especificacao funcional | 3/10 | CNES OK, DATASUS ausente, planejamento ausente |
| Integracao com ecossistema (Wanda) | 2/10 | Sem `/analyze`, sem subagente |
| Valor para o clinico | 4/10 | Busca de unidades funciona, indicadores nao |
| Infraestrutura | 8/10 | Docker, config, graceful degradation |
| **Maturidade geral** | **5/10** | Base excelente, funcionalidade incompleta |

---

## Proximos Passos Recomendados (Ordem de Prioridade)

1. **[URGENTE]** Criar `zilda/subagent/zilda_subagent.py` + endpoint `/api/v1/analyze` para Wanda conseguir usar a Zilda
2. **[ALTA]** Adicionar leitos/profissionais/servicos ao `cnes_client.py` — dados disponiveis na API publica
3. **[ALTA]** Iniciar `datasus_client.py` com foco em SIH (internacoes por municipio)
4. **[MEDIA]** Motor de vazios assistenciais (populacao vs leitos)
5. **[BAIXA]** UI Streamlit para equipe de gestao visualizar mapas de cobertura
