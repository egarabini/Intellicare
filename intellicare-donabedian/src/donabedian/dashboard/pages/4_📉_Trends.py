"""
Trends page - Temporal trend analysis.

Page for analyzing temporal trends and patterns.
"""

import streamlit as st
import pandas as pd
from donabedian.dashboard import config
from donabedian.dashboard.api_client import DonabedianAPIClient
from donabedian.dashboard.components import charts, metrics, filters
from donabedian.dashboard.utils import cache, formatters


# Page configuration
st.set_page_config(
    page_title=f"{config.PAGE_TITLE} - Trends",
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
)


# Initialize API client
@st.cache_resource
def get_api_client() -> DonabedianAPIClient:
    """Get cached API client instance."""
    return DonabedianAPIClient(config.API_BASE_URL)


def main():
    """Main page function."""
    st.title("📉 Análise de Tendências")
    
    st.markdown("""
    Análise temporal de **tendências** e **padrões** nos indicadores de qualidade.
    
    - **Direção da Tendência**: Melhorando, Estável, Piorando
    - **Variação Percentual**: Mudança do primeiro ao último valor
    - **Estatísticas**: Mínimo, Máximo, Média
    """)
    
    st.markdown("---")
    
    # Sidebar filters
    period_days = filters.period_filter(key="trends_period")
    
    # Get API client
    client = get_api_client()
    
    # Load indicators for selection
    try:
        indicators_response = cache.get_cached_indicators(client, page=1, page_size=100)
        indicators = indicators_response.get("items", [])
    except Exception as e:
        st.error(f"❌ Erro ao carregar indicadores: {str(e)}")
        return
    
    if not indicators:
        st.warning("Nenhum indicador disponível")
        return
    
    # Indicator selector
    st.subheader("📊 Selecione um Indicador")
    
    indicator_options = {f"{ind.get('name')} (ID: {ind.get('id')})": ind.get('id') 
                        for ind in indicators}
    
    selected_name = st.selectbox(
        "Indicador",
        options=list(indicator_options.keys()),
        index=0,
    )
    
    selected_id = indicator_options[selected_name]
    
    # Find selected indicator
    selected_indicator = next((ind for ind in indicators if ind.get("id") == selected_id), None)
    
    if not selected_indicator:
        st.error("Indicador não encontrado")
        return
    
    st.markdown("---")
    
    # Load trend data
    try:
        with st.spinner("Carregando dados de tendência..."):
            trend_data = cache.get_cached_indicator_trend(client, selected_id, period_days)
    except Exception as e:
        st.error(f"❌ Erro ao carregar tendência: {str(e)}")
        return
    
    # Extract data
    indicator_name = trend_data.get("indicator_name")
    time_series = trend_data.get("time_series", [])
    trend_analysis = trend_data.get("trend_analysis", {})
    target_value = trend_data.get("target_value")
    current_score = trend_data.get("current_score", 0)
    period_start = trend_data.get("period_start")
    period_end = trend_data.get("period_end")
    
    # Display period info
    st.info(f"📅 Período: {formatters.format_date(period_start)} a {formatters.format_date(period_end)}")
    
    # Summary metrics
    st.subheader("📊 Resumo da Tendência")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        metrics.display_score_metric(
            label="Score Atual",
            score=current_score,
        )
    
    with col2:
        direction = trend_analysis.get("direction", "insufficient_data")
        st.markdown(f"**Direção:**")
        st.markdown(metrics.display_trend_indicator(direction), unsafe_allow_html=True)
    
    with col3:
        change_pct = trend_analysis.get("change_percent")
        if change_pct is not None:
            st.metric(
                label="Variação",
                value=formatters.format_percentage(change_pct),
                delta=f"{change_pct:+.1f}%"
            )
        else:
            st.metric(label="Variação", value="N/A")
    
    with col4:
        data_points = trend_analysis.get("data_points", 0)
        st.metric(
            label="Pontos de Dados",
            value=data_points,
        )
    
    st.markdown("---")
    
    # Trend chart
    if time_series:
        st.subheader("📈 Evolução Temporal")
        
        trend_fig = charts.create_trend_line_chart(
            time_series=time_series,
            indicator_name=indicator_name,
            target_value=target_value
        )
        st.plotly_chart(trend_fig, use_container_width=True, config=config.CHART_CONFIG)
    else:
        st.warning("Sem dados de série temporal disponíveis")
    
    st.markdown("---")
    
    # Statistics
    st.subheader("📊 Estatísticas")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        first_value = trend_analysis.get("first_value")
        st.metric(
            label="Primeiro Valor",
            value=formatters.format_value(first_value) if first_value is not None else "N/A"
        )
    
    with col2:
        last_value = trend_analysis.get("last_value")
        st.metric(
            label="Último Valor",
            value=formatters.format_value(last_value) if last_value is not None else "N/A"
        )
    
    with col3:
        avg_value = trend_analysis.get("average_value")
        st.metric(
            label="Média",
            value=formatters.format_value(avg_value) if avg_value is not None else "N/A"
        )
    
    with col4:
        min_value = trend_analysis.get("min_value")
        st.metric(
            label="Mínimo",
            value=formatters.format_value(min_value) if min_value is not None else "N/A"
        )
    
    with col5:
        max_value = trend_analysis.get("max_value")
        st.metric(
            label="Máximo",
            value=formatters.format_value(max_value) if max_value is not None else "N/A"
        )
    
    st.markdown("---")
    
    # Data table
    if time_series:
        st.subheader("📋 Dados Detalhados")
        
        df_data = []
        for point in time_series:
            df_data.append({
                "Data": formatters.format_date(point.get("date")),
                "Valor": point.get("value"),
                "Score": point.get("score"),
                "Status": point.get("status", "").upper(),
            })
        
        df = pd.DataFrame(df_data)
        
        # Display table
        st.dataframe(
            df.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            hide_index=True,
        )
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"trend_{indicator_name}_{period_start}_{period_end}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()

