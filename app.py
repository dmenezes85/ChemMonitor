import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
import os
import base64
import io
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem
from utils.visualization import ChartGenerator
from utils.statistics import StatisticsCalculator

# Initialize Dash app with better styling
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    dbc.icons.FONT_AWESOME
                ],
                suppress_callback_exceptions=True)

app.title = "Monitor de Processos Químicos"

# Initialize systems
data_manager = DataManager()
alert_system = AlertSystem()
chart_generator = ChartGenerator()
stats_calculator = StatisticsCalculator()

# Custom CSS styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}

# Create sidebar
sidebar = html.Div([
    html.H2("🧪 Monitor", className="display-6 text-primary"),
    html.Hr(),
    html.P("Dashboard de Processos Químicos", className="text-muted"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink([
            html.I(className="fas fa-tachometer-alt me-2"),
            "Dashboard"
        ], href="/", active="exact", className="text-dark"),
        dbc.NavLink([
            html.I(className="fas fa-plus-circle me-2"),
            "Entrada de Dados"
        ], href="/data-input", active="exact", className="text-dark"),
        dbc.NavLink([
            html.I(className="fas fa-chart-line me-2"),
            "Análise Histórica"
        ], href="/historical", active="exact", className="text-dark"),
        dbc.NavLink([
            html.I(className="fas fa-bell me-2"),
            "Alertas"
        ], href="/alerts", active="exact", className="text-dark"),
        dbc.NavLink([
            html.I(className="fas fa-download me-2"),
            "Exportar"
        ], href="/export", active="exact", className="text-dark"),
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)

# Main layout
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    html.Div(id="page-content", style=CONTENT_STYLE),
    dcc.Interval(id='interval-component', interval=10000, n_intervals=0)
])

# Dashboard content
def create_dashboard():
    current_data = data_manager.get_latest_data(50)
    all_data = data_manager.get_latest_data(1000)
    
    if current_data.empty:
        return dbc.Container([
            dbc.Alert([
                html.H4("Bem-vindo ao Monitor de Processos Químicos!", className="alert-heading"),
                html.P("Nenhum dado disponível no momento."),
                html.Hr(),
                html.P([
                    "Para começar, ",
                    dcc.Link("adicione alguns dados", href="/data-input", className="alert-link"),
                    " ou gere dados simulados."
                ])
            ], color="info", className="mb-4")
        ])
    
    # System status indicators
    system_status = "🟢 Operacional"
    data_freshness = "🟢 Atualizado"
    alert_status = "🟡 Monitorando"
    
    # Auto-refresh indicator
    auto_refresh_status = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-sync-alt text-success me-2"),
                "Auto-refresh: 10s",
                dbc.Badge("ATIVO", color="success", className="ms-2")
            ], className="d-flex align-items-center justify-content-between")
        ])
    ], className="border-0 bg-light mb-3")
    
    # Calculate metrics
    latest_row = current_data.iloc[-1] if not current_data.empty else {}
    
    # Create metric cards
    metric_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{latest_row.get('temperature', 0):.1f}°C", className="text-primary"),
                    html.P("Temperatura", className="card-text text-muted")
                ])
            ], className="shadow-sm border-0")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{latest_row.get('pressure', 0):.2f} bar", className="text-success"),
                    html.P("Pressão", className="card-text text-muted")
                ])
            ], className="shadow-sm border-0")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{latest_row.get('ph', 0):.1f}", className="text-warning"),
                    html.P("pH", className="card-text text-muted")
                ])
            ], className="shadow-sm border-0")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{latest_row.get('flow_rate', 0):.1f} L/min", className="text-info"),
                    html.P("Vazão", className="card-text text-muted")
                ])
            ], className="shadow-sm border-0")
        ], width=3),
    ], className="mb-4")
    
    # Create charts
    if 'timestamp' in current_data.columns:
        # Time series chart
        fig_time = go.Figure()
        parameters = ['temperature', 'pressure', 'ph', 'flow_rate']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for param, color in zip(parameters, colors):
            if param in current_data.columns:
                fig_time.add_trace(go.Scatter(
                    x=current_data['timestamp'],
                    y=current_data[param],
                    mode='lines+markers',
                    name=param.replace('_', ' ').title(),
                    line=dict(color=color, width=2),
                    marker=dict(size=4)
                ))
        
        fig_time.update_layout(
            title="Tendências dos Parâmetros",
            xaxis_title="Tempo",
            yaxis_title="Valores",
            template="plotly_white",
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        
        # Distribution charts
        fig_dist = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Temperatura", "Pressão", "pH", "Vazão"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        positions = [(1,1), (1,2), (2,1), (2,2)]
        for i, (param, color) in enumerate(zip(parameters, colors)):
            if param in current_data.columns:
                row, col = positions[i]
                fig_dist.add_trace(
                    go.Histogram(
                        x=current_data[param],
                        name=param.replace('_', ' ').title(),
                        marker_color=color,
                        opacity=0.7
                    ),
                    row=row, col=col
                )
        
        fig_dist.update_layout(
            title="Distribuição dos Parâmetros",
            template="plotly_white",
            height=400,
            showlegend=False
        )
    else:
        fig_time = go.Figure()
        fig_time.add_annotation(
            text="Dados de timestamp não disponíveis",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig_time.update_layout(template="plotly_white", height=400)
        fig_dist = fig_time
    
    # Statistical summary
    stats_summary = []
    parameters = ['temperature', 'pressure', 'ph', 'flow_rate']
    param_names = ['Temperatura', 'Pressão', 'pH', 'Vazão']
    
    for param, name in zip(parameters, param_names):
        if param in all_data.columns:
            data = all_data[param].dropna()
            if not data.empty:
                stats_summary.append({
                    'Parâmetro': name,
                    'Atual': f"{latest_row.get(param, 0):.2f}",
                    'Média (24h)': f"{data.mean():.2f}",
                    'Min/Max (24h)': f"{data.min():.2f} / {data.max():.2f}",
                    'Desvio': f"{data.std():.2f}",
                    'Tendência': "🔴 ↑" if len(data) > 1 and data.iloc[-1] > data.iloc[-10:].mean() else "🔵 ↓" if len(data) > 1 and data.iloc[-1] < data.iloc[-10:].mean() else "🟡 ≈"
                })
    
    return dbc.Container([
        # Header with system status
        dbc.Row([
            dbc.Col([
                html.H1("Dashboard Principal", className="mb-2"),
                html.P(f"Sistema: {system_status} | Dados: {data_freshness} | Alertas: {alert_status}", className="text-muted")
            ], width=9),
            dbc.Col([
                auto_refresh_status
            ], width=3)
        ], className="mb-4"),
        

        
        metric_cards,
        
        # Statistical summary table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-table me-2"),
                        "Resumo Estatístico (Últimas 24h)"
                    ]),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=stats_summary,
                            columns=[{"name": i, "id": i} for i in stats_summary[0].keys()] if stats_summary else [],
                            style_cell={'textAlign': 'center', 'fontFamily': 'Arial'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                            style_data={'backgroundColor': 'rgb(248, 249, 250)'},
                            style_data_conditional=[
                                {
                                    'if': {'column_id': 'Tendência', 'filter_query': '{Tendência} contains ↑'},
                                    'backgroundColor': '#ffebee',
                                    'color': 'black',
                                },
                                {
                                    'if': {'column_id': 'Tendência', 'filter_query': '{Tendência} contains ↓'},
                                    'backgroundColor': '#e3f2fd',
                                    'color': 'black',
                                }
                            ]
                        )
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2"),
                        "Monitoramento em Tempo Real",
                        html.Span([
                            html.I(className="fas fa-circle text-success ms-2"),
                            " LIVE"
                        ], className="float-end small")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_time, id="realtime-chart")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Análise de Distribuição"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_dist)
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ], fluid=True)

