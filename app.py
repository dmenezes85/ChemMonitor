import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
import os
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem
from utils.visualization import ChartGenerator
from utils.statistics import StatisticsCalculator

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Chemical Process Monitor"

# Initialize systems
data_manager = DataManager()
alert_system = AlertSystem()
chart_generator = ChartGenerator()
stats_calculator = StatisticsCalculator()

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🧪 Chemical Process Monitoring Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Navigation tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Dashboard Principal", tab_id="dashboard"),
                dbc.Tab(label="Entrada de Dados", tab_id="data-input"),
                dbc.Tab(label="Análise Histórica", tab_id="historical"),
                dbc.Tab(label="Configuração de Alertas", tab_id="alerts"),
                dbc.Tab(label="Exportar Dados", tab_id="export")
            ], id="tabs", active_tab="dashboard")
        ])
    ], className="mb-4"),
    
    # Main content area
    dbc.Row([
        dbc.Col([
            html.Div(id="tab-content")
        ])
    ]),
    
    # Auto-refresh component
    dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
], fluid=True)

# Dashboard principal content
def create_dashboard_content():
    current_data = data_manager.get_latest_data()
    
    if current_data.empty:
        return dbc.Alert([
            html.H4("Nenhum dado disponível", className="alert-heading"),
            html.P("Por favor, adicione alguns dados usando a aba 'Entrada de Dados'.")
        ], color="warning")
    
    # Métricas atuais
    metrics_cards = []
    parameters = ['temperature', 'pressure', 'ph', 'flow_rate']
    parameter_labels = {
        'temperature': ('Temperatura', '°C'),
        'pressure': ('Pressão', 'bar'),
        'ph': ('pH', ''),
        'flow_rate': ('Vazão', 'L/min')
    }
    
    for param in parameters:
        if param in current_data.columns:
            value = current_data[param].iloc[-1] if not current_data[param].empty else 0
            label, unit = parameter_labels[param]
            
            metrics_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(f"{value:.2f}", className="card-title"),
                            html.P(f"{label} ({unit})", className="card-text")
                        ])
                    ])
                ], width=3)
            )
    
    # Gráficos em tempo real
    if 'timestamp' in current_data.columns:
        fig = chart_generator.create_multi_line_chart(current_data, 'timestamp', parameters[:4])
    else:
        fig = chart_generator._create_empty_chart("Dados de timestamp não encontrados")
    
    return html.Div([
        dbc.Row([
            html.H3("📊 Status Atual do Processo"),
        ], className="mb-3"),
        
        dbc.Row(metrics_cards, className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H4("Tendências em Tempo Real"),
                dcc.Graph(figure=fig)
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H4("Alertas Ativos"),
                html.Div(id="active-alerts")
            ])
        ])
    ])

# Data input content
def create_data_input_content():
    return html.Div([
        dbc.Row([
            html.H3("📝 Entrada de Dados"),
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Upload de Arquivo CSV"),
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Arraste e solte ou ',
                                html.A('selecione um arquivo')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            multiple=False
                        ),
                        html.Div(id='output-data-upload')
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Entrada Manual"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Temperatura (°C)"),
                                dbc.Input(id="temp-input", type="number", value=25.0)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Pressão (bar)"),
                                dbc.Input(id="pressure-input", type="number", value=1.0)
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("pH"),
                                dbc.Input(id="ph-input", type="number", value=7.0)
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Vazão (L/min)"),
                                dbc.Input(id="flow-input", type="number", value=10.0)
                            ], width=6)
                        ], className="mt-2"),
                        dbc.Button("Adicionar Dados", id="add-data-btn", color="primary", className="mt-3"),
                        html.Div(id="add-data-output")
                    ])
                ])
            ], width=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H4("Gerar Dados Simulados"),
                dbc.Button("Gerar 24h de Dados", id="simulate-btn", color="secondary"),
                html.Div(id="simulate-output")
            ])
        ], className="mt-4")
    ])

