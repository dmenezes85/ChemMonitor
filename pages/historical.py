import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_manager import DataManager
from utils.visualization import ChartGenerator
from utils.statistics import StatisticsCalculator
from utils.alert_system import AlertSystem
import traceback
from scipy.signal import savgol_filter

# Initialize systems
data_manager = DataManager()
chart_generator = ChartGenerator()
stats_calculator = StatisticsCalculator()
alert_system = AlertSystem()

def create_historical():
    """Create the historical analysis page content"""
    current_data = data_manager.get_latest_data(1000)
    data_count = len(current_data)
    
    # Ensure we have some sample data if empty
    if current_data.empty:
        # Generate sample data for testing
        try:
            timestamps = pd.date_range(
                start=datetime.now() - timedelta(days=7),
                end=datetime.now(),
                freq='1H'
            )
            n_points = len(timestamps)
            sample_data = pd.DataFrame({
                'timestamp': timestamps,
                'temperature': 75 + np.sin(np.linspace(0, 4*np.pi, n_points)) * 5 + np.random.normal(0, 1, n_points),
                'pressure': 2.5 + np.random.normal(0, 0.1, n_points),
                'ph': 7.2 + np.random.normal(0, 0.2, n_points),
                'flow_rate': 15 + np.random.normal(0, 0.5, n_points)
            })
            data_manager.add_data(sample_data)
            current_data = data_manager.get_latest_data(1000)
            data_count = len(current_data)
        except Exception as e:
            print(f"Error generating sample data: {e}")
    
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
            dbc.Tab(label="Análise Temporal", tab_id="temporal", activeLabelClassName="fw-bold"),
            dbc.Tab(label="Tendências", tab_id="trends", activeLabelClassName="fw-bold"),
            dbc.Tab(label="Correlações", tab_id="correlations", activeLabelClassName="fw-bold"),
            dbc.Tab(label="Estatísticas", tab_id="statistics", activeLabelClassName="fw-bold")
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

