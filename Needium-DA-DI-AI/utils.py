#The configs for the utilities

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union
import json

def format_number(number: Union[int, float]) -> str:
    """Format numbers with appropriate suffixes (K, M, B)"""
    try:
        if not isinstance(number, (int, float)) or pd.isna(number):
            return "0"
        
        number = float(number)
        
        if abs(number) >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f}B"
        elif abs(number) >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif abs(number) >= 1_000:
            return f"{number / 1_000:.1f}K"
        else:
            return f"{number:.0f}"
    except:
        return "0"

def format_currency(amount: Union[int, float], currency: str = "USD") -> str:
    """Format currency values"""
    try:
        if not isinstance(amount, (int, float)) or pd.isna(amount):
            return "$0.00"
        
        if currency == "USD":
            if abs(amount) >= 1_000_000:
                return f"${amount / 1_000_000:.1f}M"
            elif abs(amount) >= 1_000:
                return f"${amount / 1_000:.1f}K"
            else:
                return f"${amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"
    except:
        return "$0.00"

def format_percentage(value: Union[int, float], decimal_places: int = 1) -> str:
    """Format percentage values"""
    try:
        if not isinstance(value, (int, float)) or pd.isna(value):
            return "0.0%"
        
        return f"{value:.{decimal_places}f}%"
    except:
        return "0.0%"

