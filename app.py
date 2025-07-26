import streamlit as st
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

# Page configuration
st.set_page_config(
    page_title="Chemical Process Monitor",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize data manager and alert system
@st.cache_resource
def initialize_systems():
    data_manager = DataManager()
    alert_system = AlertSystem()
    chart_generator = ChartGenerator()
    stats_calculator = StatisticsCalculator()
    return data_manager, alert_system, chart_generator, stats_calculator

data_manager, alert_system, chart_generator, stats_calculator = initialize_systems()

# Main dashboard
def main_dashboard():
    st.title("🧪 Chemical Process Monitoring Dashboard")
    st.markdown("---")
    
    # Load current data
    current_data = data_manager.get_latest_data()
    
    if current_data.empty:
        st.warning("No data available. Please add some data using the Data Input page.")
        st.info("👈 Use the sidebar to navigate to different sections of the dashboard.")
        return
    
    # Real-time metrics overview
    st.subheader("📊 Current Process Status")
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'temperature' in current_data.columns:
            temp_val = current_data['temperature'].iloc[-1] if not current_data['temperature'].empty else 0
            st.metric("Temperature (°C)", f"{temp_val:.1f}")
        
    with col2:
        if 'pressure' in current_data.columns:
            pressure_val = current_data['pressure'].iloc[-1] if not current_data['pressure'].empty else 0
            st.metric("Pressure (bar)", f"{pressure_val:.2f}")
    
    with col3:
        if 'ph' in current_data.columns:
            ph_val = current_data['ph'].iloc[-1] if not current_data['ph'].empty else 7.0
            st.metric("pH Level", f"{ph_val:.2f}")
    
    with col4:
        if 'flow_rate' in current_data.columns:
            flow_val = current_data['flow_rate'].iloc[-1] if not current_data['flow_rate'].empty else 0
            st.metric("Flow Rate (L/min)", f"{flow_val:.1f}")
    
    st.markdown("---")
    
    # Alert status
    st.subheader("🚨 Alert Status")
    alerts = alert_system.check_alerts(current_data)
    
    if alerts:
        for alert in alerts:
            if alert['severity'] == 'Critical':
                st.error(f"🔴 **CRITICAL**: {alert['message']}")
            elif alert['severity'] == 'Warning':
                st.warning(f"🟡 **WARNING**: {alert['message']}")
            else:
                st.info(f"🔵 **INFO**: {alert['message']}")
    else:
        st.success("✅ All parameters within normal ranges")
    
    st.markdown("---")
    
    # Real-time charts
    st.subheader("📈 Real-time Trends")
    
    # Time range selector
    time_range = st.selectbox(
        "Select time range:",
        ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"],
        index=1
    )
    
    # Filter data based on time range
    hours_map = {"Last 1 hour": 1, "Last 6 hours": 6, "Last 24 hours": 24, "Last 7 days": 168}
    hours = hours_map[time_range]
    
    filtered_data = data_manager.get_data_by_time_range(hours)
    
    if not filtered_data.empty:
        # Create multiple chart tabs
        tab1, tab2, tab3 = st.tabs(["📊 Line Charts", "🎯 Gauges", "📈 Distribution"])
        
        with tab1:
            # Temperature and Pressure charts
            col1, col2 = st.columns(2)
            
            with col1:
                if 'temperature' in filtered_data.columns:
                    fig_temp = chart_generator.create_line_chart(
                        filtered_data, 'timestamp', 'temperature', 
                        "Temperature Over Time", "Temperature (°C)"
                    )
                    st.plotly_chart(fig_temp, use_container_width=True, key="temp_line_chart")
            
            with col2:
                if 'pressure' in filtered_data.columns:
                    fig_pressure = chart_generator.create_line_chart(
                        filtered_data, 'timestamp', 'pressure', 
                        "Pressure Over Time", "Pressure (bar)"
                    )
                    st.plotly_chart(fig_pressure, use_container_width=True, key="pressure_line_chart")
            
            # pH and Flow Rate charts
            col3, col4 = st.columns(2)
            
            with col3:
                if 'ph' in filtered_data.columns:
                    fig_ph = chart_generator.create_line_chart(
                        filtered_data, 'timestamp', 'ph', 
                        "pH Level Over Time", "pH"
                    )
                    st.plotly_chart(fig_ph, use_container_width=True, key="ph_line_chart")
            
            with col4:
                if 'flow_rate' in filtered_data.columns:
                    fig_flow = chart_generator.create_line_chart(
                        filtered_data, 'timestamp', 'flow_rate', 
                        "Flow Rate Over Time", "Flow Rate (L/min)"
                    )
                    st.plotly_chart(fig_flow, use_container_width=True, key="flow_line_chart")
        
        with tab2:
            # Gauge charts for current values
            col1, col2 = st.columns(2)
            
            with col1:
                if 'temperature' in current_data.columns:
                    temp_val = current_data['temperature'].iloc[-1]
                    fig_temp_gauge = chart_generator.create_gauge_chart(
                        temp_val, "Temperature", "°C", 0, 200
                    )
                    st.plotly_chart(fig_temp_gauge, use_container_width=True, key="temp_gauge_chart")
                
                if 'ph' in current_data.columns:
                    ph_val = current_data['ph'].iloc[-1]
                    fig_ph_gauge = chart_generator.create_gauge_chart(
                        ph_val, "pH Level", "", 0, 14
                    )
                    st.plotly_chart(fig_ph_gauge, use_container_width=True, key="ph_gauge_chart")
            
            with col2:
                if 'pressure' in current_data.columns:
                    pressure_val = current_data['pressure'].iloc[-1]
                    fig_pressure_gauge = chart_generator.create_gauge_chart(
                        pressure_val, "Pressure", "bar", 0, 10
                    )
                    st.plotly_chart(fig_pressure_gauge, use_container_width=True, key="pressure_gauge_chart")
                
                if 'flow_rate' in current_data.columns:
                    flow_val = current_data['flow_rate'].iloc[-1]
                    fig_flow_gauge = chart_generator.create_gauge_chart(
                        flow_val, "Flow Rate", "L/min", 0, 100
                    )
                    st.plotly_chart(fig_flow_gauge, use_container_width=True, key="flow_gauge_chart")
        
        with tab3:
            # Distribution histograms
            numeric_columns = filtered_data.select_dtypes(include=[np.number]).columns
            selected_params = st.multiselect(
                "Select parameters for distribution analysis:",
                numeric_columns.tolist(),
                default=numeric_columns.tolist()[:2] if len(numeric_columns) >= 2 else numeric_columns.tolist()
            )
            
            if selected_params:
                for i, param in enumerate(selected_params):
                    fig_hist = chart_generator.create_histogram(
                        filtered_data[param], f"{param.title()} Distribution"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_chart_{i}")
    
    else:
        st.info("No data available for the selected time range.")
    
    # Statistics summary
    st.markdown("---")
    st.subheader("📊 Statistical Summary")
    
    if not current_data.empty:
        stats_summary = stats_calculator.calculate_basic_stats(filtered_data)
        if not stats_summary.empty:
            st.dataframe(stats_summary, use_container_width=True)
    
    # Auto-refresh option
    st.markdown("---")
    auto_refresh = st.checkbox("Enable auto-refresh (30 seconds)")
    
    if auto_refresh:
        st.rerun()

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    st.markdown("---")
    
    # System status
    st.subheader("System Status")
    data_count = len(data_manager.get_all_data())
    st.metric("Total Data Points", data_count)
    
    alert_count = len(alert_system.check_alerts(data_manager.get_latest_data()))
    if alert_count > 0:
        st.metric("Active Alerts", alert_count, delta=alert_count, delta_color="inverse")
    else:
        st.metric("Active Alerts", 0)
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    if st.button("🧹 Clear All Data"):
        if st.session_state.get('confirm_clear', False):
            data_manager.clear_all_data()
            st.success("All data cleared!")
            st.session_state.confirm_clear = False
            st.rerun()
        else:
            st.session_state.confirm_clear = True
            st.warning("Click again to confirm data clearing")

# Main content
if __name__ == "__main__":
    main_dashboard()