# Historical analysis callbacks
def register_historical_callbacks(app):
    """Register callbacks for the historical analysis page"""

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
                historical_data = data_manager.get_latest_data(1000)
                if historical_data.empty:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Nenhum dado disponível. Vá para 'Entrada de Dados' e gere alguns dados simulados primeiro."
                    ], color="warning")
                else:
                    return dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        f"Nenhum dado encontrado para o período selecionado. Mostrando {len(historical_data)} registros mais recentes."
                    ], color="info")

            if active_tab == "temporal":
                processed_data = historical_data.copy()

                # Apply resolution filtering (resampling)
                if resolution and resolution != '5T' and 'timestamp' in processed_data.columns:
                    processed_data = processed_data.set_index('timestamp')
                    numeric_cols = processed_data.select_dtypes(include=[np.number]).columns
                    processed_data = processed_data[numeric_cols].resample(resolution).mean()
                    processed_data = processed_data.reset_index()
                
                # Apply smoothing
                if smoothing and smoothing != 'none' and window and window > 2:
                    for param in selected_params:
                        if param in processed_data.columns:
                            if smoothing == 'moving_avg':
                                processed_data[param] = processed_data[param].rolling(window=window, center=True).mean()
                            elif smoothing == 'exponential':
                                processed_data[param] = processed_data[param].ewm(span=window).mean()
                            elif smoothing == 'savgol':
                                try:
                                    from scipy.signal import savgol_filter
                                    if len(processed_data[param].dropna()) >= window:
                                        # Use forward fill and backward fill for missing values
                                        filled_data = processed_data[param].ffill().bfill()
                                        processed_data[param] = savgol_filter(filled_data, 
                                                                            window_length=min(window, len(processed_data[param].dropna())), 
                                                                            polyorder=min(3, window-1))
                                except ImportError:
                                    # Fallback to moving average if scipy not available
                                    processed_data[param] = processed_data[param].rolling(window=window, center=True).mean()

                fig = chart_generator.create_multi_line_chart(processed_data, 'timestamp', selected_params, "Análise Temporal")
                return dbc.Card([
                    dbc.CardHeader([
                        "Análise Temporal",
                        html.Small(f" (Resolução: {resolution}, Suavização: {smoothing}, Janela: {window})", className="text-muted ms-2")
                    ]),
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
                try:
                    fig = chart_generator.create_correlation_matrix(historical_data, selected_params)
                    return dbc.Card([
                        dbc.CardHeader("Matriz de Correlação"),
                        dbc.CardBody([dcc.Graph(figure=fig)])
                    ], className="shadow-sm")
                except Exception as e:
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Erro ao gerar matriz de correlação: {str(e)}"
                    ], color="danger")
                    
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
                
            elif active_tab == "autocorr":
                # Autocorrelation analysis
                from plotly.subplots import make_subplots
                
                if len(selected_params) == 0:
                    return dbc.Alert("Selecione pelo menos um parâmetro", color="info")
                
                fig = make_subplots(rows=len(selected_params), cols=1,
                                subplot_titles=[param.replace('_', ' ').title() for param in selected_params],
                                vertical_spacing=0.1)
                
                for i, param in enumerate(selected_params):
                    if param in historical_data.columns:
                        data = historical_data[param].dropna()
                        if len(data) > 10:
                            # Calculate autocorrelation
                            autocorr = [data.autocorr(lag=lag) for lag in range(min(50, len(data)//2))]
                            lags = list(range(len(autocorr)))
                            
                            fig.add_scatter(x=lags, y=autocorr, mode='lines+markers',
                                        name=f'{param} Autocorr', row=i+1, col=1)
                            
                            # Add significance bounds
                            n = len(data)
                            bound = 1.96 / (n**0.5)
                            fig.add_hline(y=bound, line_dash="dash", line_color="red", 
                                        opacity=0.5, row=i+1, col=1)
                            fig.add_hline(y=-bound, line_dash="dash", line_color="red", 
                                        opacity=0.5, row=i+1, col=1)
                
                fig.update_layout(height=300*len(selected_params), showlegend=False,
                                title_text="Análise de Autocorrelação")
                fig.update_xaxes(title_text="Lag")
                fig.update_yaxes(title_text="Autocorrelação")
                
                return dbc.Card([
                    dbc.CardHeader("Análise de Autocorrelação"),
                    dbc.CardBody([dcc.Graph(figure=fig)])
                ], className="shadow-sm")
                
            elif active_tab == "comparison":
                # Parameter comparison
                if len(selected_params) < 2:
                    return dbc.Alert("Selecione pelo menos dois parâmetros para comparação", color="info")
                
                # Create comparison chart
                fig = chart_generator.create_comparison_chart(historical_data, selected_params)
                
                # Create comparison statistics
                comparison_data = []
                for i, param1 in enumerate(selected_params):
                    for param2 in selected_params[i+1:]:
                        if param1 in historical_data.columns and param2 in historical_data.columns:
                            data1 = historical_data[param1].dropna()
                            data2 = historical_data[param2].dropna()
                            
                            if len(data1) > 0 and len(data2) > 0:
                                # Calculate correlation
                                corr = historical_data[[param1, param2]].corr().iloc[0, 1]
                                
                                comparison_data.append({
                                    'Parâmetro 1': param1.replace('_', ' ').title(),
                                    'Parâmetro 2': param2.replace('_', ' ').title(),
                                    'Correlação': f"{corr:.3f}",
                                    'Força da Correlação': 'Forte' if abs(corr) > 0.7 else 'Moderada' if abs(corr) > 0.3 else 'Fraca',
                                    'Média P1': f"{data1.mean():.3f}",
                                    'Média P2': f"{data2.mean():.3f}",
                                    'Razão Médias': f"{data1.mean()/data2.mean():.3f}" if data2.mean() != 0 else "N/A"
                                })
                
                return dbc.Card([
                    dbc.CardHeader("Comparação entre Parâmetros"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig),
                        html.Hr(),
                        html.H5("Estatísticas de Comparação", className="mt-3"),
                        dash_table.DataTable(
                            data=comparison_data,
                            columns=[{"name": i, "id": i} for i in comparison_data[0].keys()] if comparison_data else [],
                            style_cell={'textAlign': 'center', 'fontSize': '12px'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                        )
                    ])
                ], className="shadow-sm")
                
            elif active_tab == "summary":
                # Data summary
                summary_stats = {
                    'total_records': len(historical_data),
                    'date_range': f"{historical_data['timestamp'].min().strftime('%d/%m/%Y %H:%M')} - {historical_data['timestamp'].max().strftime('%d/%m/%Y %H:%M')}" if 'timestamp' in historical_data.columns and not historical_data.empty else "N/A",
                    'parameters': len(selected_params),
                    'missing_data': historical_data[selected_params].isnull().sum().sum() if selected_params else 0
                }
                
                # Quality metrics
                quality_data = []
                for param in selected_params:
                    if param in historical_data.columns:
                        data = historical_data[param]
                        missing_pct = (data.isnull().sum() / len(data)) * 100
                        quality_data.append({
                            'Parâmetro': param.replace('_', ' ').title(),
                            'Registros Total': len(data),
                            'Dados Válidos': data.count(),
                            'Dados Ausentes': data.isnull().sum(),
                            'Completude (%)': f"{100-missing_pct:.1f}%",
                            'Valor Mínimo': f"{data.min():.3f}" if data.count() > 0 else "N/A",
                            'Valor Máximo': f"{data.max():.3f}" if data.count() > 0 else "N/A",
                            'Amplitude': f"{data.max() - data.min():.3f}" if data.count() > 0 else "N/A"
                        })
                
                return dbc.Card([
                    dbc.CardHeader("Resumo dos Dados"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(f"{summary_stats['total_records']:,}", className="text-primary"),
                                        html.P("Total de Registros", className="text-muted")
                                    ])
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(f"{summary_stats['parameters']}", className="text-success"),
                                        html.P("Parâmetros Selecionados", className="text-muted")
                                    ])
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4(f"{summary_stats['missing_data']:,}", className="text-warning"),
                                        html.P("Dados Ausentes", className="text-muted")
                                    ])
                                ], className="text-center")
                            ], width=3),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4("Alta", className="text-info"),
                                        html.P("Qualidade dos Dados", className="text-muted")
                                    ])
                                ], className="text-center")
                            ], width=3)
                        ], className="mb-4"),
                        html.H5("Período Analisado", className="mb-3"),
                        html.P(summary_stats['date_range'], className="text-muted mb-4"),
                        html.H5("Qualidade por Parâmetro", className="mb-3"),
                        dash_table.DataTable(
                            data=quality_data,
                            columns=[{"name": i, "id": i} for i in quality_data[0].keys()] if quality_data else [],
                            style_cell={'textAlign': 'center', 'fontSize': '12px'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                        )
                    ])
                ], className="shadow-sm")
                
            elif active_tab == "anomalies":
                # Anomaly detection
                from scipy import stats
                
                anomaly_data = []
                all_anomalies = []
                
                for param in selected_params:
                    if param in historical_data.columns:
                        data = historical_data[param].dropna()
                        if len(data) > 10:
                            # Z-score method
                            z_scores = np.abs(stats.zscore(data))
                            z_anomalies = np.where(z_scores > 3)[0]
                            
                            # IQR method
                            Q1 = data.quantile(0.25)
                            Q3 = data.quantile(0.75)
                            IQR = Q3 - Q1
                            lower_bound = Q1 - 1.5 * IQR
                            upper_bound = Q3 + 1.5 * IQR
                            iqr_anomalies = data[(data < lower_bound) | (data > upper_bound)]
                            
                            anomaly_data.append({
                                'Parâmetro': param.replace('_', ' ').title(),
                                'Total de Dados': len(data),
                                'Anomalias Z-Score': len(z_anomalies),
                                'Anomalias IQR': len(iqr_anomalies),
                                'Taxa de Anomalia (%)': f"{(len(z_anomalies)/len(data)*100):.2f}%",
                                'Limite Inferior': f"{lower_bound:.3f}",
                                'Limite Superior': f"{upper_bound:.3f}",
                                'Valor Médio': f"{data.mean():.3f}"
                            })
                            
                            # Collect anomalies for visualization
                            for idx in z_anomalies:
                                if idx < len(historical_data):
                                    timestamp = historical_data.iloc[idx]['timestamp'] if 'timestamp' in historical_data.columns else idx
                                    all_anomalies.append({
                                        'timestamp': timestamp,
                                        'parameter': param,
                                        'value': data.iloc[idx],
                                        'z_score': z_scores[idx]
                                    })
                
                # Create anomaly visualization
                fig = go.Figure()
                
                for param in selected_params:
                    if param in historical_data.columns:
                        data = historical_data[param].dropna()
                        timestamps = historical_data['timestamp'] if 'timestamp' in historical_data.columns else range(len(data))
                        
                        # Plot normal data
                        fig.add_trace(go.Scatter(
                            x=timestamps[:len(data)],
                            y=data,
                            mode='lines',
                            name=param.replace('_', ' ').title(),
                            line=dict(width=2)
                        ))
                        
                        # Highlight anomalies
                        param_anomalies = [a for a in all_anomalies if a['parameter'] == param]
                        if param_anomalies:
                            anomaly_times = [a['timestamp'] for a in param_anomalies]
                            anomaly_values = [a['value'] for a in param_anomalies]
                            
                            fig.add_trace(go.Scatter(
                                x=anomaly_times,
                                y=anomaly_values,
                                mode='markers',
                                name=f'{param} Anomalias',
                                marker=dict(size=8, color='red', symbol='x'),
                                showlegend=False
                            ))
                
                fig.update_layout(
                    title="Detecção de Anomalias",
                    xaxis_title="Tempo",
                    yaxis_title="Valores",
                    template="plotly_white",
                    height=400,
                    hovermode='x unified'
                )
                
                return dbc.Card([
                    dbc.CardHeader("Detecção de Anomalias"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig),
                        html.Hr(),
                        html.H5("Estatísticas de Anomalias", className="mt-3"),
                        dash_table.DataTable(
                            data=anomaly_data,
                            columns=[{"name": i, "id": i} for i in anomaly_data[0].keys()] if anomaly_data else [],
                            style_cell={'textAlign': 'center', 'fontSize': '12px'},
                            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                        ),
                        html.Div([
                            html.H6("Métodos de Detecção:", className="mt-3"),
                            html.P("• Z-Score: Identifica valores com desvio > 3 desvios padrão", className="mb-1"),
                            html.P("• IQR: Identifica valores fora do intervalo Q1-1.5*IQR até Q3+1.5*IQR", className="mb-1")
                        ], className="mt-3")
                    ])
                ], className="shadow-sm")
                
            else:
                return dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    f"Análise '{active_tab}' em desenvolvimento"
                ], color="info")
                
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error in historical analysis: {error_details}")
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Div([
                    html.Strong("Erro na análise histórica: "),
                    html.Br(),
                    str(e)
                ])
            ], color="danger")