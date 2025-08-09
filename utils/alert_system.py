import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class AlertSystem:
    """Manages alert configurations, threshold monitoring, and alert history."""
    
    def __init__(self, config_file: str = "data/alert_config.json", history_file: str = "data/alert_history.json"):
        """Initialize the alert system with configuration and history files."""
        self.config_file = config_file
        self.history_file = history_file
        self.data_dir = "data"
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize configuration file if it doesn't exist
        if not os.path.exists(config_file):
            self._initialize_config_file()
        
        # Initialize history file if it doesn't exist
        if not os.path.exists(history_file):
            self._initialize_history_file()
        
        # Cache for alert cooldowns
        self._alert_cooldowns = {}
    
    def _initialize_config_file(self) -> None:
        """Initialize an empty alert configuration file."""
        empty_config = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            },
            'parameters': {}
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(empty_config, f, indent=2)
    
    def _initialize_history_file(self) -> None:
        """Initialize an empty alert history file."""
        empty_history = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_alerts': 0
            },
            'alerts': []
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(empty_history, f, indent=2)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_config_file()
            return self._load_config()
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save alert configuration to file."""
        try:
            config['metadata']['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving alert config: {e}")
            return False
    
    def _load_history(self) -> Dict[str, Any]:
        """Load alert history from file."""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_history_file()
            return self._load_history()
    
    def _save_history(self, history: Dict[str, Any]) -> bool:
        """Save alert history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving alert history: {e}")
            return False
    
    def get_alert_configs(self) -> Dict[str, Any]:
        """Get all alert configurations."""
        try:
            config = self._load_config()
            return config.get('parameters', {})
        except Exception as e:
            print(f"Error loading alert configs: {e}")
            return {}
    
    def set_alert_config(self, parameter: str, config_data: Dict[str, Any]) -> bool:
        """Set alert configuration for a parameter."""
        try:
            config = self._load_config()
            config['parameters'][parameter] = config_data
            return self._save_config(config)
        except Exception as e:
            print(f"Error setting alert config: {e}")
            return False

    def save_alert_config(self, parameter: str, config: Dict[str, Any]) -> bool:
        """
        Save alert configuration for a specific parameter.
        
        Args:
            parameter: Parameter name
            config: Alert configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            alert_config = self._load_config()
            alert_config['parameters'][parameter] = config
            return self._save_config(alert_config)
        except Exception as e:
            print(f"Error saving alert config for {parameter}: {e}")
            return False
    
    def get_alert_config(self, parameter: str) -> Optional[Dict[str, Any]]:
        """
        Get alert configuration for a specific parameter.
        
        Args:
            parameter: Parameter name
            
        Returns:
            Dict or None: Alert configuration if exists
        """
        try:
            config = self._load_config()
            return config['parameters'].get(parameter)
        except Exception as e:
            print(f"Error getting alert config for {parameter}: {e}")
            return None
    
    def get_configured_parameters(self) -> List[str]:
        """
        Get list of parameters with alert configurations.
        
        Returns:
            List[str]: List of configured parameter names
        """
        try:
            config = self._load_config()
            return list(config['parameters'].keys())
        except Exception as e:
            print(f"Error getting configured parameters: {e}")
            return []
    
    def check_alerts(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Check current data against alert thresholds.
        
        Args:
            data: Current process data
            
        Returns:
            List[Dict]: List of active alerts
        """
        alerts = []
        
        if data.empty:
            return alerts
        
        try:
            config = self._load_config()
            current_time = datetime.now()
            
            for parameter, param_config in config['parameters'].items():
                if not param_config.get('enabled', True):
                    continue
                
                if parameter not in data.columns:
                    continue
                
                # Get current value (latest value)
                current_value = data[parameter].iloc[-1] if not data[parameter].empty else None
                
                if current_value is None or pd.isna(current_value):
                    continue
                
                # Check cooldown
                cooldown_key = f"{parameter}"
                if cooldown_key in self._alert_cooldowns:
                    cooldown_end = self._alert_cooldowns[cooldown_key]
                    if current_time < cooldown_end:
                        continue
                
                # Check thresholds
                alert_triggered = False
                alert_severity = None
                alert_message = None
                
                # Critical thresholds
                if param_config.get('critical_low') is not None and current_value <= param_config['critical_low']:
                    alert_severity = 'Critical'
                    alert_message = f"{parameter} is critically low: {current_value:.2f} (threshold: {param_config['critical_low']:.2f})"
                    alert_triggered = True
                elif param_config.get('critical_high') is not None and current_value >= param_config['critical_high']:
                    alert_severity = 'Critical'
                    alert_message = f"{parameter} is critically high: {current_value:.2f} (threshold: {param_config['critical_high']:.2f})"
                    alert_triggered = True
                
                # Warning thresholds (only if no critical alert)
                elif param_config.get('warning_low') is not None and current_value <= param_config['warning_low']:
                    alert_severity = 'Warning'
                    alert_message = f"{parameter} is below warning threshold: {current_value:.2f} (threshold: {param_config['warning_low']:.2f})"
                    alert_triggered = True
                elif param_config.get('warning_high') is not None and current_value >= param_config['warning_high']:
                    alert_severity = 'Warning'
                    alert_message = f"{parameter} is above warning threshold: {current_value:.2f} (threshold: {param_config['warning_high']:.2f})"
                    alert_triggered = True
                
                if alert_triggered:
                    alert = {
                        'parameter': parameter,
                        'severity': alert_severity,
                        'message': alert_message,
                        'current_value': float(current_value),
                        'timestamp': current_time.isoformat(),
                        'config': param_config
                    }
                    
                    alerts.append(alert)
                    
                    # Log to history
                    self._log_alert_to_history(alert)
                    
                    # Set cooldown
                    cooldown_minutes = param_config.get('cooldown_minutes', 15)
                    self._alert_cooldowns[cooldown_key] = current_time + timedelta(minutes=cooldown_minutes)
            
            return alerts
            
        except Exception as e:
            print(f"Error checking alerts: {e}")
            return []
    
    def _log_alert_to_history(self, alert: Dict[str, Any]) -> None:
        """Log an alert to the history file."""
        try:
            history = self._load_history()
            
            # Add alert to history
            history['alerts'].append(alert)
            
            # Update metadata
            history['metadata']['total_alerts'] = len(history['alerts'])
            history['metadata']['last_alert'] = alert['timestamp']
            
            # Keep only last 1000 alerts to prevent file from growing too large
            if len(history['alerts']) > 1000:
                history['alerts'] = history['alerts'][-1000:]
                history['metadata']['total_alerts'] = 1000
            
            self._save_history(history)
            
        except Exception as e:
            print(f"Error logging alert to history: {e}")
    
    def get_alert_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get alert history for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[Dict]: Alert history
        """
        try:
            history = self._load_history()
            
            if not history['alerts']:
                return []
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            
            filtered_alerts = []
            for alert in history['alerts']:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if alert_time >= cutoff_date:
                    filtered_alerts.append(alert)
            
            return filtered_alerts
            
        except Exception as e:
            print(f"Error getting alert history: {e}")
            return []
    
    def clear_alert_history(self) -> bool:
        """Clear all alert history."""
        try:
            self._initialize_history_file()
            return True
        except Exception as e:
            print(f"Error clearing alert history: {e}")
            return False
    
    def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get alert statistics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict: Alert statistics
        """
        try:
            alerts = self.get_alert_history(days)
            
            if not alerts:
                return {
                    'total_alerts': 0,
                    'critical_alerts': 0,
                    'warning_alerts': 0,
                    'alerts_by_parameter': {},
                    'alerts_by_day': {},
                    'most_frequent_parameter': None,
                    'average_alerts_per_day': 0
                }
            
            # Count by severity
            critical_count = sum(1 for alert in alerts if alert['severity'] == 'Critical')
            warning_count = sum(1 for alert in alerts if alert['severity'] == 'Warning')
            
            # Count by parameter
            param_counts = {}
            for alert in alerts:
                param = alert['parameter']
                param_counts[param] = param_counts.get(param, 0) + 1
            
            # Count by day
            day_counts = {}
            for alert in alerts:
                alert_date = datetime.fromisoformat(alert['timestamp']).date()
                day_key = alert_date.isoformat()
                day_counts[day_key] = day_counts.get(day_key, 0) + 1
            
            # Most frequent parameter
            most_frequent_param = max(param_counts.items(), key=lambda x: x[1])[0] if param_counts else None
            
            # Average alerts per day
            avg_alerts_per_day = len(alerts) / days if days > 0 else 0
            
            return {
                'total_alerts': len(alerts),
                'critical_alerts': critical_count,
                'warning_alerts': warning_count,
                'alerts_by_parameter': param_counts,
                'alerts_by_day': day_counts,
                'most_frequent_parameter': most_frequent_param,
                'average_alerts_per_day': round(avg_alerts_per_day, 2)
            }
            
        except Exception as e:
            print(f"Error getting alert statistics: {e}")
            return {}
    
    def delete_parameter_config(self, parameter: str) -> bool:
        """
        Delete alert configuration for a specific parameter.
        
        Args:
            parameter: Parameter name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = self._load_config()
            
            if parameter in config['parameters']:
                del config['parameters'][parameter]
                return self._save_config(config)
            
            return True
            
        except Exception as e:
            print(f"Error deleting parameter config: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export current alert configuration.
        
        Returns:
            Dict: Complete alert configuration
        """
        try:
            return self._load_config()
        except Exception as e:
            print(f"Error exporting config: {e}")
            return {}
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """
        Import alert configuration.
        
        Args:
            config: Alert configuration to import
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate configuration structure
            if 'parameters' not in config:
                return False
            
            # Update metadata
            if 'metadata' not in config:
                config['metadata'] = {}
            
            config['metadata']['imported_at'] = datetime.now().isoformat()
            
            return self._save_config(config)
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def test_alert_conditions(self, parameter: str, test_value: float) -> Dict[str, Any]:
        """
        Test what alerts would be triggered for a given parameter value.
        
        Args:
            parameter: Parameter name
            test_value: Value to test
            
        Returns:
            Dict: Test results
        """
        try:
            config = self.get_alert_config(parameter)
            
            if not config:
                return {'error': 'No configuration found for parameter'}
            
            result = {
                'parameter': parameter,
                'test_value': test_value,
                'alerts_triggered': [],
                'status': 'Normal'
            }
            
            # Check thresholds
            if config.get('critical_low') is not None and test_value <= config['critical_low']:
                result['alerts_triggered'].append({
                    'severity': 'Critical',
                    'type': 'Low',
                    'threshold': config['critical_low'],
                    'message': f"Value {test_value} is below critical low threshold {config['critical_low']}"
                })
                result['status'] = 'Critical Low'
            
            elif config.get('critical_high') is not None and test_value >= config['critical_high']:
                result['alerts_triggered'].append({
                    'severity': 'Critical',
                    'type': 'High',
                    'threshold': config['critical_high'],
                    'message': f"Value {test_value} is above critical high threshold {config['critical_high']}"
                })
                result['status'] = 'Critical High'
            
            elif config.get('warning_low') is not None and test_value <= config['warning_low']:
                result['alerts_triggered'].append({
                    'severity': 'Warning',
                    'type': 'Low',
                    'threshold': config['warning_low'],
                    'message': f"Value {test_value} is below warning low threshold {config['warning_low']}"
                })
                result['status'] = 'Warning Low'
            
            elif config.get('warning_high') is not None and test_value >= config['warning_high']:
                result['alerts_triggered'].append({
                    'severity': 'Warning',
                    'type': 'High',
                    'threshold': config['warning_high'],
                    'message': f"Value {test_value} is above warning high threshold {config['warning_high']}"
                })
                result['status'] = 'Warning High'
            
            return result
            
        except Exception as e:
            print(f"Error testing alert conditions: {e}")
            return {'error': str(e)}
