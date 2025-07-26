import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class ChartGenerator:
    """Generates interactive charts and visualizations for chemical process data."""
    
    def __init__(self, theme='light'):
        """Initialize the chart generator with default styling."""
        self.theme = theme
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Theme-based layout configuration
        if theme == 'dark':
            self.default_layout = {
                'template': 'plotly_dark',
                'paper_bgcolor': '#0E1117',
                'plot_bgcolor': '#0E1117',
                'font': {'size': 12, 'color': '#FAFAFA'},
                'title_font': {'size': 16, 'color': '#FAFAFA'},
                'showlegend': True,
                'hovermode': 'x unified'
            }
        else:
            self.default_layout = {
                'template': 'plotly_white',
                'font': {'size': 12},
                'title_font': {'size': 16},
                'showlegend': True,
                'hovermode': 'x unified'
            }
    
    def set_theme(self, theme):
        """Update the theme for chart generation."""
        self.theme = theme
        if theme == 'dark':
            self.default_layout.update({
                'template': 'plotly_dark',
                'paper_bgcolor': '#0E1117',
                'plot_bgcolor': '#0E1117',
                'font': {'size': 12, 'color': '#FAFAFA'},
                'title_font': {'size': 16, 'color': '#FAFAFA'}
            })
        else:
            self.default_layout = {
                'template': 'plotly_white',
                'font': {'size': 12},
                'title_font': {'size': 16},
                'showlegend': True,
                'hovermode': 'x unified'
            }
    
    def create_line_chart(self, 
                         data: pd.DataFrame, 
                         x_column: str, 
                         y_column: str,
                         title: str = "",
                         y_title: str = "",
                         color_column: Optional[str] = None,
                         show_markers: bool = True,
                         line_width: int = 2) -> go.Figure:
        """
        Create an interactive line chart.
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            title: Chart title
            y_title: Y-axis title
            color_column: Optional column for color grouping
            show_markers: Whether to show markers on the line
            line_width: Width of the line
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            # Filter out missing values
            clean_data = data[[x_column, y_column]].dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            if color_column and color_column in data.columns:
                # Multi-series line chart
                fig = px.line(
                    clean_data, 
                    x=x_column, 
                    y=y_column, 
                    color=color_column,
                    markers=show_markers
                )
            else:
                # Single series line chart
                mode = 'lines+markers' if show_markers else 'lines'
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=clean_data[x_column],
                    y=clean_data[y_column],
                    mode=mode,
                    name=y_column.title(),
                    line=dict(width=line_width, color=self.default_colors[0]),
                    marker=dict(size=4) if show_markers else None
                ))
            
            # Create layout dict without conflicting title
            layout_dict = dict(self.default_layout)
            layout_dict.update({
                'title': title,
                'xaxis_title': x_column.title(),
                'yaxis_title': y_title or y_column.title()
            })
            fig.update_layout(**layout_dict)
            
            # Add range selector for time series
            if 'timestamp' in x_column.lower() or 'time' in x_column.lower():
                fig.update_layout(
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1h", step="hour", stepmode="backward"),
                                dict(count=6, label="6h", step="hour", stepmode="backward"),
                                dict(count=1, label="1d", step="day", stepmode="backward"),
                                dict(count=7, label="7d", step="day", stepmode="backward"),
                                dict(step="all")
                            ])
                        ),
                        rangeslider=dict(visible=True),
                        type="date"
                    )
                )
            
            return fig
            
        except Exception as e:
            print(f"Error creating line chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_gauge_chart(self, 
                          value: float, 
                          title: str = "",
                          unit: str = "",
                          min_value: float = 0,
                          max_value: float = 100,
                          thresholds: Optional[Dict[str, float]] = None) -> go.Figure:
        """
        Create a gauge chart for displaying current values.
        
        Args:
            value: Current value to display
            title: Gauge title
            unit: Unit of measurement
            min_value: Minimum value on the gauge
            max_value: Maximum value on the gauge
            thresholds: Optional dict with 'warning' and 'critical' thresholds
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            # Determine gauge color based on thresholds
            gauge_color = "green"
            if thresholds:
                if value >= thresholds.get('critical_high', float('inf')) or value <= thresholds.get('critical_low', float('-inf')):
                    gauge_color = "red"
                elif value >= thresholds.get('warning_high', float('inf')) or value <= thresholds.get('warning_low', float('-inf')):
                    gauge_color = "orange"
            
            # Create gauge steps
            steps = [
                {'range': [min_value, max_value], 'color': "lightgray"}
            ]
            
            # Add threshold zones if provided
            if thresholds:
                if 'warning_low' in thresholds:
                    steps.append({'range': [min_value, thresholds['warning_low']], 'color': "yellow"})
                if 'critical_low' in thresholds:
                    steps.append({'range': [min_value, thresholds['critical_low']], 'color': "red"})
                if 'warning_high' in thresholds:
                    steps.append({'range': [thresholds['warning_high'], max_value], 'color': "yellow"})
                if 'critical_high' in thresholds:
                    steps.append({'range': [thresholds['critical_high'], max_value], 'color': "red"})
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"{title}<br>{unit}" if unit else title},
                gauge={
                    'axis': {'range': [min_value, max_value]},
                    'bar': {'color': gauge_color},
                    'steps': steps,
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': value
                    }
                }
            ))
            
            fig.update_layout(
                height=400,
                **self.default_layout
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating gauge chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_histogram(self, 
                        data: pd.Series, 
                        title: str = "",
                        bins: int = 30,
                        show_normal_curve: bool = False) -> go.Figure:
        """
        Create a histogram for data distribution analysis.
        
        Args:
            data: Series containing the data
            title: Chart title
            bins: Number of bins for the histogram
            show_normal_curve: Whether to overlay a normal distribution curve
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            # Remove missing values
            clean_data = data.dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            fig = go.Figure()
            
            # Add histogram
            fig.add_trace(go.Histogram(
                x=clean_data,
                nbinsx=bins,
                name="Data Distribution",
                opacity=0.7,
                marker_color=self.default_colors[0]
            ))
            
            # Add normal curve if requested
            if show_normal_curve:
                mean = clean_data.mean()
                std = clean_data.std()
                
                # Generate normal distribution curve
                x_range = np.linspace(clean_data.min(), clean_data.max(), 100)
                normal_curve = ((1/(std * np.sqrt(2 * np.pi))) * 
                              np.exp(-0.5 * ((x_range - mean) / std) ** 2))
                
                # Scale to match histogram
                normal_curve = normal_curve * len(clean_data) * (clean_data.max() - clean_data.min()) / bins
                
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=normal_curve,
                    mode='lines',
                    name='Normal Distribution',
                    line=dict(color='red', width=2, dash='dash')
                ))
            
            # Create layout dict without conflicting title
            layout_dict = dict(self.default_layout)
            layout_dict.update({
                'title': title,
                'xaxis_title': data.name.title() if data.name else "Value",
                'yaxis_title': "Frequency"
            })
            fig.update_layout(**layout_dict)
            
            return fig
            
        except Exception as e:
            print(f"Error creating histogram: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_box_plot(self, 
                       data: pd.DataFrame, 
                       y_column: str,
                       x_column: Optional[str] = None,
                       title: str = "") -> go.Figure:
        """
        Create a box plot for statistical analysis.
        
        Args:
            data: DataFrame containing the data
            y_column: Column for y-axis values
            x_column: Optional column for grouping
            title: Chart title
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            clean_data = data[y_column].dropna() if x_column is None else data[[x_column, y_column]].dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            if x_column:
                fig = px.box(data, x=x_column, y=y_column, title=title)
            else:
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=clean_data,
                    name=y_column.title(),
                    marker_color=self.default_colors[0]
                ))
            
            # Create layout dict without conflicting title
            layout_dict = dict(self.default_layout)
            layout_dict.update({
                'title': title,
                'yaxis_title': y_column.title()
            })
            fig.update_layout(**layout_dict)
            
            return fig
            
        except Exception as e:
            print(f"Error creating box plot: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_scatter_plot(self, 
                           data: pd.DataFrame, 
                           x_column: str, 
                           y_column: str,
                           title: str = "",
                           color_column: Optional[str] = None,
                           size_column: Optional[str] = None,
                           trendline: bool = False) -> go.Figure:
        """
        Create a scatter plot for correlation analysis.
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            title: Chart title
            color_column: Optional column for color coding
            size_column: Optional column for bubble size
            trendline: Whether to add a trendline
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            columns_needed = [x_column, y_column]
            if color_column:
                columns_needed.append(color_column)
            if size_column:
                columns_needed.append(size_column)
            
            clean_data = data[columns_needed].dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            # Create scatter plot
            fig = px.scatter(
                clean_data, 
                x=x_column, 
                y=y_column,
                color=color_column,
                size=size_column,
                title=title,
                trendline="ols" if trendline else None
            )
            
            fig.update_layout(
                xaxis_title=x_column.title(),
                yaxis_title=y_column.title(),
                **self.default_layout
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating scatter plot: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_multi_line_chart(self, 
                               data: pd.DataFrame, 
                               x_column: str, 
                               y_columns: List[str],
                               title: str = "",
                               normalize: bool = False) -> go.Figure:
        """
        Create a multi-line chart for comparing multiple parameters.
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis
            y_columns: List of column names for y-axis
            title: Chart title
            normalize: Whether to normalize values to 0-1 scale
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            columns_needed = [x_column] + y_columns
            clean_data = data[columns_needed].dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            fig = go.Figure()
            
            for i, y_col in enumerate(y_columns):
                y_data = clean_data[y_col]
                
                # Normalize if requested
                if normalize:
                    y_min, y_max = y_data.min(), y_data.max()
                    if y_max > y_min:
                        y_data = (y_data - y_min) / (y_max - y_min)
                
                fig.add_trace(go.Scatter(
                    x=clean_data[x_column],
                    y=y_data,
                    mode='lines+markers',
                    name=y_col.title(),
                    line=dict(color=self.default_colors[i % len(self.default_colors)], width=2),
                    marker=dict(size=4)
                ))
            
            y_title = "Normalized Value (0-1)" if normalize else "Value"
            
            fig.update_layout(
                title=title,
                xaxis_title=x_column.title(),
                yaxis_title=y_title,
                **self.default_layout
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating multi-line chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_heatmap(self, 
                      data: pd.DataFrame, 
                      title: str = "",
                      color_scale: str = "RdBu_r") -> go.Figure:
        """
        Create a correlation heatmap.
        
        Args:
            data: DataFrame containing numeric data
            title: Chart title
            color_scale: Color scale for the heatmap
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            # Calculate correlation matrix
            corr_matrix = data.corr()
            
            if corr_matrix.empty:
                return self._create_empty_chart("No numeric data available")
            
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale=color_scale,
                title=title
            )
            
            fig.update_layout(**self.default_layout)
            
            return fig
            
        except Exception as e:
            print(f"Error creating heatmap: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def create_time_series_with_alerts(self, 
                                     data: pd.DataFrame, 
                                     x_column: str, 
                                     y_column: str,
                                     title: str = "",
                                     thresholds: Optional[Dict[str, float]] = None) -> go.Figure:
        """
        Create a time series chart with alert threshold lines.
        
        Args:
            data: DataFrame containing the data
            x_column: Column name for x-axis (timestamp)
            y_column: Column name for y-axis
            title: Chart title
            thresholds: Dict with threshold values
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            clean_data = data[[x_column, y_column]].dropna()
            
            if clean_data.empty:
                return self._create_empty_chart("No data available")
            
            fig = go.Figure()
            
            # Add main data line
            fig.add_trace(go.Scatter(
                x=clean_data[x_column],
                y=clean_data[y_column],
                mode='lines+markers',
                name=y_column.title(),
                line=dict(color=self.default_colors[0], width=2),
                marker=dict(size=4)
            ))
            
            # Add threshold lines if provided
            if thresholds:
                x_range = [clean_data[x_column].min(), clean_data[x_column].max()]
                
                if 'critical_high' in thresholds:
                    fig.add_hline(
                        y=thresholds['critical_high'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Critical High"
                    )
                
                if 'warning_high' in thresholds:
                    fig.add_hline(
                        y=thresholds['warning_high'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="Warning High"
                    )
                
                if 'warning_low' in thresholds:
                    fig.add_hline(
                        y=thresholds['warning_low'],
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="Warning Low"
                    )
                
                if 'critical_low' in thresholds:
                    fig.add_hline(
                        y=thresholds['critical_low'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Critical Low"
                    )
            
            fig.update_layout(
                title=title,
                xaxis_title=x_column.title(),
                yaxis_title=y_column.title(),
                **self.default_layout
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating time series with alerts: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message."""
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=message,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            **self.default_layout
        )
        
        return fig
    
    def create_dashboard_summary_chart(self, 
                                     data: pd.DataFrame, 
                                     parameters: List[str],
                                     chart_type: str = "line") -> go.Figure:
        """
        Create a summary chart for dashboard overview.
        
        Args:
            data: DataFrame containing the data
            parameters: List of parameters to include
            chart_type: Type of chart ('line', 'bar', 'area')
            
        Returns:
            go.Figure: Plotly figure object
        """
        try:
            if 'timestamp' not in data.columns:
                return self._create_empty_chart("No timestamp data available")
            
            # Create subplots
            rows = len(parameters)
            if rows == 0:
                return self._create_empty_chart("No parameters selected")
            
            fig = make_subplots(
                rows=rows,
                cols=1,
                subplot_titles=[param.title() for param in parameters],
                vertical_spacing=0.1
            )
            
            for i, param in enumerate(parameters, 1):
                if param in data.columns:
                    param_data = data[['timestamp', param]].dropna()
                    
                    if not param_data.empty:
                        if chart_type == "line":
                            trace = go.Scatter(
                                x=param_data['timestamp'],
                                y=param_data[param],
                                mode='lines',
                                name=param.title(),
                                line=dict(color=self.default_colors[(i-1) % len(self.default_colors)])
                            )
                        elif chart_type == "area":
                            trace = go.Scatter(
                                x=param_data['timestamp'],
                                y=param_data[param],
                                mode='lines',
                                fill='tonexty' if i > 1 else 'tozeroy',
                                name=param.title(),
                                line=dict(color=self.default_colors[(i-1) % len(self.default_colors)])
                            )
                        else:  # bar
                            trace = go.Bar(
                                x=param_data['timestamp'],
                                y=param_data[param],
                                name=param.title(),
                                marker_color=self.default_colors[(i-1) % len(self.default_colors)]
                            )
                        
                        fig.add_trace(trace, row=i, col=1)
            
            fig.update_layout(
                height=300 * rows,
                title="Process Parameters Overview",
                showlegend=False,
                **self.default_layout
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating dashboard summary chart: {e}")
            return self._create_empty_chart(f"Error: {str(e)}")
