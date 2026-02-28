"""Componentes de gráficos reutilizáveis."""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any
from florence.ui.config import STATUS_COLORS, THEME_COLORS


def create_lab_bar_chart(interpretations: List[Dict[str, Any]]) -> go.Figure:
    """Cria gráfico de barras de exames vs referência.
    
    Args:
        interpretations: Lista de interpretações
        
    Returns:
        Figura Plotly
    """
    labs = []
    values = []
    colors = []
    
    for interp in interpretations:
        labs.append(interp.get("lab_name", ""))
        values.append(interp.get("value", 0))
        status = interp.get("status", "normal")
        colors.append(STATUS_COLORS.get(status.lower(), "#6c757d"))
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labs,
        y=values,
        marker=dict(color=colors),
        text=values,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Valores dos Exames",
        xaxis_title="Exame",
        yaxis_title="Valor",
        height=400
    )
    
    return fig


def create_gauge_chart(value: float, min_val: float, max_val: float, 
                       lab_name: str, status: str) -> go.Figure:
    """Cria gauge chart para exame.
    
    Args:
        value: Valor do exame
        min_val: Valor mínimo de referência
        max_val: Valor máximo de referência
        lab_name: Nome do exame
        status: Status do exame
        
    Returns:
        Figura Plotly
    """
    color = STATUS_COLORS.get(status.lower(), "#6c757d")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': lab_name},
        delta={'reference': (min_val + max_val) / 2},
        gauge={
            'axis': {'range': [None, max_val * 1.5]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, min_val], 'color': "lightgray"},
                {'range': [min_val, max_val], 'color': "lightgreen"},
                {'range': [max_val, max_val * 1.5], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val
            }
        }
    ))
    
    fig.update_layout(height=250)
    
    return fig


def create_radar_chart(panel_data: Dict[str, float]) -> go.Figure:
    """Cria radar chart para painel completo.
    
    Args:
        panel_data: Dicionário {exame: valor_normalizado}
        
    Returns:
        Figura Plotly
    """
    categories = list(panel_data.keys())
    values = list(panel_data.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Valores',
        line=dict(color=THEME_COLORS["primary"])
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=False,
        title="Painel de Exames (Normalizado)"
    )
    
    return fig


def create_correlation_network(correlations: List[Dict[str, Any]]) -> go.Figure:
    """Cria gráfico de rede de correlações.
    
    Args:
        correlations: Lista de correlações detectadas
        
    Returns:
        Figura Plotly
    """
    # Simplificado - apenas mostra correlações como barras
    patterns = [c.get("pattern_name", "") for c in correlations]
    significances = [c.get("significance", "normal") for c in correlations]
    
    colors = [STATUS_COLORS.get(s.lower(), "#6c757d") for s in significances]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=patterns,
        x=[1] * len(patterns),
        orientation='h',
        marker=dict(color=colors),
        text=significances,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Padrões Clínicos Detectados",
        xaxis_title="",
        yaxis_title="Padrão",
        showlegend=False,
        height=max(200, len(patterns) * 50)
    )
    
    return fig


def create_trend_line_chart(dates: List[str], values: List[float], 
                            lab_name: str, min_ref: float = None, 
                            max_ref: float = None) -> go.Figure:
    """Cria gráfico de linha de tendências.
    
    Args:
        dates: Lista de datas
        values: Lista de valores
        lab_name: Nome do exame
        min_ref: Valor mínimo de referência (opcional)
        max_ref: Valor máximo de referência (opcional)
        
    Returns:
        Figura Plotly
    """
    fig = go.Figure()
    
    # Linha de valores
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name=lab_name,
        line=dict(color=THEME_COLORS["primary"], width=2),
        marker=dict(size=8)
    ))
    
    # Faixas de referência
    if min_ref is not None and max_ref is not None:
        fig.add_hrect(
            y0=min_ref, y1=max_ref,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="Faixa Normal",
            annotation_position="top left"
        )
    
    fig.update_layout(
        title=f"Tendência: {lab_name}",
        xaxis_title="Data",
        yaxis_title="Valor",
        hovermode='x unified',
        height=400
    )
    
    return fig