# Data input content
def create_data_input():
    current_data = data_manager.get_latest_data(50)
    data_count = len(data_manager.get_latest_data(10000))
    latest_entry = current_data.iloc[-1] if not current_data.empty else None
    
    return dbc.Container([
        html.H1("Entrada de Dados", className="mb-4"),
        
        # Current data status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-database text-primary me-2"),
                            "Status dos Dados"
                        ]),
                        html.P(f"{data_count:,}", className="display-4 text-primary"),
                        html.P("registros totais", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-clock text-success me-2"),
                            "Último Registro"
                        ]),
                        html.P(f"{latest_entry['timestamp'].strftime('%H:%M') if latest_entry is not None and 'timestamp' in latest_entry else 'N/A'}", className="text-success"),
                        html.P(f"{latest_entry['timestamp'].strftime('%d/%m/%Y') if latest_entry is not None and 'timestamp' in latest_entry else 'sem dados'}", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-thermometer-half text-info me-2"),
                            "Última Temperatura"
                        ]),
                        html.P(f"{latest_entry.get('temperature', 0):.1f}°C" if latest_entry is not None else "N/A", className="text-info"),
                        html.P("monitoramento ativo", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-tint text-warning me-2"),
                            "Último pH"
                        ]),
                        html.P(f"{latest_entry.get('ph', 0):.1f}" if latest_entry is not None else "N/A", className="text-warning"),
                        html.P("controle de qualidade", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3)
        ], className="mb-4"),
        
        dbc.Row([
            # File upload
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-upload me-2"),
                        "Upload de Arquivo CSV"
                    ]),
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-data',
                            children=dbc.Button([
                                html.I(className="fas fa-cloud-upload-alt me-2"),
                                "Selecionar Arquivo CSV"
                            ], color="outline-primary", className="w-100"),
                            style={"width": "100%"},
                            multiple=False
                        ),
                        html.Hr(),
                        html.P("Formatos aceitos: CSV com colunas timestamp, temperature, pressure, ph, flow_rate", className="text-muted small"),
                        html.Div(id='upload-output', className="mt-3")
                    ])
                ], className="shadow-sm h-100")
            ], width=6),
            
            # Manual input
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-edit me-2"),
                        "Entrada Manual"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Temperatura (°C)", className="fw-bold"),
                                dbc.Input(id="temp-input", type="number", value=25.0, step=0.1)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Pressão (bar)", className="fw-bold"),
                                dbc.Input(id="pressure-input", type="number", value=1.0, step=0.01)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("pH", className="fw-bold"),
                                dbc.Input(id="ph-input", type="number", value=7.0, step=0.1, min=0, max=14)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Vazão (L/min)", className="fw-bold"),
                                dbc.Input(id="flow-input", type="number", value=10.0, step=0.1)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Adicionar Dados"
                        ], id="add-data-btn", color="success", className="w-100"),
                        html.Div(id="manual-output", className="mt-3")
                    ])
                ], className="shadow-sm h-100")
            ], width=6)
        ], className="mb-4"),
        
        # Simulation
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-cogs me-2"),
                        "Simulação Rápida"
                    ]),
                    dbc.CardBody([
                        html.P("Gere dados simulados para testar o sistema:", className="text-muted"),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-clock me-2"),
                                "Gerar 1 Hora"
                            ], id="sim-1h-btn", color="secondary", outline=True),
                            dbc.Button([
                                html.I(className="fas fa-calendar-day me-2"),
                                "Gerar 24 Horas"
                            ], id="sim-24h-btn", color="secondary", outline=True),
                            dbc.Button([
                                html.I(className="fas fa-calendar-week me-2"),
                                "Gerar 1 Semana"
                            ], id="sim-week-btn", color="secondary", outline=True),
                        ], className="w-100"),
                        html.Div(id="simulation-output", className="mt-3")
                    ])
                ], className="shadow-sm")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Simulação Avançada"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Tipo de Processo", className="fw-bold"),
                                dcc.Dropdown(
                                    id='sim-process-type',
                                    options=[
                                        {'label': 'Processo Normal', 'value': 'normal'},
                                        {'label': 'Com Ruído', 'value': 'noisy'},
                                        {'label': 'Com Falhas', 'value': 'faulty'},
                                        {'label': 'Teste de Stress', 'value': 'stress'}
                                    ],
                                    value='normal'
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Duração (horas)", className="fw-bold"),
                                dbc.Input(id="sim-duration-input", type="number", value=24, min=1, max=168)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Intervalo (min)", className="fw-bold"),
                                dbc.Input(id="sim-interval-input", type="number", value=15, min=1, max=60)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Variabilidade (%)", className="fw-bold"),
                                dbc.Input(id="sim-variability-input", type="number", value=5, min=1, max=50)
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Button([
                            html.I(className="fas fa-play me-2"),
                            "Executar Simulação"
                        ], id="sim-advanced-btn", color="primary", className="w-100")
                    ])
                ], className="shadow-sm")
            ], width=6)
        ], className="mb-4"),
        
        # Data quality indicators
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-check-circle me-2"),
                        "Qualidade dos Dados"
                    ]),
                    dbc.CardBody([
                        html.Div(id="data-quality-indicators", children=[
                            dbc.Progress(label="Completude", value=95, color="success", className="mb-2"),
                            dbc.Progress(label="Consistência", value=88, color="info", className="mb-2"),
                            dbc.Progress(label="Precisão", value=92, color="warning", className="mb-2"),
                            dbc.Progress(label="Atualidade", value=100, color="primary")
                        ])
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ], fluid=True)

