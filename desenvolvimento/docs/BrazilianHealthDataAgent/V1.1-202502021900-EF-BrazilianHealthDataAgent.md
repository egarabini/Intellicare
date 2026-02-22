# Especificação Funcional - Brazilian Health Data Agent
**Projeto:** IntelliCare - Portal de Agentes Inteligentes em Saúde Pública  
**Versão:** 1.0  
**Data:** 2025-02-02  
**Autor:** Equipe IntelliCare  
**Status:** 📋 Em Planejamento

---

## 1. VISÃO GERAL

### 1.1 Objetivo
Criar um agente especializado em consultar dados públicos de saúde brasileiros através das APIs oficiais do Ministério da Saúde, IBGE e outras fontes governamentais, integrando-o ao ecossistema IntelliCare.

### 1.2 Contexto
O IntelliCare é uma plataforma de agentes de IA para saúde pública. Este novo agente complementará o sistema existente fornecendo acesso a dados oficiais brasileiros em tempo real, permitindo análises baseadas em informações governamentais atualizadas.

### 1.3 Escopo
**Incluído:**
- Integração com API de Dados Abertos do Ministério da Saúde
- Consulta de estabelecimentos de saúde (CNES)
- Consulta de tipos de unidades de saúde
- Consulta de municípios com macrorregiões e regiões de saúde
- Cache inteligente de dados
- Tratamento de erros e fallbacks
- Documentação completa

**Não Incluído (Futuro):**
- Integração com DATASUS (SIH, SIA, SINAN)
- Análise preditiva de dados
- Dashboard de visualização
- Exportação de relatórios

---

## 2. REQUISITOS FUNCIONAIS

### RF01 - Consulta de Tipos de Unidades de Saúde
**Prioridade:** Alta  
**Descrição:** O sistema deve permitir consultar todos os tipos de unidades de saúde cadastrados no CNES.

**Critérios de Aceitação:**
- ✅ Retornar lista completa de tipos de unidade
- ✅ Incluir código e descrição de cada tipo
- ✅ Permitir busca por código específico
- ✅ Tempo de resposta < 3 segundos
- ✅ Cache de 24 horas (dados raramente mudam)

**Exemplo de Uso:**
```
Usuário: "Quais são os tipos de unidades de saúde disponíveis?"
Agente: Retorna lista com 80+ tipos (Posto de Saúde, UPA, Hospital, etc.)
```

### RF02 - Consulta de Estabelecimentos de Saúde
**Prioridade:** Alta  
**Descrição:** O sistema deve permitir buscar estabelecimentos de saúde com filtros avançados.

**Critérios de Aceitação:**
- ✅ Filtrar por UF (código do estado)
- ✅ Filtrar por município (código IBGE)
- ✅ Filtrar por tipo de unidade
- ✅ Filtrar por status (ativo/inativo)
- ✅ Filtrar por recursos (centro cirúrgico, obstétrico, etc.)
- ✅ Paginação (limit/offset)
- ✅ Retornar dados completos (CNES, CNPJ, endereço, telefone, etc.)
- ✅ Tempo de resposta < 5 segundos

**Filtros Disponíveis:**
| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| codigo_uf | integer | Código do estado | 27 (Alagoas) |
| codigo_municipio | integer | Código IBGE do município | 270850 |
| codigo_tipo_unidade | integer | Tipo de unidade | 1 (Posto de Saúde) |
| status | integer | 1=Ativo, 0=Inativo | 1 |
| estabelecimento_possui_centro_cirurgico | integer | 1=Sim, 0=Não | 1 |
| estabelecimento_possui_centro_obstetrico | integer | 1=Sim, 0=Não | 1 |
| data_atualizacao | string | Data YYYY-MM-DD | 2025-01-01 |
| limit | integer | Itens por página (max 100) | 100 |
| offset | integer | Página (inicia em 0) | 0 |

**Exemplo de Uso:**
```
Usuário: "Quantos hospitais ativos existem em Alagoas com centro cirúrgico?"
Agente: Consulta API com filtros e retorna lista + contagem
```

