import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import io
from utils.data_manager import DataManager
from utils.statistics import StatisticsCalculator
from utils.alert_system import AlertSystem

# Initialize systems
data_manager = DataManager()
stats_calculator = StatisticsCalculator()
alert_system = AlertSystem()

def create_export():
    """Create the export page content"""
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
                        html.P("CSV, JSON, Excel", className="text-info"),
                        html.P("exportação direta", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-bar text-warning me-2"),
                            "Relatórios"
                        ]),
                        html.P("3 tipos", className="text-warning"),
                        html.P("operacional, estatístico, alertas", className="text-muted")
                    ])
                ], className="shadow-sm border-0")
            ], width=3)
        ], className="mb-4"),
        
        # Quick export section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-bolt me-2"),
                        "Exportação Rápida"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-file-csv me-2"),
                                    "Exportar CSV"
                                ], id="export-csv-btn", color="success", className="w-100 mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-file-code me-2"),
                                    "Exportar JSON"
                                ], id="export-json-btn", color="info", className="w-100 mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-file-excel me-2"),
                                    "Exportar Excel"
                                ], id="export-excel-btn", color="success", outline=True, className="w-100 mb-2")
                            ], width=4)
                        ]),
                        html.Div(id="export-output", className="mt-3"),
                        dcc.Download(id="download-csv"),
                        dcc.Download(id="download-json"),  
                        dcc.Download(id="download-excel")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        # Custom export section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Exportação Personalizada"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Período", className="fw-bold"),
                                dcc.DatePickerRange(
                                    id='export-date-range',
                                    start_date=datetime.now() - timedelta(days=7),
                                    end_date=datetime.now(),
                                    display_format='DD/MM/YYYY'
                                )
                            ], width=6),
                            dbc.Col([
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
                                    multi=True,
                                    placeholder="Selecione os parâmetros"
                                )
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-download me-2"),
                                    "Exportar Dados Personalizados"
                                ], id="export-custom-btn", color="primary", className="w-100")
                            ], width=12)
                        ]),
                        html.Div(id="export-custom-output", className="mt-3")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ], className="mb-4"),
        
        # Report generation section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-file-medical me-2"),
                        "Geração de Relatórios"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-clipboard me-2"),
                                    "Relatório Operacional"
                                ], id="report-operational-btn", color="primary", className="w-100 mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Relatório Estatístico"
                                ], id="report-stats-btn", color="info", className="w-100 mb-2")
                            ], width=4),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-bell me-2"),
                                    "Relatório de Alertas"
                                ], id="report-alerts-btn", color="warning", className="w-100 mb-2")
                            ], width=4)
                        ]),
                        html.Div(id="report-output", className="mt-3")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ], fluid=True)

