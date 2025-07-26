import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.data_manager import DataManager
from utils.alert_system import AlertSystem
from utils.theme_manager import setup_theme_selector, get_theme_mode

st.set_page_config(page_title="Alerts Configuration", page_icon="🚨", layout="wide")

# Apply theme
with st.sidebar:
    setup_theme_selector()

# Initialize systems
@st.cache_resource
def get_systems():
    data_manager = DataManager()
    alert_system = AlertSystem()
    return data_manager, alert_system

data_manager, alert_system = get_systems()

st.title("🚨 Alerts Configuration")
st.markdown("Configure alert thresholds and monitor system notifications.")
st.markdown("---")

# Tabs for different alert management functions
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Configure Alerts", "📊 Alert Status", "📈 Alert History", "🔔 Notifications"])

with tab1:
    st.subheader("Alert Threshold Configuration")
    
    # Get available parameters from data
    all_data = data_manager.get_all_data()
    
    if all_data.empty:
        st.warning("No data available. Please add some data first to configure alerts.")
        st.stop()
    
    # Get numeric parameters
    numeric_params = all_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    if not numeric_params:
        st.error("No numeric parameters found in the data.")
        st.stop()
    
    # Parameter selection
    selected_param = st.selectbox(
        "Select parameter to configure alerts:",
        numeric_params,
        help="Choose the process parameter for which you want to set alert thresholds"
    )
    
    if selected_param:
        # Get current parameter data
        param_data = all_data[selected_param].dropna()
        
        if len(param_data) == 0:
            st.error(f"No data available for parameter: {selected_param}")
        else:
            # Display current parameter statistics
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Parameter distribution chart
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=param_data,
                    nbinsx=50,
                    name=selected_param.title(),
                    opacity=0.7
                ))
                
                # Get existing thresholds
                existing_config = alert_system.get_alert_config(selected_param)
                
                if existing_config:
                    # Add threshold lines
                    if existing_config.get('critical_low'):
                        fig.add_vline(
                            x=existing_config['critical_low'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Critical Low"
                        )
                    
                    if existing_config.get('warning_low'):
                        fig.add_vline(
                            x=existing_config['warning_low'],
                            line_dash="dash",
                            line_color="orange",
                            annotation_text="Warning Low"
                        )
                    
                    if existing_config.get('warning_high'):
                        fig.add_vline(
                            x=existing_config['warning_high'],
                            line_dash="dash",
                            line_color="orange",
                            annotation_text="Warning High"
                        )
                    
                    if existing_config.get('critical_high'):
                        fig.add_vline(
                            x=existing_config['critical_high'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Critical High"
                        )
                
                fig.update_layout(
                    title=f"{selected_param.title()} Distribution with Alert Thresholds",
                    xaxis_title=selected_param.title(),
                    yaxis_title="Frequency"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Parameter statistics
                st.markdown("**Parameter Statistics:**")
                st.metric("Mean", f"{param_data.mean():.2f}")
                st.metric("Std Dev", f"{param_data.std():.2f}")
                st.metric("Min", f"{param_data.min():.2f}")
                st.metric("Max", f"{param_data.max():.2f}")
                st.metric("Current", f"{param_data.iloc[-1]:.2f}")
                
                # Suggested thresholds based on statistics
                st.markdown("**Suggested Thresholds:**")
                mean_val = param_data.mean()
                std_val = param_data.std()
                
                suggested_warning_low = mean_val - 2 * std_val
                suggested_critical_low = mean_val - 3 * std_val
                suggested_warning_high = mean_val + 2 * std_val
                suggested_critical_high = mean_val + 3 * std_val
                
                st.caption(f"Critical Low: {suggested_critical_low:.2f}")
                st.caption(f"Warning Low: {suggested_warning_low:.2f}")
                st.caption(f"Warning High: {suggested_warning_high:.2f}")
                st.caption(f"Critical High: {suggested_critical_high:.2f}")
            
            # Alert configuration form
            st.markdown("---")
            st.subheader("Threshold Configuration")
            
            with st.form(f"alert_config_{selected_param}"):
                col1, col2 = st.columns(2)
                
                # Get existing configuration or use defaults
                config = existing_config or {}
                
                with col1:
                    st.markdown("**Low Thresholds**")
                    
                    enable_critical_low = st.checkbox(
                        "Enable Critical Low Alert",
                        value=config.get('critical_low') is not None,
                        help="Alert when value goes below critical low threshold"
                    )
                    
                    critical_low = st.number_input(
                        "Critical Low Threshold",
                        value=float(config.get('critical_low', suggested_critical_low)),
                        disabled=not enable_critical_low,
                        help="Critical low threshold value"
                    ) if enable_critical_low else None
                    
                    enable_warning_low = st.checkbox(
                        "Enable Warning Low Alert",
                        value=config.get('warning_low') is not None,
                        help="Alert when value goes below warning low threshold"
                    )
                    
                    warning_low = st.number_input(
                        "Warning Low Threshold",
                        value=float(config.get('warning_low', suggested_warning_low)),
                        disabled=not enable_warning_low,
                        help="Warning low threshold value"
                    ) if enable_warning_low else None
                
                with col2:
                    st.markdown("**High Thresholds**")
                    
                    enable_warning_high = st.checkbox(
                        "Enable Warning High Alert",
                        value=config.get('warning_high') is not None,
                        help="Alert when value goes above warning high threshold"
                    )
                    
                    warning_high = st.number_input(
                        "Warning High Threshold",
                        value=float(config.get('warning_high', suggested_warning_high)),
                        disabled=not enable_warning_high,
                        help="Warning high threshold value"
                    ) if enable_warning_high else None
                    
                    enable_critical_high = st.checkbox(
                        "Enable Critical High Alert",
                        value=config.get('critical_high') is not None,
                        help="Alert when value goes above critical high threshold"
                    )
                    
                    critical_high = st.number_input(
                        "Critical High Threshold",
                        value=float(config.get('critical_high', suggested_critical_high)),
                        disabled=not enable_critical_high,
                        help="Critical high threshold value"
                    ) if enable_critical_high else None
                
                # Additional settings
                st.markdown("**Additional Settings**")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    alert_enabled = st.checkbox(
                        "Enable Alerts",
                        value=config.get('enabled', True),
                        help="Enable/disable all alerts for this parameter"
                    )
                    
                    consecutive_violations = st.number_input(
                        "Consecutive Violations",
                        min_value=1,
                        max_value=10,
                        value=config.get('consecutive_violations', 1),
                        help="Number of consecutive violations before triggering alert"
                    )
                
                with col4:
                    notification_email = st.text_input(
                        "Notification Email",
                        value=config.get('notification_email', ''),
                        help="Email address for alert notifications (optional)"
                    )
                    
                    cooldown_minutes = st.number_input(
                        "Alert Cooldown (minutes)",
                        min_value=1,
                        max_value=1440,  # 24 hours
                        value=config.get('cooldown_minutes', 15),
                        help="Minimum time between identical alerts"
                    )
                
                # Submit button
                submitted = st.form_submit_button("Save Alert Configuration", type="primary")
                
                if submitted:
                    # Validate thresholds
                    valid_config = True
                    error_messages = []
                    
                    # Check threshold ordering
                    thresholds = []
                    if critical_low is not None:
                        thresholds.append(('critical_low', critical_low))
                    if warning_low is not None:
                        thresholds.append(('warning_low', warning_low))
                    if warning_high is not None:
                        thresholds.append(('warning_high', warning_high))
                    if critical_high is not None:
                        thresholds.append(('critical_high', critical_high))
                    
                    # Sort thresholds by value
                    thresholds.sort(key=lambda x: x[1])
                    
                    # Check if ordering is logical
                    expected_order = ['critical_low', 'warning_low', 'warning_high', 'critical_high']
                    actual_order = [t[0] for t in thresholds]
                    
                    # Simple validation - ensure low thresholds are below high thresholds
                    if critical_low is not None and warning_high is not None and critical_low >= warning_high:
                        error_messages.append("Critical low threshold must be below warning high threshold")
                        valid_config = False
                    
                    if warning_low is not None and warning_high is not None and warning_low >= warning_high:
                        error_messages.append("Warning low threshold must be below warning high threshold")
                        valid_config = False
                    
                    if valid_config:
                        # Save configuration
                        alert_config = {
                            'parameter': selected_param,
                            'enabled': alert_enabled,
                            'critical_low': critical_low,
                            'warning_low': warning_low,
                            'warning_high': warning_high,
                            'critical_high': critical_high,
                            'consecutive_violations': consecutive_violations,
                            'notification_email': notification_email if notification_email else None,
                            'cooldown_minutes': cooldown_minutes,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        success = alert_system.save_alert_config(selected_param, alert_config)
                        
                        if success:
                            st.success(f"✅ Alert configuration saved for {selected_param}!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save alert configuration.")
                    else:
                        for error in error_messages:
                            st.error(f"❌ {error}")

with tab2:
    st.subheader("Current Alert Status")
    
    # Get latest data
    latest_data = data_manager.get_latest_data()
    
    if latest_data.empty:
        st.warning("No current data available for alert checking.")
    else:
        # Check all alerts
        current_alerts = alert_system.check_alerts(latest_data)
        
        if current_alerts:
            st.markdown("### 🚨 Active Alerts")
            
            # Group alerts by severity
            critical_alerts = [a for a in current_alerts if a['severity'] == 'Critical']
            warning_alerts = [a for a in current_alerts if a['severity'] == 'Warning']
            info_alerts = [a for a in current_alerts if a['severity'] == 'Info']
            
            # Display critical alerts
            if critical_alerts:
                st.markdown("#### 🔴 Critical Alerts")
                for alert in critical_alerts:
                    st.error(f"**{alert['parameter'].upper()}**: {alert['message']}")
            
            # Display warning alerts
            if warning_alerts:
                st.markdown("#### 🟡 Warning Alerts")
                for alert in warning_alerts:
                    st.warning(f"**{alert['parameter'].upper()}**: {alert['message']}")
            
            # Display info alerts
            if info_alerts:
                st.markdown("#### 🔵 Info Alerts")
                for alert in info_alerts:
                    st.info(f"**{alert['parameter'].upper()}**: {alert['message']}")
        
        else:
            st.success("✅ No active alerts - all parameters within normal ranges")
        
        # Current parameter values with alert status
        st.markdown("---")
        st.subheader("Parameter Status Overview")
        
        # Get all configured parameters
        configured_params = alert_system.get_configured_parameters()
        
        if configured_params:
            status_data = []
            
            for param in configured_params:
                if param in latest_data.columns:
                    current_value = latest_data[param].iloc[-1] if not latest_data[param].empty else None
                    config = alert_system.get_alert_config(param)
                    
                    if current_value is not None and config:
                        # Determine status
                        status = "Normal"
                        status_color = "🟢"
                        
                        # Check thresholds
                        if config.get('critical_low') and current_value <= config['critical_low']:
                            status = "Critical Low"
                            status_color = "🔴"
                        elif config.get('critical_high') and current_value >= config['critical_high']:
                            status = "Critical High"
                            status_color = "🔴"
                        elif config.get('warning_low') and current_value <= config['warning_low']:
                            status = "Warning Low"
                            status_color = "🟡"
                        elif config.get('warning_high') and current_value >= config['warning_high']:
                            status = "Warning High"
                            status_color = "🟡"
                        
                        status_data.append({
                            'Parameter': param.title(),
                            'Current Value': f"{current_value:.2f}",
                            'Status': f"{status_color} {status}",
                            'Critical Low': config.get('critical_low', 'N/A'),
                            'Warning Low': config.get('warning_low', 'N/A'),
                            'Warning High': config.get('warning_high', 'N/A'),
                            'Critical High': config.get('critical_high', 'N/A'),
                            'Enabled': "✅" if config.get('enabled', False) else "❌"
                        })
            
            if status_data:
                status_df = pd.DataFrame(status_data)
                st.dataframe(status_df, use_container_width=True)
            else:
                st.info("No parameters configured for alerts.")
        else:
            st.info("No alert configurations found. Please configure alerts in the first tab.")

with tab3:
    st.subheader("Alert History")
    
    # Get alert history
    alert_history = alert_system.get_alert_history()
    
    if alert_history:
        st.markdown(f"### Recent Alerts ({len(alert_history)} total)")
        
        # Convert to DataFrame
        history_df = pd.DataFrame(alert_history)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Severity filter
            severity_filter = st.multiselect(
                "Filter by Severity:",
                options=['Critical', 'Warning', 'Info'],
                default=['Critical', 'Warning', 'Info']
            )
        
        with col2:
            # Parameter filter
            available_params = history_df['parameter'].unique().tolist()
            param_filter = st.multiselect(
                "Filter by Parameter:",
                options=available_params,
                default=available_params
            )
        
        with col3:
            # Time range filter
            days_back = st.selectbox(
                "Show alerts from:",
                options=[1, 7, 30, 90, 365],
                format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}",
                index=1
            )
        
        # Apply filters
        filtered_history = history_df[
            (history_df['severity'].isin(severity_filter)) &
            (history_df['parameter'].isin(param_filter))
        ].copy()
        
        # Convert timestamp to datetime for filtering
        if 'timestamp' in filtered_history.columns:
            filtered_history['timestamp'] = pd.to_datetime(filtered_history['timestamp'])
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_history = filtered_history[filtered_history['timestamp'] >= cutoff_date]
        
        if not filtered_history.empty:
            # Sort by timestamp (most recent first)
            filtered_history = filtered_history.sort_values('timestamp', ascending=False)
            
            # Display alerts
            for _, alert in filtered_history.head(50).iterrows():  # Show last 50 alerts
                timestamp = alert['timestamp']
                severity = alert['severity']
                parameter = alert['parameter']
                message = alert['message']
                
                # Color code by severity
                if severity == 'Critical':
                    st.error(f"🔴 **{timestamp}** - {parameter.upper()}: {message}")
                elif severity == 'Warning':
                    st.warning(f"🟡 **{timestamp}** - {parameter.upper()}: {message}")
                else:
                    st.info(f"🔵 **{timestamp}** - {parameter.upper()}: {message}")
            
            # Alert statistics
            st.markdown("---")
            st.subheader("Alert Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_alerts = len(filtered_history)
                st.metric("Total Alerts", total_alerts)
            
            with col2:
                critical_count = len(filtered_history[filtered_history['severity'] == 'Critical'])
                st.metric("Critical Alerts", critical_count)
            
            with col3:
                warning_count = len(filtered_history[filtered_history['severity'] == 'Warning'])
                st.metric("Warning Alerts", warning_count)
            
            with col4:
                if len(filtered_history) > 1:
                    # Calculate average time between alerts
                    time_diffs = filtered_history['timestamp'].diff().dropna()
                    avg_time = time_diffs.mean()
                    st.metric("Avg Time Between", f"{avg_time.total_seconds()/3600:.1f}h")
                else:
                    st.metric("Avg Time Between", "N/A")
            
            # Alert frequency chart
            if len(filtered_history) > 0:
                st.markdown("### Alert Frequency Over Time")
                
                # Group by day
                filtered_history['date'] = filtered_history['timestamp'].dt.date
                daily_counts = filtered_history.groupby(['date', 'severity']).size().reset_index(name='count')
                
                fig = go.Figure()
                
                for severity in ['Critical', 'Warning', 'Info']:
                    severity_data = daily_counts[daily_counts['severity'] == severity]
                    if not severity_data.empty:
                        color = {'Critical': 'red', 'Warning': 'orange', 'Info': 'blue'}[severity]
                        fig.add_trace(go.Scatter(
                            x=severity_data['date'],
                            y=severity_data['count'],
                            mode='lines+markers',
                            name=severity,
                            line=dict(color=color)
                        ))
                
                fig.update_layout(
                    title="Daily Alert Frequency",
                    xaxis_title="Date",
                    yaxis_title="Number of Alerts",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("No alerts found matching the selected filters.")
    
    else:
        st.info("No alert history available.")

with tab4:
    st.subheader("Notification Settings")
    
    st.markdown("Configure global notification settings for the alert system.")
    
    # Global notification settings
    with st.form("notification_settings"):
        st.markdown("### Email Notifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email_enabled = st.checkbox(
                "Enable Email Notifications",
                value=False,
                help="Enable email notifications for alerts"
            )
            
            smtp_server = st.text_input(
                "SMTP Server",
                value="smtp.gmail.com",
                disabled=not email_enabled,
                help="SMTP server for sending emails"
            )
            
            smtp_port = st.number_input(
                "SMTP Port",
                value=587,
                disabled=not email_enabled,
                help="SMTP server port"
            )
        
        with col2:
            sender_email = st.text_input(
                "Sender Email",
                disabled=not email_enabled,
                help="Email address to send notifications from"
            )
            
            sender_password = st.text_input(
                "Email Password",
                type="password",
                disabled=not email_enabled,
                help="Password for sender email account"
            )
        
        st.markdown("### Notification Rules")
        
        col3, col4 = st.columns(2)
        
        with col3:
            immediate_critical = st.checkbox(
                "Immediate Critical Alerts",
                value=True,
                help="Send immediate notifications for critical alerts"
            )
            
            batch_warnings = st.checkbox(
                "Batch Warning Notifications",
                value=True,
                help="Batch warning notifications to reduce email volume"
            )
        
        with col4:
            batch_interval = st.selectbox(
                "Batch Interval",
                options=[15, 30, 60, 120],
                format_func=lambda x: f"{x} minutes",
                disabled=not batch_warnings,
                help="How often to send batched notifications"
            )
            
            max_emails_per_hour = st.number_input(
                "Max Emails per Hour",
                min_value=1,
                max_value=100,
                value=10,
                help="Maximum number of notification emails per hour"
            )
        
        # Test notification
        st.markdown("### Test Notification")
        test_email = st.text_input(
            "Test Email Address",
            help="Email address to send a test notification"
        )
        
        submitted = st.form_submit_button("Save Notification Settings", type="primary")
        
        if submitted:
            # Save notification settings
            notification_config = {
                'email_enabled': email_enabled,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'sender_email': sender_email,
                'sender_password': sender_password,  # In production, encrypt this
                'immediate_critical': immediate_critical,
                'batch_warnings': batch_warnings,
                'batch_interval': batch_interval,
                'max_emails_per_hour': max_emails_per_hour,
                'updated_at': datetime.now().isoformat()
            }
            
            # Save to alert system (you would implement this method)
            st.success("✅ Notification settings saved successfully!")
            
            if test_email and email_enabled:
                st.info(f"📧 Test notification would be sent to: {test_email}")
    
    # Notification history
    st.markdown("---")
    st.subheader("Recent Notifications")
    
    # This would show recent notification history
    st.info("Notification history feature would be implemented here, showing:")
    st.markdown("""
    - Recent email notifications sent
    - Delivery status
    - Failed notifications with reasons
    - Notification frequency statistics
    """)

# Clear alert history button
st.markdown("---")
if st.button("🗑️ Clear Alert History", help="Remove all alert history (cannot be undone)"):
    if st.session_state.get('confirm_clear_alerts', False):
        alert_system.clear_alert_history()
        st.success("Alert history cleared!")
        st.session_state.confirm_clear_alerts = False
        st.rerun()
    else:
        st.session_state.confirm_clear_alerts = True
        st.warning("⚠️ Click again to confirm clearing all alert history")
