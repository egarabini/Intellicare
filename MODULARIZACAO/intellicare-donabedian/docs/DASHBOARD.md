# 📊 Dashboard Streamlit - Guia de Uso

## Visão Geral

O Dashboard Streamlit do módulo **intellicare-donabedian** fornece uma interface visual interativa para monitoramento e análise de indicadores de qualidade baseados no framework de Donabedian.

**URL**: `http://localhost:8501`

**Tecnologias**:
- Streamlit 1.30+
- Plotly 5.18+ (gráficos interativos)
- Pandas (manipulação de dados)
- httpx (comunicação com API)

---

## 🏠 Estrutura do Dashboard

O dashboard é composto por **4 páginas principais**:

### 1. 🏠 Home - Visão Geral
### 2. 🏛️ Pilares - Análise por Pilar
### 3. 📊 Indicadores - Gestão de Indicadores
### 4. 📈 Tendências - Análise Temporal

---

## 1️⃣ Página Home - Visão Geral

### Funcionalidades

**Métricas Principais** (4 cards):
- Total de Pilares
- Total de Indicadores
- Total de Medições
- Taxa de Conformidade Geral

**Gráfico Radar** - 7 Pilares de Donabedian:
- Visualização dos 7 pilares em formato radar
- Scores de 0 a 10 para cada pilar
- Interativo (hover para detalhes)

**Distribuição de Status**:
- Gráfico de pizza com distribuição de indicadores por status
- Verde (meta atingida)
- Amarelo (próximo à meta)
- Vermelho (abaixo da meta)

**Indicadores Recentes**:
- Tabela com últimas medições
- Ordenação por data
- Filtros por status

### Como Usar

1. Acesse `http://localhost:8501`
2. Visualize as métricas principais no topo
3. Analise o gráfico radar para identificar pilares com baixo desempenho
4. Verifique a distribuição de status
5. Revise os indicadores recentes na tabela

---

## 2️⃣ Página Pilares - Análise por Pilar

### Funcionalidades

**Seletor de Pilar**:
- Dropdown com os 7 pilares
- Seleção única

**Métricas do Pilar Selecionado**:
- Score do pilar (0-10)
- Total de indicadores associados
- Taxa de conformidade
- Indicadores atingindo meta

**Gráfico de Barras** - Indicadores do Pilar:
- Comparação de valores medidos vs. metas
- Cores por status (verde/amarelo/vermelho)
- Interativo (hover para detalhes)

**Tabela de Indicadores**:
- Lista completa de indicadores do pilar
- Colunas: Nome, Valor Atual, Meta, Status, Última Medição
- Ordenação por qualquer coluna
- Filtros por status

**Gráfico de Linha** - Evolução Temporal:
- Evolução dos indicadores ao longo do tempo
- Múltiplas linhas (um indicador por linha)
- Zoom e pan interativos

### Como Usar

1. Navegue para a página "Pilares" no menu lateral
2. Selecione um pilar no dropdown
3. Analise as métricas do pilar
4. Identifique indicadores problemáticos no gráfico de barras
5. Verifique a evolução temporal no gráfico de linha
6. Use a tabela para detalhes específicos

---

## 3️⃣ Página Indicadores - Gestão de Indicadores

### Funcionalidades

**Filtros Avançados**:
- **Dimensão da Tríade**: Structure, Process, Outcome
- **Pilar**: Filtro por pilar específico
- **Status**: Verde, Amarelo, Vermelho
- **Período**: Seletor de data inicial e final

**Lista de Indicadores**:
- Tabela paginada com todos os indicadores
- Colunas: Nome, Descrição, Fórmula, Unidade, Dimensão, Meta, Status
- Ordenação por qualquer coluna
- Busca por texto

**Detalhes do Indicador**:
- Clique em um indicador para ver detalhes
- Informações completas (fórmula, meta, operador)
- Histórico de medições
- Gráfico de evolução

**Gráfico de Dispersão** - Indicadores vs. Metas:
- Eixo X: Valor alvo
- Eixo Y: Valor medido
- Cores por status
- Linha de referência (meta = medido)

### Como Usar

1. Navegue para a página "Indicadores"
2. Use os filtros para refinar a lista
3. Analise a tabela de indicadores
4. Clique em um indicador para ver detalhes
5. Use o gráfico de dispersão para identificar desvios

---

## 4️⃣ Página Tendências - Análise Temporal

### Funcionalidades