### RF03 - Consulta de Municípios com Regiões de Saúde
**Prioridade:** Alta  
**Descrição:** O sistema deve permitir consultar municípios brasileiros com informações de macrorregião e região de saúde.

**Critérios de Aceitação:**
- ✅ Buscar por nome do município
- ✅ Filtrar por UF (sigla)
- ✅ Filtrar por código de região de saúde
- ✅ Filtrar por macrorregião de saúde
- ✅ Retornar população estimada (IBGE 2022)
- ✅ Paginação (limit/offset)
- ✅ Tempo de resposta < 3 segundos

**Dados Retornados:**
- Código e nome do município
- UF (código e sigla)
- Região do país
- Macrorregião de saúde (código e nome)
- Região de saúde (código e nome)
- População estimada IBGE 2022

**Exemplo de Uso:**
```
Usuário: "Qual a macrorregião de saúde de Serra/ES?"
Agente: Retorna "METROPOLITANA" com código 3207
```

---

## 3. REQUISITOS NÃO FUNCIONAIS

### RNF01 - Performance
- Tempo de resposta médio: < 3 segundos
- Timeout de API: 10 segundos
- Cache de dados estáticos: 24 horas
- Cache de dados dinâmicos: 1 hora

### RNF02 - Disponibilidade
- Uptime esperado: 99.5% (dependente das APIs governamentais)
- Fallback para cache em caso de indisponibilidade
- Retry automático (3 tentativas com backoff exponencial)

### RNF03 - Segurança
- Validação de todos os parâmetros de entrada
- Sanitização de dados antes de retornar
- Prevenção de injection attacks (SQL, NoSQL, Command)
- Logs de auditoria de todas as consultas
- **Nota:** Rate limiting será implementado em versão futura

### RNF04 - Escalabilidade
- Suportar 1000 requisições simultâneas
- Cache distribuído (Redis)
- Processamento assíncrono

### RNF05 - Manutenibilidade
- Código documentado (docstrings)
- Testes unitários (cobertura > 80%)
- Testes de integração com APIs
- Logs estruturados (JSON)

---

## 4. REGRAS DE NEGÓCIO

### RN01 - Cache Inteligente
- Tipos de unidade: cache de 7 dias (dados estáticos)
- Estabelecimentos: cache de 1 hora (dados dinâmicos)
- Municípios: cache de 7 dias (dados estáticos)
- Invalidar cache manualmente via admin quando necessário

### RN02 - Tratamento de Erros
- API indisponível: retornar dados do cache
- Timeout: retry 3x com backoff (1s, 2s, 4s)
- Dados inválidos: retornar erro descritivo
- Rate limit excedido: aguardar e tentar novamente

### RN03 - Paginação
- Limite máximo: 100 itens por página
- Padrão: 20 itens por página
- Offset inicia em 0
- Retornar total de registros no header

### RN04 - Validação de Parâmetros
- Código UF: 11-53 (códigos IBGE válidos)
- Código município: 6-7 dígitos
- Código tipo unidade: 1-99
- Data: formato YYYY-MM-DD
- Limit: 1-100
- Offset: >= 0

---

## 5. CASOS DE USO

### UC01 - Listar Tipos de Unidades
**Ator:** Gestor de Saúde  
**Pré-condições:** Usuário autenticado  
**Fluxo Principal:**
1. Usuário solicita lista de tipos de unidades
2. Sistema consulta API ou cache
3. Sistema retorna lista ordenada por código
4. Sistema exibe descrições formatadas

**Fluxo Alternativo:**
- API indisponível: retorna dados do cache
- Cache vazio: retorna erro amigável

### UC02 - Buscar Estabelecimentos por Região
**Ator:** Analista de Saúde Pública  
**Pré-condições:** Usuário autenticado  
**Fluxo Principal:**
1. Usuário especifica UF e/ou município
2. Usuário aplica filtros opcionais (tipo, status, recursos)
3. Sistema valida parâmetros
4. Sistema consulta API com paginação
5. Sistema retorna lista de estabelecimentos
6. Sistema exibe total de resultados

