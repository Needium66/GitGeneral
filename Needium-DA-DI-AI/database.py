#The configs for the database

import sqlite3
import pandas as pd
from datetime import datetime
import os
from typing import Optional

class DatabaseManager:
    """Manages SQLite database operations for the analytics platform"""
    
    def __init__(self, db_path: str = "analytics_platform.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sales data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            customer_id TEXT NOT NULL,
            order_date TEXT NOT NULL,
            location TEXT,
            payment_method TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # User activity table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            page_url TEXT,
            user_agent TEXT,
            ip_address TEXT,
            location TEXT,
            timestamp TEXT NOT NULL,
            session_duration INTEGER,
            device_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # System metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            cpu_usage REAL NOT NULL,
            memory_usage REAL NOT NULL,
            disk_usage REAL NOT NULL,
            network_in REAL,
            network_out REAL,
            response_time REAL,
            error_rate REAL,
            timestamp TEXT NOT NULL,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Data quality metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            metric_value REAL NOT NULL,
            threshold_value REAL,
            passed BOOLEAN NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Alerts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            source_table TEXT,
            metric_value REAL,
            threshold_value REAL,
            timestamp TEXT NOT NULL,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales_data(order_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales_data(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_data(product_name)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_type ON user_activity(activity_type)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_server ON system_metrics(server_id)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_timestamp ON quality_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        conn.commit()
        conn.close()
    
    def insert_sales_data(self, df: pd.DataFrame):
        """Insert sales data into the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql('sales_data', conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            print(f"Error inserting sales data: {str(e)}")
    
    def insert_user_activity(self, df: pd.DataFrame):
        """Insert user activity data into the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql('user_activity', conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            print(f"Error inserting user activity data: {str(e)}")
    
    def insert_system_metrics(self, df: pd.DataFrame):
        """Insert system metrics data into the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql('system_metrics', conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            print(f"Error inserting system metrics data: {str(e)}")
    
    def insert_quality_metric(self, table_name: str, metric_type: str, 
                            metric_value: float, threshold_value: float, passed: bool):
        """Insert a quality metric record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO quality_metrics 
            (table_name, metric_type, metric_value, threshold_value, passed, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (table_name, metric_type, metric_value, threshold_value, passed, 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error inserting quality metric: {str(e)}")
    
    def insert_alert(self, alert_type: str, severity: str, message: str, 
                    source_table: str = None, metric_value: float = None, 
                    threshold_value: float = None):
        """Insert an alert record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO alerts 
            (alert_type, severity, message, source_table, metric_value, threshold_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alert_type, severity, message, source_table, metric_value, threshold_value,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error inserting alert: {str(e)}")
    
    def get_sales_data(self, limit: int = None) -> pd.DataFrame:
        """Get sales data from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM sales_data ORDER BY order_date DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting sales data: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_sales_data(self, limit: int = 10) -> pd.DataFrame:
        """Get recent sales data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT order_id, product_name, quantity, price, total_amount, 
                   customer_id, order_date, location, status
            FROM sales_data 
            ORDER BY order_date DESC 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting recent sales data: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_user_data(self, limit: int = 10) -> pd.DataFrame:
        """Get recent user activity data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT user_id, activity_type, page_url, location, 
                   timestamp, device_type
            FROM user_activity 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting recent user data: {str(e)}")
            return pd.DataFrame()
    
    def get_recent_system_data(self, limit: int = 10) -> pd.DataFrame:
        """Get recent system metrics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT server_id, cpu_usage, memory_usage, disk_usage, 
                   response_time, timestamp, status
            FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting recent system data: {str(e)}")
            return pd.DataFrame()
    
    def get_table_count(self, table_name: str) -> int:
        """Get total record count for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except Exception as e:
            print(f"Error getting table count for {table_name}: {str(e)}")
            return 0
    
    def get_total_records(self) -> int:
        """Get total records across all main tables"""
        try:
            sales_count = self.get_table_count('sales_data')
            activity_count = self.get_table_count('user_activity')
            metrics_count = self.get_table_count('system_metrics')
            
            return sales_count + activity_count + metrics_count
        except Exception as e:
            print(f"Error getting total records: {str(e)}")
            return 0
    
    def get_last_update_time(self, table_name: str) -> Optional[str]:
        """Get the last update time for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if table_name == 'sales_data':
                cursor.execute("SELECT MAX(order_date) FROM sales_data")
            elif table_name == 'user_activity':
                cursor.execute("SELECT MAX(timestamp) FROM user_activity")
            elif table_name == 'system_metrics':
                cursor.execute("SELECT MAX(timestamp) FROM system_metrics")
            else:
                return None
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error getting last update time for {table_name}: {str(e)}")
            return None
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage database size"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Clean old sales data
            cursor.execute("""
            DELETE FROM sales_data 
            WHERE datetime(order_date) < datetime(?, '-{} days')
            """.format(days_to_keep), (cutoff_date,))
            
            # Clean old user activity
            cursor.execute("""
            DELETE FROM user_activity 
            WHERE datetime(timestamp) < datetime(?, '-{} days')
            """.format(days_to_keep), (cutoff_date,))
            
            # Clean old system metrics
            cursor.execute("""
            DELETE FROM system_metrics 
            WHERE datetime(timestamp) < datetime(?, '-{} days')
            """.format(days_to_keep), (cutoff_date,))
            
            # Clean old quality metrics
            cursor.execute("""
            DELETE FROM quality_metrics 
            WHERE datetime(timestamp) < datetime(?, '-{} days')
            """.format(days_to_keep), (cutoff_date,))
            
            # Clean old resolved alerts
            cursor.execute("""
            DELETE FROM alerts 
            WHERE datetime(timestamp) < datetime(?, '-{} days') AND resolved = TRUE
            """.format(days_to_keep), (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            print(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            print(f"Error cleaning up old data: {str(e)}")
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            stats = {
                'sales_records': self.get_table_count('sales_data'),
                'activity_records': self.get_table_count('user_activity'),
                'metrics_records': self.get_table_count('system_metrics'),
                'quality_records': self.get_table_count('quality_metrics'),
                'alert_records': self.get_table_count('alerts'),
                'database_size_mb': round(os.path.getsize(self.db_path) / (1024 * 1024), 2) if os.path.exists(self.db_path) else 0
            }
            
            stats['total_records'] = (
                stats['sales_records'] + 
                stats['activity_records'] + 
                stats['metrics_records']
            )
            
            return stats
        except Exception as e:
            print(f"Error getting database stats: {str(e)}")
            return {}
