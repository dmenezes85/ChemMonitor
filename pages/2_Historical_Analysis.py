import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from utils.data_manager import DataManager
from utils.visualization import ChartGenerator
from utils.statistics import StatisticsCalculator

st.set_page_config(page_title="Historical Analysis", page_icon="📈", layout="wide")

# Initialize utilities
@st.cache_resource
def get_utilities():
    data_manager = DataManager()
    chart_generator = ChartGenerator()
    stats_calculator = StatisticsCalculator()
    return data_manager, chart_generator, stats_calculator

data_manager, chart_generator, stats_calculator = get_utilities()

st.title("📈 Historical Data Analysis")
st.markdown("Analyze trends, patterns, and correlations in your chemical process data.")
st.markdown("---")

# Load data
all_data = data_manager.get_all_data()

if all_data.empty:
    st.warning("No historical data available. Please add some data first using the Data Input page.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Analysis Filters")
    
    # Date range filter
    st.subheader("Time Range")
    if 'timestamp' in all_data.columns:
        min_date = all_data['timestamp'].min().date()
        max_date = all_data['timestamp'].max().date()
        
        date_range = st.date_input(
            "Select date range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            # Filter data by date range
            mask = (all_data['timestamp'].dt.date >= start_date) & (all_data['timestamp'].dt.date <= end_date)
            filtered_data = all_data[mask].copy()
        else:
            filtered_data = all_data.copy()
    else:
        filtered_data = all_data.copy()
    
    # Parameter selection
    st.subheader("Parameters")
    numeric_columns = filtered_data.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_columns:
        selected_params = st.multiselect(
            "Select parameters to analyze:",
            numeric_columns,
            default=numeric_columns[:4] if len(numeric_columns) >= 4 else numeric_columns
        )
    else:
        st.warning("No numeric parameters found in the data.")
        selected_params = []
    
    # Data aggregation
    st.subheader("Data Aggregation")
    aggregation_level = st.selectbox(
        "Aggregation level:",
        ["Raw Data", "Hourly Average", "Daily Average", "Weekly Average"],
        help="Aggregate data to reduce noise and identify trends"
    )

# Apply filters
if selected_params:
    analysis_data = filtered_data[['timestamp'] + selected_params].copy()
    
    # Apply aggregation
    if aggregation_level != "Raw Data":
        freq_map = {
            "Hourly Average": "H",
            "Daily Average": "D", 
            "Weekly Average": "W"
        }
        freq = freq_map[aggregation_level]
        
        analysis_data = analysis_data.set_index('timestamp')
        analysis_data = analysis_data.resample(freq).mean().reset_index()
        analysis_data = analysis_data.dropna()

# Main analysis tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Trend Analysis", 
    "🔗 Correlation Analysis", 
    "📉 Statistical Analysis", 
    "🎯 Process Comparison", 
    "📋 Data Summary"
])

