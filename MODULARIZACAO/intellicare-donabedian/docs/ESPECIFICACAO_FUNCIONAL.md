# intellicare-donabedian v1.0.0 — Especificacao Funcional

> **Para:** DEV1
> **De:** Arquitetura IntelliCare
> **Data:** 2026-02-08
> **Workflow:** DEV1 le esta spec funcional → escreve spec tecnica → revisamos → implementa

---

> Homenagem a Avedis Donabedian (1919-2000), medico libanes-americano considerado o pai da garantia da qualidade em saude. Criou a triade Estrutura-Processo-Resultado e os 7 pilares da qualidade que sao referencia mundial ate hoje.

---

## 1. O Que E o Donabedian

O intellicare-donabedian e um **modulo independente** de avaliacao da qualidade assistencial em saude. Ele permite que gestores e equipes de qualidade monitorem, avaliem e melhorem os servicos de saude usando frameworks consagrados da literatura.

**Publico-alvo:** Gestores de qualidade, diretores clinicos, gestores municipais de saude.

**Entregavel:** Um sistema que roda sozinho (`docker compose up`) com dashboard visual e API REST.

---

## 2. Framework Teorico (O DEV1 Precisa Entender Isso)

### 2.1 A Triade de Donabedian

Donabedian propoe que a qualidade em saude seja avaliada em 3 dimensoes:

```
ESTRUTURA → PROCESSO → RESULTADO
(O que se tem)  (O que se faz)  (O que se obtem)
```

**Estrutura:** Os recursos disponiveis — instalacoes fisicas, equipamentos, profissionais qualificados, protocolos escritos, sistemas de informacao.

**Processo:** As atividades realizadas — consultas, procedimentos, prescricoes, adesao a protocolos, tempo de atendimento, encaminhamentos.

**Resultado:** Os desfechos obtidos — mortalidade, reinternacao, satisfacao do paciente, melhora clinica, infeccoes hospitalares.

**Relacao:** Uma boa Estrutura favorece bons Processos, que levam a bons Resultados. Mas nao e automatico — por isso se mede as 3 dimensoes.

### 2.2 Os 7 Pilares da Qualidade

Donabedian definiu 7 atributos que juntos formam a qualidade em saude:

| # | Pilar | Pergunta-chave | Exemplo de Indicador |
|:-:|-------|----------------|---------------------|
| 1 | **Eficacia** | O cuidado funciona em condicoes ideais? | Taxa de cura de pneumonia com tratamento padrao |
| 2 | **Efetividade** | O cuidado funciona na pratica? | Taxa real de controle pressorico na populacao |
| 3 | **Eficiencia** | Usa bem os recursos? | Custo por internacao, tempo medio de permanencia |
| 4 | **Otimidade** | O custo-beneficio e adequado? | QALY (Quality-Adjusted Life Year) por real investido |
| 5 | **Aceitabilidade** | O paciente aceita e adere? | Taxa de abandono de tratamento, satisfacao pesquisa |
| 6 | **Legitimidade** | Atende expectativas da sociedade? | Cobertura vacinal, equipes de ESF por habitante |
| 7 | **Equidade** | O acesso e justo para todos? | Diferenca de mortalidade entre regioes, raca, renda |

### 2.3 Indicadores Brasileiros (Contexto SUS)

O Donabedian vai trabalhar com indicadores do contexto brasileiro:

**PMAQ (Programa de Melhoria do Acesso e da Qualidade):**
- Avalia equipes de Atencao Basica
- Indicadores: cobertura, resolubilidade, satisfacao
- Ciclos de avaliacao com certificacao

**IQASUS (Indicadores de Qualidade da Assistencia SUS):**
- Indicadores hospitalares padronizados
- Taxa de infeccao hospitalar
- Taxa de mortalidade por grupo de causas
- Taxa de reinternacao em 30 dias
- Tempo medio de permanencia

**Indicadores Hospitalares Gerais:**
- Taxa de ocupacao de leitos
- Giro de leitos
- Taxa de cesarea
- Taxa de infeccao de sitio cirurgico
- Mortalidade por infarto (porta-balao < 90min)

