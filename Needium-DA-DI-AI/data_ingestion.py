#The configs for data ingestion

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sqlite3
from typing import Dict, Any
import threading
import time

class DataIngestionManager:
    """Manages simulated real-time data ingestion from multiple sources"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.product_names = [
            "Wireless Headphones", "Smartphone", "Laptop", "Tablet", "Smart Watch",
            "Gaming Console", "Bluetooth Speaker", "Camera", "Monitor", "Keyboard",
            "Mouse", "Charger", "Phone Case", "Screen Protector", "USB Cable",
            "External Hard Drive", "Memory Card", "Power Bank", "Webcam", "Microphone"
        ]
        self.user_agents = [
            "Chrome", "Firefox", "Safari", "Edge", "Opera"
        ]
        self.locations = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
            "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
        ]
        
    def simulate_data_ingestion(self):
        """Simulate real-time data ingestion from all sources"""
        try:
            self.ingest_sales_data()
            self.ingest_user_activity()
            self.ingest_system_metrics()
        except Exception as e:
            print(f"Error in data ingestion: {str(e)}")
    
    def ingest_sales_data(self):
        """Generate and ingest simulated sales data"""
        try:
            # Generate 5-15 sales records
            num_records = random.randint(5, 15)
            sales_data = []
            
            base_time = datetime.now()
            
            for i in range(num_records):
                # Create realistic sales data
                product = random.choice(self.product_names)
                quantity = random.randint(1, 5)
                
                # Price based on product type with some randomness
                base_prices = {
                    "Smartphone": 699, "Laptop": 999, "Tablet": 399, "Gaming Console": 499,
                    "Wireless Headphones": 199, "Smart Watch": 299, "Camera": 799,
                    "Monitor": 349, "Bluetooth Speaker": 99, "Keyboard": 79,
                    "Mouse": 49, "Charger": 29, "Phone Case": 19, "Screen Protector": 15,
                    "USB Cable": 12, "External Hard Drive": 129, "Memory Card": 39,
                    "Power Bank": 59, "Webcam": 89, "Microphone": 159
                }
                
                base_price = base_prices.get(product, 99)
                # Add ±20% randomness to price
                price = base_price * random.uniform(0.8, 1.2)
                
                order_time = base_time - timedelta(
                    seconds=random.randint(0, 3600)  # Within last hour
                )
                
                sales_data.append({
                    'order_id': f"ORD{random.randint(100000, 999999)}",
                    'product_name': product,
                    'quantity': quantity,
                    'price': round(price, 2),
                    'total_amount': round(price * quantity, 2),
                    'customer_id': f"CUST{random.randint(1000, 9999)}",
                    'order_date': order_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'location': random.choice(self.locations),
                    'payment_method': random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Apple Pay']),
                    'status': random.choice(['Completed', 'Pending', 'Processing'])
                })
            
            sales_df = pd.DataFrame(sales_data)
            self.db_manager.insert_sales_data(sales_df)
            
        except Exception as e:
            print(f"Error ingesting sales data: {str(e)}")
    
    def ingest_user_activity(self):
        """Generate and ingest simulated user activity data"""
        try:
            # Generate 10-30 user activity records
            num_records = random.randint(10, 30)
            activity_data = []
            
            base_time = datetime.now()
            
            for i in range(num_records):
                activity_time = base_time - timedelta(
                    seconds=random.randint(0, 3600)  # Within last hour
                )
                
                activity_data.append({
                    'user_id': f"USER{random.randint(1000, 9999)}",
                    'session_id': f"SESS{random.randint(100000, 999999)}",
                    'activity_type': random.choice([
                        'page_view', 'product_view', 'add_to_cart', 'checkout_start',
                        'checkout_complete', 'search', 'filter', 'login', 'logout'
                    ]),
                    'page_url': f"/products/{random.choice(self.product_names).lower().replace(' ', '-')}",
                    'user_agent': random.choice(self.user_agents),
                    'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    'location': random.choice(self.locations),
                    'timestamp': activity_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'session_duration': random.randint(30, 1800),  # 30 seconds to 30 minutes
                    'device_type': random.choice(['Desktop', 'Mobile', 'Tablet'])
                })
            
            activity_df = pd.DataFrame(activity_data)
            self.db_manager.insert_user_activity(activity_df)
            
        except Exception as e:
            print(f"Error ingesting user activity data: {str(e)}")
    
    def ingest_system_metrics(self):
        """Generate and ingest simulated system metrics"""
        try:
            # Generate system metrics for the last few minutes
            num_records = random.randint(3, 8)
            metrics_data = []
            
            base_time = datetime.now()
            
            # Simulate some trending in metrics
            base_cpu = random.uniform(20, 80)
            base_memory = random.uniform(30, 85)
            base_disk = random.uniform(10, 70)
            
            for i in range(num_records):
                metric_time = base_time - timedelta(
                    minutes=i * 2  # Every 2 minutes
                )
                
                # Add small random variations to create realistic trends
                cpu_usage = max(0, min(100, base_cpu + random.uniform(-10, 10)))
                memory_usage = max(0, min(100, base_memory + random.uniform(-5, 5)))
                disk_usage = max(0, min(100, base_disk + random.uniform(-2, 2)))
                
                metrics_data.append({
                    'server_id': random.choice(['WEB-01', 'WEB-02', 'API-01', 'DB-01', 'CACHE-01']),
                    'cpu_usage': round(cpu_usage, 2),
                    'memory_usage': round(memory_usage, 2),
                    'disk_usage': round(disk_usage, 2),
                    'network_in': round(random.uniform(1, 100), 2),  # MB/s
                    'network_out': round(random.uniform(1, 50), 2),  # MB/s
                    'response_time': round(random.uniform(50, 500), 2),  # milliseconds
                    'error_rate': round(random.uniform(0, 5), 3),  # percentage
                    'timestamp': metric_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': random.choice(['healthy', 'warning', 'critical']) if random.random() < 0.1 else 'healthy'
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            self.db_manager.insert_system_metrics(metrics_df)
            
        except Exception as e:
            print(f"Error ingesting system metrics: {str(e)}")
    
    def get_source_status(self, source_type: str) -> Dict[str, Any]:
        """Get status information for a specific data source"""
        try:
            if source_type == 'sales':
                record_count = self.db_manager.get_table_count('sales_data')
                last_update = self.db_manager.get_last_update_time('sales_data')
            elif source_type == 'users':
                record_count = self.db_manager.get_table_count('user_activity')
                last_update = self.db_manager.get_last_update_time('user_activity')
            elif source_type == 'system':
                record_count = self.db_manager.get_table_count('system_metrics')
                last_update = self.db_manager.get_last_update_time('system_metrics')
            else:
                return {'active': False, 'last_update': 'Unknown', 'record_count': 0}
            
            # Consider source active if updated within last 5 minutes
            is_active = False
            if last_update:
                try:
                    last_update_dt = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
                    is_active = (datetime.now() - last_update_dt).total_seconds() < 300
                except:
                    pass
            
            return {
                'active': is_active,
                'last_update': last_update or 'Never',
                'record_count': record_count
            }
            
        except Exception as e:
            print(f"Error getting source status: {str(e)}")
            return {'active': False, 'last_update': 'Error', 'record_count': 0}
