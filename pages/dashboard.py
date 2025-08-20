import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime
import plotly.graph_objects as go
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem
from utils.visualization import ChartGenerator
from utils.statistics import StatisticsCalculator
import traceback

# Initialize systems
data_manager = DataManager()
alert_system = AlertSystem()
chart_generator = ChartGenerator()
stats_calculator = StatisticsCalculator()

def create_dashboard_content():
    """Create the main dashboard page content"""
    try:
        current_data = data_manager.get_latest_data(50)

        if current_data.empty:
            return dbc.Container([
                dbc.Alert([
                    html.H4("Bem-vindo ao Monitor de Processos Químicos!", className="alert-heading"),
                    html.P("Nenhum dado disponível no momento."),
                    html.Hr(),
                    html.P([
                        "Utilize a seção ",
                        html.A("Entrada de Dados", href="/data-input", className="alert-link"),
                        " para adicionar dados ao sistema."
                    ])
                ], color="info")
            ], className="mt-4")

        # Get latest values
        latest_row = current_data.iloc[-1]
        temp_value = latest_row['temperature']
        pressure_value = latest_row['pressure']
        ph_value = latest_row['ph']
        flow_value = latest_row['flow_rate']

        # Calculate statistics
        temp_stats = current_data['temperature'].describe()
        pressure_stats = current_data['pressure'].describe()
        ph_stats = current_data['ph'].describe()
        flow_stats = current_data['flow_rate'].describe()

        # Get active alerts
        active_alerts = alert_system.check_alerts(current_data)

        # Create charts
        fig_time = chart_generator.create_time_series_with_alerts(
            data=current_data,
            x_column='timestamp',
            y_column='temperature',
            title='Evolução Temporal - Temperatura',
            thresholds=None
        )
        
        # Create distribution chart (using histogram)
        fig_dist = chart_generator.create_histogram(
            data=current_data['temperature'],
            title='Distribuição - Temperatura',
            bins=20
        )

        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("📊 Dashboard de Monitoramento", className="text-primary"),
                    html.P("Visão em tempo real dos processos químicos", className="text-muted")
                ], width=8),
                dbc.Col([
                    html.Div([
                        html.Small("Última atualização:", className="text-muted"),
                        html.Br(),
                        html.Small(datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                  className="text-primary")
                    ], className="text-end")
                ], width=4)
            ], className="mb-4"),

            # Metric cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🌡️ Temperatura", className="card-title text-primary"),
                            html.H2(f"{temp_value:.1f}°C", className="card-text"),
                            html.Small(f"Min: {temp_stats['min']:.1f}°C | Max: {temp_stats['max']:.1f}°C",
                                      className="text-muted")
                        ])
                    ], className="h-100 shadow-sm")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("⚙️ Pressão", className="card-title text-primary"),
                            html.H2(f"{pressure_value:.1f} PSI", className="card-text"),
                            html.Small(f"Min: {pressure_stats['min']:.1f} PSI | Max: {pressure_stats['max']:.1f} PSI",
                                      className="text-muted")
                        ])
                    ], className="h-100 shadow-sm")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🧪 pH", className="card-title text-primary"),
                            html.H2(f"{ph_value:.2f}", className="card-text"),
                            html.Small(f"Min: {ph_stats['min']:.2f} | Max: {ph_stats['max']:.2f}",
                                      className="text-muted")
                        ])
                    ], className="h-100 shadow-sm")
                ], width=3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("㎥ Fluxo", className="card-title text-primary"),
                            html.H2(f"{flow_value:.1f} L/min", className="card-text"),
                            html.Small(f"Min: {flow_stats['min']:.1f} L/min | Max: {flow_stats['max']:.1f} L/min",
                                      className="text-muted")
                        ])
                    ], className="h-100 shadow-sm")
                ], width=3)
            ], className="mb-4"),

            # Charts row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Evolução Temporal"),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_time, id='time-series-chart')
                        ])
                    ], className="h-100 shadow-sm")
                ], width=8),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Distribuição"),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_dist, id='distribution-chart')
                        ])
                    ], className="h-100 shadow-sm")
                ], width=4)
            ], className="mb-4"),

            # Alerts section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-bell me-2"),
                            "Alertas Ativos"
                        ]),
                        dbc.CardBody([
                            html.Div([
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.Div([
                                            html.Strong(alert['parameter'].title()),
                                            html.Small(f" - {alert['message']}", className="text-muted"),
                                            html.Br(),
                                            html.Small(f"Valor: {alert['current_value']:.2f} | {alert['timestamp']}",
                                                      className="text-muted")
                                        ])
                                    ], color="danger" if alert['severity'] == 'Critical' else "warning")
                                    for alert in active_alerts
                                ])
                            ])
                        ])
                    ], className="h-100 shadow-sm")
                ], width=12)
            ], className="mb-4")
        ], fluid=True)
    except Exception as e:
        return dbc.Container([
            dbc.Alert([
                html.H4("Erro ao carregar o dashboard", className="alert-heading"),
                html.P(f"Ocorreu um erro: {str(e)}"),
                html.Hr(),
                html.Pre(traceback.format_exc(), className="text-muted")
            ], color="danger")
        ], className="mt-4")

def create_dashboard():
    """Create the main dashboard page"""
    return html.Div([
        html.Div(id='dashboard-content', children=create_dashboard_content())
    ])

def register_dashboard_callbacks(app):
    """Register dashboard callbacks"""
    
    @app.callback(
        Output('time-series-chart', 'figure'),
        Input('global-interval', 'n_intervals')
    )
    def update_realtime_chart(n):
        """Update realtime chart with latest data"""
        try:
            current_data = data_manager.get_latest_data(50)
            if current_data.empty:
                # Return empty figure with message
                fig = go.Figure()
                fig.add_annotation(
                    text="Dados não disponíveis",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font_size=16
                )
                fig.update_layout(
                    title="Evolução Temporal",
                    xaxis_title="Tempo",
                    yaxis_title="Valores",
                    showlegend=False,
                    hovermode="x unified"
                )
                return fig

            fig = chart_generator.create_time_series_with_alerts(
                data=current_data,
                x_column='timestamp',
                y_column='temperature',
                title='Evolução Temporal - Temperatura',
                thresholds=None
            )
            return fig
        except Exception as e:
            print(f"Erro no callback do gráfico: {e}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Erro: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font_size=16
            )
            fig.update_layout(
                title="Evolução Temporal",
                xaxis_title="Tempo",
                yaxis_title="Valores",
                showlegend=False,
                hovermode="x unified"
            )
            return fig

    @app.callback(
        Output('dashboard-content', 'children'),
        Input('global-interval', 'n_intervals')
    )
    def update_dashboard_content(n):
        """Update the entire dashboard content periodically"""
        try:
            return create_dashboard_content()
        except Exception as e:
            print(f"Erro no callback de atualização do dashboard: {e}")
            import traceback
            traceback.print_exc()
            return dbc.Container([
                dbc.Alert([
                    html.H4("Erro ao atualizar o dashboard", className="alert-heading"),
                    html.P(f"Ocorreu um erro: {str(e)}")
                ], color="danger")
            ], className="mt-4")