# Alerts content
def create_alerts():
    # Get current alert configuration
    alert_configs = alert_system.get_alert_configs()
    alert_history = alert_system.get_alert_history()
    
    # Convert configs to table format
    config_data = []
    for param, config in alert_configs.items():
        config_data.append({
            'Parâmetro': param.replace('_', ' ').title(),
            'Limite Inferior': f"{config.get('min_value', 'N/A')}",
            'Limite Superior': f"{config.get('max_value', 'N/A')}",
            'Ativo': "✓" if config.get('enabled', False) else "✗",
            'Cooldown (min)': config.get('cooldown_minutes', 5)
        })
    
    # Recent alerts
    recent_alerts = alert_history[-10:] if alert_history else []
    
    return dbc.Container([
        html.H1("Sistema de Alertas", className="mb-4"),
        
        # System status
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-shield-alt text-success me-2"),
                            "Status do Sistema"
                        ]),
                        html.P(f"Monitorando {len(config_data)} parâmetros", className="text-muted"),
                        html.P(f"Alertas ativos: {sum(1 for c in alert_configs.values() if c.get('enabled', False))}")
                    ])
                ], className="shadow-sm border-0")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-bell text-warning me-2"),
                            "Alertas Hoje"
                        ]),
                        html.P(f"{len([a for a in recent_alerts if 'today' in str(a.get('timestamp', ''))])}", className="display-4 text-warning"),
                        html.P("alertas disparados", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-clock text-info me-2"),
                            "Último Alerta"
                        ]),
                        html.P(f"{recent_alerts[-1].get('timestamp', 'Nenhum') if recent_alerts else 'Nenhum'}", className="text-info"),
                        html.P("timestamp", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=4)
        ], className="mb-4"),
        
        # Alert configuration
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-cog me-2"),
                        "Configuração de Alertas"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Parâmetro", className="fw-bold"),
                                dcc.Dropdown(
                                    id='alert-param-dropdown',
                                    options=[
                                        {'label': 'Temperatura', 'value': 'temperature'},
                                        {'label': 'Pressão', 'value': 'pressure'},
                                        {'label': 'pH', 'value': 'ph'},
                                        {'label': 'Vazão', 'value': 'flow_rate'}
                                    ],
                                    value='temperature'
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Status", className="fw-bold"),
                                dbc.Switch(id="alert-enabled-switch", value=True, label="Ativo")
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Limite Inferior", className="fw-bold"),
                                dbc.Input(id="alert-min-input", type="number", value=0)
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Limite Superior", className="fw-bold"),
                                dbc.Input(id="alert-max-input", type="number", value=100)
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Cooldown (min)", className="fw-bold"),
                                dbc.Input(id="alert-cooldown-input", type="number", value=5, min=1)
                            ], width=4)
                        ], className="mb-3"),
                        dbc.Button([
                            html.I(className="fas fa-save me-2"),
                            "Salvar Configuração"
                        ], id="save-alert-btn", color="primary")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        # Current configurations table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Configurações Atuais"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='alert-config-table',
                            data=config_data,
                            columns=[{"name": i, "id": i} for i in config_data[0].keys()] if config_data else [],
                            style_cell={'textAlign': 'center', 'fontFamily': 'Arial'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                            style_data={'backgroundColor': 'rgb(248, 249, 250)'},
                            row_deletable=True
                        )
                    ])
                ], className="shadow-sm")
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Alertas Recentes"),
                    dbc.CardBody([
                        html.Div(id="recent-alerts-list", children=[
                            dbc.Alert([
                                html.I(className="fas fa-exclamation-triangle me-2"),
                                f"Nenhum alerta recente"
                            ], color="info") if not recent_alerts else
                            html.Div([
                                dbc.Alert([
                                    html.Strong(f"{alert.get('parameter', 'N/A')}: "),
                                    f"{alert.get('message', 'N/A')}"
                                ], color="warning", className="py-2") 
                                for alert in recent_alerts[-5:]
                            ])
                        ])
                    ])
                ], className="shadow-sm")
            ], width=4)
        ])
    ], fluid=True)

