# 🎨 SPRINT SEMANA 2 - INTERFACE WEB (UI)

**Período**: 24-28 Fevereiro 2026 (5 dias)  
**Objetivo**: Criar interface web para visualização e interação com Florence  
**Status**: 🟢 PRONTO PARA INICIAR

---

## 🎯 OBJETIVOS DA SEMANA

1. ✅ Dashboard de análises clínicas (Streamlit)
2. ✅ Visualização de tendências e gráficos
3. ✅ Interface de consulta RAG
4. ✅ Exportação de relatórios (PDF/Excel)

---

## 📊 CONTEXTO

### O que já existe

**Semana 1 (Completa)**:
- ✅ 10 endpoints API (7 core + 3 RAG)
- ✅ 396 testes (330% da meta)
- ✅ 10 protocolos clínicos indexados
- ✅ Documentação completa (2.450 linhas)

### Referências de UI no IntelliCare

**Donabedian Dashboard** (Streamlit):
- `intellicare-donabedian/src/donabedian/dashboard/`
- Multi-page app com navegação
- Gráficos Plotly
- Filtros interativos
- Cache de dados

**Portal IntelliCare** (React):
- `intellicare-portal/frontend/`
- React 19 + TypeScript + Vite
- Tailwind CSS 4
- Recharts para gráficos
- React Router 7

### Decisão de Stack

**Escolha**: **Streamlit** (como Donabedian)

**Razão**:
- ✅ Rápido desenvolvimento (5 dias)
- ✅ Integração nativa com Python
- ✅ Já usado no ecossistema IntelliCare
- ✅ Ideal para dashboards analíticos
- ✅ Menos complexidade (sem build frontend)

---

## 📅 DIA 1: Setup + Dashboard Principal (24 FEV)

### Objetivo
Criar estrutura base e dashboard principal

### Tarefas

#### Task 1.1: Estrutura de Diretórios
```bash
florence/ui/
├── __init__.py
├── main.py                    # App principal
├── config.py                  # Configurações UI
├── pages/
│   ├── 1_🏠_Home.py          # Dashboard principal
│   ├── 2_🔬_Analise.py       # Análise de exames
│   ├── 3_📈_Tendencias.py    # Visualização de tendências
│   ├── 4_🤖_RAG.py           # Consulta RAG
│   └── 5_📄_Relatorios.py    # Exportação
├── components/
│   ├── __init__.py
│   ├── charts.py              # Gráficos reutilizáveis
│   ├── filters.py             # Filtros de sidebar
│   ├── metrics.py             # Cards de métricas
│   └── tables.py              # Tabelas formatadas
└── utils/
    ├── __init__.py
    ├── api_client.py          # Cliente API Florence
    ├── cache.py               # Cache de dados
    └── formatters.py          # Formatação de dados
```

#### Task 1.2: Dependências
**Arquivo**: `pyproject.toml`

```toml
[project.optional-dependencies]
ui = [
    "streamlit>=1.31.0",
    "plotly>=5.18.0",
    "pandas>=2.1.0",
    "openpyxl>=3.1.0",      # Excel export
    "reportlab>=4.0.0",      # PDF export
    "python-dateutil>=2.8.0",
]
```

#### Task 1.3: App Principal
**Arquivo**: `florence/ui/main.py`

**Conteúdo**:
- Configuração da página
- Sidebar com navegação
- Logo e título
- Informações do módulo
- Links para documentação

#### Task 1.4: API Client
**Arquivo**: `florence/ui/utils/api_client.py`

**Métodos**:
- `get_health()` - Health check
- `get_info()` - Informações do módulo
- `interpret_labs()` - Interpretação de exames
- `analyze_labs()` - Análise completa
- `analyze_with_rag()` - Análise com RAG
- `query_rag()` - Query direta RAG
- `get_protocols()` - Listar protocolos

#### Task 1.5: Dashboard Home
**Arquivo**: `florence/ui/pages/1_🏠_Home.py`

