#The configs for analytics

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any

class AnalyticsEngine:
    """Advanced analytics engine for business intelligence"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key business metrics"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            # Revenue metrics
            revenue_query = """
            SELECT 
                SUM(total_amount) as total_revenue,
                COUNT(DISTINCT order_id) as total_orders,
                AVG(total_amount) as avg_order_value
            FROM sales_data
            WHERE datetime(order_date) >= datetime('now', '-24 hours')
            """
            
            revenue_result = pd.read_sql_query(revenue_query, conn)
            
            # Previous 24 hours for comparison
            prev_revenue_query = """
            SELECT 
                SUM(total_amount) as prev_revenue,
                COUNT(DISTINCT order_id) as prev_orders
            FROM sales_data
            WHERE datetime(order_date) >= datetime('now', '-48 hours')
            AND datetime(order_date) < datetime('now', '-24 hours')
            """
            
            prev_revenue_result = pd.read_sql_query(prev_revenue_query, conn)
            
            # User metrics
            user_query = """
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_activities
            FROM user_activity
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            """
            
            user_result = pd.read_sql_query(user_query, conn)
            
            # Previous user metrics
            prev_user_query = """
            SELECT 
                COUNT(DISTINCT user_id) as prev_users
            FROM user_activity
            WHERE datetime(timestamp) >= datetime('now', '-48 hours')
            AND datetime(timestamp) < datetime('now', '-24 hours')
            """
            
            prev_user_result = pd.read_sql_query(prev_user_query, conn)
            
            # System metrics
            system_query = """
            SELECT 
                AVG(cpu_usage) as avg_cpu,
                AVG(memory_usage) as avg_memory,
                AVG(response_time) as avg_response_time
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime('now', '-1 hour')
            """
            
            system_result = pd.read_sql_query(system_query, conn)
            
            # Previous system metrics
            prev_system_query = """
            SELECT 
                AVG(cpu_usage) as prev_cpu
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime('now', '-2 hours')
            AND datetime(timestamp) < datetime('now', '-1 hour')
            """
            
            prev_system_result = pd.read_sql_query(prev_system_query, conn)
            
            conn.close()
            
            # Calculate metrics and changes
            current_revenue = revenue_result.iloc[0]['total_revenue'] or 0
            prev_revenue = prev_revenue_result.iloc[0]['prev_revenue'] or 0
            revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            current_orders = revenue_result.iloc[0]['total_orders'] or 0
            prev_orders = prev_revenue_result.iloc[0]['prev_orders'] or 0
            orders_change = current_orders - prev_orders
            
            current_users = user_result.iloc[0]['active_users'] or 0
            prev_users = prev_user_result.iloc[0]['prev_users'] or 0
            users_change = current_users - prev_users
            
            current_cpu = system_result.iloc[0]['avg_cpu'] or 0
            prev_cpu = prev_system_result.iloc[0]['prev_cpu'] or 0
            cpu_change = current_cpu - prev_cpu
            
            return {
                'total_revenue': current_revenue,
                'revenue_change': revenue_change,
                'total_orders': current_orders,
                'orders_change': orders_change,
                'active_users': current_users,
                'users_change': users_change,
                'avg_cpu': current_cpu,
                'cpu_change': cpu_change,
                'avg_order_value': revenue_result.iloc[0]['avg_order_value'] or 0,
                'avg_response_time': system_result.iloc[0]['avg_response_time'] or 0
            }
            
        except Exception as e:
            print(f"Error getting key metrics: {str(e)}")
            return {
                'total_revenue': 0, 'revenue_change': 0, 'total_orders': 0, 'orders_change': 0,
                'active_users': 0, 'users_change': 0, 'avg_cpu': 0, 'cpu_change': 0,
                'avg_order_value': 0, 'avg_response_time': 0
            }
    
    def get_revenue_trend(self) -> pd.DataFrame:
        """Get revenue trend over time"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                datetime(order_date, 'start of hour') as hour,
                SUM(total_amount) as revenue,
                COUNT(DISTINCT order_id) as orders
            FROM sales_data
            WHERE datetime(order_date) >= datetime('now', '-24 hours')
            GROUP BY datetime(order_date, 'start of hour')
            ORDER BY hour
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if not result.empty:
                result['timestamp'] = pd.to_datetime(result['hour'])
                result = result.drop('hour', axis=1)
            
            return result
            
        except Exception as e:
            print(f"Error getting revenue trend: {str(e)}")
            return pd.DataFrame()
    
    def get_user_activity_trend(self) -> pd.DataFrame:
        """Get user activity trend over time"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                datetime(timestamp, 'start of hour') as hour,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_activities
            FROM user_activity
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY datetime(timestamp, 'start of hour')
            ORDER BY hour
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if not result.empty:
                result['timestamp'] = pd.to_datetime(result['hour'])
                result = result.drop('hour', axis=1)
            
            return result
            
        except Exception as e:
            print(f"Error getting user activity trend: {str(e)}")
            return pd.DataFrame()
    
    def get_system_metrics(self) -> pd.DataFrame:
        """Get system metrics over time"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                timestamp,
                AVG(cpu_usage) as cpu_usage,
                AVG(memory_usage) as memory_usage,
                AVG(response_time) as response_time
            FROM system_metrics
            WHERE datetime(timestamp) >= datetime('now', '-6 hours')
            GROUP BY timestamp
            ORDER BY timestamp
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if not result.empty:
                result['timestamp'] = pd.to_datetime(result['timestamp'])
            
            return result
            
        except Exception as e:
            print(f"Error getting system metrics: {str(e)}")
            return pd.DataFrame()
    
    def get_product_analysis(self, start_date, end_date) -> pd.DataFrame:
        """Get product performance analysis"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                product_name,
                SUM(total_amount) as total_revenue,
                SUM(quantity) as total_quantity,
                COUNT(DISTINCT order_id) as order_count,
                AVG(price) as avg_price,
                AVG(quantity) as avg_quantity_per_order
            FROM sales_data
            WHERE date(order_date) BETWEEN ? AND ?
            GROUP BY product_name
            ORDER BY total_revenue DESC
            """
            
            result = pd.read_sql_query(query, conn, params=[start_date, end_date])
            conn.close()
            
            if not result.empty:
                # Calculate additional metrics
                result['revenue_per_order'] = result['total_revenue'] / result['order_count']
                result['revenue_share'] = (result['total_revenue'] / result['total_revenue'].sum() * 100).round(2)
            
            return result
            
        except Exception as e:
            print(f"Error getting product analysis: {str(e)}")
            return pd.DataFrame()
    
    def get_customer_segments(self) -> pd.DataFrame:
        """Get customer segmentation data"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                customer_id,
                COUNT(DISTINCT order_id) as total_orders,
                SUM(total_amount) as total_spent,
                AVG(total_amount) as avg_order_value,
                MIN(order_date) as first_order,
                MAX(order_date) as last_order
            FROM sales_data
            GROUP BY customer_id
            HAVING COUNT(DISTINCT order_id) > 0
            ORDER BY total_spent DESC
            LIMIT 1000
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if not result.empty:
                # Calculate customer lifetime value and recency
                result['first_order'] = pd.to_datetime(result['first_order'])
                result['last_order'] = pd.to_datetime(result['last_order'])
                result['customer_lifetime'] = (result['last_order'] - result['first_order']).dt.days
                result['days_since_last_order'] = (datetime.now() - result['last_order']).dt.days
                
                # Simple customer segmentation
                def segment_customer(row):
                    if row['total_orders'] >= 5 and row['total_spent'] >= 1000:
                        return 'VIP'
                    elif row['total_orders'] >= 3 and row['total_spent'] >= 500:
                        return 'Loyal'
                    elif row['total_orders'] >= 2:
                        return 'Regular'
                    else:
                        return 'New'
                
                result['segment'] = result.apply(segment_customer, axis=1)
            
            return result
            
        except Exception as e:
            print(f"Error getting customer segments: {str(e)}")
            return pd.DataFrame()
    
    def get_hourly_patterns(self) -> pd.DataFrame:
        """Analyze hourly patterns in user activity and sales"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            # Sales patterns
            sales_query = """
            SELECT 
                CAST(strftime('%H', order_date) AS INTEGER) as hour,
                COUNT(*) as sales_count,
                SUM(total_amount) as sales_revenue
            FROM sales_data
            WHERE datetime(order_date) >= datetime('now', '-7 days')
            GROUP BY CAST(strftime('%H', order_date) AS INTEGER)
            ORDER BY hour
            """
            
            sales_result = pd.read_sql_query(sales_query, conn)
            
            # Activity patterns
            activity_query = """
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as activity_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_activity
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY CAST(strftime('%H', timestamp) AS INTEGER)
            ORDER BY hour
            """
            
            activity_result = pd.read_sql_query(activity_query, conn)
            conn.close()
            
            # Merge the results
            if not sales_result.empty and not activity_result.empty:
                result = pd.merge(sales_result, activity_result, on='hour', how='outer')
                result = result.fillna(0)
            elif not sales_result.empty:
                result = sales_result
                result['activity_count'] = 0
                result['unique_users'] = 0
            elif not activity_result.empty:
                result = activity_result
                result['sales_count'] = 0
                result['sales_revenue'] = 0
            else:
                result = pd.DataFrame()
            
            return result
            
        except Exception as e:
            print(f"Error getting hourly patterns: {str(e)}")
            return pd.DataFrame()
    
    def get_conversion_funnel(self) -> pd.DataFrame:
        """Analyze user conversion funnel"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            
            query = """
            SELECT 
                activity_type,
                COUNT(*) as activity_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_activity
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY activity_type
            ORDER BY activity_count DESC
            """
            
            result = pd.read_sql_query(query, conn)
            conn.close()
            
            if not result.empty:
                # Calculate conversion rates (simplified)
                total_users = result['unique_users'].max()
                result['conversion_rate'] = (result['unique_users'] / total_users * 100).round(2)
            
            return result
            
        except Exception as e:
            print(f"Error getting conversion funnel: {str(e)}")
            return pd.DataFrame()
    
    def detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in key metrics"""
        try:
            anomalies = []
            
            # Check revenue anomalies
            revenue_data = self.get_revenue_trend()
            if not revenue_data.empty and len(revenue_data) > 5:
                mean_revenue = revenue_data['revenue'].mean()
                std_revenue = revenue_data['revenue'].std()
                
                for _, row in revenue_data.iterrows():
                    if abs(row['revenue'] - mean_revenue) > 2 * std_revenue:
                        anomalies.append({
                            'type': 'revenue_anomaly',
                            'timestamp': row['timestamp'],
                            'value': row['revenue'],
                            'expected_range': f"{mean_revenue - 2*std_revenue:.2f} - {mean_revenue + 2*std_revenue:.2f}",
                            'severity': 'high' if abs(row['revenue'] - mean_revenue) > 3 * std_revenue else 'medium'
                        })
            
            # Check system performance anomalies
            system_data = self.get_system_metrics()
            if not system_data.empty:
                high_cpu_threshold = 90
                high_memory_threshold = 95
                
                high_cpu = system_data[system_data['cpu_usage'] > high_cpu_threshold]
                high_memory = system_data[system_data['memory_usage'] > high_memory_threshold]
                
                for _, row in high_cpu.iterrows():
                    anomalies.append({
                        'type': 'cpu_anomaly',
                        'timestamp': row['timestamp'],
                        'value': row['cpu_usage'],
                        'threshold': high_cpu_threshold,
                        'severity': 'high'
                    })
                
                for _, row in high_memory.iterrows():
                    anomalies.append({
                        'type': 'memory_anomaly',
                        'timestamp': row['timestamp'],
                        'value': row['memory_usage'],
                        'threshold': high_memory_threshold,
                        'severity': 'critical'
                    })
            
            return {
                'anomalies': anomalies,
                'total_count': len(anomalies),
                'high_severity_count': len([a for a in anomalies if a['severity'] in ['high', 'critical']])
            }
            
        except Exception as e:
            print(f"Error detecting anomalies: {str(e)}")
            return {'anomalies': [], 'total_count': 0, 'high_severity_count': 0}