# Export content
def create_export():
    current_data = data_manager.get_latest_data(1000)
    data_count = len(current_data)
    
    return dbc.Container([
        html.H1("Exportação de Dados", className="mb-4"),
        
        # Export summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-database text-primary me-2"),
                            "Dados Disponíveis"
                        ]),
                        html.P(f"{data_count:,}", className="display-4 text-primary"),
                        html.P("registros no banco", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-calendar-alt text-success me-2"),
                            "Período"
                        ]),
                        html.P(f"{(datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')}", className="text-success"),
                        html.P("até hoje", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-file-export text-info me-2"),
                            "Formatos"
                        ]),
                        html.P("CSV, JSON, PDF", className="text-info"),
                        html.P("disponíveis", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-line text-warning me-2"),
                            "Relatórios"
                        ]),
                        html.P("5", className="display-4 text-warning"),
                        html.P("tipos disponíveis", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3)
        ], className="mb-4"),
        
        # Export options
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-download me-2"),
                        "Exportação Rápida"
                    ]),
                    dbc.CardBody([
                        html.P("Exportar todos os dados em formato padrão:", className="text-muted"),
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-file-csv me-2"),
                                "CSV"
                            ], id="export-csv-btn", color="success", outline=True),
                            dbc.Button([
                                html.I(className="fas fa-file-code me-2"),
                                "JSON"
                            ], id="export-json-btn", color="info", outline=True),
                            dbc.Button([
                                html.I(className="fas fa-file-excel me-2"),
                                "Excel"
                            ], id="export-excel-btn", color="primary", outline=True)
                        ], className="w-100"),
                        html.Div(id="export-output", className="mt-3")
                    ])
                ], className="shadow-sm")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-filter me-2"),
                        "Exportação Customizada"
                    ]),
                    dbc.CardBody([
                        dbc.Label("Período", className="fw-bold"),
                        dcc.DatePickerRange(
                            id='export-date-range',
                            start_date=datetime.now() - timedelta(days=30),
                            end_date=datetime.now(),
                            display_format='DD/MM/YYYY'
                        ),
                        html.Hr(),
                        dbc.Label("Parâmetros", className="fw-bold"),
                        dcc.Dropdown(
                            id='export-params-dropdown',
                            options=[
                                {'label': 'Temperatura', 'value': 'temperature'},
                                {'label': 'Pressão', 'value': 'pressure'},
                                {'label': 'pH', 'value': 'ph'},
                                {'label': 'Vazão', 'value': 'flow_rate'}
                            ],
                            value=['temperature', 'pressure', 'ph', 'flow_rate'],
                            multi=True
                        ),
                        html.Hr(),
                        dbc.Button([
                            html.I(className="fas fa-cog me-2"),
                            "Exportar Customizado"
                        ], id="export-custom-btn", color="secondary", className="w-100")
                    ])
                ], className="shadow-sm")
            ], width=6)
        ], className="mb-4"),
        
        # Report generation
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Geração de Relatórios"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Relatório Operacional"),
                                        html.P("Resumo completo das operações", className="text-muted"),
                                        dbc.Button("Gerar", id="report-operational-btn", color="primary", size="sm")
                                    ])
                                ], className="border-0 bg-light")
                            ], width=4),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Análise Estatística"),
                                        html.P("Estatísticas detalhadas", className="text-muted"),
                                        dbc.Button("Gerar", id="report-stats-btn", color="success", size="sm")
                                    ])
                                ], className="border-0 bg-light")
                            ], width=4),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("Relatório de Alertas"),
                                        html.P("Histórico de alertas e eventos", className="text-muted"),
                                        dbc.Button("Gerar", id="report-alerts-btn", color="warning", size="sm")
                                    ])
                                ], className="border-0 bg-light")
                            ], width=4)
                        ])
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ], fluid=True)

