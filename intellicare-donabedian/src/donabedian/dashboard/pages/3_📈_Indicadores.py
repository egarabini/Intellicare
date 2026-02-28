"""
Indicators page - Detailed indicator analysis.

Page for analyzing quality indicators in detail.
"""

import streamlit as st
import pandas as pd
from donabedian.dashboard import config
from donabedian.dashboard.api_client import DonabedianAPIClient
from donabedian.dashboard.components import charts, metrics, filters
from donabedian.dashboard.utils import cache, formatters


# Page configuration
st.set_page_config(
    page_title=f"{config.PAGE_TITLE} - Indicadores",
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
    st.title("📈 Indicadores de Qualidade")
    
    st.markdown("""
    Análise detalhada dos **Indicadores de Qualidade** organizados pela **Tríade de Donabedian**:
    
    - **Estrutura** - Indicadores relacionados a recursos e infraestrutura
    - **Processo** - Indicadores relacionados a atividades e procedimentos
    - **Resultado** - Indicadores relacionados a outcomes e impactos
    """)
    
    st.markdown("---")
    
    # Sidebar filters
    period_days = filters.period_filter(key="indicators_period")
    triad_filter_value = filters.triad_filter(key="indicators_triad")
    
    # Get API client
    client = get_api_client()
    
    # Load data
    try:
        with st.spinner("Carregando dados dos indicadores..."):
            indicators_data = cache.get_cached_dashboard_indicators(client, period_days)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return
    
    # Extract data
    indicator_summaries = indicators_data.get("indicator_summaries", [])
    by_triad = indicators_data.get("by_triad", {})
    total_indicators = indicators_data.get("total_indicators", 0)
    period_start = indicators_data.get("period_start")
    period_end = indicators_data.get("period_end")
    
    # Display period info
    st.info(f"📅 Período: {formatters.format_date(period_start)} a {formatters.format_date(period_end)}")
    
    # Filter by triad if selected
    if triad_filter_value:
        indicator_summaries = by_triad.get(triad_filter_value, [])
        st.info(f"🔍 Filtrando por: {formatters.format_triad_name(triad_filter_value)}")
    
    st.markdown("---")
    
    # Summary metrics
    st.subheader("📊 Resumo Geral")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total de Indicadores",
            value=len(indicator_summaries),
        )
    
    with col2:
        if indicator_summaries:
            avg_score = sum(ind.get("current_score", 0) for ind in indicator_summaries) / len(indicator_summaries)
            metrics.display_score_metric(
                label="Score Médio",
                score=avg_score,
            )
        else:
            st.metric(label="Score Médio", value="N/A")
    
    with col3:
        total_measurements = sum(ind.get("measurement_count", 0) for ind in indicator_summaries)
        st.metric(
            label="Total de Medições",
            value=formatters.format_integer(total_measurements),
        )
    
    st.markdown("---")
    
    # Indicators by triad
    st.subheader("🔺 Indicadores por Tríade")
    
    col1, col2, col3 = st.columns(3)
    
    triad_cols = [col1, col2, col3]
    triad_keys = ["structure", "process", "outcome"]
    
    for i, (col, key) in enumerate(zip(triad_cols, triad_keys)):
        triad_indicators = by_triad.get(key, [])
        count = len(triad_indicators)
        
        if triad_indicators:
            avg_score = sum(ind.get("current_score", 0) for ind in triad_indicators) / count
        else:
            avg_score = 0
        
        with col:
            metrics.create_metric_card(
                title=formatters.format_triad_name(key),
                value=f"{count} indicadores",
                subtitle=f"Score: {formatters.format_score(avg_score)}",
                color=list(config.TRIAD_COLORS.keys())[i]
            )
    
    st.markdown("---")
    
    # Detailed indicator list
    st.subheader("📋 Lista de Indicadores")
    
    if not indicator_summaries:
        st.warning("Nenhum indicador encontrado para os filtros selecionados")
        return
    
    # Create dataframe
    df_data = []
    for ind in indicator_summaries:
        df_data.append({
            "ID": ind.get("indicator_id"),
            "Nome": ind.get("indicator_name"),
            "Tríade": formatters.format_triad_name(ind.get("triad_dimension", "")),
            "Pilares": ind.get("pillar_count", 0),
            "Medições": ind.get("measurement_count", 0),
            "Score": ind.get("current_score", 0),
            "Último Valor": ind.get("latest_value"),
            "Status": ind.get("latest_status", "").upper() if ind.get("latest_status") else "N/A",
            "Meta": ind.get("target_value"),
        })
    
    df = pd.DataFrame(df_data)
    
    # Display table with styling
    st.dataframe(
        df.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
        use_container_width=True,
        hide_index=True,
    )
    
    st.markdown("---")
    
    # Detailed view for selected indicator
    st.subheader("🔍 Detalhamento de Indicador")
    
    # Indicator selector
    indicator_options = {f"{ind.get('indicator_name')} (ID: {ind.get('indicator_id')})": ind.get('indicator_id') 
                        for ind in indicator_summaries}
    
    selected_name = st.selectbox(
        "Selecione um indicador para ver detalhes",
        options=["Nenhum"] + list(indicator_options.keys()),
        index=0,
    )
    
    if selected_name != "Nenhum":
        selected_id = indicator_options[selected_name]
        
        # Find indicator data
        selected_indicator = next((ind for ind in indicator_summaries if ind.get("indicator_id") == selected_id), None)
        
        if selected_indicator:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                score = selected_indicator.get("current_score", 0)
                metrics.display_score_metric(label="Score Atual", score=score)
            
            with col2:
                latest_value = selected_indicator.get("latest_value")
                st.metric(
                    label="Último Valor",
                    value=formatters.format_value(latest_value) if latest_value is not None else "N/A"
                )
            
            with col3:
                target = selected_indicator.get("target_value")
                st.metric(
                    label="Meta",
                    value=formatters.format_value(target) if target is not None else "N/A"
                )
            
            with col4:
                status = selected_indicator.get("latest_status", "").lower()
                if status:
                    st.markdown(f"**Status:** {metrics.display_status_badge(status)}", unsafe_allow_html=True)
            
            # Load trend data
            try:
                with st.spinner("Carregando tendência..."):
                    trend_data = cache.get_cached_indicator_trend(client, selected_id, period_days)
                    
                    time_series = trend_data.get("time_series", [])
                    target_value = trend_data.get("target_value")
                    indicator_name = trend_data.get("indicator_name")
                    
                    if time_series:
                        trend_fig = charts.create_trend_line_chart(
                            time_series=time_series,
                            indicator_name=indicator_name,
                            target_value=target_value
                        )
                        st.plotly_chart(trend_fig, use_container_width=True, config=config.CHART_CONFIG)
                    else:
                        st.info("Sem dados de tendência disponíveis")
            
            except Exception as e:
                st.warning(f"Não foi possível carregar tendência: {str(e)}")


if __name__ == "__main__":
    main()

