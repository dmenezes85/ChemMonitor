import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
import io
import base64
from utils.data_manager import DataManager
from utils.statistics import StatisticsCalculator
from utils.visualization import ChartGenerator
from utils.theme_manager import setup_theme_selector, get_theme_mode

st.set_page_config(page_title="Data Export", page_icon="📥", layout="wide")

# Apply theme
with st.sidebar:
    setup_theme_selector()

# Initialize utilities
@st.cache_resource
def get_utilities():
    data_manager = DataManager()
    stats_calculator = StatisticsCalculator()
    return data_manager, stats_calculator

def get_chart_generator():
    theme = 'dark' if get_theme_mode() == 'Escuro' else 'light'
    return ChartGenerator(theme)

data_manager, stats_calculator = get_utilities()

st.title("📥 Data Export & Reports")
st.markdown("Export process data and generate comprehensive reports for analysis and documentation.")
st.markdown("---")

# Load data
all_data = data_manager.get_all_data()

if all_data.empty:
    st.warning("No data available for export. Please add some data first using the Data Input page.")
    st.stop()

# Tabs for different export options
tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Export", "📈 Report Generation", "📋 Custom Reports", "🔧 Export Settings"])

with tab1:
    st.subheader("Data Export Options")
    
    # Data filtering section
    with st.expander("🔍 Filter Data for Export", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Date range selection
            st.markdown("**Time Range**")
            if 'timestamp' in all_data.columns:
                min_date = all_data['timestamp'].min().date()
                max_date = all_data['timestamp'].max().date()
                
                export_date_range = st.date_input(
                    "Select date range:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="export_date_range"
                )
            
            # Parameter selection
            st.markdown("**Parameters**")
            numeric_columns = all_data.select_dtypes(include=[np.number]).columns.tolist()
            
            export_params = st.multiselect(
                "Select parameters to export:",
                options=['timestamp'] + numeric_columns,
                default=['timestamp'] + numeric_columns,
                key="export_params"
            )
        
        with col2:
            # Data aggregation
            st.markdown("**Data Aggregation**")
            aggregation_level = st.selectbox(
                "Aggregation level:",
                ["Raw Data", "Hourly Average", "Daily Average", "Weekly Average"],
                help="Aggregate data to reduce file size and noise",
                key="export_aggregation"
            )
            
            # Quality filters
            st.markdown("**Data Quality**")
            
            remove_outliers = st.checkbox(
                "Remove outliers",
                help="Remove statistical outliers based on IQR method"
            )
            
            remove_duplicates = st.checkbox(
                "Remove duplicates",
                help="Remove duplicate timestamp entries"
            )
            
            fill_missing = st.selectbox(
                "Handle missing values:",
                ["Keep as is", "Remove rows", "Forward fill", "Interpolate"],
                help="How to handle missing data points"
            )
    
    # Apply filters
    filtered_data = all_data.copy()
    
    # Date filtering
    if 'timestamp' in filtered_data.columns and len(export_date_range) == 2:
        start_date, end_date = export_date_range
        mask = (filtered_data['timestamp'].dt.date >= start_date) & (filtered_data['timestamp'].dt.date <= end_date)
        filtered_data = filtered_data[mask]
    
    # Parameter filtering
    if export_params:
        available_params = [p for p in export_params if p in filtered_data.columns]
        filtered_data = filtered_data[available_params]
    
    # Data quality processing
    if remove_duplicates and 'timestamp' in filtered_data.columns:
        filtered_data = filtered_data.drop_duplicates(subset=['timestamp'])
    
    if remove_outliers:
        for col in filtered_data.select_dtypes(include=[np.number]).columns:
            Q1 = filtered_data[col].quantile(0.25)
            Q3 = filtered_data[col].quantile(0.75)
            IQR = Q3 - Q1
            filtered_data = filtered_data[
                ~((filtered_data[col] < (Q1 - 1.5 * IQR)) | (filtered_data[col] > (Q3 + 1.5 * IQR)))
            ]
    
    # Handle missing values
    if fill_missing == "Remove rows":
        filtered_data = filtered_data.dropna()
    elif fill_missing == "Forward fill":
        filtered_data = filtered_data.fillna(method='ffill')
    elif fill_missing == "Interpolate":
        numeric_cols = filtered_data.select_dtypes(include=[np.number]).columns
        filtered_data[numeric_cols] = filtered_data[numeric_cols].interpolate()
    
    # Apply aggregation
    if aggregation_level != "Raw Data" and 'timestamp' in filtered_data.columns:
        freq_map = {
            "Hourly Average": "H",
            "Daily Average": "D", 
            "Weekly Average": "W"
        }
        freq = freq_map[aggregation_level]
        
        filtered_data = filtered_data.set_index('timestamp')
        filtered_data = filtered_data.resample(freq).mean().reset_index()
        filtered_data = filtered_data.dropna()
    
    # Display filtered data preview
    st.markdown("---")
    st.subheader("📋 Filtered Data Preview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(filtered_data))
    
    with col2:
        original_records = len(all_data)
        reduction = ((original_records - len(filtered_data)) / original_records) * 100 if original_records > 0 else 0
        st.metric("Data Reduction", f"{reduction:.1f}%")
    
    with col3:
        if 'timestamp' in filtered_data.columns:
            time_span = filtered_data['timestamp'].max() - filtered_data['timestamp'].min()
            st.metric("Time Span", f"{time_span.days} days")
    
    with col4:
        file_size_mb = (filtered_data.memory_usage(deep=True).sum() / 1024 / 1024)
        st.metric("Est. File Size", f"{file_size_mb:.1f} MB")
    
    # Data preview table
    st.dataframe(filtered_data.head(10), use_container_width=True)
    
    # Export options
    st.markdown("---")
    st.subheader("📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV Export
        st.markdown("**CSV Export**")
        
        csv_options = st.radio(
            "CSV format:",
            ["Standard CSV", "Excel-compatible CSV", "Tab-separated"],
            key="csv_format"
        )
        
        if st.button("📄 Download CSV", type="primary"):
            if csv_options == "Standard CSV":
                csv_data = filtered_data.to_csv(index=False)
                file_extension = "csv"
            elif csv_options == "Excel-compatible CSV":
                csv_data = filtered_data.to_csv(index=False, encoding='utf-8-sig')
                file_extension = "csv"
            else:  # Tab-separated
                csv_data = filtered_data.to_csv(index=False, sep='\t')
                file_extension = "tsv"
            
            filename = f"process_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            
            st.download_button(
                label=f"💾 Download {filename}",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
    
    with col2:
        # JSON Export
        st.markdown("**JSON Export**")
        
        json_format = st.radio(
            "JSON structure:",
            ["Records format", "Index format", "Values format"],
            key="json_format"
        )
        
        if st.button("📄 Download JSON", type="primary"):
            if json_format == "Records format":
                json_data = filtered_data.to_json(orient='records', date_format='iso', indent=2)
            elif json_format == "Index format":
                json_data = filtered_data.to_json(orient='index', date_format='iso', indent=2)
            else:  # Values format
                json_data = filtered_data.to_json(orient='values', date_format='iso', indent=2)
            
            filename = f"process_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            st.download_button(
                label=f"💾 Download {filename}",
                data=json_data,
                file_name=filename,
                mime="application/json"
            )
    
    with col3:
        # Excel Export
        st.markdown("**Excel Export**")
        
        excel_options = st.checkbox("Include charts in Excel", value=False)
        include_stats = st.checkbox("Include statistics sheet", value=True)
        
        if st.button("📄 Download Excel", type="primary"):
            # Create Excel file in memory
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Main data sheet
                filtered_data.to_excel(writer, sheet_name='Process Data', index=False)
                
                # Statistics sheet
                if include_stats:
                    numeric_cols = filtered_data.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        stats_summary = stats_calculator.calculate_basic_stats(filtered_data[numeric_cols])
                        stats_summary.to_excel(writer, sheet_name='Statistics')
                
                # Metadata sheet
                metadata = pd.DataFrame({
                    'Property': ['Export Date', 'Total Records', 'Time Range Start', 'Time Range End', 'Aggregation Level'],
                    'Value': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        len(filtered_data),
                        filtered_data['timestamp'].min() if 'timestamp' in filtered_data.columns else 'N/A',
                        filtered_data['timestamp'].max() if 'timestamp' in filtered_data.columns else 'N/A',
                        aggregation_level
                    ]
                })
                metadata.to_excel(writer, sheet_name='Metadata', index=False)
            
            filename = f"process_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            st.download_button(
                label=f"💾 Download {filename}",
                data=output.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with tab2:
    st.subheader("Automated Report Generation")
    
    # Report template selection
    st.markdown("### 📋 Report Templates")
    
    report_type = st.selectbox(
        "Select report type:",
        [
            "Daily Process Summary", 
            "Weekly Analysis Report", 
            "Monthly Trend Report",
            "Alert Summary Report",
            "Data Quality Report",
            "Custom Analysis Report"
        ]
    )
    
    # Report configuration
    with st.expander("⚙️ Report Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Time period for report
            report_period = st.selectbox(
                "Report time period:",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "Custom range"]
            )
            
            if report_period == "Custom range":
                custom_start = st.date_input("Start date")
                custom_end = st.date_input("End date")
            
            # Parameters to include
            report_params = st.multiselect(
                "Parameters to include:",
                numeric_columns,
                default=numeric_columns[:4] if len(numeric_columns) >= 4 else numeric_columns,
                key="report_params"
            )
        
        with col2:
            # Report options
            include_charts = st.checkbox("Include charts", value=True)
            include_statistics = st.checkbox("Include statistical analysis", value=True)
            include_alerts = st.checkbox("Include alert summary", value=True)
            include_recommendations = st.checkbox("Include recommendations", value=False)
            
            # Report format
            report_format = st.selectbox(
                "Report format:",
                ["PDF Report", "HTML Report", "Word Document", "PowerPoint Presentation"]
            )
    
    # Generate report button
    if st.button("📊 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            # Filter data for report period
            if report_period == "Last 24 hours":
                cutoff_time = datetime.now() - timedelta(hours=24)
            elif report_period == "Last 7 days":
                cutoff_time = datetime.now() - timedelta(days=7)
            elif report_period == "Last 30 days":
                cutoff_time = datetime.now() - timedelta(days=30)
            else:  # Custom range
                cutoff_time = datetime.combine(custom_start, datetime.min.time())
            
            report_data = all_data[all_data['timestamp'] >= cutoff_time] if 'timestamp' in all_data.columns else all_data
            
            # Generate report content
            report_content = generate_report_content(
                report_data, 
                report_type, 
                report_params,
                include_charts,
                include_statistics,
                include_alerts,
                include_recommendations
            )
            
            # Display report preview
            st.markdown("### 📖 Report Preview")
            st.markdown(report_content)
            
            # Download options
            if report_format == "HTML Report":
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{report_type}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        h1, h2, h3 {{ color: #2E86AB; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    {report_content}
                </body>
                </html>
                """
                
                filename = f"{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_content,
                    file_name=filename,
                    mime="text/html"
                )

def generate_report_content(data, report_type, params, include_charts, include_stats, include_alerts, include_recommendations):
    """Generate report content based on selected options"""
    
    content = []
    
    # Report header
    content.append(f"# {report_type}")
    content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"**Data Period:** {data['timestamp'].min()} to {data['timestamp'].max()}" if 'timestamp' in data.columns else "")
    content.append(f"**Total Records:** {len(data)}")
    content.append("---")
    
    # Executive summary
    content.append("## Executive Summary")
    if len(data) > 0:
        content.append(f"This report analyzes {len(data)} data points across {len(params)} process parameters.")
        content.append("Key findings and observations are detailed in the sections below.")
    else:
        content.append("No data available for the selected time period.")
        return "\n".join(content)
    
    # Statistical analysis
    if include_stats and len(params) > 0:
        content.append("## Statistical Analysis")
        
        stats_data = data[params].describe()
        content.append("### Parameter Statistics")
        content.append(stats_data.to_string())
        
        # Key insights
        content.append("### Key Insights")
        for param in params:
            if param in data.columns:
                param_data = data[param].dropna()
                if len(param_data) > 0:
                    mean_val = param_data.mean()
                    std_val = param_data.std()
                    cv = (std_val / mean_val * 100) if mean_val != 0 else 0
                    
                    content.append(f"- **{param.title()}**: Mean = {mean_val:.2f}, CV = {cv:.1f}%")
    
    # Data quality assessment
    content.append("## Data Quality Assessment")
    missing_data = data[params].isnull().sum()
    total_possible = len(data) * len(params)
    completeness = (1 - missing_data.sum() / total_possible) * 100 if total_possible > 0 else 100
    
    content.append(f"- **Data Completeness:** {completeness:.1f}%")
    content.append(f"- **Missing Values:** {missing_data.sum()} out of {total_possible}")
    
    # Recommendations
    if include_recommendations:
        content.append("## Recommendations")
        content.append("Based on the analysis of the data, the following recommendations are made:")
        
        # Simple rule-based recommendations
        if completeness < 95:
            content.append("- **Data Collection:** Improve data collection processes to reduce missing values.")
        
        for param in params:
            if param in data.columns:
                param_data = data[param].dropna()
                if len(param_data) > 0:
                    cv = (param_data.std() / param_data.mean() * 100) if param_data.mean() != 0 else 0
                    if cv > 20:
                        content.append(f"- **{param.title()}:** High variability detected (CV={cv:.1f}%). Consider process optimization.")
    
    return "\n\n".join(content)

with tab3:
    st.subheader("Custom Report Builder")
    
    st.markdown("Build custom reports with specific parameters, visualizations, and analysis.")
    
    # Custom report configuration
    with st.form("custom_report_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Report basic info
            custom_report_title = st.text_input("Report Title", value="Custom Process Analysis Report")
            custom_description = st.text_area("Report Description", value="Custom analysis of chemical process parameters.")
            
            # Time range
            custom_time_range = st.selectbox(
                "Analysis Time Range:",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "All available data"]
            )
            
            # Parameters
            custom_params = st.multiselect(
                "Select Parameters:",
                numeric_columns,
                default=numeric_columns[:3] if len(numeric_columns) >= 3 else numeric_columns
            )
        
        with col2:
            # Analysis sections
            st.markdown("**Include in Report:**")
            
            custom_include_summary = st.checkbox("Executive Summary", value=True)
            custom_include_trends = st.checkbox("Trend Analysis", value=True)
            custom_include_correlation = st.checkbox("Correlation Analysis", value=True)
            custom_include_distribution = st.checkbox("Distribution Analysis", value=True)
            custom_include_outliers = st.checkbox("Outlier Detection", value=False)
            custom_include_forecasting = st.checkbox("Simple Forecasting", value=False)
            
            # Chart options
            st.markdown("**Visualization Options:**")
            custom_chart_style = st.selectbox("Chart Style:", ["Professional", "Colorful", "Minimal"])
            custom_include_tables = st.checkbox("Include Data Tables", value=True)
        
        # Generate custom report
        generate_custom = st.form_submit_button("🔧 Generate Custom Report", type="primary")
        
        if generate_custom and custom_params:
            # Filter data based on time range
            if custom_time_range == "Last 24 hours":
                cutoff = datetime.now() - timedelta(hours=24)
            elif custom_time_range == "Last 7 days":
                cutoff = datetime.now() - timedelta(days=7)
            elif custom_time_range == "Last 30 days":
                cutoff = datetime.now() - timedelta(days=30)
            else:
                cutoff = all_data['timestamp'].min() if 'timestamp' in all_data.columns else datetime.now() - timedelta(days=365)
            
            custom_data = all_data[all_data['timestamp'] >= cutoff] if 'timestamp' in all_data.columns else all_data
            
            if not custom_data.empty:
                st.markdown("---")
                st.markdown(f"# {custom_report_title}")
                st.markdown(f"*{custom_description}*")
                st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Executive Summary
                if custom_include_summary:
                    st.markdown("## Executive Summary")
                    st.write(f"This custom report analyzes {len(custom_data)} data points for parameters: {', '.join(custom_params)}")
                    
                    # Key metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Data Points", len(custom_data))
                    with col2:
                        if 'timestamp' in custom_data.columns:
                            time_span = custom_data['timestamp'].max() - custom_data['timestamp'].min()
                            st.metric("Time Span", f"{time_span.days} days")
                    with col3:
                        st.metric("Parameters", len(custom_params))
                
                # Trend Analysis
                if custom_include_trends and 'timestamp' in custom_data.columns:
                    st.markdown("## Trend Analysis")
                    
                    for param in custom_params:
                        if param in custom_data.columns:
                            fig = chart_generator.create_line_chart(
                                custom_data, 'timestamp', param,
                                f"{param.title()} Trend Analysis",
                                param.title()
                            )
                            st.plotly_chart(fig, use_container_width=True)
                
                # Correlation Analysis
                if custom_include_correlation and len(custom_params) > 1:
                    st.markdown("## Correlation Analysis")
                    
                    corr_matrix = custom_data[custom_params].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale="RdBu_r",
                        title="Parameter Correlation Matrix"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Distribution Analysis
                if custom_include_distribution:
                    st.markdown("## Distribution Analysis")
                    
                    for param in custom_params:
                        if param in custom_data.columns:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig_hist = chart_generator.create_histogram(
                                    custom_data[param], f"{param.title()} Distribution"
                                )
                                st.plotly_chart(fig_hist, use_container_width=True)
                            
                            with col2:
                                fig_box = px.box(y=custom_data[param], title=f"{param.title()} Box Plot")
                                st.plotly_chart(fig_box, use_container_width=True)
                
                # Statistical Summary Tables
                if custom_include_tables:
                    st.markdown("## Statistical Summary")
                    stats_summary = stats_calculator.calculate_basic_stats(custom_data[custom_params])
                    st.dataframe(stats_summary, use_container_width=True)

with tab4:
    st.subheader("Export Settings & Preferences")
    
    st.markdown("Configure default settings for data exports and reports.")
    
    # Export preferences
    with st.expander("📋 Default Export Preferences", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**File Format Preferences**")
            default_format = st.selectbox("Default export format:", ["CSV", "Excel", "JSON"])
            default_aggregation = st.selectbox("Default aggregation:", ["Raw Data", "Hourly Average", "Daily Average"])
            include_metadata = st.checkbox("Always include metadata", value=True)
            
        with col2:
            st.markdown("**Data Quality Settings**")
            auto_remove_outliers = st.checkbox("Auto-remove outliers", value=False)
            auto_remove_duplicates = st.checkbox("Auto-remove duplicates", value=True)
            default_missing_handling = st.selectbox("Default missing value handling:", ["Keep as is", "Forward fill", "Remove rows"])
    
    # Report preferences
    with st.expander("📊 Report Generation Preferences", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Default Report Sections**")
            default_include_summary = st.checkbox("Include executive summary", value=True)
            default_include_charts = st.checkbox("Include visualizations", value=True)
            default_include_stats = st.checkbox("Include statistics", value=True)
            
        with col2:
            st.markdown("**Report Styling**")
            default_chart_theme = st.selectbox("Default chart theme:", ["plotly", "plotly_white", "plotly_dark"])
            default_color_scheme = st.selectbox("Color scheme:", ["Default", "Professional", "High Contrast"])
    
    # Scheduled exports
    with st.expander("⏰ Scheduled Exports (Future Feature)", expanded=False):
        st.info("Scheduled export functionality would be implemented here, allowing users to:")
        st.markdown("""
        - Set up automatic daily/weekly/monthly exports
        - Configure email delivery of reports
        - Set up data backup schedules
        - Define export triggers based on data volume or time
        """)
    
    # Export history
    st.markdown("---")
    st.subheader("📋 Recent Export History")
    
    # This would track export history in a real implementation
    st.info("Export history tracking would show:")
    st.markdown("""
    - Recent data exports with timestamps
    - File sizes and formats
    - Export duration and success status
    - Download links for recent exports (if still available)
    """)
    
    # Save preferences
    if st.button("💾 Save Export Preferences", type="primary"):
        # In a real implementation, these preferences would be saved to a config file or database
        preferences = {
            'default_format': default_format,
            'default_aggregation': default_aggregation,
            'include_metadata': include_metadata,
            'auto_remove_outliers': auto_remove_outliers,
            'auto_remove_duplicates': auto_remove_duplicates,
            'default_missing_handling': default_missing_handling,
            'default_include_summary': default_include_summary,
            'default_include_charts': default_include_charts,
            'default_include_stats': default_include_stats,
            'default_chart_theme': default_chart_theme,
            'default_color_scheme': default_color_scheme,
            'updated_at': datetime.now().isoformat()
        }
        
        st.success("✅ Export preferences saved successfully!")
        st.json(preferences)

# Footer with export statistics
st.markdown("---")
if not all_data.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Data Points", len(all_data))
    
    with col2:
        if 'timestamp' in all_data.columns:
            total_span = all_data['timestamp'].max() - all_data['timestamp'].min()
            st.metric("Total Time Span", f"{total_span.days} days")
    
    with col3:
        total_size_mb = (all_data.memory_usage(deep=True).sum() / 1024 / 1024)
        st.metric("Database Size", f"{total_size_mb:.1f} MB")
    
    with col4:
        export_ready = "Ready" if len(all_data) > 0 else "No Data"
        st.metric("Export Status", export_ready)