with tab1:
    st.subheader("Trend Analysis")
    
    if selected_params and not analysis_data.empty:
        # Individual parameter trends
        st.markdown("### Individual Parameter Trends")
        
        # Parameter selection for detailed view
        primary_param = st.selectbox(
            "Select primary parameter for detailed analysis:",
            selected_params,
            key="trend_param"
        )
        
        if primary_param:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Main trend chart
                fig = chart_generator.create_line_chart(
                    analysis_data, 'timestamp', primary_param,
                    f"{primary_param.title()} Trend Over Time",
                    primary_param.title()
                )
                
                # Add moving average
                if len(analysis_data) > 5:
                    window_size = min(10, len(analysis_data) // 3)
                    analysis_data[f'{primary_param}_ma'] = analysis_data[primary_param].rolling(window=window_size).mean()
                    
                    fig.add_trace(
                        go.Scatter(
                            x=analysis_data['timestamp'],
                            y=analysis_data[f'{primary_param}_ma'],
                            mode='lines',
                            name=f'Moving Average ({window_size} points)',
                            line=dict(color='red', width=2, dash='dash')
                        )
                    )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Trend statistics
                st.markdown("**Trend Statistics:**")
                
                param_data = analysis_data[primary_param].dropna()
                if len(param_data) > 1:
                    # Calculate trend slope
                    x = np.arange(len(param_data))
                    slope, intercept = np.polyfit(x, param_data, 1)
                    
                    st.metric("Trend Slope", f"{slope:.4f}")
                    
                    # Overall change
                    total_change = param_data.iloc[-1] - param_data.iloc[0]
                    percent_change = (total_change / param_data.iloc[0]) * 100 if param_data.iloc[0] != 0 else 0
                    
                    st.metric("Total Change", f"{total_change:.2f}")
                    st.metric("Percent Change", f"{percent_change:.1f}%")
                    
                    # Volatility
                    volatility = param_data.std()
                    st.metric("Volatility (StdDev)", f"{volatility:.2f}")
        
        # Multi-parameter comparison
        st.markdown("### Multi-Parameter Comparison")
        
        if len(selected_params) > 1:
            # Normalize data for comparison
            comparison_params = st.multiselect(
                "Select parameters to compare:",
                selected_params,
                default=selected_params[:3],
                key="comparison_params"
            )
            
            if len(comparison_params) > 1:
                # Create normalized comparison chart
                fig = go.Figure()
                
                for param in comparison_params:
                    # Normalize to 0-1 scale
                    param_data = analysis_data[param].dropna()
                    if len(param_data) > 0:
                        normalized = (param_data - param_data.min()) / (param_data.max() - param_data.min())
                        
                        fig.add_trace(
                            go.Scatter(
                                x=analysis_data['timestamp'],
                                y=normalized,
                                mode='lines',
                                name=param.title(),
                                line=dict(width=2)
                            )
                        )
                
                fig.update_layout(
                    title="Normalized Parameter Comparison",
                    xaxis_title="Time",
                    yaxis_title="Normalized Value (0-1)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Select parameters from the sidebar to perform trend analysis.")

with tab2:
    st.subheader("Correlation Analysis")
    
    if len(selected_params) > 1 and not analysis_data.empty:
        # Correlation matrix
        st.markdown("### Parameter Correlation Matrix")
        
        corr_data = analysis_data[selected_params].corr()
        
        fig = px.imshow(
            corr_data,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Parameter Correlation Matrix"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Strongest correlations
        st.markdown("### Strongest Correlations")
        
        # Get correlation pairs
        corr_pairs = []
        for i in range(len(corr_data.columns)):
            for j in range(i+1, len(corr_data.columns)):
                param1 = corr_data.columns[i]
                param2 = corr_data.columns[j]
                correlation = corr_data.iloc[i, j]
                corr_pairs.append({
                    'Parameter 1': param1,
                    'Parameter 2': param2,
                    'Correlation': correlation,
                    'Strength': 'Strong' if abs(correlation) > 0.7 else 'Moderate' if abs(correlation) > 0.4 else 'Weak'
                })
        
        corr_df = pd.DataFrame(corr_pairs)
        corr_df = corr_df.sort_values('Correlation', key=abs, ascending=False)
        
        st.dataframe(corr_df, use_container_width=True)
        
        # Scatter plots for strong correlations
        strong_corrs = corr_df[corr_df['Strength'] == 'Strong'].head(3)
        
        if not strong_corrs.empty:
            st.markdown("### Scatter Plot Analysis")
            
            for _, row in strong_corrs.iterrows():
                param1, param2 = row['Parameter 1'], row['Parameter 2']
                correlation = row['Correlation']
                
                fig = px.scatter(
                    analysis_data,
                    x=param1,
                    y=param2,
                    title=f"{param1.title()} vs {param2.title()} (r={correlation:.3f})",
                    trendline="ols"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Select at least 2 parameters from the sidebar to perform correlation analysis.")

with tab3:
    st.subheader("Statistical Analysis")
    
    if selected_params and not analysis_data.empty:
        # Basic statistics
        st.markdown("### Descriptive Statistics")
        
        stats_summary = stats_calculator.calculate_basic_stats(analysis_data[selected_params])
        st.dataframe(stats_summary, use_container_width=True)
        
        # Distribution analysis
        st.markdown("### Distribution Analysis")
        
        selected_param_dist = st.selectbox(
            "Select parameter for distribution analysis:",
            selected_params,
            key="dist_param"
        )
        
        if selected_param_dist:
            col1, col2 = st.columns(2)
            
            with col1:
                # Histogram
                fig_hist = chart_generator.create_histogram(
                    analysis_data[selected_param_dist],
                    f"{selected_param_dist.title()} Distribution"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Box plot
                fig_box = px.box(
                    y=analysis_data[selected_param_dist],
                    title=f"{selected_param_dist.title()} Box Plot"
                )
                fig_box.update_layout(showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True)
        
        # Statistical tests
        st.markdown("### Statistical Tests")
        
        param_data = analysis_data[selected_param_dist].dropna()
        
        if len(param_data) > 10:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Normality test (simplified)
                from scipy import stats
                
                # Shapiro-Wilk test for normality (if scipy is available)
                try:
                    stat, p_value = stats.shapiro(param_data[:5000])  # Limit sample size
                    st.metric("Normality Test", "Normal" if p_value > 0.05 else "Non-normal")
                    st.caption(f"p-value: {p_value:.4f}")
                except:
                    st.metric("Normality Test", "N/A")
            
            with col2:
                # Outliers detection (IQR method)
                Q1 = param_data.quantile(0.25)
                Q3 = param_data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = param_data[(param_data < Q1 - 1.5*IQR) | (param_data > Q3 + 1.5*IQR)]
                
                st.metric("Outliers", len(outliers))
                st.caption(f"{len(outliers)/len(param_data)*100:.1f}% of data")
            
            with col3:
                # Stability check (coefficient of variation)
                cv = (param_data.std() / param_data.mean()) * 100 if param_data.mean() != 0 else float('inf')
                stability = "Stable" if cv < 10 else "Moderate" if cv < 30 else "Unstable"
                
                st.metric("Process Stability", stability)
                st.caption(f"CV: {cv:.1f}%")
    
    else:
        st.info("Select parameters from the sidebar to perform statistical analysis.")

with tab4:
    st.subheader("Process Comparison")
    
    if selected_params and not analysis_data.empty:
        st.markdown("### Time Period Comparison")
        
        # Split data into periods for comparison
        comparison_type = st.selectbox(
            "Select comparison type:",
            ["Before/After Split", "Weekday/Weekend", "Shift Comparison", "Custom Periods"]
        )
        
        if comparison_type == "Before/After Split":
            split_date = st.date_input(
                "Select split date:",
                value=analysis_data['timestamp'].quantile(0.5).date(),
                min_value=analysis_data['timestamp'].min().date(),
                max_value=analysis_data['timestamp'].max().date()
            )
            
            before_data = analysis_data[analysis_data['timestamp'].dt.date < split_date]
            after_data = analysis_data[analysis_data['timestamp'].dt.date >= split_date]
            
            comparison_param = st.selectbox(
                "Select parameter to compare:",
                selected_params,
                key="comparison_param"
            )
            
            if len(before_data) > 0 and len(after_data) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Before Split**")
                    before_stats = before_data[comparison_param].describe()
                    st.dataframe(before_stats)
                
                with col2:
                    st.markdown("**After Split**")
                    after_stats = after_data[comparison_param].describe()
                    st.dataframe(after_stats)
                
                # Comparison visualization
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=before_data[comparison_param],
                    name='Before',
                    opacity=0.7,
                    nbinsx=30
                ))
                
                fig.add_trace(go.Histogram(
                    x=after_data[comparison_param],
                    name='After',
                    opacity=0.7,
                    nbinsx=30
                ))
                
                fig.update_layout(
                    title=f"{comparison_param.title()} Distribution Comparison",
                    barmode='overlay',
                    xaxis_title=comparison_param.title(),
                    yaxis_title='Frequency'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        elif comparison_type == "Weekday/Weekend":
            analysis_data['day_type'] = analysis_data['timestamp'].dt.dayofweek.apply(
                lambda x: 'Weekend' if x >= 5 else 'Weekday'
            )
            
            comparison_param = st.selectbox(
                "Select parameter to compare:",
                selected_params,
                key="weekday_comparison_param"
            )
            
            weekday_data = analysis_data[analysis_data['day_type'] == 'Weekday'][comparison_param]
            weekend_data = analysis_data[analysis_data['day_type'] == 'Weekend'][comparison_param]
            
            if len(weekday_data) > 0 and len(weekend_data) > 0:
                fig = px.box(
                    analysis_data,
                    x='day_type',
                    y=comparison_param,
                    title=f"{comparison_param.title()}: Weekday vs Weekend"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistical comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Weekday Statistics**")
                    st.dataframe(weekday_data.describe())
                
                with col2:
                    st.markdown("**Weekend Statistics**")
                    st.dataframe(weekend_data.describe())
    
    else:
        st.info("Select parameters from the sidebar to perform process comparison.")

with tab5:
    st.subheader("Data Summary")
    
    if not analysis_data.empty:
        # Overall data summary
        st.markdown("### Dataset Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", len(analysis_data))
        
        with col2:
            if 'timestamp' in analysis_data.columns:
                time_span = analysis_data['timestamp'].max() - analysis_data['timestamp'].min()
                st.metric("Time Span", f"{time_span.days} days")
        
        with col3:
            st.metric("Parameters", len(selected_params))
        
        with col4:
            completeness = (1 - analysis_data[selected_params].isnull().sum().sum() / 
                          (len(analysis_data) * len(selected_params))) * 100
            st.metric("Data Completeness", f"{completeness:.1f}%")
        
        # Missing data analysis
        st.markdown("### Missing Data Analysis")
        
        missing_data = analysis_data[selected_params].isnull().sum()
        missing_percent = (missing_data / len(analysis_data)) * 100
        
        missing_df = pd.DataFrame({
            'Parameter': missing_data.index,
            'Missing Count': missing_data.values,
            'Missing Percentage': missing_percent.values
        })
        
        st.dataframe(missing_df, use_container_width=True)
        
        # Data quality issues
        st.markdown("### Data Quality Issues")
        
        quality_issues = []
        
        for param in selected_params:
            param_data = analysis_data[param].dropna()
            
            if len(param_data) > 0:
                # Check for duplicates
                duplicates = len(param_data) - len(param_data.drop_duplicates())
                
                # Check for outliers
                Q1 = param_data.quantile(0.25)
                Q3 = param_data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = len(param_data[(param_data < Q1 - 1.5*IQR) | (param_data > Q3 + 1.5*IQR)])
                
                # Check for constant values
                constant_values = len(param_data.unique()) == 1
                
                quality_issues.append({
                    'Parameter': param,
                    'Duplicate Values': duplicates,
                    'Outliers': outliers,
                    'Constant Values': constant_values,
                    'Zero Values': (param_data == 0).sum()
                })
        
        quality_df = pd.DataFrame(quality_issues)
        st.dataframe(quality_df, use_container_width=True)
        
        # Sample data preview
        st.markdown("### Sample Data")
        st.dataframe(analysis_data.head(20), use_container_width=True)
    
    else:
        st.info("No data available for analysis.")

# Export filtered data
if not analysis_data.empty:
    st.markdown("---")
    st.subheader("📥 Export Filtered Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download as CSV"):
            csv = analysis_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"filtered_process_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Download Summary Report"):
            # Create summary report
            summary_report = []
            summary_report.append("# Process Data Analysis Report")
            summary_report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_report.append(f"Data Points: {len(analysis_data)}")
            summary_report.append(f"Parameters: {', '.join(selected_params)}")
            summary_report.append("")
            
            if selected_params:
                summary_report.append("## Statistical Summary")
                stats_summary = stats_calculator.calculate_basic_stats(analysis_data[selected_params])
                summary_report.append(stats_summary.to_string())
            
            report_text = "\n".join(summary_report)
            
            st.download_button(
                label="Download Report",
                data=report_text,
                file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