# Export callbacks
def register_export_callbacks(app):
    """Register callbacks for the export page"""
    
    @app.callback(
        [Output("download-csv", "data"),
         Output("download-json", "data"),
         Output("download-excel", "data"),
         Output("export-output", "children")],
        [Input("export-csv-btn", "n_clicks"),
         Input("export-json-btn", "n_clicks"),
         Input("export-excel-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def export_data(btn_csv, btn_json, btn_excel):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, ""
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            # Get all data
            df = data_manager.get_all_data()
            
            if df.empty:
                return (dash.no_update, dash.no_update, dash.no_update, 
                       dbc.Alert([
                           html.I(className="fas fa-exclamation-triangle me-2"),
                           "Nenhum dado disponível para exportação"
                       ], color="warning"))
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if button_id == "export-csv-btn":
                # Convert to CSV
                csv_string = df.to_csv(index=False)
                
                return (dcc.send_data_frame(df.to_csv, f"process_data_{timestamp}.csv", index=False),
                        dash.no_update, 
                        dash.no_update,
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Arquivo CSV exportado com sucesso! {len(df)} registros exportados."
                        ], color="success"))
                
            elif button_id == "export-json-btn":
                # Convert to JSON
                json_string = df.to_json(orient='records', date_format='iso')
                
                return (dash.no_update,
                        dcc.send_string(json_string, f"process_data_{timestamp}.json"),
                        dash.no_update,
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Arquivo JSON exportado com sucesso! {len(df)} registros exportados."
                        ], color="success"))
                
            elif button_id == "export-excel-btn":
                # Convert to Excel
                return (dash.no_update,
                        dash.no_update,
                        dcc.send_data_frame(df.to_excel, f"process_data_{timestamp}.xlsx", index=False, sheet_name='ProcessData'),
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Arquivo Excel exportado com sucesso! {len(df)} registros exportados."
                        ], color="success"))
                
        except Exception as e:
            return (dash.no_update, dash.no_update, dash.no_update,
                   dbc.Alert([
                       html.I(className="fas fa-exclamation-triangle me-2"),
                       f"Erro na exportação: {str(e)}"
                   ], color="danger"))
        
        return dash.no_update, dash.no_update, dash.no_update, ""

    @app.callback(
        Output("export-custom-output", "children"),
        [Input("export-custom-btn", "n_clicks")],
        [State("export-date-range", "start_date"),
         State("export-date-range", "end_date"),
         State("export-params-dropdown", "value")],
        prevent_initial_call=True
    )
    def export_custom_data(n_clicks, start_date, end_date, selected_params):
        if n_clicks is None:
            return ""
            
        try:
            # Get data for the selected date range
            df = data_manager.get_data_by_date_range(start_date, end_date)
            
            if df.empty:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Nenhum dado encontrado para o período selecionado"
                ], color="warning")
            
            # Filter by selected parameters
            if selected_params:
                # Ensure timestamp is included
                columns_to_include = ['timestamp'] + [param for param in selected_params if param in df.columns]
                df = df[columns_to_include]
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Convert to CSV
            csv_string = df.to_csv(index=False)
            csv_bytes = io.BytesIO(csv_string.encode())
            
            return dcc.send_bytes(
                csv_bytes.getvalue(),
                f"process_data_{timestamp}.csv"
            )
            
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro na exportação personalizada: {str(e)}"
            ], color="danger")

    @app.callback(
        Output("report-output", "children"),
        [Input("report-operational-btn", "n_clicks"),
         Input("report-stats-btn", "n_clicks"),
         Input("report-alerts-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def generate_report(btn_op, btn_stats, btn_alerts):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        try:
            # Get all data
            df = data_manager.get_all_data()
            
            if df.empty:
                return dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Nenhum dado disponível para geração de relatório"
                ], color="warning")
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if button_id == "report-operational-btn":
                # Operational report
                report_data = {
                    "tipo": "relatorio_operacional",
                    "periodo": {
                        "inicio": df['timestamp'].min().isoformat() if 'timestamp' in df.columns else "N/A",
                        "fim": df['timestamp'].max().isoformat() if 'timestamp' in df.columns else "N/A"
                    },
                    "parametros": {
                        "temperatura": {
                            "media": float(df['temperature'].mean()) if 'temperature' in df.columns else None,
                            "minimo": float(df['temperature'].min()) if 'temperature' in df.columns else None,
                            "maximo": float(df['temperature'].max()) if 'temperature' in df.columns else None
                        },
                        "pressao": {
                            "media": float(df['pressure'].mean()) if 'pressure' in df.columns else None,
                            "minimo": float(df['pressure'].min()) if 'pressure' in df.columns else None,
                            "maximo": float(df['pressure'].max()) if 'pressure' in df.columns else None
                        },
                        "ph": {
                            "medio": float(df['ph'].mean()) if 'ph' in df.columns else None,
                            "minimo": float(df['ph'].min()) if 'ph' in df.columns else None,
                            "maximo": float(df['ph'].max()) if 'ph' in df.columns else None
                        },
                        "vazao": {
                            "media": float(df['flow_rate'].mean()) if 'flow_rate' in df.columns else None,
                            "minimo": float(df['flow_rate'].min()) if 'flow_rate' in df.columns else None,
                            "maximo": float(df['flow_rate'].max()) if 'flow_rate' in df.columns else None
                        }
                    },
                    "estatisticas": {
                        "total_registros": len(df),
                        "periodo_analise": f"{len(df)} registros"
                    }
                }
                
                # Save report to JSON file
                filename = f"relatorio_operacional_{timestamp}.json"
                with open(f"exports/{filename}", "w") as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Relatório operacional gerado com sucesso: {filename}"
                ], color="success")
                
            elif button_id == "report-stats-btn":
                # Statistical report
                report_data = {
                    "tipo": "relatorio_estatisticas",
                    "periodo": {
                        "inicio": df['timestamp'].min().isoformat() if 'timestamp' in df.columns else "N/A",
                        "fim": df['timestamp'].max().isoformat() if 'timestamp' in df.columns else "N/A"
                    },
                    "estatisticas": {}
                }
                
                # Calculate statistics for each parameter
                for param in ['temperature', 'pressure', 'ph', 'flow_rate']:
                    if param in df.columns:
                        data = df[param].dropna()
                        if len(data) > 0:
                            report_data["estatisticas"][param] = {
                                "media": float(data.mean()),
                                "mediana": float(data.median()),
                                "desvio_padrao": float(data.std()),
                                "minimo": float(data.min()),
                                "maximo": float(data.max()),
                                "q1": float(data.quantile(0.25)),
                                "q3": float(data.quantile(0.75))
                            }
                
                # Save report to JSON file
                filename = f"relatorio_estatisticas_{timestamp}.json"
                with open(f"exports/{filename}", "w") as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Relatório estatístico gerado com sucesso: {filename}"
                ], color="success")
                
            elif button_id == "report-alerts-btn":
                # Alerts report
                alert_history = alert_system.get_alert_history()
                
                report_data = {
                    "tipo": "relatorio_alertas",
                    "periodo": {
                        "inicio": df['timestamp'].min().isoformat() if 'timestamp' in df.columns else "N/A",
                        "fim": df['timestamp'].max().isoformat() if 'timestamp' in df.columns else "N/A"
                    },
                    "configuracoes": alert_system.get_alert_configs(),
                    "historico": alert_history
                }
                
                # Save report to JSON file
                filename = f"relatorio_alertas_{timestamp}.json"
                with open(f"exports/{filename}", "w") as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                return dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Relatório de alertas gerado com sucesso: {filename}"
                ], color="success")
                
        except Exception as e:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Erro na geração de relatório: {str(e)}"
            ], color="danger")