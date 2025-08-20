import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import base64
import io
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem
import plotly.graph_objects as go

# Initialize systems
data_manager = DataManager()
alert_system = AlertSystem()

def create_data_input():
    """Create the data input page content"""
    current_data = data_manager.get_latest_data(50)
    data_count = len(data_manager.get_latest_data(10000))
    latest_entry = current_data.iloc[-1] if not current_data.empty else None
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Entrada de Dados", className="mb-0")
            ], width=8),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-info-circle me-1"),
                        "Status"
                    ], id="data-status-btn", color="info", size="sm"),
                    dbc.Button([
                        html.I(className="fas fa-trash me-1"),
                        "Limpar Dados"
                    ], id="clear-data-btn", color="danger", size="sm")
                ], className="w-100")
            ], width=4)
        ], className="mb-4"),
        
        # Clear data output
        html.Div(id="clear-data-output", className="mb-3"),
        
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
                        dbc.Alert([
                            html.I(className="fas fa-info-circle me-2"),
                            "Novos dados serão ADICIONADOS aos existentes. Use 'Limpar Dados' para começar do zero."
                        ], color="warning", className="mb-3"),
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

# Data input callbacks
def register_data_input_callbacks(app):
    """Register callbacks for the data input page"""

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

    @app.callback(
        Output("upload-output", "children"),
        [Input("upload-data", "contents")],
        [State("upload-data", "filename")]
    )
    def upload_data(contents, filename):
        if contents is not None:
            try:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

                # Validate required columns
                required_columns = ['timestamp', 'temperature', 'pressure', 'ph', 'flow_rate']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Colunas ausentes no arquivo: {', '.join(missing_columns)}"
                    ], color="danger")

                # Convert timestamp column
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Add data to system
                success = data_manager.add_data(df)
                if success:
                    return dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        f"Arquivo '{filename}' carregado com sucesso! {len(df)} registros adicionados."
                    ], color="success", duration=5000)
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Erro ao adicionar dados do arquivo"
                    ], color="danger")
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erro ao processar arquivo: {str(e)}"
                ], color="danger")
        return ""

    @app.callback(
        Output("simulation-output", "children"),
        [Input("sim-1h-btn", "n_clicks"),
        Input("sim-24h-btn", "n_clicks"),
        Input("sim-week-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def generate_simulation_data(btn1, btn2, btn3):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            if button_id == "sim-1h-btn":
                hours = 1
                freq = '5T'
            elif button_id == "sim-24h-btn":
                hours = 24
                freq = '15T'
            elif button_id == "sim-week-btn":
                hours = 168
                freq = '1H'
            else:
                return ""
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            timestamps = pd.date_range(start=start_time, end=end_time, freq=freq)
            n_points = len(timestamps)
            if n_points == 0:
                return dbc.Alert("Nenhum ponto de dados gerado.", color="warning")
            temp_base = 75
            temp_variation = 10 * np.sin(np.linspace(0, 4*np.pi, n_points)) + np.random.normal(0, 2, n_points)
            temperature = temp_base + temp_variation

            pressure = 2.5 + np.random.normal(0, 0.1, n_points)
            ph = 7.2 + np.random.normal(0, 0.1, n_points)
            flow_base = 15
            flow_variation = 3 * np.sin(np.linspace(0, 2*np.pi, n_points)) + np.random.normal(0, 0.5, n_points)
            flow_rate = flow_base + flow_variation

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
                    f"Dados simulados gerados com sucesso! {len(simulated_data)} registros adicionados."
                ], color="success", duration=5000)
            else:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Erro ao adicionar dados simulados"
                ], color="danger")
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro ao gerar dados simulados: {str(e)}"
            ], color="danger")

    @app.callback(
        Output("clear-data-output", "children"),
        [Input("clear-data-btn", "n_clicks"),
        Input("data-status-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_data_actions(clear_clicks, status_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "clear-data-btn":
            try:
                success = data_manager.clear_all_data()
                if success:
                    return dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        "Todos os dados foram removidos com sucesso! Agora você pode gerar novos dados sem sobreposição."
                    ], color="success", duration=5000)
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Erro ao limpar os dados. Tente novamente."
                    ], color="danger", duration=5000)
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erro ao limpar dados: {str(e)}"
                ], color="danger", duration=5000)
        elif button_id == "data-status-btn":
            try:
                summary = data_manager.get_data_summary()
                total_records = summary.get('total_records', 0)
                parameters = summary.get('parameters', [])
                
                if total_records > 0:
                    date_range = summary.get('date_range', {})
                    start_date = date_range.get('start', 'N/A')
                    end_date = date_range.get('end', 'N/A')
                    
                    return dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-info-circle me-2"),
                            "Status dos Dados"
                        ]),
                        html.P([
                            html.Strong("Total de registros: "), f"{total_records:,}",
                            html.Br(),
                            html.Strong("Parâmetros monitorados: "), f"{len(parameters)}",
                            html.Br(),
                            html.Strong("Período: "), f"{start_date[:10] if start_date != 'N/A' else 'N/A'} até {end_date[:10] if end_date != 'N/A' else 'N/A'}"
                        ])
                    ], color="info", duration=8000)
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-database me-2"),
                        "Nenhum dado encontrado. Use a simulação ou carregue arquivos CSV para começar."
                    ], color="warning", duration=5000)
            except Exception as e:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Erro ao verificar status: {str(e)}"
                ], color="danger", duration=5000)
        
        return ""