# Historical analysis content
def create_historical_content():
    return html.Div([
        dbc.Row([
            html.H3("📈 Análise Histórica"),
        ], className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Filtros"),
                    dbc.CardBody([
                        dbc.Label("Período"),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            start_date=datetime.now() - timedelta(days=7),
                            end_date=datetime.now()
                        ),
                        dbc.Label("Parâmetros", className="mt-2"),
                        dcc.Dropdown(
                            id='parameter-dropdown',
                            options=[
                                {'label': 'Temperatura', 'value': 'temperature'},
                                {'label': 'Pressão', 'value': 'pressure'},
                                {'label': 'pH', 'value': 'ph'},
                                {'label': 'Vazão', 'value': 'flow_rate'}
                            ],
                            value=['temperature', 'pressure'],
                            multi=True
                        )
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                html.Div(id="historical-charts")
            ], width=9)
        ])
    ])

# Callback for tab content
@callback(Output('tab-content', 'children'), [Input('tabs', 'active_tab')])
def render_tab_content(active_tab):
    if active_tab == "dashboard":
        return create_dashboard_content()
    elif active_tab == "data-input":
        return create_data_input_content()
    elif active_tab == "historical":
        return create_historical_content()
    elif active_tab == "alerts":
        return html.Div("Configuração de alertas em desenvolvimento...")
    elif active_tab == "export":
        return html.Div("Exportação de dados em desenvolvimento...")
    return html.Div("Selecione uma aba")

# Callback for manual data input
@callback(
    Output('add-data-output', 'children'),
    [Input('add-data-btn', 'n_clicks')],
    [State('temp-input', 'value'),
     State('pressure-input', 'value'),
     State('ph-input', 'value'),
     State('flow-input', 'value')]
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
                return dbc.Alert("Dados adicionados com sucesso!", color="success", duration=3000)
            else:
                return dbc.Alert("Erro ao adicionar dados", color="danger", duration=3000)
        except Exception as e:
            return dbc.Alert(f"Erro: {str(e)}", color="danger", duration=3000)
    return ""

# Callback for data simulation
@callback(
    Output('simulate-output', 'children'),
    [Input('simulate-btn', 'n_clicks')]
)
def simulate_data(n_clicks):
    if n_clicks:
        try:
            # Generate 24 hours of simulated data
            timestamps = pd.date_range(
                start=datetime.now() - timedelta(hours=24),
                end=datetime.now(),
                freq='10T'  # Every 10 minutes
            )
            
            n_points = len(timestamps)
            
            # Generate realistic process data with some noise
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
                return dbc.Alert(f"Gerados {n_points} pontos de dados simulados!", color="success", duration=3000)
            else:
                return dbc.Alert("Erro ao gerar dados simulados", color="danger", duration=3000)
        except Exception as e:
            return dbc.Alert(f"Erro: {str(e)}", color="danger", duration=3000)
    return ""

# Callback for historical analysis
@callback(
    Output('historical-charts', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('parameter-dropdown', 'value')]
)
def update_historical_charts(start_date, end_date, selected_params):
    if not selected_params:
        return html.Div("Selecione pelo menos um parâmetro")
    
    try:
        historical_data = data_manager.get_data_by_date_range(start_date, end_date)
        
        if historical_data.empty:
            return dbc.Alert("Nenhum dado encontrado para o período selecionado", color="info")
        
        # Create time series chart
        if 'timestamp' in historical_data.columns:
            fig = chart_generator.create_multi_line_chart(historical_data, 'timestamp', selected_params)
        else:
            fig = chart_generator._create_empty_chart("Dados de timestamp não encontrados")
        
        # Create statistics summary
        stats = stats_calculator.calculate_basic_stats(historical_data[selected_params])
        
        return html.Div([
            dcc.Graph(figure=fig),
            html.H5("Estatísticas do Período"),
            dash_table.DataTable(
                data=stats.reset_index().to_dict('records'),
                columns=[{"name": i, "id": i} for i in stats.reset_index().columns],
                style_cell={'textAlign': 'left'}
            )
        ])
    except Exception as e:
        return dbc.Alert(f"Erro ao carregar dados históricos: {str(e)}", color="danger")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)