---

## 3. Funcionalidades Esperadas na v1.0.0

### 3.1 Avaliacao por Triade

O sistema deve permitir que o gestor cadastre e avalie indicadores organizados nas 3 dimensoes:

**Entrada:** Indicadores numericos com meta, valor atual, periodo.

**Saida:** Score de cada dimensao (0-100), status visual (semaforo: verde/amarelo/vermelho), tendencia (melhorando/estavel/piorando).

**Exemplo:**
```
ESTRUTURA
  |- Profissionais por leito: 2.3 (meta: 2.5) -> Amarelo
  |- Protocolos atualizados: 85% (meta: 90%) -> Amarelo
  '- Equipamentos calibrados: 98% (meta: 95%) -> Verde

PROCESSO
  |- Adesao ao checklist cirurgico: 92% (meta: 95%) -> Amarelo
  |- Tempo porta-balao: 78min (meta: 90min) -> Verde
  '- Alta programada: 65% (meta: 70%) -> Amarelo

RESULTADO
  |- Mortalidade geral: 3.2% (meta: <4%) -> Verde
  |- Reinternacao 30d: 12% (meta: <10%) -> Vermelho
  '- Satisfacao paciente: 82% (meta: 85%) -> Amarelo
```

### 3.2 Avaliacao por Pilares

Para cada pilar, o sistema calcula um score baseado nos indicadores associados.

**Entrada:** Mapeamento de indicadores para pilares (um indicador pode pertencer a mais de um pilar).

**Saida:** Score de cada pilar (0-100), radar chart dos 7 pilares, recomendacoes de melhoria.

**Exemplo de radar:**
```
        Eficacia (85)
           /\
          /  \
Equidade /    \ Efetividade
  (60)  /      \  (78)
       /        \
      /          \
     Legitimidade  Eficiencia
       (72)         (68)
      \          /
       \        /
 Aceitabilidade  Otimidade
     (80)         (55)
```

### 3.3 Dashboard de Qualidade

Tela principal com:

1. **Resumo executivo** — Score geral + semaforo + tendencia
2. **Triade** — 3 cards (Estrutura, Processo, Resultado) com scores
3. **Radar dos 7 pilares** — Grafico radar interativo
4. **Timeline** — Evolucao dos indicadores nos ultimos 12 meses
5. **Alertas** — Indicadores abaixo da meta ou em tendencia negativa
6. **Benchmarking** — Comparacao com media regional/nacional (quando disponivel)

### 3.4 Gestao de Indicadores

- CRUD de indicadores (nome, descricao, formula, meta, pilar, dimensao da triade)
- Importacao de dados (CSV, JSON, ou entrada manual)
- Periodos: mensal, trimestral, semestral, anual
- Historico completo com versao

### 3.5 Relatorios

- Relatorio PDF/HTML para gestores
- Comparativo entre periodos
- Recomendacoes automatizadas baseadas nos gaps

### 3.6 API REST (Contrato IntelliCare)

O modulo DEVE expor:
```
GET  /api/v1/health              -> Status do modulo
GET  /api/v1/info                -> Nome, versao, capabilities
POST /api/v1/assess              -> Avaliacao completa (triade + pilares)
GET  /api/v1/indicators          -> Lista de indicadores cadastrados
GET  /api/v1/indicators/{id}     -> Detalhe de um indicador
POST /api/v1/indicators          -> Cadastrar indicador
PUT  /api/v1/indicators/{id}     -> Atualizar indicador
GET  /api/v1/dashboard           -> Dados consolidados para o dashboard
GET  /api/v1/trends/{indicator}  -> Tendencia de um indicador
```

---

## 4. Dados de Entrada (De Onde Vem)

Na v1.0.0, os dados entram por:
1. **Entrada manual** via dashboard (formulario)
2. **Importacao CSV** (template padrao fornecido)
3. **API REST** (para integracoes futuras)

**NAO precisa** na v1.0.0:
- Integracao direta com FHIR Server
- Integracao com DATASUS
- Integracao com outros modulos IntelliCare

