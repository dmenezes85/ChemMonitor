import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
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
    dcc.Interval(id='global-interval', interval=10000, n_intervals=0)  # Intervalo global
])

# Import page modules
from pages.dashboard import create_dashboard, register_dashboard_callbacks
from pages.data_input import create_data_input, register_data_input_callbacks
from pages.alerts import create_alerts, register_alerts_callbacks
from pages.export import create_export, register_export_callbacks
from pages.historical import create_historical, register_historical_callbacks

# Page routing callback
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
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


# Register all callbacks
register_dashboard_callbacks(app)
register_data_input_callbacks(app)
register_alerts_callbacks(app)
register_export_callbacks(app)
register_historical_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
