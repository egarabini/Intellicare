# 🎨 Guia da Interface Web - Florence UI

**Versão**: 1.0.0  
**Data**: 2026-02-28  
**Autor**: IntelliCare Team

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Execução](#instalação-e-execução)
3. [Páginas da Interface](#páginas-da-interface)
4. [Componentes Reutilizáveis](#componentes-reutilizáveis)
5. [Configuração](#configuração)
6. [Exemplos de Uso](#exemplos-de-uso)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

A **Florence UI** é uma interface web moderna e intuitiva para o módulo de análise clínica Florence, construída com **Streamlit**.

### Funcionalidades Principais

- 🏠 **Dashboard**: Visão geral com KPIs e gráficos
- 🔬 **Análise**: Interpretação de exames laboratoriais
- 📈 **Tendências**: Visualização de dados históricos
- 🤖 **RAG**: Consulta a protocolos clínicos
- 📄 **Relatórios**: Exportação em múltiplos formatos

### Tecnologias

- **Streamlit** 1.30+: Framework web
- **Plotly** 5.18+: Gráficos interativos
- **Pandas** 2.1+: Manipulação de dados
- **openpyxl** 3.1+: Exportação Excel
- **reportlab** 4.0+: Geração de PDF

---

## 🚀 Instalação e Execução

### Pré-requisitos

1. Python 3.11+
2. Florence API rodando (porta 8002)
3. Dependências instaladas

### Instalação

```bash
# Navegar para o diretório
cd MODULARIZACAO/intellicare-florence

# Instalar dependências
poetry install

# Ou com pip
pip install -e .
```

### Executar a UI

```bash
# Com Streamlit
streamlit run florence/ui/main.py

# Ou especificar porta
streamlit run florence/ui/main.py --server.port 8502
```

A interface estará disponível em: **http://localhost:8502**

### Variáveis de Ambiente

```bash
# URL da API Florence (opcional)
export FLORENCE_API_URL=http://localhost:8002
```

---

## 📄 Páginas da Interface

### 1. 🏠 Home - Dashboard Principal

**Arquivo**: `florence/ui/pages/1_🏠_Home.py`

**Funcionalidades**:
- 4 KPIs principais (Total Análises, Exames Críticos, Protocolos RAG, Tempo Médio)
- Gráfico de análises por dia (últimos 30 dias)
- Distribuição de status (pie chart)
- Recursos disponíveis (exames, painéis, correlações)
- Top 5 exames mais solicitados

**Como usar**:
1. Acesse a página "🏠 Home" no menu lateral
2. Visualize os KPIs e gráficos
3. Monitore o status da API na sidebar

---

### 2. 🔬 Análise - Interpretação de Exames

**Arquivo**: `florence/ui/pages/2_🔬_Analise.py`

**Funcionalidades**:
- Formulário de entrada (Patient ID + exames + valores)
- Análise com/sem RAG
- Tabela de interpretações
- Gráfico de barras de valores
- Correlações clínicas detectadas
- Protocolos RAG relevantes
- Histórico de análises (últimas 10)

**Como usar**:
1. Informe o **Patient ID**
2. Selecione os **exames** desejados
3. Informe os **valores** dos exames
4. (Opcional) Ative **"Incluir RAG"** e informe query
5. Clique em **"🔬 Analisar"**
6. Visualize os resultados:
   - Interpretações com status (✅ ⚠️ 🔴)
   - Gráfico de barras colorido
   - Correlações detectadas
   - Protocolos relevantes (se RAG ativado)
7. Consulte o histórico no expander

**Exemplo**:
```
Patient ID: PAC-12345
Exames: hemoglobin, glucose, creatinine
Valores: 12.5, 110, 1.2
Incluir RAG: ✓
Query: protocolo para anemia
```

---

### 3. 📈 Tendências - Visualização Temporal

**Arquivo**: `florence/ui/pages/3_📈_Tendencias.py`

**Funcionalidades**:
- Upload de CSV/Excel com dados históricos
- Template de arquivo para download
- Validação de formato
- Preview dos dados
- Seleção de exames e período
- 3 tipos de gráficos:
  - **Line Chart**: Evolução temporal
  - **Heatmap**: Correlação entre exames
  - **Box Plot**: Distribuição dos valores

**Como usar**:
1. Baixe o **template CSV** (botão "⬇️ Baixar Template CSV")
2. Preencha com seus dados históricos
3. Faça **upload** do arquivo
4. Selecione os **exames** para análise (até 5)
5. Escolha o **período** (date range)
6. Selecione a **agregação** (Diário/Semanal/Mensal)
7. Visualize os gráficos

**Formato do CSV**:
```csv
date,patient_id,hemoglobin,glucose,creatinine
2026-01-01,PAC-001,14.5,95,0.9
2026-01-02,PAC-001,14.3,98,0.9
...
```

---

### 4. 🤖 RAG - Consulta a Protocolos

**Arquivo**: `florence/ui/pages/4_🤖_RAG.py`

**Funcionalidades**:
- Consulta manual com query em linguagem natural
- Slider para número de resultados (top_k: 1-10)
- Lista de 10 protocolos disponíveis
- Filtros (especialidade, palavra-chave)
- Resultados com:
  - Score de relevância (progress bar)
  - Top 3 chunks mais relevantes
  - Conteúdo completo do protocolo
  - Metadata (especialidade, versão, última atualização)

**Como usar**:
1. Digite sua **consulta** em linguagem natural
2. Ajuste o **número de resultados** (slider)
3. Clique em **"🔎 Buscar Protocolos"**
4. Visualize os resultados:
   - Score de relevância
   - Trechos mais relevantes
   - Protocolo completo (expander)
5. (Opcional) Filtre protocolos por especialidade ou palavra-chave

**Exemplos de queries**:
- "protocolo para tratamento de diabetes tipo 2"
- "diretrizes para hipertensão arterial"
- "manejo de dislipidemia"
- "rastreamento de câncer de mama"

---

### 5. 📄 Relatórios - Exportação

**Arquivo**: `florence/ui/pages/5_📄_Relatorios.py`

**Funcionalidades**:
- Seleção de análise do histórico
- Preview da análise
- Exportação em 3 formatos:
  - **Excel**: 4 abas (Informações, Interpretações, Correlações, Resultados)
  - **JSON**: Formato estruturado para integração
  - **HTML**: Relatório formatado para impressão/PDF

**Como usar**:
1. Selecione a **análise** desejada (dropdown)
2. Visualize o **preview** (Patient ID, Data/Hora, Exames)
3. Escolha o **formato** de exportação:
   - **📊 Exportar Excel**: Planilha com múltiplas abas
   - **📋 Exportar JSON**: Dados estruturados
   - **📄 Exportar HTML**: Relatório formatado
4. Clique no botão de download

**Formatos de arquivo**:
- Excel: `florence_analise_PAC-12345_20260228_143022.xlsx`
- JSON: `florence_analise_PAC-12345_20260228_143022.json`
- HTML: `florence_analise_PAC-12345_20260228_143022.html`

---

## 🧩 Componentes Reutilizáveis

### Charts (florence/ui/components/charts.py)

**Funções**:
- `create_lab_bar_chart()`: Gráfico de barras de exames
- `create_gauge_chart()`: Gauge para exame individual
- `create_radar_chart()`: Radar chart para painéis
- `create_correlation_network()`: Rede de correlações
- `create_trend_line_chart()`: Linha de tendências

### Tables (florence/ui/components/tables.py)

**Funções**:
- `interpretation_table()`: Tabela de interpretações
- `correlation_table()`: Tabela de correlações
- `protocol_table()`: Tabela de protocolos RAG
- `history_table()`: Tabela de histórico

### Metrics (florence/ui/components/metrics.py)

**Funções**:
- `metric_card()`: Card de métrica individual
- `kpi_row()`: Linha de KPIs
- `status_badge()`: Badge HTML de status
- `info_box()`: Caixa de informação
- `progress_indicator()`: Indicador de progresso
- `summary_card()`: Card de sumário

---

## ⚙️ Configuração

### Arquivo: florence/ui/config.py

**Configurações principais**:

```python
# API
API_BASE_URL = "http://localhost:8002"

# UI
PAGE_TITLE = "Florence - Análise Clínica"
PAGE_ICON = "🏥"
LAYOUT = "wide"

# Cache
CACHE_TTL = 300  # 5 minutos

# Cores
STATUS_COLORS = {
    "normal": "#28a745",
    "low": "#ffc107",
    "high": "#ffc107",
    "critical_low": "#dc3545",
    "critical_high": "#dc3545",
}

THEME_COLORS = {
    "primary": "#0066cc",
    "secondary": "#6c757d",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
}
```

### Arquivo: .streamlit/config.toml

**Tema e servidor**:

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

[browser]
gatherUsageStats = false
```

---

## 💡 Exemplos de Uso

### Exemplo 1: Análise Simples

1. Acesse **"🔬 Análise"**
2. Patient ID: `PAC-001`
3. Selecione: `hemoglobin`, `glucose`
4. Valores: `12.5`, `110`
5. Clique **"🔬 Analisar"**
6. Resultado: Interpretações + gráfico

### Exemplo 2: Análise com RAG

1. Acesse **"🔬 Análise"**
2. Patient ID: `PAC-002`
3. Selecione: `glucose`, `hba1c`
4. Valores: `180`, `8.5`
5. Ative **"Incluir RAG"**
6. Query: `protocolo diabetes`
7. Clique **"🔬 Analisar"**
8. Resultado: Interpretações + correlações + protocolos

### Exemplo 3: Tendências

1. Acesse **"📈 Tendências"**
2. Baixe template CSV
3. Preencha com 30 dias de dados
4. Upload do arquivo
5. Selecione exames: `glucose`, `hba1c`
6. Período: últimos 30 dias
7. Visualize gráficos

### Exemplo 4: Consulta RAG

1. Acesse **"🤖 RAG"**
2. Query: `tratamento hipertensão`
3. Top K: `5`
4. Clique **"🔎 Buscar"**
5. Visualize protocolos relevantes

### Exemplo 5: Exportação

1. Realize uma análise
2. Acesse **"📄 Relatórios"**
3. Selecione a análise
4. Clique **"📊 Exportar Excel"**
5. Abra o arquivo baixado

---

## 🔧 Troubleshooting

### Problema 1: API Offline

**Sintoma**: ❌ API Offline na sidebar

**Solução**:
```bash
# Verificar se API está rodando
curl http://localhost:8002/health

# Iniciar API
cd MODULARIZACAO/intellicare-florence
uvicorn florence.api.app:app --reload --port 8002
```

### Problema 2: Erro ao Carregar Recursos

**Sintoma**: ❌ Erro ao carregar recursos da API

**Solução**:
1. Verificar conexão com API
2. Limpar cache (botão "🔄 Limpar Cache" na sidebar)
3. Recarregar página (F5)

### Problema 3: Upload de CSV Falha

**Sintoma**: ❌ Colunas obrigatórias faltando

**Solução**:
1. Baixar template CSV
2. Verificar colunas: `date`, `patient_id`
3. Formato de data: `YYYY-MM-DD`

### Problema 4: Exportação Excel Falha

**Sintoma**: Erro ao exportar Excel

**Solução**:
```bash
# Instalar openpyxl
pip install openpyxl
```

### Problema 5: Gráficos Não Aparecem

**Sintoma**: Gráficos em branco

**Solução**:
```bash
# Instalar plotly
pip install plotly
```

---

## 📚 Recursos Adicionais

- [Documentação Florence](../README.md)
- [API Reference](API_REFERENCE.md)
- [RAG Protocolos](RAG_PROTOCOLOS.md)
- [Streamlit Docs](https://docs.streamlit.io)

---

**Versão**: 1.0.0  
**Última Atualização**: 2026-02-28  
**Suporte**: dev@intellicare.health