Essas integracoes virao nas versoes futuras (v1.1+).

---

## 5. Requisitos Nao-Funcionais

| Requisito | Especificacao |
|-----------|--------------|
| Linguagem | Python 3.11+ |
| API | FastAPI |
| UI | Streamlit |
| Banco de dados | PostgreSQL (via SQLAlchemy 2.0) |
| Container | Docker + docker-compose |
| Testes | pytest, cobertura >= 80% |
| Startup | `docker compose up` funcional em < 2 min |
| Linting | ruff |
| Tipos | mypy (strict) |

### Portas
- API REST: **8003** (para nao conflitar com outros modulos)
- Streamlit: **8503**
- PostgreSQL: **5433** (mapeamento externo)

---

## 6. Dados Seed (Para Demonstracao)

O modulo deve vir com dados de demonstracao para que possamos testar:

**Cenario seed:** Hospital Regional Ficticio — 12 meses de indicadores

Indicadores seed (minimo 15):
- Taxa de infeccao hospitalar (mensal)
- Taxa de mortalidade geral (mensal)
- Taxa de reinternacao em 30 dias (mensal)
- Tempo medio de permanencia (mensal)
- Taxa de ocupacao de leitos (mensal)
- Satisfacao do paciente (trimestral)
- Adesao ao checklist cirurgico (mensal)
- Profissionais por leito (trimestral)
- Protocolos atualizados (semestral)
- Taxa de cesarea (mensal)
- Tempo porta-balao IAM (mensal)
- Cobertura vacinal (trimestral)
- Taxa de abandono de tratamento (mensal)
- Giro de leitos (mensal)
- Equipamentos calibrados (semestral)

Cada indicador com 12 pontos de dados (simulando 1 ano).

---

## 7. O Que NAO Faz Parte da v1.0.0

Para manter o escopo controlado:

- Integracao com FHIR Server
- Integracao com outros modulos IntelliCare
- Integracao com DATASUS/PMAQ automatica
- Machine Learning para predicao de indicadores
- Autenticacao/autorizacao (Keycloak)
- Multi-tenancy (multiplos hospitais)

Tudo isso e roadmap para v1.1+.

---

## 8. Criterios de Aceite (Quando Consideramos Pronto)

- [ ] `docker compose up` sobe o modulo em < 2 min
- [ ] Dashboard Streamlit acessivel com dados seed
- [ ] API REST respondendo nos endpoints listados
- [ ] Radar dos 7 pilares renderizando corretamente
- [ ] Triade com semaforos funcionando
- [ ] Timeline de indicadores com 12 meses
- [ ] Pelo menos 15 indicadores seed carregados
- [ ] Testes automatizados >= 80% cobertura
- [ ] Funciona SEM nenhum outro modulo IntelliCare instalado
- [ ] README com instrucoes de setup em 15 minutos

---

## 9. Referencia Bibliografica para o DEV1

O DEV1 DEVE ler antes de comecar a spec tecnica:

1. **Donabedian, A.** "The Definition of Quality and Approaches to Its Assessment" (1980)
   - Conceito da triade Estrutura-Processo-Resultado

2. **Donabedian, A.** "The Seven Pillars of Quality" (1990)
   - Artigo que define os 7 atributos da qualidade

3. **Resumo acessivel:** https://blogdaqualidade.com.br/saude-os-7-pilares-da-qualidade-de-avedis-donabedian/

4. **IQASUS:** Consultar indicadores padrao do MS/DATASUS

---

## 10. Proximo Passo do DEV1

Apos ler esta especificacao funcional:

1. Estudar o framework de Donabedian (referencia na secao 9)
2. Escrever a **Especificacao Tecnica** em `docs/ESPECIFICACAO_TECNICA.md`
   - Estrutura de diretorios proposta
   - Modelos de dados (tabelas, schemas Pydantic)
   - Arquitetura da API (rotas, payloads, responses)
   - Componentes do dashboard Streamlit
   - Estrategia de testes
3. Submeter para revisao ANTES de comecar a implementar
4. Apos aprovacao, implementar e registrar progresso em `steps/`
