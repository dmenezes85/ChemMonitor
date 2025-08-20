import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem

# Initialize systems
data_manager = DataManager()
alert_system = AlertSystem()

def create_alerts():
    """Create the alerts page content"""
    # Get current alert configuration
    alert_configs = alert_system.get_alert_configs()
    alert_history = alert_system.get_alert_history()

    # Convert configs to table format
    config_data = []
    for param, config in alert_configs.items():
        config_data.append({
            'parameter': param.title(),
            'min_value': config.get('min', 'N/A'),
            'max_value': config.get('max', 'N/A'),
            'cooldown': config.get('cooldown', 'N/A'),
            'enabled': 'Ativo' if config.get('enabled', False) else 'Inativo'
        })

    # Convert history to display format
    history_data = []
    for alert in alert_history[-10:]:  # Last 10 alerts
        history_data.append({
            'timestamp': alert['timestamp'],
            'parameter': alert['parameter'].title(),
            'value': f"{alert['value']:.2f}",
            'message': alert['message']
        })

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("🔔 Sistema de Alertas", className="text-primary"),
                html.P("Configure e monitore alertas para parâmetros críticos", className="text-muted")
            ], width=12)
        ], className="mb-4"),

        # Alert Configuration Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🛠️ Configuração de Alertas"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Parâmetro", className="fw-bold"),
                                dcc.Dropdown(
                                    id='alert-param-dropdown',
                                    options=[
                                        {'label': 'Temperatura', 'value': 'temperature'},
                                        {'label': 'Pressão', 'value': 'pressure'},
                                        {'label': 'pH', 'value': 'ph'},
                                        {'label': 'Vazão', 'value': 'flow_rate'}
                                    ],
                                    value='temperature',
                                    className="mb-3"
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Valor Mínimo", className="fw-bold"),
                                dbc.Input(
                                    id='alert-min-value',
                                    type='number',
                                    placeholder='Valor mínimo',
                                    className="mb-3"
                                )
                            ], width=6),

                            dbc.Col([
                                html.Label("Valor Máximo", className="fw-bold"),
                                dbc.Input(
                                    id='alert-max-value',
                                    type='number',
                                    placeholder='Valor máximo',
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Tempo de Cooldown (minutos)", className="fw-bold"),
                                dbc.Input(
                                    id='alert-cooldown',
                                    type='number',
                                    placeholder='Minutos',
                                    value=5,
                                    className="mb-3"
                                )
                            ], width=6),

                            dbc.Col([
                                html.Label("Status", className="fw-bold"),
                                dbc.Switch(
                                    id='alert-enabled',
                                    label="Ativar Alerta",
                                    value=True,
                                    className="mb-3"
                                )
                            ], width=6)
                        ]),

                        dbc.Button(
                            "💾 Salvar Configuração",
                            id='save-alert-config',
                            color="primary",
                            className="w-100"
                        ),

                        html.Div(id='alert-save-status', className="mt-3")
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        # Current Configuration and History
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Configurações Atuais"),
                    dbc.CardBody([
                        dash.dash_table.DataTable(
                            id='alert-config-table',
                            columns=[
                                {'name': 'Parâmetro', 'id': 'parameter'},
                                {'name': 'Min', 'id': 'min_value'},
                                {'name': 'Max', 'id': 'max_value'},
                                {'name': 'Cooldown (min)', 'id': 'cooldown'},
                                {'name': 'Status', 'id': 'enabled'}
                            ],
                            data=config_data,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px'
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            }
                        )
                    ])
                ], className="mb-4 shadow-sm")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📜 Histórico de Alertas"),
                    dbc.CardBody([
                        dash.dash_table.DataTable(
                            id='alert-history-table',
                            columns=[
                                {'name': 'Data/Hora', 'id': 'timestamp'},
                                {'name': 'Parâmetro', 'id': 'parameter'},
                                {'name': 'Valor', 'id': 'value'},
                                {'name': 'Mensagem', 'id': 'message'}
                            ],
                            data=history_data,
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'padding': '10px'
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            page_size=10
                        )
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ], fluid=True)

def register_alerts_callbacks(app):
    """Register alerts page callbacks"""

    @app.callback(
        [Output('alert-min-value', 'value'),
         Output('alert-max-value', 'value'),
         Output('alert-cooldown', 'value'),
         Output('alert-enabled', 'value')],
        Input('alert-param-dropdown', 'value')
    )
    def load_alert_config(param):
        """Load alert configuration for selected parameter"""
        config = alert_system.get_alert_configs().get(param, {})
        min_val = config.get('min', '')
        max_val = config.get('max', '')
        cooldown = config.get('cooldown', 5)
        enabled = config.get('enabled', True)
        return min_val, max_val, cooldown, enabled

    @app.callback(
        [Output('alert-config-table', 'data'),
         Output('alert-save-status', 'children')],
        Input('save-alert-config', 'n_clicks'),
        [State('alert-param-dropdown', 'value'),
         State('alert-min-value', 'value'),
         State('alert-max-value', 'value'),
         State('alert-cooldown', 'value'),
         State('alert-enabled', 'value')],
        prevent_initial_call=True
    )
    def save_alert_config(n_clicks, param, min_val, max_val, cooldown, enabled):
        """Save alert configuration"""
        if n_clicks is None:
            raise dash.exceptions.PreventUpdate

        try:
            # Save configuration
            alert_system.update_alert_config(param, min_val, max_val, cooldown, enabled)

            # Refresh configuration table
            alert_configs = alert_system.get_alert_configs()
            config_data = []
            for p, config in alert_configs.items():
                config_data.append({
                    'parameter': p.title(),
                    'min_value': config.get('min', 'N/A'),
                    'max_value': config.get('max', 'N/A'),
                    'cooldown': config.get('cooldown', 'N/A'),
                    'enabled': 'Ativo' if config.get('enabled', False) else 'Inativo'
                })

            status_message = dbc.Alert("Configuração salva com sucesso!", color="success")
            return config_data, status_message

        except Exception as e:
            status_message = dbc.Alert(f"Erro ao salvar configuração: {str(e)}", color="danger")
            # Return unchanged data
            alert_configs = alert_system.get_alert_configs()
            config_data = []
            for p, config in alert_configs.items():
                config_data.append({
                    'parameter': p.title(),
                    'min_value': config.get('min', 'N/A'),
                    'max_value': config.get('max', 'N/A'),
                    'cooldown': config.get('cooldown', 'N/A'),
                    'enabled': 'Ativo' if config.get('enabled', False) else 'Inativo'
                })
            return config_data, status_message
    
    
