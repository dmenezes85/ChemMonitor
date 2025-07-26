import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
import warnings

# Suppress warnings for statistical calculations
warnings.filterwarnings('ignore')

class StatisticsCalculator:
    """Provides statistical analysis capabilities for chemical process data."""
    
    def __init__(self):
        """Initialize the statistics calculator."""
        pass
    
    def calculate_basic_stats(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate basic statistical measures for numeric columns.
        
        Args:
            data: DataFrame containing numeric data
            
        Returns:
            pd.DataFrame: Statistical summary
        """
        try:
            # Select only numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty:
                return pd.DataFrame()
            
            # Calculate basic statistics
            stats_df = numeric_data.describe()
            
            # Add additional statistics
            additional_stats = {}
            
            for column in numeric_data.columns:
                col_data = numeric_data[column].dropna()
                
                if len(col_data) > 0:
                    # Coefficient of variation
                    cv = (col_data.std() / col_data.mean() * 100) if col_data.mean() != 0 else 0
                    
                    # Range
                    data_range = col_data.max() - col_data.min()
                    
                    # Median absolute deviation
                    mad = np.median(np.abs(col_data - col_data.median()))
                    
                    # Skewness and kurtosis
                    skewness = col_data.skew()
                    kurtosis = col_data.kurtosis()
                    
                    additional_stats[column] = {
                        'cv_percent': cv,
                        'range': data_range,
                        'mad': mad,
                        'skewness': skewness,
                        'kurtosis': kurtosis,
                        'missing_count': numeric_data[column].isnull().sum(),
                        'missing_percent': (numeric_data[column].isnull().sum() / len(numeric_data)) * 100
                    }
                else:
                    additional_stats[column] = {
                        'cv_percent': np.nan,
                        'range': np.nan,
                        'mad': np.nan,
                        'skewness': np.nan,
                        'kurtosis': np.nan,
                        'missing_count': len(numeric_data),
                        'missing_percent': 100.0
                    }
            
            # Convert additional stats to DataFrame and combine
            additional_df = pd.DataFrame(additional_stats).T
            
            # Reorder and combine statistics
            combined_stats = pd.concat([stats_df.T, additional_df], axis=1)
            
            # Round for better presentation
            combined_stats = combined_stats.round(4)
            
            return combined_stats.T
            
        except Exception as e:
            print(f"Error calculating basic statistics: {e}")
            return pd.DataFrame()
    
    def detect_outliers(self, data: pd.Series, method: str = 'iqr') -> Dict[str, Any]:
        """
        Detect outliers in a data series.
        
        Args:
            data: Data series to analyze
            method: Method to use ('iqr', 'zscore', 'modified_zscore')
            
        Returns:
            Dict: Outlier detection results
        """
        try:
            clean_data = data.dropna()
            
            if len(clean_data) == 0:
                return {'outliers': [], 'outlier_count': 0, 'outlier_percentage': 0}
            
            outliers = []
            
            if method == 'iqr':
                Q1 = clean_data.quantile(0.25)
                Q3 = clean_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(clean_data))
                outliers = clean_data[z_scores > 3]
                
            elif method == 'modified_zscore':
                median = clean_data.median()
                mad = np.median(np.abs(clean_data - median))
                modified_z_scores = 0.6745 * (clean_data - median) / mad
                outliers = clean_data[np.abs(modified_z_scores) > 3.5]
            
            outlier_count = len(outliers)
            outlier_percentage = (outlier_count / len(clean_data)) * 100
            
            return {
                'outliers': outliers.tolist(),
                'outlier_indices': outliers.index.tolist(),
                'outlier_count': outlier_count,
                'outlier_percentage': outlier_percentage,
                'method_used': method,
                'total_points': len(clean_data)
            }
            
        except Exception as e:
            print(f"Error detecting outliers: {e}")
            return {'outliers': [], 'outlier_count': 0, 'outlier_percentage': 0}
    
    def calculate_correlation_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix for numeric columns.
        
        Args:
            data: DataFrame containing numeric data
            
        Returns:
            pd.DataFrame: Correlation matrix
        """
        try:
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty or len(numeric_data.columns) < 2:
                return pd.DataFrame()
            
            correlation_matrix = numeric_data.corr()
            
            return correlation_matrix
            
        except Exception as e:
            print(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    def find_strong_correlations(self, data: pd.DataFrame, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find pairs of variables with strong correlations.
        
        Args:
            data: DataFrame containing numeric data
            threshold: Correlation threshold (absolute value)
            
        Returns:
            List[Dict]: List of strong correlations
        """
        try:
            corr_matrix = self.calculate_correlation_matrix(data)
            
            if corr_matrix.empty:
                return []
            
            strong_correlations = []
            
            # Get upper triangle of correlation matrix (avoid duplicates)
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    param1 = corr_matrix.columns[i]
                    param2 = corr_matrix.columns[j]
                    correlation = corr_matrix.iloc[i, j]
                    
                    if abs(correlation) >= threshold:
                        strength = self._classify_correlation_strength(abs(correlation))
                        
                        strong_correlations.append({
                            'parameter_1': param1,
                            'parameter_2': param2,
                            'correlation': correlation,
                            'abs_correlation': abs(correlation),
                            'strength': strength,
                            'direction': 'positive' if correlation > 0 else 'negative'
                        })
            
            # Sort by absolute correlation value (strongest first)
            strong_correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
            
            return strong_correlations
            
        except Exception as e:
            print(f"Error finding strong correlations: {e}")
            return []
    
    def _classify_correlation_strength(self, abs_correlation: float) -> str:
        """Classify correlation strength based on absolute value."""
        if abs_correlation >= 0.9:
            return 'Very Strong'
        elif abs_correlation >= 0.7:
            return 'Strong'
        elif abs_correlation >= 0.5:
            return 'Moderate'
        elif abs_correlation >= 0.3:
            return 'Weak'
        else:
            return 'Very Weak'
    
    def calculate_trend_analysis(self, data: pd.Series, x_values: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Perform trend analysis on a data series.
        
        Args:
            data: Data series to analyze
            x_values: Optional x-values (if None, uses index)
            
        Returns:
            Dict: Trend analysis results
        """
        try:
            clean_data = data.dropna()
            
            if len(clean_data) < 2:
                return {'trend': 'insufficient_data'}
            
            if x_values is None:
                x_vals = np.arange(len(clean_data))
            else:
                x_vals = x_values.iloc[:len(clean_data)]
                if not pd.api.types.is_numeric_dtype(x_vals):
                    x_vals = np.arange(len(clean_data))
            
            # Linear regression for trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, clean_data)
            
            # Classify trend
            if p_value < 0.05:  # Statistically significant
                if slope > 0:
                    trend_direction = 'increasing'
                else:
                    trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
            
            # Calculate trend strength
            trend_strength = abs(r_value)
            
            # Change metrics
            total_change = clean_data.iloc[-1] - clean_data.iloc[0]
            percent_change = (total_change / clean_data.iloc[0] * 100) if clean_data.iloc[0] != 0 else 0
            
            return {
                'trend': trend_direction,
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'p_value': p_value,
                'std_error': std_err,
                'trend_strength': trend_strength,
                'total_change': total_change,
                'percent_change': percent_change,
                'start_value': clean_data.iloc[0],
                'end_value': clean_data.iloc[-1],
                'is_significant': p_value < 0.05
            }
            
        except Exception as e:
            print(f"Error calculating trend analysis: {e}")
            return {'trend': 'error', 'error': str(e)}
    
    def calculate_process_capability(self, data: pd.Series, 
                                   lower_spec_limit: float, 
                                   upper_spec_limit: float,
                                   target: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate process capability indices.
        
        Args:
            data: Process data
            lower_spec_limit: Lower specification limit
            upper_spec_limit: Upper specification limit
            target: Target value (if None, uses midpoint of spec limits)
            
        Returns:
            Dict: Process capability metrics
        """
        try:
            clean_data = data.dropna()
            
            if len(clean_data) == 0:
                return {'error': 'No data available'}
            
            if target is None:
                target = (lower_spec_limit + upper_spec_limit) / 2
            
            mean = clean_data.mean()
            std_dev = clean_data.std()
            
            if std_dev == 0:
                return {'error': 'Standard deviation is zero'}
            
            # Calculate capability indices
            cp = (upper_spec_limit - lower_spec_limit) / (6 * std_dev)
            cpu = (upper_spec_limit - mean) / (3 * std_dev)
            cpl = (mean - lower_spec_limit) / (3 * std_dev)
            cpk = min(cpu, cpl)
            
            # Calculate Cpm (capability index with respect to target)
            cpm = (upper_spec_limit - lower_spec_limit) / (6 * np.sqrt(std_dev**2 + (mean - target)**2))
            
            # Calculate percentage within spec limits
            within_spec = clean_data[(clean_data >= lower_spec_limit) & (clean_data <= upper_spec_limit)]
            percent_within_spec = (len(within_spec) / len(clean_data)) * 100
            
            # Process performance classification
            if cpk >= 1.33:
                performance_level = 'Excellent'
            elif cpk >= 1.0:
                performance_level = 'Adequate'
            elif cpk >= 0.67:
                performance_level = 'Poor'
            else:
                performance_level = 'Unacceptable'
            
            return {
                'cp': cp,
                'cpu': cpu,
                'cpl': cpl,
                'cpk': cpk,
                'cpm': cpm,
                'mean': mean,
                'std_dev': std_dev,
                'target': target,
                'lower_spec_limit': lower_spec_limit,
                'upper_spec_limit': upper_spec_limit,
                'percent_within_spec': percent_within_spec,
                'performance_level': performance_level,
                'sample_size': len(clean_data)
            }
            
        except Exception as e:
            print(f"Error calculating process capability: {e}")
            return {'error': str(e)}
    
    def perform_normality_test(self, data: pd.Series) -> Dict[str, Any]:
        """
        Test data for normality using multiple methods.
        
        Args:
            data: Data series to test
            
        Returns:
            Dict: Normality test results
        """
        try:
            clean_data = data.dropna()
            
            if len(clean_data) < 3:
                return {'error': 'Insufficient data for normality testing'}
            
            results = {}
            
            # Shapiro-Wilk test (best for small samples)
            if len(clean_data) <= 5000:
                try:
                    shapiro_stat, shapiro_p = stats.shapiro(clean_data)
                    results['shapiro_wilk'] = {
                        'statistic': shapiro_stat,
                        'p_value': shapiro_p,
                        'is_normal': shapiro_p > 0.05
                    }
                except:
                    results['shapiro_wilk'] = {'error': 'Test failed'}
            
            # Kolmogorov-Smirnov test
            try:
                # Standardize data for comparison with standard normal
                standardized = (clean_data - clean_data.mean()) / clean_data.std()
                ks_stat, ks_p = stats.kstest(standardized, 'norm')
                results['kolmogorov_smirnov'] = {
                    'statistic': ks_stat,
                    'p_value': ks_p,
                    'is_normal': ks_p > 0.05
                }
            except:
                results['kolmogorov_smirnov'] = {'error': 'Test failed'}
            
            # D'Agostino's normality test
            try:
                dag_stat, dag_p = stats.normaltest(clean_data)
                results['dagostino'] = {
                    'statistic': dag_stat,
                    'p_value': dag_p,
                    'is_normal': dag_p > 0.05
                }
            except:
                results['dagostino'] = {'error': 'Test failed'}
            
            # Overall assessment
            normal_tests = [result.get('is_normal', False) for result in results.values() 
                          if isinstance(result, dict) and 'is_normal' in result]
            
            if normal_tests:
                # Consider normal if majority of tests indicate normality
                overall_normal = sum(normal_tests) > len(normal_tests) / 2
                results['overall_assessment'] = {
                    'is_normal': overall_normal,
                    'confidence': 'high' if all(normal_tests) or not any(normal_tests) else 'moderate'
                }
            
            return results
            
        except Exception as e:
            print(f"Error performing normality test: {e}")
            return {'error': str(e)}
    
    def calculate_control_limits(self, data: pd.Series, n_sigma: float = 3) -> Dict[str, float]:
        """
        Calculate statistical control limits for process monitoring.
        
        Args:
            data: Process data
            n_sigma: Number of standard deviations for control limits
            
        Returns:
            Dict: Control limits
        """
        try:
            clean_data = data.dropna()
            
            if len(clean_data) == 0:
                return {}
            
            mean = clean_data.mean()
            std_dev = clean_data.std()
            
            upper_control_limit = mean + (n_sigma * std_dev)
            lower_control_limit = mean - (n_sigma * std_dev)
            
            # Warning limits (typically 2 sigma)
            upper_warning_limit = mean + (2 * std_dev)
            lower_warning_limit = mean - (2 * std_dev)
            
            return {
                'center_line': mean,
                'upper_control_limit': upper_control_limit,
                'lower_control_limit': lower_control_limit,
                'upper_warning_limit': upper_warning_limit,
                'lower_warning_limit': lower_warning_limit,
                'standard_deviation': std_dev,
                'n_sigma': n_sigma
            }
            
        except Exception as e:
            print(f"Error calculating control limits: {e}")
            return {}
    
    def analyze_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive data quality analysis.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            Dict: Data quality assessment
        """
        try:
            quality_report = {
                'overview': {},
                'missing_data': {},
                'duplicates': {},
                'outliers': {},
                'data_types': {},
                'recommendations': []
            }
            
            # Overview
            quality_report['overview'] = {
                'total_rows': len(data),
                'total_columns': len(data.columns),
                'numeric_columns': len(data.select_dtypes(include=[np.number]).columns),
                'datetime_columns': len(data.select_dtypes(include=['datetime64']).columns),
                'object_columns': len(data.select_dtypes(include=['object']).columns)
            }
            
            # Missing data analysis
            missing_counts = data.isnull().sum()
            missing_percentages = (missing_counts / len(data)) * 100
            
            quality_report['missing_data'] = {
                'columns_with_missing': missing_counts[missing_counts > 0].to_dict(),
                'missing_percentages': missing_percentages[missing_percentages > 0].to_dict(),
                'total_missing_values': missing_counts.sum(),
                'overall_completeness': ((len(data) * len(data.columns) - missing_counts.sum()) / 
                                       (len(data) * len(data.columns)) * 100) if len(data) > 0 else 100
            }
            
            # Duplicate analysis
            duplicate_rows = data.duplicated().sum()
            quality_report['duplicates'] = {
                'duplicate_rows': duplicate_rows,
                'duplicate_percentage': (duplicate_rows / len(data)) * 100 if len(data) > 0 else 0
            }
            
            # Outlier analysis for numeric columns
            numeric_data = data.select_dtypes(include=[np.number])
            outlier_summary = {}
            
            for column in numeric_data.columns:
                outlier_info = self.detect_outliers(numeric_data[column])
                outlier_summary[column] = {
                    'outlier_count': outlier_info['outlier_count'],
                    'outlier_percentage': outlier_info['outlier_percentage']
                }
            
            quality_report['outliers'] = outlier_summary
            
            # Data type analysis
            quality_report['data_types'] = data.dtypes.astype(str).to_dict()
            
            # Generate recommendations
            recommendations = []
            
            # Missing data recommendations
            for column, percentage in missing_percentages.items():
                if percentage > 50:
                    recommendations.append(f"Column '{column}' has {percentage:.1f}% missing values - consider removing or investigating data collection issues")
                elif percentage > 20:
                    recommendations.append(f"Column '{column}' has {percentage:.1f}% missing values - consider imputation strategies")
            
            # Duplicate recommendations
            if duplicate_rows > 0:
                recommendations.append(f"Found {duplicate_rows} duplicate rows ({duplicate_rows/len(data)*100:.1f}%) - consider deduplication")
            
            # Outlier recommendations
            for column, outlier_info in outlier_summary.items():
                if outlier_info['outlier_percentage'] > 10:
                    recommendations.append(f"Column '{column}' has {outlier_info['outlier_percentage']:.1f}% outliers - investigate data quality or process variations")
            
            quality_report['recommendations'] = recommendations
            
            return quality_report
            
        except Exception as e:
            print(f"Error analyzing data quality: {e}")
            return {'error': str(e)}
    
    def calculate_rolling_statistics(self, data: pd.Series, window: int = 10) -> pd.DataFrame:
        """
        Calculate rolling statistics for time series analysis.
        
        Args:
            data: Time series data
            window: Rolling window size
            
        Returns:
            pd.DataFrame: Rolling statistics
        """
        try:
            if len(data) < window:
                return pd.DataFrame()
            
            rolling_stats = pd.DataFrame({
                'value': data,
                'rolling_mean': data.rolling(window=window).mean(),
                'rolling_std': data.rolling(window=window).std(),
                'rolling_min': data.rolling(window=window).min(),
                'rolling_max': data.rolling(window=window).max(),
                'rolling_median': data.rolling(window=window).median()
            })
            
            # Calculate rolling coefficient of variation
            rolling_stats['rolling_cv'] = (rolling_stats['rolling_std'] / rolling_stats['rolling_mean']) * 100
            
            # Calculate upper and lower control bounds
            rolling_stats['upper_bound'] = rolling_stats['rolling_mean'] + 2 * rolling_stats['rolling_std']
            rolling_stats['lower_bound'] = rolling_stats['rolling_mean'] - 2 * rolling_stats['rolling_std']
            
            return rolling_stats
            
        except Exception as e:
            print(f"Error calculating rolling statistics: {e}")
            return pd.DataFrame()
