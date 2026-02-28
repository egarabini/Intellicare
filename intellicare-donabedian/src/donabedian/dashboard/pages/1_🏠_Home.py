"""
Home page - Dashboard Overview.

Main dashboard page with overall quality metrics and KPIs.
"""

import streamlit as st
from donabedian.dashboard import config
from donabedian.dashboard.api_client import DonabedianAPIClient
from donabedian.dashboard.components import charts, metrics, filters
from donabedian.dashboard.utils import cache, formatters


# Page configuration
st.set_page_config(
    page_title=f"{config.PAGE_TITLE} - Home",
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
    st.title("🏠 Dashboard - Visão Geral")
    
    # Sidebar filters
    period_days = filters.period_filter(key="home_period")
    
    # Get API client
    client = get_api_client()
    
    # Load data
    try:
        with st.spinner("Carregando dados..."):
            dashboard_data = cache.get_cached_dashboard_overview(client, period_days)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.info(f"Verifique se a API está rodando em: `{config.API_BASE_URL}`")
        return
    
    # Extract data
    overall_score = dashboard_data.get("overall_score", 0)
    status_dist = dashboard_data.get("status_distribution", {})
    pillar_summaries = dashboard_data.get("pillar_summaries", [])
    triad_summaries = dashboard_data.get("triad_summaries", [])
    top_performers = dashboard_data.get("top_performers", [])
    bottom_performers = dashboard_data.get("bottom_performers", [])
    
    # Display period info
    period_start = dashboard_data.get("period_start")
    period_end = dashboard_data.get("period_end")
    st.info(f"📅 Período: {formatters.format_date(period_start)} a {formatters.format_date(period_end)}")
    
    st.markdown("---")
    
    # Overall Score
    st.subheader("📊 Score Geral de Qualidade")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        metrics.display_score_metric(
            label="Score Geral",
            score=overall_score,
            help_text="Média ponderada dos 7 pilares de qualidade"
        )
    
    with col2:
        green_pct = status_dist.get("green_percentage", 0)
        st.metric(
            label="✅ Verde",
            value=formatters.format_percentage(green_pct),
            help="Percentual de medições que atingiram a meta"
        )
    
    with col3:
        yellow_pct = status_dist.get("yellow_percentage", 0)
        st.metric(
            label="⚠️ Amarelo",
            value=formatters.format_percentage(yellow_pct),
            help="Percentual de medições próximas à meta"
        )
    
    with col4:
        red_pct = status_dist.get("red_percentage", 0)
        st.metric(
            label="❌ Vermelho",
            value=formatters.format_percentage(red_pct),
            help="Percentual de medições abaixo da meta"
        )
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 7 Pilares de Qualidade")
        if pillar_summaries:
            radar_fig = charts.create_pillar_radar_chart(pillar_summaries)
            st.plotly_chart(radar_fig, use_container_width=True, config=config.CHART_CONFIG)
        else:
            st.warning("Sem dados de pilares disponíveis")
    
    with col2:
        st.subheader("📊 Distribuição de Status")
        if status_dist:
            pie_fig = charts.create_status_distribution_pie(status_dist)
            st.plotly_chart(pie_fig, use_container_width=True, config=config.CHART_CONFIG)
        else:
            st.warning("Sem dados de distribuição disponíveis")
    
    st.markdown("---")
    
    # Pillar scores bar chart
    st.subheader("📊 Comparação de Pilares")
    if pillar_summaries:
        bar_fig = charts.create_pillar_bar_chart(pillar_summaries)
        st.plotly_chart(bar_fig, use_container_width=True, config=config.CHART_CONFIG)
    else:
        st.warning("Sem dados de pilares disponíveis")
    
    st.markdown("---")
    
    # Triad summary
    st.subheader("🔺 Tríade de Donabedian")
    
    if triad_summaries:
        col1, col2, col3 = st.columns(3)
        
        for i, triad in enumerate(triad_summaries):
            dimension = triad.get("dimension", "")
            score = triad.get("score", 0)
            indicator_count = triad.get("indicator_count", 0)
            
            with [col1, col2, col3][i]:
                metrics.create_metric_card(
                    title=formatters.format_triad_name(dimension),
                    value=formatters.format_score(score),
                    subtitle=f"{indicator_count} indicadores",
                    color=list(config.TRIAD_COLORS.keys())[i] if i < 3 else "primary"
                )
    else:
        st.info("Sem dados da tríade disponíveis")
    
    st.markdown("---")
    
    # Top and Bottom Performers
    col1, col2 = st.columns(2)
    
    with col1:
        if top_performers:
            metrics.display_top_performers(
                performers=top_performers[:5],
                title="🏆 Top 5 Indicadores",
                is_bottom=False
            )
        else:
            st.info("Sem dados de top performers")
    
    with col2:
        if bottom_performers:
            metrics.display_top_performers(
                performers=bottom_performers[:5],
                title="⚠️ Bottom 5 Indicadores",
                is_bottom=True
            )
        else:
            st.info("Sem dados de bottom performers")


if __name__ == "__main__":
    main()

