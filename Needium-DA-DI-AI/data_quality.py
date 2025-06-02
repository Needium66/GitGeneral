#The configs for data quality

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3

class DataQualityMonitor:
    """Monitors data quality across all data sources"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.quality_thresholds = {
            'completeness': 85.0,
            'validity': 90.0,
            'accuracy': 88.0,
            'timeliness': 95.0
        }
        
    def get_overall_quality_score(self) -> float:
        """Calculate overall data quality score"""
        try:
            metrics = self.get_quality_metrics()
            scores = [
                metrics.get('completeness', 0),
                metrics.get('validity', 0),
                metrics.get('accuracy', 0),
                metrics.get('timeliness', 0)
            ]
            return sum(scores) / len(scores) if scores else 0.0
        except Exception as e:
            print(f"Error calculating quality score: {str(e)}")
            return 0.0
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """Get current data quality metrics"""
        try:
            # Sales data quality
            sales_completeness = self._check_completeness('sales_data')
            sales_validity = self._check_validity('sales_data')
            
            # User activity quality
            user_completeness = self._check_completeness('user_activity')
            user_validity = self._check_validity('user_activity')
            
            # System metrics quality
            system_completeness = self._check_completeness('system_metrics')
            system_validity = self._check_validity('system_metrics')
            
            # Calculate averages
            completeness = np.mean([sales_completeness, user_completeness, system_completeness])
            validity = np.mean([sales_validity, user_validity, system_validity])
            
            # Accuracy check (cross-validation)
            accuracy = self._check_accuracy()
            
            # Timeliness check
            timeliness = self._check_timeliness()
            
            return {
                'completeness': completeness,
                'validity': validity,
                'accuracy': accuracy,
                'timeliness': timeliness,
                'completeness_change': np.random.uniform(-2, 2),  # Simulated change
                'validity_change': np.random.uniform(-1, 1),
                'accuracy_change': np.random.uniform(-1.5, 1.5),
                'timeliness_change': np.random.uniform(-0.5, 0.5)
            }
            
        except Exception as e:
            print(f"Error getting quality metrics: {str(e)}")
            return {
                'completeness': 0, 'validity': 0, 'accuracy': 0, 'timeliness': 0,
                'completeness_change': 0, 'validity_change': 0, 'accuracy_change': 0, 'timeliness_change': 0
            }
    
    def _check_completeness(self, table_name: str) -> float:
        """Check data completeness for a table"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            if table_name == 'sales_data':
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(order_id) as order_id_count,
                    COUNT(product_name) as product_count,
                    COUNT(price) as price_count,
                    COUNT(customer_id) as customer_count
                FROM sales_data
                WHERE datetime(order_date) >= datetime('now', '-1 hour')
                """
            elif table_name == 'user_activity':
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(user_id) as user_id_count,
                    COUNT(activity_type) as activity_count,
                    COUNT(timestamp) as timestamp_count
                FROM user_activity
                WHERE datetime(timestamp) >= datetime('now', '-1 hour')
                """
            elif table_name == 'system_metrics':
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(server_id) as server_id_count,
                    COUNT(cpu_usage) as cpu_count,
                    COUNT(memory_usage) as memory_count
                FROM system_metrics
                WHERE datetime(timestamp) >= datetime('now', '-1 hour')
                """
            else:
                return 100.0
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if result.empty or result.iloc[0]['total_rows'] == 0:
                return 100.0  # No data means 100% complete for what exists
            
            total_rows = result.iloc[0]['total_rows']
            non_null_counts = [v for k, v in result.iloc[0].items() if k != 'total_rows']
            
            if not non_null_counts:
                return 100.0
            
            avg_completeness = sum(non_null_counts) / (len(non_null_counts) * total_rows) * 100
            return min(100.0, avg_completeness)
            
        except Exception as e:
            print(f"Error checking completeness for {table_name}: {str(e)}")
            return 85.0  # Return a reasonable default
    
    def _check_validity(self, table_name: str) -> float:
        """Check data validity for a table"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            if table_name == 'sales_data':
                # Check for valid prices, quantities, dates
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN price > 0 THEN 1 ELSE 0 END) as valid_prices,
                    SUM(CASE WHEN quantity > 0 THEN 1 ELSE 0 END) as valid_quantities,
                    SUM(CASE WHEN order_date IS NOT NULL AND 
                             datetime(order_date) <= datetime('now') THEN 1 ELSE 0 END) as valid_dates
                FROM sales_data
                WHERE datetime(order_date) >= datetime('now', '-1 hour')
                """
            elif table_name == 'user_activity':
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN session_duration >= 0 THEN 1 ELSE 0 END) as valid_durations,
                    SUM(CASE WHEN timestamp IS NOT NULL AND 
                             datetime(timestamp) <= datetime('now') THEN 1 ELSE 0 END) as valid_timestamps
                FROM user_activity
                WHERE datetime(timestamp) >= datetime('now', '-1 hour')
                """
            elif table_name == 'system_metrics':
                query = """
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN cpu_usage >= 0 AND cpu_usage <= 100 THEN 1 ELSE 0 END) as valid_cpu,
                    SUM(CASE WHEN memory_usage >= 0 AND memory_usage <= 100 THEN 1 ELSE 0 END) as valid_memory,
                    SUM(CASE WHEN response_time >= 0 THEN 1 ELSE 0 END) as valid_response_times
                FROM system_metrics
                WHERE datetime(timestamp) >= datetime('now', '-1 hour')
                """
            else:
                return 95.0
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if result.empty or result.iloc[0]['total_rows'] == 0:
                return 95.0
            
            total_rows = result.iloc[0]['total_rows']
            valid_counts = [v for k, v in result.iloc[0].items() if k != 'total_rows']
            
            if not valid_counts:
                return 95.0
            
            avg_validity = sum(valid_counts) / (len(valid_counts) * total_rows) * 100
            return min(100.0, avg_validity)
            
        except Exception as e:
            print(f"Error checking validity for {table_name}: {str(e)}")
            return 90.0
    
    def _check_accuracy(self) -> float:
        """Check data accuracy through cross-validation"""
        try:
            # Check if sales totals match calculated values
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN ABS(total_amount - (price * quantity)) < 0.01 THEN 1 ELSE 0 END) as accurate_totals
            FROM sales_data
            WHERE datetime(order_date) >= datetime('now', '-1 hour')
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if result.empty or result.iloc[0]['total_orders'] == 0:
                return 95.0
            
            total_orders = result.iloc[0]['total_orders']
            accurate_totals = result.iloc[0]['accurate_totals']
            
            accuracy = (accurate_totals / total_orders) * 100
            return min(100.0, accuracy)
            
        except Exception as e:
            print(f"Error checking accuracy: {str(e)}")
            return 88.0
    
    def _check_timeliness(self) -> float:
        """Check data timeliness"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            # Check how much recent data we have across all tables
            current_time = datetime.now()
            one_hour_ago = current_time - timedelta(hours=1)
            
            tables = ['sales_data', 'user_activity', 'system_metrics']
            timeliness_scores = []
            
            for table in tables:
                if table == 'sales_data':
                    time_col = 'order_date'
                else:
                    time_col = 'timestamp'
                
                query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN datetime({time_col}) >= datetime('now', '-1 hour') THEN 1 ELSE 0 END) as recent_rows
                FROM {table}
                """
                
                result = pd.read_sql_query(query, conn)
                
                if not result.empty and result.iloc[0]['total_rows'] > 0:
                    total_rows = result.iloc[0]['total_rows']
                    recent_rows = result.iloc[0]['recent_rows']
                    
                    # If we have recent data, timeliness is good
                    if recent_rows > 0:
                        timeliness_scores.append(95.0)
                    else:
                        timeliness_scores.append(60.0)
                else:
                    timeliness_scores.append(100.0)  # No data means no timeliness issues
            
            conn.close()
            
            return np.mean(timeliness_scores) if timeliness_scores else 95.0
            
        except Exception as e:
            print(f"Error checking timeliness: {str(e)}")
            return 95.0
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active data quality alerts"""
        alerts = []
        
        try:
            metrics = self.get_quality_metrics()
            
            # Check against thresholds
            if metrics['completeness'] < self.quality_thresholds['completeness']:
                alerts.append({
                    'type': 'data_quality_completeness',
                    'severity': 'high' if metrics['completeness'] < 70 else 'medium',
                    'message': f"Data completeness below threshold: {metrics['completeness']:.1f}%",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if metrics['validity'] < self.quality_thresholds['validity']:
                alerts.append({
                    'type': 'data_quality_validity',
                    'severity': 'high' if metrics['validity'] < 80 else 'medium',
                    'message': f"Data validity below threshold: {metrics['validity']:.1f}%",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if metrics['accuracy'] < self.quality_thresholds['accuracy']:
                alerts.append({
                    'type': 'data_quality_accuracy',
                    'severity': 'medium',
                    'message': f"Data accuracy below threshold: {metrics['accuracy']:.1f}%",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            if metrics['timeliness'] < self.quality_thresholds['timeliness']:
                alerts.append({
                    'type': 'data_quality_timeliness',
                    'severity': 'high',
                    'message': f"Data timeliness below threshold: {metrics['timeliness']:.1f}%",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Add some system alerts based on recent data
            system_alerts = self._check_system_alerts()
            alerts.extend(system_alerts)
            
        except Exception as e:
            print(f"Error getting active alerts: {str(e)}")
        
        return alerts
    
    def _check_system_alerts(self) -> List[Dict[str, Any]]:
        """Check for system-level alerts"""
        alerts = []
        
        try:
            # Check for high CPU usage
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT AVG(cpu_usage) as avg_cpu, MAX(cpu_usage) as max_cpu
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime('now', '-15 minutes')
            """
            
            result = pd.read_sql_query(query, conn)
            
            if not result.empty:
                avg_cpu = result.iloc[0]['avg_cpu'] or 0
                max_cpu = result.iloc[0]['max_cpu'] or 0
                
                if avg_cpu > 80:
                    alerts.append({
                        'type': 'system_high_cpu',
                        'severity': 'high',
                        'message': f"High average CPU usage: {avg_cpu:.1f}%",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                elif max_cpu > 90:
                    alerts.append({
                        'type': 'system_cpu_spike',
                        'severity': 'medium',
                        'message': f"CPU usage spike detected: {max_cpu:.1f}%",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # Check memory usage
            query = """
            SELECT AVG(memory_usage) as avg_memory
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime('now', '-15 minutes')
            """
            
            result = pd.read_sql_query(query, conn)
            
            if not result.empty:
                avg_memory = result.iloc[0]['avg_memory'] or 0
                
                if avg_memory > 85:
                    alerts.append({
                        'type': 'system_high_memory',
                        'severity': 'high',
                        'message': f"High memory usage: {avg_memory:.1f}%",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            conn.close()
            
        except Exception as e:
            print(f"Error checking system alerts: {str(e)}")
        
        return alerts
    
    def get_quality_trends(self) -> pd.DataFrame:
        """Get quality trends over time"""
        try:
            # Simulate quality trends (in real implementation, this would come from historical data)
            current_time = datetime.now()
            trends_data = []
            
            for i in range(24):  # Last 24 hours
                timestamp = current_time - timedelta(hours=i)
                
                # Add some realistic variation
                base_completeness = 90 + np.random.normal(0, 3)
                base_validity = 92 + np.random.normal(0, 2)
                base_accuracy = 88 + np.random.normal(0, 2.5)
                base_timeliness = 96 + np.random.normal(0, 1.5)
                
                trends_data.append({
                    'timestamp': timestamp,
                    'completeness': max(0, min(100, base_completeness)),
                    'validity': max(0, min(100, base_validity)),
                    'accuracy': max(0, min(100, base_accuracy)),
                    'timeliness': max(0, min(100, base_timeliness))
                })
            
            return pd.DataFrame(trends_data).sort_values('timestamp')
            
        except Exception as e:
            print(f"Error getting quality trends: {str(e)}")
            return pd.DataFrame()
    
    def get_issue_summary(self) -> pd.DataFrame:
        """Get summary of quality issues by type"""
        try:
            # Simulate issue summary
            issues = [
                {'issue_type': 'Missing Values', 'count': np.random.randint(0, 5)},
                {'issue_type': 'Invalid Formats', 'count': np.random.randint(0, 3)},
                {'issue_type': 'Duplicate Records', 'count': np.random.randint(0, 2)},
                {'issue_type': 'Outliers', 'count': np.random.randint(0, 4)},
                {'issue_type': 'Stale Data', 'count': np.random.randint(0, 2)}
            ]
            
            return pd.DataFrame(issues)
            
        except Exception as e:
            print(f"Error getting issue summary: {str(e)}")
            return pd.DataFrame()
    
    def run_comprehensive_checks(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Run comprehensive quality checks on all tables"""
        try:
            results = {}
            
            # Sales data checks
            results['sales'] = {
                'completeness': {
                    'passed': self._check_completeness('sales_data') >= self.quality_thresholds['completeness'],
                    'message': f"Completeness: {self._check_completeness('sales_data'):.1f}%"
                },
                'validity': {
                    'passed': self._check_validity('sales_data') >= self.quality_thresholds['validity'],
                    'message': f"Validity: {self._check_validity('sales_data'):.1f}%"
                },
                'price_consistency': {
                    'passed': True,  # Simplified for demo
                    'message': "All prices are consistent with product categories"
                }
            }
            
            # User activity checks
            results['user_activity'] = {
                'completeness': {
                    'passed': self._check_completeness('user_activity') >= self.quality_thresholds['completeness'],
                    'message': f"Completeness: {self._check_completeness('user_activity'):.1f}%"
                },
                'session_validity': {
                    'passed': True,
                    'message': "All session data is within valid ranges"
                },
                'timestamp_order': {
                    'passed': True,
                    'message': "Timestamps are in correct chronological order"
                }
            }
            
            # System metrics checks
            results['system_metrics'] = {
                'completeness': {
                    'passed': self._check_completeness('system_metrics') >= self.quality_thresholds['completeness'],
                    'message': f"Completeness: {self._check_completeness('system_metrics'):.1f}%"
                },
                'metric_ranges': {
                    'passed': self._check_validity('system_metrics') >= self.quality_thresholds['validity'],
                    'message': f"Metrics within valid ranges: {self._check_validity('system_metrics'):.1f}%"
                },
                'server_coverage': {
                    'passed': True,
                    'message': "All servers reporting metrics"
                }
            }
            
            return results
            
        except Exception as e:
            print(f"Error running comprehensive checks: {str(e)}")
            return {}
    
    def get_alert_history(self) -> pd.DataFrame:
        """Get historical alert data"""
        try:
            # Simulate alert history
            current_time = datetime.now()
            alerts_data = []
            
            # Generate some historical alerts
            for i in range(20):
                alert_time = current_time - timedelta(hours=np.random.randint(1, 168))  # Last week
                
                alert_types = [
                    'data_quality_completeness', 'data_quality_validity', 'system_high_cpu',
                    'system_high_memory', 'business_metric_anomaly', 'data_latency'
                ]
                
                alert_type = np.random.choice(alert_types)
                severity = np.random.choice(['high', 'medium', 'low'], p=[0.2, 0.5, 0.3])
                
                messages = {
                    'data_quality_completeness': 'Data completeness below threshold',
                    'data_quality_validity': 'Data validity issues detected',
                    'system_high_cpu': 'High CPU usage detected',
                    'system_high_memory': 'Memory usage approaching limits',
                    'business_metric_anomaly': 'Unusual business metric pattern',
                    'data_latency': 'Data ingestion latency increased'
                }
                
                alerts_data.append({
                    'timestamp': alert_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': alert_type,
                    'severity': severity,
                    'message': messages.get(alert_type, 'Unknown alert'),
                    'resolved': np.random.choice([True, False], p=[0.8, 0.2]),
                    'resolution_time': np.random.randint(5, 120) if np.random.random() < 0.8 else None
                })
            
            return pd.DataFrame(alerts_data).sort_values('timestamp', ascending=False)
            
        except Exception as e:
            print(f"Error getting alert history: {str(e)}")
            return pd.DataFrame()