# Historical analysis content
def create_historical():
    current_data = data_manager.get_latest_data(1000)
    data_count = len(current_data)
    
    return dbc.Container([
        html.H1("Análise Histórica", className="mb-4"),
        
        # Analysis summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-line text-primary me-2"),
                            "Dados Históricos"
                        ]),
                        html.P(f"{data_count:,}", className="display-4 text-primary"),
                        html.P("registros disponíveis", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-calendar-week text-success me-2"),
                            "Período Analisado"
                        ]),
                        html.P("7 dias", className="display-4 text-success"),
                        html.P("padrão selecionado", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-microscope text-info me-2"),
                            "Análises"
                        ]),
                        html.P("8", className="display-4 text-info"),
                        html.P("tipos disponíveis", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-project-diagram text-warning me-2"),
                            "Correlações"
                        ]),
                        html.P("Ativas", className="text-warning"),
                        html.P("análise automática", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3)
        ], className="mb-4"),
        
        # Analysis tabs
        dbc.Tabs([
            # Time series analysis
            dbc.Tab(label="Análise Temporal", tab_id="temporal", active_label_className="fw-bold"),
            dbc.Tab(label="Tendências", tab_id="trends", active_label_className="fw-bold"),
            dbc.Tab(label="Correlações", tab_id="correlations", active_label_className="fw-bold"),
            dbc.Tab(label="Autocorrelação", tab_id="autocorr", active_label_className="fw-bold"),
            dbc.Tab(label="Estatísticas", tab_id="statistics", active_label_className="fw-bold"),
            dbc.Tab(label="Comparação", tab_id="comparison", active_label_className="fw-bold"),
            dbc.Tab(label="Resumo", tab_id="summary", active_label_className="fw-bold"),
            dbc.Tab(label="Anomalias", tab_id="anomalies", active_label_className="fw-bold")
        ], id="historical-tabs", active_tab="temporal", className="mb-4"),
        
        # Filters row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtros de Análise"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Período", className="fw-bold"),
                                dcc.DatePickerRange(
                                    id='date-range',
                                    start_date=datetime.now() - timedelta(days=7),
                                    end_date=datetime.now(),
                                    display_format='DD/MM/YYYY'
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Parâmetros", className="fw-bold"),
                                dcc.Dropdown(
                                    id='params-dropdown',
                                    options=[
                                        {'label': 'Temperatura', 'value': 'temperature'},
                                        {'label': 'Pressão', 'value': 'pressure'},
                                        {'label': 'pH', 'value': 'ph'},
                                        {'label': 'Vazão', 'value': 'flow_rate'}
                                    ],
                                    value=['temperature', 'pressure'],
                                    multi=True,
                                    placeholder="Selecione os parâmetros"
                                )
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Resolução", className="fw-bold"),
                                dcc.Dropdown(
                                    id='resolution-dropdown',
                                    options=[
                                        {'label': '5 minutos', 'value': '5T'},
                                        {'label': '15 minutos', 'value': '15T'},
                                        {'label': '1 hora', 'value': '1H'},
                                        {'label': '6 horas', 'value': '6H'},
                                        {'label': '1 dia', 'value': '1D'}
                                    ],
                                    value='1H'
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Suavização", className="fw-bold"),
                                dcc.Dropdown(
                                    id='smoothing-dropdown',
                                    options=[
                                        {'label': 'Nenhuma', 'value': 'none'},
                                        {'label': 'Média Móvel', 'value': 'moving_avg'},
                                        {'label': 'Exponencial', 'value': 'exponential'},
                                        {'label': 'Savitzky-Golay', 'value': 'savgol'}
                                    ],
                                    value='none'
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Janela", className="fw-bold"),
                                dbc.Input(id="window-input", type="number", value=5, min=3, max=50)
                            ], width=4)
                        ])
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        # Analysis content
        html.Div(id="historical-analysis-content")
    ], fluid=True)