**Seções**:
1. KPIs principais (cards)
   - Total de análises
   - Exames críticos
   - Protocolos disponíveis
   - Tempo médio de resposta
2. Gráfico de análises por dia (últimos 30 dias)
3. Distribuição de status (normal/anormal/crítico)
4. Top 5 exames mais solicitados

### Entregáveis Dia 1
- ✅ Estrutura de diretórios criada
- ✅ Dependências instaladas
- ✅ App principal funcionando
- ✅ API client implementado
- ✅ Dashboard Home com KPIs

---

## 📅 DIA 2: Página de Análise (25 FEV)

### Objetivo
Criar interface para análise de exames

### Tarefas

#### Task 2.1: Formulário de Entrada
**Arquivo**: `florence/ui/pages/2_🔬_Analise.py`

**Componentes**:
1. Input de Patient ID
2. Seleção de exames (multiselect)
3. Input de valores (number_input dinâmico)
4. Botão "Analisar"
5. Opção "Incluir RAG" (checkbox)

#### Task 2.2: Exibição de Resultados
**Seções**:
1. **Interpretações**
   - Tabela com exame, valor, status, referência
   - Colorização por status (verde/amarelo/vermelho)
2. **Correlações Detectadas**
   - Cards com padrões clínicos
   - Descrição e significância
3. **Protocolos Relevantes** (se RAG ativado)
   - Lista de protocolos
   - Score de relevância
   - Link para visualizar protocolo completo

#### Task 2.3: Gráficos de Análise
**Componentes**:
- Gráfico de barras: valores vs referência
- Gauge charts para exames críticos
- Radar chart para painéis completos

#### Task 2.4: Histórico de Análises
**Funcionalidade**:
- Salvar análises em session_state
- Exibir histórico em expander
- Comparar análises anteriores

### Entregáveis Dia 2
- ✅ Formulário de análise funcionando
- ✅ Exibição de resultados formatada
- ✅ Gráficos de análise
- ✅ Histórico de análises

---

## 📅 DIA 3: Visualização de Tendências (26 FEV)

### Objetivo
Criar interface para análise de tendências temporais

### Tarefas

#### Task 3.1: Input de Dados Temporais
**Arquivo**: `florence/ui/pages/3_📈_Tendencias.py`

**Componentes**:
1. Upload de CSV/Excel com dados históricos
2. Template de arquivo para download
3. Validação de formato
4. Preview dos dados

#### Task 3.2: Seleção de Exames
**Funcionalidade**:
- Multiselect de exames para análise
- Filtro de período (date_range)
- Opções de agregação (diário/semanal/mensal)

#### Task 3.3: Gráficos de Tendências
**Visualizações**:
1. **Line Chart**: Evolução temporal
   - Múltiplos exames no mesmo gráfico
   - Faixas de referência (área sombreada)
   - Linha de tendência (regressão linear)
2. **Heatmap**: Correlação entre exames
3. **Box Plot**: Distribuição por período

#### Task 3.4: Análise de Tendências
**Funcionalidade**:
- Chamar `/api/v1/analyze-trends`
- Exibir tendências detectadas
- Alertas de piora/melhora
- Previsão de próximos valores

### Entregáveis Dia 3
- ✅ Upload de dados históricos
- ✅ Gráficos de tendências
- ✅ Análise de tendências
- ✅ Alertas e previsões

---

## 📅 DIA 4: Interface RAG + Exportação (27 FEV)

### Objetivo
Criar interface de consulta RAG e exportação de relatórios

### Tarefas

#### Task 4.1: Interface de Consulta RAG
**Arquivo**: `florence/ui/pages/4_🤖_RAG.py`

**Seções**:
1. **Query Manual**
   - Text area para query
   - Slider para top_k (1-10)
   - Botão "Buscar Protocolos"

2. **Protocolos Disponíveis**
   - Lista de 10 protocolos
   - Filtro por especialidade
   - Busca por palavra-chave