**Fluxo Alternativo:**
- Nenhum resultado: retorna mensagem informativa
- Muitos resultados: sugere refinar filtros

### UC03 - Consultar Região de Saúde de Município
**Ator:** Coordenador Regional  
**Pré-condições:** Usuário autenticado  
**Fluxo Principal:**
1. Usuário informa nome do município e UF
2. Sistema busca na API
3. Sistema retorna dados de região e macrorregião
4. Sistema exibe população estimada

**Fluxo Alternativo:**
- Múltiplos municípios com mesmo nome: lista todos com UF
- Município não encontrado: sugere nomes similares

---

## 6. INTERFACE DO AGENTE

### 6.1 Formato de Requisição
```json
{
  "action": "get_health_units_types",
  "params": {}
}
```

```json
{
  "action": "search_establishments",
  "params": {
    "codigo_uf": 27,
    "codigo_tipo_unidade": 1,
    "status": 1,
    "limit": 50,
    "offset": 0
  }
}
```

### 6.2 Formato de Resposta
```json
{
  "success": true,
  "data": {
    "tipos_unidade": [
      {
        "codigo_tipo_unidade": 1,
        "descricao_tipo_unidade": "POSTO DE SAUDE"
      }
    ]
  },
  "metadata": {
    "source": "API Dados Abertos Saúde",
    "cached": false,
    "timestamp": "2025-02-02T19:00:00Z",
    "total_records": 80
  }
}
```

---

## 7. MÉTRICAS DE SUCESSO

### 7.1 KPIs
- **Taxa de sucesso:** > 95% das requisições
- **Tempo médio de resposta:** < 3 segundos
- **Taxa de cache hit:** > 70%
- **Uptime:** > 99%

### 7.2 Monitoramento
- Logs de todas as requisições
- Alertas para APIs indisponíveis
- Dashboard de métricas em tempo real
- Relatório semanal de uso

---

## 8. CRONOGRAMA ESTIMADO

| Fase | Atividade | Duração | Responsável |
|------|-----------|---------|-------------|
| 1 | Análise e Design | 2 dias | Arquiteto |
| 2 | Desenvolvimento Core | 3 dias | Dev Backend |
| 3 | Integração APIs | 2 dias | Dev Backend |
| 4 | Testes Unitários | 1 dia | QA |
| 5 | Testes Integração | 1 dia | QA |
| 6 | Documentação | 1 dia | Tech Writer |
| 7 | Deploy e Validação | 1 dia | DevOps |
| **TOTAL** | | **11 dias** | |

---

## 9. DEPENDÊNCIAS

### 9.1 APIs Externas
- ✅ API Dados Abertos Saúde (https://apidadosabertos.saude.gov.br)
- ✅ Sem autenticação necessária (APIs públicas)
- ⚠️ Rate limit: não documentado oficialmente
- ⚠️ **IMPORTANTE:** Validar URLs antes de iniciar desenvolvimento:
  - `/cnes/tipounidades`
  - `/cnes/estabelecimentos`
  - `/macrorregiao-e-regiao-de-saude/municipio`

### 9.2 Infraestrutura
- Redis para cache
- PostgreSQL para logs
- FastAPI backend
- Docker para deploy

---

## 10. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| API gov indisponível | Média | Alto | Cache robusto + fallback |
| Mudança de schema API | Baixa | Alto | Versionamento + testes |
| Rate limiting | Média | Médio | Cache agressivo + retry |
| Dados desatualizados | Baixa | Baixo | Validação de timestamps |

---

## 11. APROVAÇÕES

| Papel | Nome | Data | Assinatura |
|-------|------|------|------------|
| Product Owner | | | |
| Tech Lead | | | |
| Arquiteto | | | |

---

**Próximo Passo:** Especificação Técnica Detalhada (ET)