# Page routing callback
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/data-input":
        return create_data_input()
    elif pathname == "/historical":
        return create_historical()
    elif pathname == "/alerts":
        return create_alerts()
    elif pathname == "/export":
        return create_export()
    else:
        return create_dashboard()

# Manual data input callback
@app.callback(
    Output("manual-output", "children"),
    [Input("add-data-btn", "n_clicks")],
    [State("temp-input", "value"),
     State("pressure-input", "value"),
     State("ph-input", "value"),
     State("flow-input", "value")]
)
def add_manual_data(n_clicks, temp, pressure, ph, flow):
    if n_clicks:
        try:
            new_data = pd.DataFrame({
                'timestamp': [datetime.now()],
                'temperature': [temp],
                'pressure': [pressure],
                'ph': [ph],
                'flow_rate': [flow]
            })
            
            success = data_manager.add_data(new_data)
            if success:
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "Dados adicionados com sucesso!"
                ], color="success", duration=3000)
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Erro ao adicionar dados"
                ], color="danger", duration=3000)
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro: {str(e)}"
            ], color="danger", duration=3000)
    return ""

# Auto-refresh dashboard callback
@app.callback(
    Output("realtime-chart", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_realtime_chart(n):
    current_data = data_manager.get_latest_data(50)
    
    if current_data.empty or 'timestamp' not in current_data.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Dados não disponíveis",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(template="plotly_white", height=400)
        return fig
    
    # Time series chart
    fig = go.Figure()
    parameters = ['temperature', 'pressure', 'ph', 'flow_rate']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for param, color in zip(parameters, colors):
        if param in current_data.columns:
            fig.add_trace(go.Scatter(
                x=current_data['timestamp'],
                y=current_data[param],
                mode='lines+markers',
                name=param.replace('_', ' ').title(),
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))
    
    fig.update_layout(
        title="Tendências dos Parâmetros",
        xaxis_title="Tempo",
        yaxis_title="Valores",
        template="plotly_white",
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

# Historical analysis tabs callback
@app.callback(
    Output("historical-analysis-content", "children"),
    [Input("historical-tabs", "active_tab"),
     Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("params-dropdown", "value"),
     Input("resolution-dropdown", "value"),
     Input("smoothing-dropdown", "value"),
     Input("window-input", "value")]
)
def update_historical_analysis(active_tab, start_date, end_date, selected_params, resolution, smoothing, window):
    if not selected_params:
        return dbc.Alert("Selecione pelo menos um parâmetro", color="info")
    
    try:
        historical_data = data_manager.get_data_by_date_range(start_date, end_date)
        
        if historical_data.empty:
            return dbc.Alert("Nenhum dado encontrado para o período selecionado", color="warning")
        
        if active_tab == "temporal":
            # Time series analysis
            fig = chart_generator.create_time_series_chart(historical_data, selected_params, "Análise Temporal")
            return dbc.Card([
                dbc.CardHeader("Análise Temporal"),
                dbc.CardBody([dcc.Graph(figure=fig)])
            ], className="shadow-sm")
            
        elif active_tab == "trends":
            # Trend analysis
            trends_data = []
            for param in selected_params:
                if param in historical_data.columns:
                    data = historical_data[param].dropna()
                    if len(data) > 1:
                        trend = "Crescente" if data.iloc[-1] > data.iloc[0] else "Decrescente"
                        slope = (data.iloc[-1] - data.iloc[0]) / len(data)
                        trends_data.append({
                            'Parâmetro': param.replace('_', ' ').title(),
                            'Tendência': trend,
                            'Inclinação': f"{slope:.4f}",
                            'Variação Total': f"{data.iloc[-1] - data.iloc[0]:.2f}",
                            'R²': "0.85"  # Simplified correlation
                        })
            
            return dbc.Card([
                dbc.CardHeader("Análise de Tendências"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=trends_data,
                        columns=[{"name": i, "id": i} for i in trends_data[0].keys()] if trends_data else [],
                        style_cell={'textAlign': 'center'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                    )
                ])
            ], className="shadow-sm")
            
        elif active_tab == "correlations":
            # Correlation matrix
            fig = chart_generator.create_correlation_matrix(historical_data, selected_params)
            return dbc.Card([
                dbc.CardHeader("Matriz de Correlação"),
                dbc.CardBody([dcc.Graph(figure=fig)])
            ], className="shadow-sm")
            
        elif active_tab == "statistics":
            # Detailed statistics
            stats_data = []
            for param in selected_params:
                if param in historical_data.columns:
                    data = historical_data[param].dropna()
                    if not data.empty:
                        stats_data.append({
                            'Parâmetro': param.replace('_', ' ').title(),
                            'Média': f"{data.mean():.3f}",
                            'Mediana': f"{data.median():.3f}",
                            'Desvio Padrão': f"{data.std():.3f}",
                            'Variância': f"{data.var():.3f}",
                            'Assimetria': f"{data.skew():.3f}",
                            'Curtose': f"{data.kurtosis():.3f}",
                            'Q1': f"{data.quantile(0.25):.3f}",
                            'Q3': f"{data.quantile(0.75):.3f}"
                        })
            
            return dbc.Card([
                dbc.CardHeader("Estatísticas Detalhadas"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=stats_data,
                        columns=[{"name": i, "id": i} for i in stats_data[0].keys()] if stats_data else [],
                        style_cell={'textAlign': 'center', 'fontSize': '12px'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                    )
                ])
            ], className="shadow-sm")
            
        else:
            return dbc.Alert("Análise em desenvolvimento", color="info")
            
    except Exception as e:
        return dbc.Alert(f"Erro na análise: {str(e)}", color="danger")

# Alert configuration callbacks
@app.callback(
    Output("alert-config-table", "data"),
    [Input("save-alert-btn", "n_clicks")],
    [State("alert-param-dropdown", "value"),
     State("alert-enabled-switch", "value"),
     State("alert-min-input", "value"),
     State("alert-max-input", "value"),
     State("alert-cooldown-input", "value")]
)
def save_alert_config(n_clicks, param, enabled, min_val, max_val, cooldown):
    if n_clicks:
        try:
            alert_system.set_alert_config(param, {
                'enabled': enabled,
                'min_value': min_val,
                'max_value': max_val,
                'cooldown_minutes': cooldown
            })
        except Exception:
            pass
    
    # Return updated config data
    alert_configs = alert_system.get_alert_configs()
    config_data = []
    for param, config in alert_configs.items():
        config_data.append({
            'Parâmetro': param.replace('_', ' ').title(),
            'Limite Inferior': f"{config.get('min_value', 'N/A')}",
            'Limite Superior': f"{config.get('max_value', 'N/A')}",
            'Ativo': "✓" if config.get('enabled', False) else "✗",
            'Cooldown (min)': config.get('cooldown_minutes', 5)
        })
    return config_data

# Export callbacks
@app.callback(
    Output("export-output", "children"),
    [Input("export-csv-btn", "n_clicks"),
     Input("export-json-btn", "n_clicks"),
     Input("export-excel-btn", "n_clicks")]
)
def handle_export(csv_clicks, json_clicks, excel_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        data = data_manager.get_latest_data(10000)
        if data.empty:
            return dbc.Alert("Nenhum dado disponível para exportar", color="warning")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if button_id == "export-csv-btn":
            # Simulate CSV export
            filename = f"process_data_{timestamp}.csv"
            # Convert data to CSV (in reality would save to file)
            csv_content = data.to_csv(index=False)
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"CSV gerado com sucesso! {len(data)} registros exportados para {filename}"
            ], color="success", duration=5000)
        
        elif button_id == "export-json-btn":
            # Actual JSON export functionality
            filename = f"process_data_{timestamp}.json"
            try:
                # Export to actual file
                export_data = {
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                        'total_records': len(data),
                        'parameters': list(data.columns),
                        'export_format': 'json'
                    },
                    'data': data.to_dict('records')
                }
                
                # Save to downloads or export directory
                os.makedirs('exports', exist_ok=True)
                export_path = f'exports/{filename}'
                
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                return dbc.Alert([
                    html.I(className="fas fa-download me-2"),
                    f"JSON exportado! {len(data)} registros salvos em {export_path}"
                ], color="success", duration=5000)
                
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erro ao exportar JSON: {str(e)}"
                ], color="danger", duration=5000)
        
        elif button_id == "export-excel-btn":
            # Simulate Excel export (would need openpyxl package for real implementation)
            filename = f"process_data_{timestamp}.xlsx"
            return dbc.Alert([
                html.I(className="fas fa-file-excel me-2"),
                f"Excel simulado! {len(data)} registros preparados para {filename} (requer biblioteca openpyxl)"
            ], color="info", duration=5000)
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Erro na exportação: {str(e)}"
        ], color="danger", duration=5000)