def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in seconds to human readable format"""
    try:
        if not isinstance(seconds, (int, float)) or pd.isna(seconds):
            return "0s"
        
        seconds = int(seconds)
        
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        elif seconds >= 60:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "0s"

def calculate_change_percentage(current: Union[int, float], previous: Union[int, float]) -> float:
    """Calculate percentage change between two values"""
    try:
        if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
            return 0.0
        
        if pd.isna(current) or pd.isna(previous) or previous == 0:
            return 0.0
        
        return ((current - previous) / previous) * 100
    except:
        return 0.0

def generate_alert_message(alert_type: str, metric_value: Union[int, float], 
                         threshold: Union[int, float], **kwargs) -> str:
    """Generate human-readable alert messages"""
    try:
        if alert_type == "high_cpu":
            return f"CPU usage ({metric_value:.1f}%) exceeded threshold ({threshold:.1f}%)"
        elif alert_type == "high_memory":
            return f"Memory usage ({metric_value:.1f}%) exceeded threshold ({threshold:.1f}%)"
        elif alert_type == "data_quality":
            quality_type = kwargs.get('quality_type', 'unknown')
            return f"Data quality issue: {quality_type} score ({metric_value:.1f}%) below threshold ({threshold:.1f}%)"
        elif alert_type == "response_time":
            return f"Response time ({metric_value:.0f}ms) exceeded threshold ({threshold:.0f}ms)"
        elif alert_type == "error_rate":
            return f"Error rate ({metric_value:.2f}%) exceeded threshold ({threshold:.2f}%)"
        elif alert_type == "revenue_drop":
            return f"Revenue drop detected: {metric_value:.1f}% below expected threshold"
        elif alert_type == "data_freshness":
            return f"Data freshness alert: Last update was {metric_value:.0f} minutes ago"
        else:
            return f"Alert: {alert_type} - Value: {metric_value}, Threshold: {threshold}"
    except:
        return f"Alert: {alert_type}"

def validate_data_types(df: pd.DataFrame, schema: Dict[str, str]) -> Dict[str, Any]:
    """Validate data types against expected schema"""
    try:
        validation_results = {
            'passed': True,
            'errors': [],
            'warnings': []
        }
        
        for column, expected_type in schema.items():
            if column not in df.columns:
                validation_results['errors'].append(f"Missing column: {column}")
                validation_results['passed'] = False
                continue
            
            column_data = df[column]
            
            if expected_type == 'numeric':
                if not pd.api.types.is_numeric_dtype(column_data):
                    validation_results['errors'].append(f"Column {column} should be numeric")
                    validation_results['passed'] = False
            elif expected_type == 'datetime':
                try:
                    pd.to_datetime(column_data)
                except:
                    validation_results['errors'].append(f"Column {column} should be datetime")
                    validation_results['passed'] = False
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(column_data) and not pd.api.types.is_object_dtype(column_data):
                    validation_results['warnings'].append(f"Column {column} should be string/text")
        
        return validation_results
    except Exception as e:
        return {
            'passed': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': []
        }

def detect_outliers(series: pd.Series, method: str = 'iqr', multiplier: float = 1.5) -> pd.Series:
    """Detect outliers in a pandas Series"""
    try:
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            return (series < lower_bound) | (series > upper_bound)
        elif method == 'zscore':
            z_scores = np.abs((series - series.mean()) / series.std())
            return z_scores > multiplier
        else:
            return pd.Series([False] * len(series))
    except:
        return pd.Series([False] * len(series))

def calculate_data_freshness(timestamp_series: pd.Series) -> Dict[str, Any]:
    """Calculate data freshness metrics"""
    try:
        if timestamp_series.empty:
            return {
                'latest_timestamp': None,
                'oldest_timestamp': None,
                'freshness_score': 0.0,
                'minutes_since_latest': float('inf'),
                'data_span_hours': 0.0
            }
        
        # Convert to datetime if not already
        timestamp_series = pd.to_datetime(timestamp_series)
        
        latest_timestamp = timestamp_series.max()
        oldest_timestamp = timestamp_series.min()
        current_time = datetime.now()
        
        # Calculate minutes since latest data
        minutes_since_latest = (current_time - latest_timestamp).total_seconds() / 60
        
        # Calculate data span
        data_span = (latest_timestamp - oldest_timestamp).total_seconds() / 3600  # hours
        
        # Calculate freshness score (100% if data is < 5 minutes old, decreasing linearly)
        if minutes_since_latest <= 5:
            freshness_score = 100.0
        elif minutes_since_latest <= 60:
            freshness_score = 100 - (minutes_since_latest - 5) * (80 / 55)  # 80% reduction over 55 minutes
        else:
            freshness_score = max(0, 20 - (minutes_since_latest - 60) * (20 / 180))  # Remaining 20% over 3 hours
        
        return {
            'latest_timestamp': latest_timestamp,
            'oldest_timestamp': oldest_timestamp,
            'freshness_score': max(0, freshness_score),
            'minutes_since_latest': minutes_since_latest,
            'data_span_hours': data_span
        }
    except Exception as e:
        return {
            'latest_timestamp': None,
            'oldest_timestamp': None,
            'freshness_score': 0.0,
            'minutes_since_latest': float('inf'),
            'data_span_hours': 0.0,
            'error': str(e)
        }

def create_time_buckets(df: pd.DataFrame, timestamp_column: str, 
                       bucket_size: str = '1H') -> pd.DataFrame:
    """Create time-based buckets for aggregation"""
    try:
        df_copy = df.copy()
        df_copy[timestamp_column] = pd.to_datetime(df_copy[timestamp_column])
        df_copy['time_bucket'] = df_copy[timestamp_column].dt.floor(bucket_size)
        return df_copy
    except Exception as e:
        print(f"Error creating time buckets: {str(e)}")
        return df

def calculate_rolling_metrics(series: pd.Series, window: int = 7) -> pd.DataFrame:
    """Calculate rolling metrics for a time series"""
    try:
        metrics = pd.DataFrame({
            'value': series,
            'rolling_mean': series.rolling(window=window, min_periods=1).mean(),
            'rolling_std': series.rolling(window=window, min_periods=1).std(),
            'rolling_min': series.rolling(window=window, min_periods=1).min(),
            'rolling_max': series.rolling(window=window, min_periods=1).max(),
            'rolling_median': series.rolling(window=window, min_periods=1).median()
        })
        
        # Add percentage change
        metrics['pct_change'] = series.pct_change()
        metrics['rolling_pct_change'] = metrics['rolling_mean'].pct_change()
        
        return metrics
    except Exception as e:
        print(f"Error calculating rolling metrics: {str(e)}")
        return pd.DataFrame()

def export_data_to_formats(df: pd.DataFrame, base_filename: str) -> Dict[str, bytes]:
    """Export dataframe to multiple formats"""
    try:
        exports = {}
        
        # CSV export
        csv_buffer = df.to_csv(index=False)
        exports['csv'] = csv_buffer.encode('utf-8')
        
        # JSON export
        json_buffer = df.to_json(orient='records', date_format='iso')
        exports['json'] = json_buffer.encode('utf-8')
        
        # Excel export (if openpyxl is available)
        try:
            import io
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            exports['xlsx'] = excel_buffer.getvalue()
        except ImportError:
            pass  # Skip Excel export if openpyxl not available
        
        return exports
    except Exception as e:
        print(f"Error exporting data: {str(e)}")
        return {}

def generate_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive data summary"""
    try:
        summary = {
            'shape': df.shape,
            'columns': list(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict(),
        }
        
        # Numeric columns summary
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary['numeric_summary'] = df[numeric_cols].describe().to_dict()
        
        # Categorical columns summary
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            summary['categorical_summary'] = {}
            for col in categorical_cols:
                summary['categorical_summary'][col] = {
                    'unique_count': df[col].nunique(),
                    'top_values': df[col].value_counts().head(5).to_dict()
                }
        
        # Date columns summary
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            summary['date_summary'] = {}
            for col in date_cols:
                summary['date_summary'][col] = {
                    'min_date': df[col].min(),
                    'max_date': df[col].max(),
                    'date_range_days': (df[col].max() - df[col].min()).days
                }
        
        return summary
    except Exception as e:
        return {'error': f"Error generating summary: {str(e)}"}

def safe_divide(numerator: Union[int, float], denominator: Union[int, float], 
               default: Union[int, float] = 0) -> Union[int, float]:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
            return default
        return numerator / denominator
    except:
        return default

def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to specified length with suffix"""
    try:
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    except:
        return str(text)[:max_length] if len(str(text)) > max_length else str(text)
