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
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
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
    
    return dbc.Container([
        html.H1("Dashboard Principal", className="mb-4"),
        metric_cards,
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Monitoramento em Tempo Real"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_time)
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
    return dbc.Container([
        html.H1("Entrada de Dados", className="mb-4"),
        
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
                        "Simulação de Dados"
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
            ], width=12)
        ])
    ], fluid=True)

# Historical analysis content
def create_historical():
    return dbc.Container([
        html.H1("Análise Histórica", className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtros"),
                    dbc.CardBody([
                        dbc.Label("Período", className="fw-bold"),
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date=datetime.now() - timedelta(days=7),
                            end_date=datetime.now(),
                            display_format='DD/MM/YYYY',
                            style={"width": "100%"}
                        ),
                        html.Hr(),
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
                    ])
                ], className="shadow-sm")
            ], width=3),
            
            dbc.Col([
                html.Div(id="historical-content")
            ], width=9)
        ])
    ], fluid=True)

# Page routing callback
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/data-input":
        return create_data_input()
    elif pathname == "/historical":
        return create_historical()
    elif pathname == "/alerts":
        return dbc.Container([
            html.H1("Configuração de Alertas", className="mb-4"),
            dbc.Alert("Funcionalidade em desenvolvimento", color="info")
        ])
    elif pathname == "/export":
        return dbc.Container([
            html.H1("Exportar Dados", className="mb-4"),
            dbc.Alert("Funcionalidade em desenvolvimento", color="info")
        ])
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

# Simulation callbacks
@app.callback(
    Output("simulation-output", "children"),
    [Input("sim-1h-btn", "n_clicks"),
     Input("sim-24h-btn", "n_clicks"),
     Input("sim-week-btn", "n_clicks")]
)
def simulate_data(n1h, n24h, nweek):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Determine time period
    if button_id == "sim-1h-btn":
        hours = 1
        freq = '5T'  # 5 minutes
        label = "1 hora"
    elif button_id == "sim-24h-btn":
        hours = 24
        freq = '15T'  # 15 minutes
        label = "24 horas"
    elif button_id == "sim-week-btn":
        hours = 168  # 7 days
        freq = '1H'  # 1 hour
        label = "1 semana"
    else:
        return ""
    
    try:
        # Generate timestamps
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(hours=hours),
            end=datetime.now(),
            freq=freq
        )
        
        n_points = len(timestamps)
        
        # Generate realistic process data
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
                f"Gerados {n_points} pontos de dados para {label}!"
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

# Historical analysis callback
@app.callback(
    Output("historical-content", "children"),
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("params-dropdown", "value")]
)
def update_historical(start_date, end_date, selected_params):
    if not selected_params:
        return dbc.Alert("Selecione pelo menos um parâmetro", color="info")
    
    try:
        historical_data = data_manager.get_data_by_date_range(start_date, end_date)
        
        if historical_data.empty:
            return dbc.Alert("Nenhum dado encontrado para o período selecionado", color="warning")
        
        # Create time series chart
        fig = go.Figure()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i, param in enumerate(selected_params):
            if param in historical_data.columns:
                fig.add_trace(go.Scatter(
                    x=historical_data['timestamp'],
                    y=historical_data[param],
                    mode='lines+markers',
                    name=param.replace('_', ' ').title(),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))
        
        fig.update_layout(
            title="Análise Temporal dos Parâmetros",
            xaxis_title="Tempo",
            yaxis_title="Valores",
            template="plotly_white",
            height=400,
            hovermode='x unified'
        )
        
        # Calculate statistics
        stats_data = []
        for param in selected_params:
            if param in historical_data.columns:
                data = historical_data[param].dropna()
                if not data.empty:
                    stats_data.append({
                        'Parâmetro': param.replace('_', ' ').title(),
                        'Média': f"{data.mean():.2f}",
                        'Desvio Padrão': f"{data.std():.2f}",
                        'Mínimo': f"{data.min():.2f}",
                        'Máximo': f"{data.max():.2f}",
                        'Pontos': len(data)
                    })
        
        return [
            dbc.Card([
                dbc.CardHeader("Gráfico Temporal"),
                dbc.CardBody([
                    dcc.Graph(figure=fig)
                ])
            ], className="shadow-sm mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Estatísticas do Período"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=stats_data,
                        columns=[{"name": i, "id": i} for i in stats_data[0].keys()] if stats_data else [],
                        style_cell={'textAlign': 'center', 'fontFamily': 'Arial'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                        style_data={'backgroundColor': 'rgb(248, 249, 250)'}
                    )
                ])
            ], className="shadow-sm")
        ]
        
    except Exception as e:
        return dbc.Alert(f"Erro ao carregar dados históricos: {str(e)}", color="danger")

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