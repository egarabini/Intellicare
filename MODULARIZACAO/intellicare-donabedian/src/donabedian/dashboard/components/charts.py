"""
Chart components using Plotly.

Reusable chart components for the dashboard.
"""

from typing import List, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
from donabedian.dashboard import config


def create_pillar_radar_chart(pillar_scores: List[Dict[str, Any]]) -> go.Figure:
    """
    Create radar chart for the 7 pillars of quality.
    
    Args:
        pillar_scores: List of pillar score dictionaries with 'pillar_name' and 'score'
        
    Returns:
        Plotly Figure object
    """
    # Extract data
    pillar_names = [p["pillar_name"] for p in pillar_scores]
    scores = [p["score"] for p in pillar_scores]
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=pillar_names,
        fill='toself',
        name='Score',
        line=dict(color=config.COLORS["primary"], width=2),
        fillcolor=f'rgba(0, 123, 255, 0.3)',
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='',
                showticklabels=True,
            )
        ),
        showlegend=False,
        title="7 Pilares de Qualidade (Donabedian)",
        **config.PLOTLY_LAYOUT_DEFAULTS,
    )
    
    return fig


def create_status_distribution_pie(status_dist: Dict[str, Any]) -> go.Figure:
    """
    Create pie chart for status distribution.
    
    Args:
        status_dist: Dictionary with 'green_count', 'yellow_count', 'red_count'
        
    Returns:
        Plotly Figure object
    """
    labels = ['GREEN', 'YELLOW', 'RED']
    values = [
        status_dist.get('green_count', 0),
        status_dist.get('yellow_count', 0),
        status_dist.get('red_count', 0),
    ]
    colors = [config.STATUS_COLORS['green'], config.STATUS_COLORS['yellow'], config.STATUS_COLORS['red']]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
    )])
    
    fig.update_layout(
        title="Distribuição de Status",
        **config.PLOTLY_LAYOUT_DEFAULTS,
    )
    
    return fig


def create_pillar_bar_chart(pillar_scores: List[Dict[str, Any]]) -> go.Figure:
    """
    Create bar chart comparing pillar scores.
    
    Args:
        pillar_scores: List of pillar score dictionaries
        
    Returns:
        Plotly Figure object
    """
    pillar_names = [p["pillar_name"] for p in pillar_scores]
    scores = [p["score"] for p in pillar_scores]
    
    # Color bars based on score
    colors = []
    for score in scores:
        if score >= 75:
            colors.append(config.STATUS_COLORS['green'])
        elif score >= 50:
            colors.append(config.STATUS_COLORS['yellow'])
        else:
            colors.append(config.STATUS_COLORS['red'])
    
    fig = go.Figure(data=[go.Bar(
        x=pillar_names,
        y=scores,
        marker=dict(color=colors),
        text=[f"{s:.1f}" for s in scores],
        textposition='outside',
    )])
    
    fig.update_layout(
        title="Comparação de Scores por Pilar",
        xaxis_title="Pilar",
        yaxis_title="Score",
        yaxis=dict(range=[0, 105]),
        **config.PLOTLY_LAYOUT_DEFAULTS,
    )
    
    return fig


def create_trend_line_chart(
    time_series: List[Dict[str, Any]],
    indicator_name: str,
    target_value: float = None
) -> go.Figure:
    """
    Create line chart for temporal trend.
    
    Args:
        time_series: List of data points with 'date', 'value', 'status'
        indicator_name: Name of the indicator
        target_value: Optional target value to show as reference line
        
    Returns:
        Plotly Figure object
    """
    dates = [point["date"] for point in time_series]
    values = [point["value"] for point in time_series]
    statuses = [point["status"] for point in time_series]
    
    # Create line chart
    fig = go.Figure()
    
    # Add main line
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Valor',
        line=dict(color=config.COLORS["primary"], width=2),
        marker=dict(
            size=8,
            color=[config.STATUS_COLORS.get(s, config.COLORS["secondary"]) for s in statuses],
        ),
    ))
    
    # Add target line if provided
    if target_value is not None:
        fig.add_trace(go.Scatter(
            x=dates,
            y=[target_value] * len(dates),
            mode='lines',
            name='Meta',
            line=dict(color=config.COLORS["danger"], width=2, dash='dash'),
        ))
    
    fig.update_layout(
        title=f"Evolução Temporal - {indicator_name}",
        xaxis_title="Data",
        yaxis_title="Valor",
        **config.PLOTLY_LAYOUT_DEFAULTS,
    )
    
    return fig

