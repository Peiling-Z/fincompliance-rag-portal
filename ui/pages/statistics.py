"""
Statistics and Data Visualization Page
"""
import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# API Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Set page config
st.set_page_config(page_title="Statistics - FinCompliance RAG", layout="wide")

# Page title
st.title("📊 Statistics & Analytics Dashboard")

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    
    # Date range filter
    date_range = st.selectbox(
        "Time Range",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom"]
    )
    
    start_date = None
    end_date = None
    
    if date_range == "Last 7 Days":
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
    elif date_range == "Last 30 Days":
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
    elif date_range == "Last 90 Days":
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
    elif date_range == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date_input = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            start_date = start_date_input.strftime("%Y-%m-%d")
        with col2:
            end_date_input = st.date_input("End Date", datetime.now())
            end_date = end_date_input.strftime("%Y-%m-%d")
    
    # Refresh button
    refresh = st.button("🔄 Refresh Data", use_container_width=True)


def fetch_statistics(endpoint, params=None):
    """Fetch statistics from API"""
    try:
        # TODO: Add authentication headers when auth is implemented
        response = requests.get(f"{API_URL}/api/v1/statistics/{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("🔒 Authentication required. Please log in.")
            return None
        else:
            st.error(f"❌ Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")
        return None


# Fetch data
params = {}
if start_date:
    params["start_date"] = start_date
if end_date:
    params["end_date"] = end_date

# Dashboard Overview Section
st.header("📈 Overview")

dashboard_data = fetch_statistics("dashboard")

if dashboard_data:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📄 Total Documents",
            value=dashboard_data.get("total_documents", 0),
            delta=f"+{dashboard_data.get('recent_documents_7d', 0)} this week"
        )
    
    with col2:
        st.metric(
            label="✅ Processed Documents",
            value=dashboard_data.get("processed_documents", 0)
        )
    
    with col3:
        st.metric(
            label="💬 Total Queries",
            value=dashboard_data.get("total_queries", 0),
            delta=f"+{dashboard_data.get('recent_queries_7d', 0)} this week"
        )
    
    with col4:
        avg_time = dashboard_data.get("average_response_time_ms", 0)
        st.metric(
            label="⚡ Avg Response Time",
            value=f"{avg_time:.0f} ms"
        )

st.divider()

# Document Statistics Section
st.header("📚 Document Statistics")

doc_stats = fetch_statistics("documents", params)

if doc_stats:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Document Status Distribution")
        
        # Prepare data for pie chart
        status_data = doc_stats.get("status_distribution", {})
        if sum(status_data.values()) > 0:
            df_status = pd.DataFrame({
                "Status": list(status_data.keys()),
                "Count": list(status_data.values())
            })
            
            # Create pie chart
            fig = px.pie(
                df_status,
                values="Count",
                names="Status",
                title="Document Processing Status",
                color="Status",
                color_discrete_map={
                    "uploaded": "#FFA500",
                    "processing": "#1E90FF",
                    "processed": "#32CD32",
                    "failed": "#DC143C"
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No documents found for the selected time range.")
    
    with col2:
        st.subheader("Document Metrics")
        
        # Display metrics
        total_docs = doc_stats.get("total_documents", 0)
        total_chunks = doc_stats.get("total_chunks", 0)
        avg_size_bytes = doc_stats.get("average_file_size_bytes", 0)
        avg_size_mb = avg_size_bytes / (1024 * 1024)
        
        st.metric("Total Documents", total_docs)
        st.metric("Total Chunks", total_chunks)
        st.metric("Average File Size", f"{avg_size_mb:.2f} MB")
        
        if total_docs > 0:
            avg_chunks_per_doc = total_chunks / total_docs
            st.metric("Avg Chunks per Document", f"{avg_chunks_per_doc:.1f}")
    
    # Documents over time chart
    st.subheader("Documents Uploaded Over Time")
    
    docs_over_time = doc_stats.get("documents_over_time", [])
    if docs_over_time:
        df_docs_time = pd.DataFrame(docs_over_time)
        df_docs_time['date'] = pd.to_datetime(df_docs_time['date'])
        
        # Create line chart
        fig = px.line(
            df_docs_time,
            x="date",
            y="count",
            title="Daily Document Upload Activity",
            labels={"date": "Date", "count": "Documents Uploaded"},
            markers=True
        )
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No document activity data available for the selected time range.")

st.divider()

# Query Statistics Section
st.header("💬 Query Statistics")

query_stats = fetch_statistics("queries", params)

if query_stats:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Response Time Metrics")
        
        total_queries = query_stats.get("total_queries", 0)
        avg_time = query_stats.get("average_response_time_ms", 0)
        min_time = query_stats.get("min_response_time_ms", 0)
        max_time = query_stats.get("max_response_time_ms", 0)
        
        if total_queries > 0:
            # Create gauge chart for average response time
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_time,
                title={'text': "Average Response Time (ms)"},
                delta={'reference': 1000},
                gauge={
                    'axis': {'range': [None, max(max_time, 2000)]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 500], 'color': "lightgreen"},
                        {'range': [500, 1000], 'color': "yellow"},
                        {'range': [1000, max(max_time, 2000)], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 1000
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # Display min/max metrics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Min Response Time", f"{min_time:.0f} ms")
            with col_b:
                st.metric("Max Response Time", f"{max_time:.0f} ms")
        else:
            st.info("No query data available for the selected time range.")
    
    with col2:
        st.subheader("Query Volume")
        
        # Bar chart for query count
        st.metric("Total Queries", total_queries)
        
        queries_over_time = query_stats.get("queries_over_time", [])
        if queries_over_time:
            df_queries_time = pd.DataFrame(queries_over_time)
            df_queries_time['date'] = pd.to_datetime(df_queries_time['date'])
            
            # Create bar chart
            fig = px.bar(
                df_queries_time,
                x="date",
                y="count",
                title="Daily Query Activity",
                labels={"date": "Date", "count": "Queries Submitted"},
                color="count",
                color_continuous_scale="Blues"
            )
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
    
    # Combined chart: Queries and Response Time
    st.subheader("Query Activity & Response Times")
    
    queries_over_time = query_stats.get("queries_over_time", [])
    if queries_over_time:
        df_queries_time = pd.DataFrame(queries_over_time)
        df_queries_time['date'] = pd.to_datetime(df_queries_time['date'])
        
        # Create dual-axis chart
        fig = go.Figure()
        
        # Add query count bars
        fig.add_trace(go.Bar(
            x=df_queries_time['date'],
            y=df_queries_time['count'],
            name='Query Count',
            marker_color='#1E90FF',
            yaxis='y'
        ))
        
        # Add response time line
        fig.add_trace(go.Scatter(
            x=df_queries_time['date'],
            y=df_queries_time['avg_response_time_ms'],
            name='Avg Response Time (ms)',
            line=dict(color='#FF6347', width=2),
            yaxis='y2'
        ))
        
        # Update layout with dual y-axes
        fig.update_layout(
            title='Daily Query Volume and Average Response Time',
            xaxis=dict(title='Date'),
            yaxis=dict(
                title='Query Count',
                side='left'
            ),
            yaxis2=dict(
                title='Response Time (ms)',
                side='right',
                overlaying='y'
            ),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Footer
st.caption("📊 Statistics are updated in real-time based on your activity.")
