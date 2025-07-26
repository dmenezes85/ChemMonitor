import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import io
from utils.data_manager import DataManager
from utils.theme_manager import setup_theme_selector, get_theme_mode

st.set_page_config(page_title="Data Input", page_icon="📝", layout="wide")

# Apply theme
with st.sidebar:
    setup_theme_selector()

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return DataManager()

data_manager = get_data_manager()

st.title("📝 Data Input")
st.markdown("Add new process data through file upload or manual entry.")
st.markdown("---")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["📁 File Upload", "✏️ Manual Entry", "🎲 Simulate Data"])

with tab1:
    st.subheader("Upload CSV Data")
    st.markdown("Upload a CSV file containing chemical process data.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="CSV should contain columns: timestamp, temperature, pressure, ph, flow_rate, concentration"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file
            df = pd.read_csv(uploaded_file)
            
            st.subheader("Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            # Data validation
            st.subheader("Data Validation")
            
            # Check required columns
            required_columns = ['timestamp']
            optional_columns = ['temperature', 'pressure', 'ph', 'flow_rate', 'concentration']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            available_optional = [col for col in optional_columns if col in df.columns]
            
            if missing_required:
                st.error(f"Missing required columns: {missing_required}")
            else:
                st.success("✅ All required columns present")
            
            if available_optional:
                st.info(f"Available process parameters: {available_optional}")
            
            # Data type conversion
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    st.success("✅ Timestamp column successfully parsed")
                except:
                    st.error("❌ Could not parse timestamp column. Please ensure it's in a recognizable datetime format.")
            
            # Data quality checks
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Data Quality Summary:**")
                st.write(f"- Total rows: {len(df)}")
                st.write(f"- Missing values: {df.isnull().sum().sum()}")
                st.write(f"- Duplicate rows: {df.duplicated().sum()}")
            
            with col2:
                if len(df) > 0:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        st.write("**Numeric Data Ranges:**")
                        for col in numeric_cols:
                            min_val = df[col].min()
                            max_val = df[col].max()
                            st.write(f"- {col}: {min_val:.2f} to {max_val:.2f}")
            
            # Import button
            if st.button("Import Data", type="primary"):
                if not missing_required:
                    try:
                        # Save the data
                        success = data_manager.add_data(df)
                        if success:
                            st.success(f"✅ Successfully imported {len(df)} records!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to import data. Please check the data format.")
                    except Exception as e:
                        st.error(f"❌ Import failed: {str(e)}")
                else:
                    st.error("Cannot import data due to missing required columns.")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

with tab2:
    st.subheader("Manual Data Entry")
    st.markdown("Enter process data manually for real-time monitoring.")
    
    # Create input form
    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            timestamp = st.date_input(
                "Date",
                value=datetime.now().date(),
                help="Date of the measurement"
            )
            
            time_input = st.time_input(
                "Time",
                value=datetime.now().time(),
                help="Specific time of measurement"
            )
            
            temperature = st.number_input(
                "Temperature (°C)",
                min_value=-273.15,
                max_value=1000.0,
                value=25.0,
                step=0.1,
                help="Process temperature in Celsius"
            )
            
            pressure = st.number_input(
                "Pressure (bar)",
                min_value=0.0,
                max_value=100.0,
                value=1.0,
                step=0.01,
                help="Process pressure in bar"
            )
        
        with col2:
            ph = st.number_input(
                "pH Level",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1,
                help="pH level of the process"
            )
            
            flow_rate = st.number_input(
                "Flow Rate (L/min)",
                min_value=0.0,
                max_value=1000.0,
                value=10.0,
                step=0.1,
                help="Flow rate in liters per minute"
            )
            
            concentration = st.number_input(
                "Concentration (mg/L)",
                min_value=0.0,
                max_value=10000.0,
                value=100.0,
                step=1.0,
                help="Concentration in mg/L"
            )
        
        # Combine date and time
        full_timestamp = datetime.combine(timestamp, time_input)
        
        # Submit button
        submitted = st.form_submit_button("Add Data Point", type="primary")
        
        if submitted:
            # Create data record
            new_data = {
                'timestamp': [full_timestamp],
                'temperature': [temperature],
                'pressure': [pressure],
                'ph': [ph],
                'flow_rate': [flow_rate],
                'concentration': [concentration]
            }
            
            df_new = pd.DataFrame(new_data)
            
            # Add to data manager
            success = data_manager.add_data(df_new)
            
            if success:
                st.success("✅ Data point added successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to add data point.")

with tab3:
    st.subheader("Data Simulation")
    st.markdown("Generate simulated process data for testing and demonstration.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sim_duration = st.number_input(
            "Simulation Duration (hours)",
            min_value=1,
            max_value=168,  # 1 week
            value=24,
            help="Duration of simulated data"
        )
        
        sim_interval = st.selectbox(
            "Data Interval",
            ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"],
            index=2,
            help="Time interval between data points"
        )
        
    with col2:
        # Process parameters for simulation
        temp_base = st.number_input("Base Temperature (°C)", value=75.0, step=1.0)
        pressure_base = st.number_input("Base Pressure (bar)", value=2.5, step=0.1)
        ph_base = st.number_input("Base pH", value=7.2, step=0.1)
        flow_base = st.number_input("Base Flow Rate (L/min)", value=25.0, step=1.0)
    
    # Add noise and variation settings
    with st.expander("Advanced Simulation Settings"):
        noise_level = st.slider("Noise Level", 0.0, 1.0, 0.1, help="Amount of random variation")
        add_trends = st.checkbox("Add Trends", value=True, help="Include gradual changes over time")
        add_anomalies = st.checkbox("Add Anomalies", value=False, help="Include rare extreme values")
    
    if st.button("Generate Simulated Data", type="primary"):
        # Convert interval to minutes
        interval_map = {
            "1 minute": 1, "5 minutes": 5, "15 minutes": 15,
            "30 minutes": 30, "1 hour": 60
        }
        interval_minutes = interval_map[sim_interval]
        
        # Generate timestamps
        start_time = datetime.now() - timedelta(hours=sim_duration)
        end_time = datetime.now()
        timestamps = pd.date_range(start_time, end_time, freq=f'{interval_minutes}min')
        
        n_points = len(timestamps)
        
        # Generate simulated data
        np.random.seed(42)  # For reproducible results
        
        # Base patterns
        time_factor = np.linspace(0, 2*np.pi, n_points)
        
        # Temperature with daily cycle
        temperature = temp_base + 5 * np.sin(time_factor) + noise_level * np.random.normal(0, 2, n_points)
        
        # Pressure with slight correlation to temperature
        pressure = pressure_base + 0.1 * (temperature - temp_base) + noise_level * np.random.normal(0, 0.1, n_points)
        
        # pH with some random walk
        ph_changes = noise_level * np.random.normal(0, 0.1, n_points)
        ph = ph_base + np.cumsum(ph_changes * 0.01)
        ph = np.clip(ph, 6.0, 8.0)  # Keep within reasonable range
        
        # Flow rate with some correlation to pressure
        flow_rate = flow_base + 2 * (pressure - pressure_base) + noise_level * np.random.normal(0, 1, n_points)
        flow_rate = np.maximum(flow_rate, 0)  # Ensure non-negative
        
        # Concentration
        concentration = 100 + 20 * np.sin(time_factor + np.pi/4) + noise_level * np.random.normal(0, 5, n_points)
        concentration = np.maximum(concentration, 0)  # Ensure non-negative
        
        # Add trends if requested
        if add_trends:
            trend_factor = np.linspace(0, 1, n_points)
            temperature += trend_factor * 2  # Gradual temperature increase
            ph -= trend_factor * 0.2  # Gradual pH decrease
        
        # Add anomalies if requested
        if add_anomalies:
            anomaly_indices = np.random.choice(n_points, size=max(1, n_points//100), replace=False)
            temperature[anomaly_indices] += np.random.normal(0, 10, len(anomaly_indices))
            pressure[anomaly_indices] += np.random.normal(0, 1, len(anomaly_indices))
        
        # Create DataFrame
        sim_data = pd.DataFrame({
            'timestamp': timestamps,
            'temperature': temperature,
            'pressure': pressure,
            'ph': ph,
            'flow_rate': flow_rate,
            'concentration': concentration
        })
        
        # Add to data manager
        success = data_manager.add_data(sim_data)
        
        if success:
            st.success(f"✅ Generated {len(sim_data)} simulated data points!")
            
            # Show preview
            st.subheader("Generated Data Preview")
            st.dataframe(sim_data.head(10), use_container_width=True)
            
            # Show basic statistics
            st.subheader("Data Statistics")
            st.dataframe(sim_data.describe(), use_container_width=True)
            
            st.rerun()
        else:
            st.error("❌ Failed to generate simulated data.")

# Current data status
st.markdown("---")
st.subheader("📊 Current Data Status")

# Get current data statistics
all_data = data_manager.get_all_data()

if not all_data.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(all_data))
    
    with col2:
        if 'timestamp' in all_data.columns:
            time_span = all_data['timestamp'].max() - all_data['timestamp'].min()
            st.metric("Time Span", f"{time_span.days} days")
    
    with col3:
        numeric_cols = all_data.select_dtypes(include=[np.number]).columns
        st.metric("Parameters", len(numeric_cols))
    
    with col4:
        missing_percentage = (all_data.isnull().sum().sum() / (len(all_data) * len(all_data.columns))) * 100
        st.metric("Data Completeness", f"{100-missing_percentage:.1f}%")
    
    # Recent data preview
    st.subheader("Recent Data (Last 10 records)")
    recent_data = all_data.tail(10).sort_values('timestamp', ascending=False)
    st.dataframe(recent_data, use_container_width=True)

else:
    st.info("No data available. Add some data using the methods above.")
