import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class DataManager:
    """Manages chemical process data storage, retrieval, and basic operations."""
    
    def __init__(self, data_file: str = "data/process_data.json"):
        """Initialize the data manager with a data file path."""
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Create data directory if it doesn't exist
        if self.data_dir and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize empty data structure if file doesn't exist
        if not os.path.exists(data_file):
            self._initialize_data_file()
    
    def _initialize_data_file(self) -> None:
        """Initialize an empty data file."""
        empty_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_records': 0,
                'parameters': []
            },
            'data': []
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(empty_data, f, indent=2)
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from the JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_data_file()
            return self._load_data()
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to the JSON file."""
        try:
            data['metadata']['last_updated'] = datetime.now().isoformat()
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def add_data(self, new_data: pd.DataFrame) -> bool:
        """
        Add new data points to the storage.
        
        Args:
            new_data: DataFrame containing new process data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input data
            if new_data.empty:
                return False
            
            # Ensure timestamp column exists and is datetime
            if 'timestamp' not in new_data.columns:
                return False
            
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(new_data['timestamp']):
                new_data['timestamp'] = pd.to_datetime(new_data['timestamp'])
            
            # Load existing data
            storage_data = self._load_data()
            
            # Convert new data to records format
            new_records = new_data.to_dict('records')
            
            # Convert datetime objects to ISO strings for JSON storage
            for record in new_records:
                if 'timestamp' in record and hasattr(record['timestamp'], 'isoformat'):
                    record['timestamp'] = record['timestamp'].isoformat()
            
            # Add new records to existing data
            storage_data['data'].extend(new_records)
            
            # Update metadata
            storage_data['metadata']['total_records'] = len(storage_data['data'])
            
            # Update parameter list
            numeric_columns = new_data.select_dtypes(include=[np.number]).columns.tolist()
            existing_params = set(storage_data['metadata']['parameters'])
            new_params = set(numeric_columns)
            storage_data['metadata']['parameters'] = list(existing_params.union(new_params))
            
            # Save updated data
            return self._save_data(storage_data)
            
        except Exception as e:
            print(f"Error adding data: {e}")
            return False
    
    def get_all_data(self) -> pd.DataFrame:
        """
        Retrieve all stored data as a DataFrame.
        
        Returns:
            pd.DataFrame: All process data
        """
        try:
            storage_data = self._load_data()
            
            if not storage_data['data']:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(storage_data['data'])
            
            # Convert timestamp back to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            print(f"Error retrieving all data: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self, n: int = 1) -> pd.DataFrame:
        """
        Get the latest n data points.
        
        Args:
            n: Number of latest records to retrieve
            
        Returns:
            pd.DataFrame: Latest data points
        """
        try:
            all_data = self.get_all_data()
            
            if all_data.empty:
                return pd.DataFrame()
            
            return all_data.tail(n)
            
        except Exception as e:
            print(f"Error retrieving latest data: {e}")
            return pd.DataFrame()
    
    def get_data_by_time_range(self, hours: int) -> pd.DataFrame:
        """
        Get data from the last specified hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            pd.DataFrame: Data within the time range
        """
        try:
            all_data = self.get_all_data()
            
            if all_data.empty or 'timestamp' not in all_data.columns:
                return pd.DataFrame()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_data = all_data[all_data['timestamp'] >= cutoff_time]
            
            return filtered_data
            
        except Exception as e:
            print(f"Error retrieving data by time range: {e}")
            return pd.DataFrame()
    
    def get_data_by_date_range(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get data within a specific date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            pd.DataFrame: Data within the date range
        """
        try:
            all_data = self.get_all_data()
            
            if all_data.empty or 'timestamp' not in all_data.columns:
                return pd.DataFrame()
            
            mask = (all_data['timestamp'] >= start_date) & (all_data['timestamp'] <= end_date)
            filtered_data = all_data[mask]
            
            return filtered_data
            
        except Exception as e:
            print(f"Error retrieving data by date range: {e}")
            return pd.DataFrame()
    
    def get_parameter_data(self, parameter: str, hours: Optional[int] = None) -> pd.Series:
        """
        Get data for a specific parameter.
        
        Args:
            parameter: Name of the parameter
            hours: Optional number of hours to look back
            
        Returns:
            pd.Series: Parameter data
        """
        try:
            if hours:
                data = self.get_data_by_time_range(hours)
            else:
                data = self.get_all_data()
            
            if data.empty or parameter not in data.columns:
                return pd.Series()
            
            return data[parameter].dropna()
            
        except Exception as e:
            print(f"Error retrieving parameter data: {e}")
            return pd.Series()
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the stored data.
        
        Returns:
            Dict: Data summary including counts, date ranges, parameters
        """
        try:
            storage_data = self._load_data()
            all_data = self.get_all_data()
            
            summary = {
                'total_records': storage_data['metadata']['total_records'],
                'parameters': storage_data['metadata']['parameters'],
                'created_at': storage_data['metadata']['created_at'],
                'last_updated': storage_data['metadata']['last_updated'],
                'date_range': {},
                'data_quality': {}
            }
            
            if not all_data.empty and 'timestamp' in all_data.columns:
                summary['date_range'] = {
                    'start': all_data['timestamp'].min().isoformat(),
                    'end': all_data['timestamp'].max().isoformat(),
                    'span_days': (all_data['timestamp'].max() - all_data['timestamp'].min()).days
                }
                
                # Data quality metrics
                numeric_cols = all_data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    summary['data_quality'] = {
                        'missing_values': all_data[numeric_cols].isnull().sum().to_dict(),
                        'completeness_percentage': ((1 - all_data[numeric_cols].isnull().sum().sum() / 
                                                   (len(all_data) * len(numeric_cols))) * 100) if len(all_data) > 0 else 100
                    }
            
            return summary
            
        except Exception as e:
            print(f"Error getting data summary: {e}")
            return {}
    
    def delete_data_by_date_range(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Delete data within a specific date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            storage_data = self._load_data()
            
            if not storage_data['data']:
                return True
            
            # Filter out data within the date range
            filtered_records = []
            
            for record in storage_data['data']:
                if 'timestamp' in record:
                    record_time = pd.to_datetime(record['timestamp'])
                    if not (start_date <= record_time <= end_date):
                        filtered_records.append(record)
                else:
                    filtered_records.append(record)
            
            # Update storage data
            storage_data['data'] = filtered_records
            storage_data['metadata']['total_records'] = len(filtered_records)
            
            return self._save_data(storage_data)
            
        except Exception as e:
            print(f"Error deleting data by date range: {e}")
            return False
    
    def clear_all_data(self) -> bool:
        """
        Clear all stored data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._initialize_data_file()
            return True
        except Exception as e:
            print(f"Error clearing all data: {e}")
            return False
    
    def backup_data(self, backup_file: str) -> bool:
        """
        Create a backup of the current data.
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            storage_data = self._load_data()
            
            # Add backup metadata
            storage_data['backup_info'] = {
                'original_file': self.data_file,
                'backup_created_at': datetime.now().isoformat(),
                'backup_type': 'full'
            }
            
            with open(backup_file, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """
        Restore data from a backup file.
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Remove backup-specific metadata
            if 'backup_info' in backup_data:
                del backup_data['backup_info']
            
            # Save as current data
            return self._save_data(backup_data)
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def get_available_parameters(self) -> List[str]:
        """
        Get list of available parameters in the stored data.
        
        Returns:
            List[str]: List of parameter names
        """
        try:
            storage_data = self._load_data()
            return storage_data['metadata']['parameters']
        except Exception as e:
            print(f"Error getting available parameters: {e}")
            return []
    
    def optimize_storage(self) -> bool:
        """
        Optimize storage by removing duplicates and organizing data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            all_data = self.get_all_data()
            
            if all_data.empty:
                return True
            
            # Remove duplicates based on timestamp
            if 'timestamp' in all_data.columns:
                all_data = all_data.drop_duplicates(subset=['timestamp'])
                all_data = all_data.sort_values('timestamp')
            
            # Clear existing data and re-add optimized data
            self.clear_all_data()
            return self.add_data(all_data)
            
        except Exception as e:
            print(f"Error optimizing storage: {e}")
            return False