3. **Resultados da Busca**
   - Cards com protocolos relevantes
   - Score de relevância (progress bar)
   - Conteúdo do protocolo (expander)
   - Chunks relevantes destacados

#### Task 4.2: Visualização de Protocolos
**Componentes**:
- Markdown rendering do protocolo completo
- Tabela de conteúdo (TOC)
- Navegação entre seções
- Download do protocolo (MD/PDF)

#### Task 4.3: Exportação de Relatórios
**Arquivo**: `florence/ui/pages/5_📄_Relatorios.py`

**Funcionalidades**:
1. **Seleção de Dados**
   - Escolher análises do histórico
   - Filtro por período
   - Filtro por paciente

2. **Formato de Exportação**
   - Excel (.xlsx)
   - PDF (relatório formatado)
   - JSON (dados brutos)

3. **Conteúdo do Relatório**
   - Cabeçalho com logo e data
   - Sumário executivo
   - Tabela de interpretações
   - Gráficos de tendências
   - Correlações detectadas
   - Protocolos relevantes (se RAG)
   - Rodapé com disclaimers

#### Task 4.4: Geração de PDF
**Arquivo**: `florence/ui/utils/pdf_generator.py`

**Métodos**:
- `generate_analysis_report()` - Relatório de análise
- `generate_trend_report()` - Relatório de tendências
- `generate_protocol_report()` - Relatório de protocolo
- `add_header()`, `add_footer()`, `add_chart()`

### Entregáveis Dia 4
- ✅ Interface RAG funcionando
- ✅ Visualização de protocolos
- ✅ Exportação Excel
- ✅ Exportação PDF

---

## 📅 DIA 5: Polimento + Testes + Documentação (28 FEV)

### Objetivo
Finalizar UI, testar e documentar

### Tarefas

#### Task 5.1: Componentes Reutilizáveis
**Arquivo**: `florence/ui/components/`

**Criar**:
1. **charts.py**
   - `create_lab_bar_chart()` - Gráfico de barras de exames
   - `create_trend_line_chart()` - Gráfico de linha de tendências
   - `create_correlation_heatmap()` - Heatmap de correlações
   - `create_status_pie_chart()` - Pizza de distribuição de status
   - `create_gauge_chart()` - Gauge para valores críticos

2. **filters.py**
   - `period_filter()` - Filtro de período
   - `patient_filter()` - Filtro de paciente
   - `exam_filter()` - Filtro de exames
   - `status_filter()` - Filtro de status

3. **metrics.py**
   - `metric_card()` - Card de métrica
   - `kpi_row()` - Linha de KPIs
   - `status_badge()` - Badge de status

4. **tables.py**
   - `interpretation_table()` - Tabela de interpretações
   - `correlation_table()` - Tabela de correlações
   - `protocol_table()` - Tabela de protocolos

#### Task 5.2: Testes da UI
**Arquivo**: `tests/test_ui_components.py`

**Testes**:
- Teste de API client (mock)
- Teste de formatadores
- Teste de geração de PDF
- Teste de cache

#### Task 5.3: Configuração e Deploy
**Arquivo**: `florence/ui/config.py`

**Configurações**:
```python
API_BASE_URL = "http://localhost:8002"
PAGE_TITLE = "Florence - Análise Clínica"
PAGE_ICON = "🏥"
LAYOUT = "wide"
CACHE_TTL = 300  # 5 minutos
MAX_UPLOAD_SIZE = 10  # MB
```

**Arquivo**: `.streamlit/config.toml`
```toml
[theme]
primaryColor = "#0066cc"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8502
headless = true
enableCORS = false
```

#### Task 5.4: Documentação da UI
**Arquivo**: `docs/GUIA_UI_FLORENCE.md`

**Conteúdo**:
1. Instalação e setup
2. Como executar
3. Guia de uso (screenshots)
4. Funcionalidades principais
5. Troubleshooting
6. FAQ

