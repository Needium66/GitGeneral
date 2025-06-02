#The app config for the data analytics, integrating data ingestion

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import threading
import time
import json
from data_ingestion import DataIngestionManager
from data_quality import DataQualityMonitor
from analytics import AnalyticsEngine
from database import DatabaseManager
from utils import format_number, generate_alert_message

# Configure Streamlit page
st.set_page_config(
    page_title="Data Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
    st.session_state.ingestion_manager = DataIngestionManager(st.session_state.db_manager)
    st.session_state.quality_monitor = DataQualityMonitor(st.session_state.db_manager)
    st.session_state.analytics_engine = AnalyticsEngine(st.session_state.db_manager)
    st.session_state.last_update = datetime.now()
    st.session_state.auto_refresh = True
    st.session_state.refresh_interval = 30  # seconds

# Start background data ingestion if not already running
if 'ingestion_thread' not in st.session_state:
    def background_ingestion():
        while st.session_state.auto_refresh:
            try:
                st.session_state.ingestion_manager.simulate_data_ingestion()
                st.session_state.last_update = datetime.now()
                time.sleep(st.session_state.refresh_interval)
            except Exception as e:
                st.error(f"Background ingestion error: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    st.session_state.ingestion_thread = threading.Thread(target=background_ingestion, daemon=True)
    st.session_state.ingestion_thread.start()

# Main app title
st.title("📊 Real-Time Data Analytics Platform")

# Sidebar controls
st.sidebar.header("🔧 Platform Controls")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh Data", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh

# Refresh interval
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 10, 300, st.session_state.refresh_interval)
st.session_state.refresh_interval = refresh_interval

# Manual refresh button
if st.sidebar.button("🔄 Manual Refresh"):
    st.session_state.ingestion_manager.simulate_data_ingestion()
    st.session_state.last_update = datetime.now()
    st.rerun()

# Data source controls
st.sidebar.subheader("📡 Data Sources")
enable_sales = st.sidebar.checkbox("Sales Data", value=True)
enable_users = st.sidebar.checkbox("User Activity", value=True)
enable_system = st.sidebar.checkbox("System Metrics", value=True)

# Export controls
st.sidebar.subheader("📥 Export Data")
if st.sidebar.button("Export Sales Report"):
    sales_data = st.session_state.db_manager.get_sales_data()
    if not sales_data.empty:
        csv = sales_data.to_csv(index=False)
        st.sidebar.download_button(
            label="Download Sales CSV",
            data=csv,
            file_name=f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Status indicators
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🔄 Last Update", st.session_state.last_update.strftime("%H:%M:%S"))

with col2:
    total_records = st.session_state.db_manager.get_total_records()
    st.metric("📊 Total Records", format_number(total_records))

with col3:
    quality_score = st.session_state.quality_monitor.get_overall_quality_score()
    st.metric("✅ Data Quality", f"{quality_score:.1f}%")

with col4:
    active_alerts = len(st.session_state.quality_monitor.get_active_alerts())
    st.metric("🚨 Active Alerts", active_alerts)

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dashboard", "📊 Analytics", "🔍 Data Quality", "📡 Data Sources", "🚨 Alerts"])

with tab1:
    st.header("Real-Time Dashboard")
    
    # Key metrics row
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    analytics_data = st.session_state.analytics_engine.get_key_metrics()
    
    with metrics_col1:
        st.metric(
            "💰 Total Revenue", 
            f"${format_number(analytics_data.get('total_revenue', 0))}", 
            delta=f"{analytics_data.get('revenue_change', 0):+.1f}%"
        )
    
    with metrics_col2:
        st.metric(
            "🛒 Total Orders", 
            format_number(analytics_data.get('total_orders', 0)),
            delta=analytics_data.get('orders_change', 0)
        )
    
    with metrics_col3:
        st.metric(
            "👥 Active Users", 
            format_number(analytics_data.get('active_users', 0)),
            delta=analytics_data.get('users_change', 0)
        )
    
    with metrics_col4:
        st.metric(
            "⚡ System Load", 
            f"{analytics_data.get('avg_cpu', 0):.1f}%",
            delta=f"{analytics_data.get('cpu_change', 0):+.1f}%"
        )
    
    # Charts row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📈 Revenue Trend")
        revenue_data = st.session_state.analytics_engine.get_revenue_trend()
        if not revenue_data.empty:
            fig = px.line(
                revenue_data, 
                x='timestamp', 
                y='revenue',
                title="Revenue Over Time"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available yet")
    
    with chart_col2:
        st.subheader("👥 User Activity")
        user_data = st.session_state.analytics_engine.get_user_activity_trend()
        if not user_data.empty:
            fig = px.area(
                user_data, 
                x='timestamp', 
                y='active_users',
                title="Active Users Over Time"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user activity data available yet")
    
    # System metrics
    st.subheader("⚡ System Performance")
    system_col1, system_col2 = st.columns(2)
    
    with system_col1:
        system_data = st.session_state.analytics_engine.get_system_metrics()
        if not system_data.empty:
            fig = px.line(
                system_data, 
                x='timestamp', 
                y=['cpu_usage', 'memory_usage'],
                title="System Resource Usage"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No system metrics available yet")
    
    with system_col2:
        if not system_data.empty:
            latest_metrics = system_data.iloc[-1]
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = latest_metrics['cpu_usage'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Current CPU Usage"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("📊 Advanced Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.now().date())
    
    # Product performance analysis
    st.subheader("🏆 Product Performance")
    product_analysis = st.session_state.analytics_engine.get_product_analysis(start_date, end_date)
    
    if not product_analysis.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                product_analysis.head(10), 
                x='product_name', 
                y='total_revenue',
                title="Top 10 Products by Revenue"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                product_analysis.head(5), 
                values='total_revenue', 
                names='product_name',
                title="Revenue Distribution (Top 5)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Product performance table
        st.subheader("📋 Detailed Product Metrics")
        st.dataframe(
            product_analysis.head(20), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No product data available for the selected date range")
    
    # Customer segmentation
    st.subheader("👥 Customer Insights")
    customer_data = st.session_state.analytics_engine.get_customer_segments()
    
    if not customer_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(
                customer_data, 
                x='total_orders', 
                y='total_spent',
                size='avg_order_value',
                title="Customer Segmentation"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Customer value distribution
            fig = px.histogram(
                customer_data, 
                x='total_spent', 
                nbins=20,
                title="Customer Value Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("🔍 Data Quality Monitoring")
    
    # Quality overview
    quality_metrics = st.session_state.quality_monitor.get_quality_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Completeness", 
            f"{quality_metrics.get('completeness', 0):.1f}%",
            delta=f"{quality_metrics.get('completeness_change', 0):+.1f}%"
        )
    
    with col2:
        st.metric(
            "✅ Validity", 
            f"{quality_metrics.get('validity', 0):.1f}%",
            delta=f"{quality_metrics.get('validity_change', 0):+.1f}%"
        )
    
    with col3:
        st.metric(
            "🎯 Accuracy", 
            f"{quality_metrics.get('accuracy', 0):.1f}%",
            delta=f"{quality_metrics.get('accuracy_change', 0):+.1f}%"
        )
    
    with col4:
        st.metric(
            "⏱️ Timeliness", 
            f"{quality_metrics.get('timeliness', 0):.1f}%",
            delta=f"{quality_metrics.get('timeliness_change', 0):+.1f}%"
        )
    
    # Quality trend charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Quality Score Trends")
        quality_trends = st.session_state.quality_monitor.get_quality_trends()
        if not quality_trends.empty:
            fig = px.line(
                quality_trends, 
                x='timestamp', 
                y=['completeness', 'validity', 'accuracy', 'timeliness'],
                title="Data Quality Metrics Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No quality trend data available yet")
    
    with col2:
        st.subheader("🚨 Quality Issues by Type")
        issue_summary = st.session_state.quality_monitor.get_issue_summary()
        if not issue_summary.empty:
            fig = px.bar(
                issue_summary, 
                x='issue_type', 
                y='count',
                title="Data Quality Issues"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No quality issues detected")
    
    # Detailed quality checks
    st.subheader("🔍 Detailed Quality Checks")
    
    # Run quality checks button
    if st.button("🔄 Run Quality Checks"):
        with st.spinner("Running quality checks..."):
            results = st.session_state.quality_monitor.run_comprehensive_checks()
            st.success("Quality checks completed!")
            
            for table_name, checks in results.items():
                with st.expander(f"📋 {table_name.title()} Data Checks"):
                    for check_name, result in checks.items():
                        if result['passed']:
                            st.success(f"✅ {check_name}: {result['message']}")
                        else:
                            st.error(f"❌ {check_name}: {result['message']}")

with tab4:
    st.header("📡 Data Sources Management")
    
    # Data source status
    st.subheader("🔌 Source Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**💰 Sales Data**")
        sales_status = st.session_state.ingestion_manager.get_source_status('sales')
        st.write(f"Status: {'🟢 Active' if sales_status['active'] else '🔴 Inactive'}")
        st.write(f"Last Update: {sales_status['last_update']}")
        st.write(f"Records: {sales_status['record_count']}")
    
    with col2:
        st.info("**👥 User Activity**")
        user_status = st.session_state.ingestion_manager.get_source_status('users')
        st.write(f"Status: {'🟢 Active' if user_status['active'] else '🔴 Inactive'}")
        st.write(f"Last Update: {user_status['last_update']}")
        st.write(f"Records: {user_status['record_count']}")
    
    with col3:
        st.info("**⚡ System Metrics**")
        system_status = st.session_state.ingestion_manager.get_source_status('system')
        st.write(f"Status: {'🟢 Active' if system_status['active'] else '🔴 Inactive'}")
        st.write(f"Last Update: {system_status['last_update']}")
        st.write(f"Records: {system_status['record_count']}")
    
    # Data ingestion controls
    st.subheader("🎛️ Ingestion Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Sales Data"):
            st.session_state.ingestion_manager.ingest_sales_data()
            st.success("Sales data refreshed!")
    
    with col2:
        if st.button("🔄 Refresh User Data"):
            st.session_state.ingestion_manager.ingest_user_activity()
            st.success("User activity data refreshed!")
    
    with col3:
        if st.button("🔄 Refresh System Data"):
            st.session_state.ingestion_manager.ingest_system_metrics()
            st.success("System metrics refreshed!")
    
    # Recent data preview
    st.subheader("👀 Recent Data Preview")
    
    preview_source = st.selectbox("Select data source to preview:", ["Sales", "User Activity", "System Metrics"])
    
    if preview_source == "Sales":
        recent_data = st.session_state.db_manager.get_recent_sales_data(10)
    elif preview_source == "User Activity":
        recent_data = st.session_state.db_manager.get_recent_user_data(10)
    else:
        recent_data = st.session_state.db_manager.get_recent_system_data(10)
    
    if not recent_data.empty:
        st.dataframe(recent_data, use_container_width=True, hide_index=True)
    else:
        st.info(f"No recent {preview_source.lower()} data available")

with tab5:
    st.header("🚨 Alert Management")
    
    # Active alerts
    active_alerts = st.session_state.quality_monitor.get_active_alerts()
    
    if active_alerts:
        st.subheader("🔴 Active Alerts")
        
        for alert in active_alerts:
            alert_type = alert.get('type', 'Unknown')
            severity = alert.get('severity', 'medium')
            message = alert.get('message', 'No message available')
            timestamp = alert.get('timestamp', 'Unknown time')
            
            # Color code by severity
            if severity == 'high':
                st.error(f"🔴 **{alert_type}** - {message} (at {timestamp})")
            elif severity == 'medium':
                st.warning(f"🟡 **{alert_type}** - {message} (at {timestamp})")
            else:
                st.info(f"🔵 **{alert_type}** - {message} (at {timestamp})")
    else:
        st.success("🟢 No active alerts - all systems operating normally!")
    
    # Alert configuration
    st.subheader("⚙️ Alert Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Quality Thresholds**")
        completeness_threshold = st.slider("Completeness Alert Threshold (%)", 0, 100, 85)
        validity_threshold = st.slider("Validity Alert Threshold (%)", 0, 100, 90)
        
    with col2:
        st.write("**System Thresholds**")
        cpu_threshold = st.slider("CPU Usage Alert Threshold (%)", 0, 100, 80)
        memory_threshold = st.slider("Memory Usage Alert Threshold (%)", 0, 100, 85)
    
    # Alert history
    st.subheader("📚 Alert History")
    
    alert_history = st.session_state.quality_monitor.get_alert_history()
    
    if not alert_history.empty:
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity_filter = st.selectbox("Filter by Severity:", ["All", "High", "Medium", "Low"])
        
        with col2:
            type_filter = st.selectbox("Filter by Type:", ["All", "Data Quality", "System", "Business"])
        
        with col3:
            days_back = st.selectbox("Show alerts from last:", ["1 day", "7 days", "30 days", "All time"])
        
        # Apply filters
        filtered_history = alert_history.copy()
        
        if severity_filter != "All":
            filtered_history = filtered_history[filtered_history['severity'].str.title() == severity_filter]
        
        if type_filter != "All":
            filtered_history = filtered_history[filtered_history['type'].str.contains(type_filter.replace(" ", "_").lower())]
        
        if days_back != "All time":
            days = int(days_back.split()[0])
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_history = filtered_history[pd.to_datetime(filtered_history['timestamp']) >= cutoff_date]
        
        st.dataframe(filtered_history, use_container_width=True, hide_index=True)
    else:
        st.info("No alert history available")

# Footer
st.markdown("---")
st.markdown("*Data Analytics Platform - Real-time monitoring and analytics dashboard*")