**Seletor de Período**:
- Data inicial e final
- Presets: Último mês, Últimos 3 meses, Último ano

**Seletor de Indicadores**:
- Multiselect para comparar múltiplos indicadores
- Busca por nome

**Gráfico de Linha** - Evolução Temporal:
- Múltiplas linhas (um indicador por linha)
- Zoom e pan interativos
- Hover para detalhes
- Legenda interativa (clique para ocultar/mostrar)

**Gráfico de Área** - Distribuição de Status ao Longo do Tempo:
- Área empilhada com verde/amarelo/vermelho
- Visualização de tendências de conformidade

**Tabela de Estatísticas**:
- Média, Mínimo, Máximo, Desvio Padrão
- Por indicador
- Tendência (crescente/decrescente/estável)

**Gráfico de Heatmap** - Matriz de Correlação:
- Correlação entre indicadores
- Cores de -1 (correlação negativa) a +1 (correlação positiva)
- Identificação de indicadores relacionados

### Como Usar

1. Navegue para a página "Tendências"
2. Selecione o período de análise
3. Escolha os indicadores para comparar
4. Analise o gráfico de linha para identificar tendências
5. Verifique a distribuição de status ao longo do tempo
6. Use a tabela de estatísticas para insights quantitativos
7. Analise o heatmap para identificar correlações

---

## 🎨 Componentes Visuais

### Tipos de Gráficos

1. **Radar Chart** (Plotly):
   - 7 pilares de Donabedian
   - Escala 0-10
   - Cores: azul

2. **Bar Chart** (Plotly):
   - Indicadores vs. Metas
   - Cores por status (verde/amarelo/vermelho)
   - Horizontal ou vertical

3. **Line Chart** (Plotly):
   - Evolução temporal
   - Múltiplas séries
   - Zoom e pan

4. **Pie Chart** (Plotly):
   - Distribuição de status
   - Cores: verde (#28a745), amarelo (#ffc107), vermelho (#dc3545)

5. **Scatter Plot** (Plotly):
   - Indicadores vs. Metas
   - Linha de referência
   - Cores por status

6. **Area Chart** (Plotly):
   - Distribuição temporal de status
   - Área empilhada

7. **Heatmap** (Plotly):
   - Matriz de correlação
   - Escala de cores divergente

### Paleta de Cores

- **Verde** (#28a745): Meta atingida
- **Amarelo** (#ffc107): Próximo à meta
- **Vermelho** (#dc3545): Abaixo da meta
- **Azul** (#007bff): Neutro/informativo
- **Cinza** (#6c757d): Secundário

---

## 🔧 Funcionalidades Técnicas

### Cache

O dashboard utiliza cache do Streamlit para melhorar performance:

```python
@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_indicators():
    # Busca indicadores da API
    pass
```

### Formatação

- **Números**: Formatação PT-BR (vírgula para decimal)
- **Datas**: Formato DD/MM/YYYY
- **Percentuais**: 2 casas decimais + símbolo %
- **Moeda**: R$ com 2 casas decimais

### Responsividade

- Layout adaptativo para diferentes tamanhos de tela
- Gráficos responsivos (Plotly)
- Tabelas com scroll horizontal

---

## 📝 Dicas de Uso

1. **Performance**: Use os filtros para reduzir a quantidade de dados carregados
2. **Comparação**: Use a página de Tendências para comparar múltiplos indicadores
3. **Exportação**: Gráficos Plotly permitem download como PNG
4. **Zoom**: Use scroll do mouse para zoom em gráficos
5. **Pan**: Clique e arraste para mover gráficos
6. **Reset**: Duplo clique em gráficos para resetar zoom

---

## 🐛 Troubleshooting

### Dashboard não carrega

1. Verifique se a API está rodando (`http://localhost:8003/health`)
2. Verifique as variáveis de ambiente (`.env`)
3. Limpe o cache do Streamlit (menu lateral > Clear cache)

### Gráficos não aparecem

1. Verifique se há dados no período selecionado
2. Verifique os filtros aplicados
3. Recarregue a página (F5)

### Erro de conexão com API

1. Verifique se `API_BASE_URL` está correto no `.env`
2. Verifique se a API está acessível
3. Verifique logs da API para erros

---

## 🚀 Próximos Passos

- Adicionar exportação de relatórios em PDF
- Implementar alertas configuráveis
- Adicionar comparação entre períodos
- Implementar filtros salvos
- Adicionar anotações em gráficos