#### Task 5.5: Atualizar README
**Arquivo**: `README.md`

**Adicionar**:
- Seção "Interface Web (UI)"
- Como executar UI
- Screenshots
- Link para GUIA_UI_FLORENCE.md

#### Task 5.6: Docker para UI
**Arquivo**: `docker-compose.yml`

**Adicionar serviço**:
```yaml
services:
  florence-ui:
    build:
      context: .
      target: ui
    ports:
      - "8502:8502"
    environment:
      - FLORENCE_API_URL=http://florence-api:8002
    depends_on:
      - florence-api
```

### Entregáveis Dia 5
- ✅ Componentes reutilizáveis
- ✅ Testes da UI
- ✅ Configuração completa
- ✅ Documentação da UI
- ✅ Docker para UI
- ✅ README atualizado

---

## 📊 MÉTRICAS DE SUCESSO DA SEMANA 2

**Ao final da Semana 2**:
- ✅ 5 páginas Streamlit funcionais
- ✅ 10+ componentes reutilizáveis
- ✅ 3 formatos de exportação (Excel, PDF, JSON)
- ✅ Integração completa com API Florence
- ✅ Documentação completa da UI
- ✅ Docker compose funcionando
- ✅ Pronto para demonstração

---

## 🎨 DESIGN GUIDELINES

### Cores

**Status**:
- 🟢 Normal: `#28a745` (verde)
- 🟡 Borderline: `#ffc107` (amarelo)
- 🔴 Anormal: `#dc3545` (vermelho)
- ⚫ Crítico: `#6c757d` (cinza escuro)

**Tema**:
- Primary: `#0066cc` (azul IntelliCare)
- Secondary: `#6c757d` (cinza)
- Background: `#ffffff` (branco)
- Text: `#262730` (quase preto)

### Tipografia

- **Títulos**: Sans-serif, bold
- **Corpo**: Sans-serif, regular
- **Código**: Monospace

### Layout

- **Sidebar**: Navegação + filtros
- **Main**: Conteúdo principal (wide layout)
- **Cards**: Métricas e KPIs
- **Gráficos**: Plotly (interativos)

---

## 🔧 STACK TECNOLÓGICA

### Frontend
- **Streamlit 1.31+**: Framework UI
- **Plotly 5.18+**: Gráficos interativos
- **Pandas 2.1+**: Manipulação de dados

### Exportação
- **openpyxl 3.1+**: Excel export
- **reportlab 4.0+**: PDF generation

### Backend
- **Florence API**: 10 endpoints REST
- **FastAPI**: Framework backend

---

## 📚 REFERÊNCIAS

### Donabedian Dashboard
- `intellicare-donabedian/src/donabedian/dashboard/`
- Multi-page structure
- Plotly charts
- API client pattern
- Cache strategy

### Streamlit Docs
- https://docs.streamlit.io/
- Multi-page apps
- Components
- Caching

---

## ✅ CHECKLIST FINAL

### Funcionalidades
- [ ] Dashboard Home com KPIs
- [ ] Análise de exames (formulário + resultados)
- [ ] Visualização de tendências (gráficos + análise)
- [ ] Interface RAG (query + protocolos)
- [ ] Exportação de relatórios (Excel + PDF)

### Componentes
- [ ] API client
- [ ] Charts (5+ tipos)
- [ ] Filters (4+ tipos)
- [ ] Metrics cards
- [ ] Tables formatadas

### Qualidade
- [ ] Testes da UI
- [ ] Documentação completa
- [ ] Docker funcionando
- [ ] README atualizado

### Performance
- [ ] Cache de dados (5 min TTL)
- [ ] Lazy loading de gráficos
- [ ] Paginação de tabelas grandes

---

**Status**: 🟢 PRONTO PARA INICIAR
**Próxima Ação**: Criar estrutura de diretórios UI (Dia 1, Task 1.1)