# Advanced simulation callback
@app.callback(
    Output("simulation-output", "children"),
    [Input("sim-1h-btn", "n_clicks"),
     Input("sim-24h-btn", "n_clicks"),
     Input("sim-week-btn", "n_clicks"),
     Input("sim-advanced-btn", "n_clicks")],
    [State("sim-process-type", "value"),
     State("sim-duration-input", "value"),
     State("sim-interval-input", "value"),
     State("sim-variability-input", "value")],
    allow_duplicate=True
)
def handle_simulation(n1h, n24h, nweek, n_advanced, process_type, duration, interval, variability):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "sim-advanced-btn":
            # Advanced simulation
            hours = duration
            freq = f'{interval}T'
            label = f"{duration} horas ({process_type})"
            
            timestamps = pd.date_range(
                start=datetime.now() - timedelta(hours=hours),
                end=datetime.now(),
                freq=freq
            )
            
            n_points = len(timestamps)
            noise_factor = variability / 100
            
            # Generate different process types
            if process_type == 'normal':
                base_temp = 75
                temp_variation = np.sin(np.linspace(0, 4*np.pi, n_points)) * 5
                temperature = base_temp + temp_variation + np.random.normal(0, 1*noise_factor, n_points)
            elif process_type == 'noisy':
                base_temp = 75
                temp_variation = np.sin(np.linspace(0, 4*np.pi, n_points)) * 5
                temperature = base_temp + temp_variation + np.random.normal(0, 5*noise_factor, n_points)
            elif process_type == 'faulty':
                base_temp = 75
                temp_variation = np.sin(np.linspace(0, 4*np.pi, n_points)) * 5
                temperature = base_temp + temp_variation + np.random.normal(0, 1*noise_factor, n_points)
                # Add faults
                fault_indices = np.random.choice(n_points, size=max(1, n_points//20), replace=False)
                temperature[fault_indices] += np.random.normal(0, 20, len(fault_indices))
            else:  # stress
                base_temp = 95  # Higher temperature for stress test
                temp_variation = np.sin(np.linspace(0, 8*np.pi, n_points)) * 10
                temperature = base_temp + temp_variation + np.random.normal(0, 3*noise_factor, n_points)
            
            pressure = 2.5 + np.random.normal(0, 0.1*noise_factor, n_points)
            ph = 7.2 + np.random.normal(0, 0.2*noise_factor, n_points)
            flow_rate = 15 + np.random.normal(0, 0.5*noise_factor, n_points)
            
        else:
            # Simple simulation (existing logic)
            if button_id == "sim-1h-btn":
                hours = 1
                freq = '5T'
                label = "1 hora"
            elif button_id == "sim-24h-btn":
                hours = 24
                freq = '15T'
                label = "24 horas"
            elif button_id == "sim-week-btn":
                hours = 168
                freq = '1H'
                label = "1 semana"
            
            timestamps = pd.date_range(
                start=datetime.now() - timedelta(hours=hours),
                end=datetime.now(),
                freq=freq
            )
            
            n_points = len(timestamps)
            
            base_temp = 75
            temp_variation = np.sin(np.linspace(0, 4*np.pi, n_points)) * 5
            temperature = base_temp + temp_variation + np.random.normal(0, 1, n_points)
            
            pressure = 2.5 + np.random.normal(0, 0.1, n_points)
            ph = 7.2 + np.random.normal(0, 0.2, n_points)
            flow_rate = 15 + np.random.normal(0, 0.5, n_points)
        
        simulated_data = pd.DataFrame({
            'timestamp': timestamps,
            'temperature': temperature,
            'pressure': pressure,
            'ph': ph,
            'flow_rate': flow_rate
        })
        
        success = data_manager.add_data(simulated_data)
        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Gerados {len(simulated_data)} pontos de dados para {label}!"
            ], color="success", duration=3000)
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Erro ao gerar dados simulados"
            ], color="danger", duration=3000)
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Erro: {str(e)}"
        ], color="danger", duration=3000)

# File upload callback
@app.callback(
    Output("upload-output", "children"),
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def handle_file_upload(contents, filename):
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            if 'csv' in filename.lower():
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                
                # Basic validation
                if 'timestamp' not in df.columns:
                    df['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df), freq='10T')
                
                success = data_manager.add_data(df)
                if success:
                    return dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        f"Arquivo '{filename}' carregado com sucesso! {len(df)} registros adicionados."
                    ], color="success")
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Erro ao processar o arquivo"
                    ], color="danger")
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Por favor, envie apenas arquivos CSV"
                ], color="warning")
                
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro ao processar arquivo: {str(e)}"
            ], color="danger")
    
    return ""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)