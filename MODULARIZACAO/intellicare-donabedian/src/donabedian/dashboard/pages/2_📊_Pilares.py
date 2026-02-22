"""
Pillars page - Detailed pillar analysis.

Page for analyzing the 7 pillars of quality in detail.
"""

import streamlit as st
import pandas as pd
from donabedian.dashboard import config
from donabedian.dashboard.api_client import DonabedianAPIClient
from donabedian.dashboard.components import charts, metrics, filters
from donabedian.dashboard.utils import cache, formatters


# Page configuration
st.set_page_config(
    page_title=f"{config.PAGE_TITLE} - Pilares",
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
    st.title("📊 Pilares de Qualidade")
    
    st.markdown("""
    Análise detalhada dos **7 Pilares de Qualidade** segundo Donabedian (1990):
    
    1. **Eficácia** - Capacidade de produzir melhorias na saúde
    2. **Efetividade** - Grau em que melhorias são alcançadas
    3. **Eficiência** - Custo-benefício das melhorias
    4. **Otimidade** - Equilíbrio entre benefícios e custos
    5. **Aceitabilidade** - Conformidade com preferências dos pacientes
    6. **Legitimidade** - Conformidade com preferências sociais
    7. **Equidade** - Distribuição justa dos serviços
    """)
    
    st.markdown("---")
    
    # Sidebar filters
    period_days = filters.period_filter(key="pillars_period")
    
    # Get API client
    client = get_api_client()
    
    # Load data
    try:
        with st.spinner("Carregando dados dos pilares..."):
            pillars_data = cache.get_cached_dashboard_pillars(client, period_days)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return
    
    # Extract data
    pillar_summaries = pillars_data.get("pillar_summaries", [])
    overall_score = pillars_data.get("overall_score", 0)
    period_start = pillars_data.get("period_start")
    period_end = pillars_data.get("period_end")
    
    # Display period info
    st.info(f"📅 Período: {formatters.format_date(period_start)} a {formatters.format_date(period_end)}")
    
    # Overall score
    st.subheader("📊 Score Geral dos Pilares")
    metrics.display_score_metric(
        label="Score Médio",
        score=overall_score,
        help_text="Média ponderada dos 7 pilares"
    )
    
    st.markdown("---")
    
    # Bar chart
    if pillar_summaries:
        bar_fig = charts.create_pillar_bar_chart(pillar_summaries)
        st.plotly_chart(bar_fig, use_container_width=True, config=config.CHART_CONFIG)
    
    st.markdown("---")
    
    # Detailed pillar cards
    st.subheader("📋 Detalhamento por Pilar")
    
    for pillar in pillar_summaries:
        pillar_id = pillar.get("pillar_id")
        pillar_name = pillar.get("pillar_name")
        score = pillar.get("score", 0)
        indicator_count = pillar.get("indicator_count", 0)
        measurement_count = pillar.get("measurement_count", 0)
        
        # Create expander for each pillar
        with st.expander(f"**{pillar_name}** - Score: {formatters.format_score(score)}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Score do Pilar",
                    value=formatters.format_score(score),
                )
            
            with col2:
                st.metric(
                    label="Indicadores",
                    value=indicator_count,
                )
            
            with col3:
                st.metric(
                    label="Medições",
                    value=measurement_count,
                )
            
            # Try to load trend data for this pillar
            try:
                with st.spinner(f"Carregando tendência de {pillar_name}..."):
                    trend_data = cache.get_cached_pillar_trend(client, pillar_id, period_days)
                    
                    time_series = trend_data.get("aggregated_time_series", [])
                    trend_analysis = trend_data.get("trend_analysis", {})
                    
                    if time_series:
                        # Show trend chart
                        trend_fig = charts.create_trend_line_chart(
                            time_series=time_series,
                            indicator_name=pillar_name,
                            target_value=None  # No target for aggregated pillar
                        )
                        st.plotly_chart(trend_fig, use_container_width=True, config=config.CHART_CONFIG)
                        
                        # Show trend analysis
                        direction = trend_analysis.get("direction", "insufficient_data")
                        change_pct = trend_analysis.get("change_percent")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Tendência:** {formatters.format_trend_direction(direction)}", unsafe_allow_html=True)
                        
                        with col2:
                            if change_pct is not None:
                                st.markdown(f"**Variação:** {formatters.format_percentage(change_pct)}")
                    else:
                        st.info("Sem dados de tendência disponíveis para este pilar")
            
            except Exception as e:
                st.warning(f"Não foi possível carregar tendência: {str(e)}")
    
    st.markdown("---")
    
    # Summary table
    st.subheader("📊 Tabela Resumo")
    
    if pillar_summaries:
        df_data = []
        for pillar in pillar_summaries:
            df_data.append({
                "Pilar": pillar.get("pillar_name"),
                "Score": pillar.get("score", 0),
                "Indicadores": pillar.get("indicator_count", 0),
                "Medições": pillar.get("measurement_count", 0),
            })
        
        df = pd.DataFrame(df_data)
        
        # Style the dataframe
        st.dataframe(
            df.style.background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()

