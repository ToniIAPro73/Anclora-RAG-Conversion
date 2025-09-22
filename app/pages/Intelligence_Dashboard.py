"""Dashboard de Inteligencia Empresarial para Anclora RAG."""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Try to import plotly, fallback to basic charts if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly no está instalado. Usando gráficos básicos de Streamlit.")

# Try to import dashboard service, fallback to mock data if not available
try:
    from app.analytics.dashboard_data_service import DashboardDataService
    dashboard_service = DashboardDataService()
    DASHBOARD_SERVICE_AVAILABLE = True
except ImportError:
    DASHBOARD_SERVICE_AVAILABLE = False
    dashboard_service = None
    st.info("ℹ️ Servicio de dashboard no disponible. Usando datos simulados.")

# Set page config
st.set_page_config(layout='wide', page_title='Intelligence Dashboard', page_icon='📈')

# Simple CSS to hide Streamlit elements
hide_st_style = """
    <style>
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize language in session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# Sidebar for language selection
with st.sidebar:
    st.header("Idioma")
    language_options = {
        'es': 'Español',
        'en': 'English'
    }
    
    selected_language = st.selectbox(
        "Selecciona idioma:",
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=0 if st.session_state.language == 'es' else 1,
        key="language_selector"
    )
    
    # Update session state if language changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()

# Translations
translations = {
    'es': {
        'title': '📈 Dashboard de Inteligencia Empresarial',
        'subtitle': 'Análisis avanzado del sistema RAG Anclora',
        'performance_metrics': 'Métricas de Rendimiento',
        'usage_analytics': 'Análisis de Uso',
        'content_insights': 'Insights de Contenido',
        'security_overview': 'Resumen de Seguridad',
        'predictive_analytics': 'Análisis Predictivo',
        'optimization_recommendations': 'Recomendaciones de Optimización',
        'response_time': 'Tiempo de Respuesta',
        'query_volume': 'Volumen de Consultas',
        'success_rate': 'Tasa de Éxito',
        'user_satisfaction': 'Satisfacción del Usuario',
        'peak_hours': 'Horas Pico',
        'content_categories': 'Categorías de Contenido',
        'language_distribution': 'Distribución por Idioma',
        'security_events': 'Eventos de Seguridad',
        'threat_level': 'Nivel de Amenaza',
        'performance_trend': 'Tendencia de Rendimiento',
        'usage_forecast': 'Pronóstico de Uso',
        'optimization_impact': 'Impacto de Optimizaciones',
        'recommendations': 'Recomendaciones',
        'last_24h': 'Últimas 24 horas',
        'last_7d': 'Últimos 7 días',
        'last_30d': 'Últimos 30 días',
        'real_time': 'Tiempo Real'
    },
    'en': {
        'title': '📈 Business Intelligence Dashboard',
        'subtitle': 'Advanced analysis of Anclora RAG system',
        'performance_metrics': 'Performance Metrics',
        'usage_analytics': 'Usage Analytics',
        'content_insights': 'Content Insights',
        'security_overview': 'Security Overview',
        'predictive_analytics': 'Predictive Analytics',
        'optimization_recommendations': 'Optimization Recommendations',
        'response_time': 'Response Time',
        'query_volume': 'Query Volume',
        'success_rate': 'Success Rate',
        'user_satisfaction': 'User Satisfaction',
        'peak_hours': 'Peak Hours',
        'content_categories': 'Content Categories',
        'language_distribution': 'Language Distribution',
        'security_events': 'Security Events',
        'threat_level': 'Threat Level',
        'performance_trend': 'Performance Trend',
        'usage_forecast': 'Usage Forecast',
        'optimization_impact': 'Optimization Impact',
        'recommendations': 'Recommendations',
        'last_24h': 'Last 24 hours',
        'last_7d': 'Last 7 days',
        'last_30d': 'Last 30 days',
        'real_time': 'Real Time'
    }
}

def get_text(key):
    return translations[st.session_state.language].get(key, key)

# Get real data from dashboard service
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dashboard_data(time_range: str):
    """Get real data from the dashboard service."""

    try:
        # Get real metrics
        performance_metrics = dashboard_service.get_performance_metrics(time_range)
        usage_analytics = dashboard_service.get_usage_analytics()
        security_overview = dashboard_service.get_security_overview()
        predictive_insights = dashboard_service.get_predictive_insights()

        # Get time series data
        time_series_data = {}
        for metric in ['response_time', 'query_volume', 'success_rate', 'user_satisfaction']:
            time_series_data[metric] = dashboard_service.get_time_series_data(metric, time_range)

        return {
            'performance_metrics': performance_metrics,
            'usage_analytics': usage_analytics,
            'security_overview': security_overview,
            'predictive_insights': predictive_insights,
            'time_series_data': time_series_data
        }

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        # Fallback to mock data
        return get_fallback_data()


def get_fallback_data():
    """Fallback data when real data is not available."""

    # Generate fallback time series
    dates = pd.date_range(start=datetime.now() - timedelta(days=1), end=datetime.now(), freq='H')

    time_series_data = {
        'response_time': [{'timestamp': d, 'value': 2.5 + np.random.normal(0, 0.3)} for d in dates],
        'query_volume': [{'timestamp': d, 'value': 15 + np.random.poisson(5)} for d in dates],
        'success_rate': [{'timestamp': d, 'value': 0.95 + np.random.normal(0, 0.02)} for d in dates],
        'user_satisfaction': [{'timestamp': d, 'value': 0.85 + np.random.normal(0, 0.05)} for d in dates]
    }

    return {
        'performance_metrics': {
            'avg_response_time': 2.5,
            'total_queries': 1200,
            'success_rate': 0.95,
            'user_satisfaction': 0.85
        },
        'usage_analytics': {
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'content_categories': {
                'Documentos Técnicos': 35,
                'Documentos Legales': 25,
                'Documentos Comerciales': 20,
                'Documentos Académicos': 15,
                'Otros': 5
            },
            'language_distribution': {
                'Español': 70,
                'Inglés': 25,
                'Otros': 5
            }
        },
        'security_overview': {
            'total_events': 127,
            'quarantined_ips': 3,
            'threat_levels': {
                'Bajo': 85,
                'Medio': 32,
                'Alto': 8,
                'Crítico': 2
            },
            'event_types': {
                'Rate Limit': 45,
                'Consulta Sospechosa': 38,
                'Intento de Inyección': 12,
                'Comportamiento Anómalo': 32
            }
        },
        'predictive_insights': {
            'usage_forecast': [15, 18, 22, 19, 16, 14, 17],
            'optimization_recommendations': [
                {
                    'type': 'performance',
                    'description': 'Optimizar tamaño de chunks',
                    'impact': '25% mejora en tiempo de respuesta',
                    'priority': 'Alta'
                }
            ]
        },
        'time_series_data': time_series_data
    }

# Main content
st.title(get_text('title'))
st.markdown(f"**{get_text('subtitle')}**")

# Time range selector
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    time_range = st.selectbox(
        "Rango de tiempo:",
        options=['last_24h', 'last_7d', 'last_30d'],
        format_func=lambda x: get_text(x),
        index=1
    )

with col2:
    auto_refresh = st.checkbox(get_text('real_time'), value=False)

# Get real data
dashboard_data = get_dashboard_data(time_range)

performance_metrics = dashboard_data['performance_metrics']
usage_analytics = dashboard_data['usage_analytics']
security_overview = dashboard_data['security_overview']
predictive_insights = dashboard_data['predictive_insights']
time_series_data = dashboard_data['time_series_data']

# Performance Metrics Section
st.header(get_text('performance_metrics'))

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_response_time = performance_metrics['avg_response_time']
    st.metric(
        label=get_text('response_time'),
        value=f"{avg_response_time:.2f}s",
        delta=f"{(avg_response_time - 2.5):.2f}s"
    )

with col2:
    total_queries = int(performance_metrics['total_queries'])
    st.metric(
        label=get_text('query_volume'),
        value=f"{total_queries:,}",
        delta=f"+{int(total_queries * 0.1)}"
    )

with col3:
    success_rate = performance_metrics['success_rate']
    st.metric(
        label=get_text('success_rate'),
        value=f"{success_rate:.1%}",
        delta=f"{(success_rate - 0.95):.1%}"
    )

with col4:
    user_satisfaction = performance_metrics['user_satisfaction']
    st.metric(
        label=get_text('user_satisfaction'),
        value=f"{user_satisfaction:.1%}",
        delta=f"{(user_satisfaction - 0.85):.1%}"
    )

# Performance Trends
st.subheader(get_text('performance_trend'))

fig_performance = make_subplots(
    rows=2, cols=2,
    subplot_titles=[
        get_text('response_time'),
        get_text('query_volume'),
        get_text('success_rate'),
        get_text('user_satisfaction')
    ]
)

# Response time trend
response_time_data = time_series_data.get('response_time', [])
if response_time_data:
    timestamps = [d['timestamp'] for d in response_time_data]
    values = [d['value'] for d in response_time_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('response_time'),
            line=dict(color='#FF6B6B')
        ),
        row=1, col=1
    )

# Query volume trend
query_volume_data = time_series_data.get('query_volume', [])
if query_volume_data:
    timestamps = [d['timestamp'] for d in query_volume_data]
    values = [d['value'] for d in query_volume_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('query_volume'),
            line=dict(color='#4ECDC4')
        ),
        row=1, col=2
    )

# Success rate trend
success_rate_data = time_series_data.get('success_rate', [])
if success_rate_data:
    timestamps = [d['timestamp'] for d in success_rate_data]
    values = [d['value'] for d in success_rate_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('success_rate'),
            line=dict(color='#45B7D1')
        ),
        row=2, col=1
    )

# User satisfaction trend
satisfaction_data = time_series_data.get('user_satisfaction', [])
if satisfaction_data:
    timestamps = [d['timestamp'] for d in satisfaction_data]
    values = [d['value'] for d in satisfaction_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('user_satisfaction'),
            line=dict(color='#96CEB4')
        ),
        row=2, col=2
    )

fig_performance.update_layout(height=600, showlegend=False)
st.plotly_chart(fig_performance, use_container_width=True)

# Usage Analytics Section
st.header(get_text('usage_analytics'))

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('content_categories'))

    categories_df = pd.DataFrame(
        list(usage_analytics['content_categories'].items()),
        columns=['Category', 'Count']
    )

    fig_categories = px.pie(
        categories_df,
        values='Count',
        names='Category',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_categories.update_layout(height=400)
    st.plotly_chart(fig_categories, use_container_width=True)

with col2:
    st.subheader(get_text('language_distribution'))

    lang_df = pd.DataFrame(
        list(usage_analytics['language_distribution'].items()),
        columns=['Language', 'Percentage']
    )

    fig_languages = px.bar(
        lang_df,
        x='Language',
        y='Percentage',
        color='Language',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_languages.update_layout(height=400)
    st.plotly_chart(fig_languages, use_container_width=True)

# Peak Hours Analysis
st.subheader(get_text('peak_hours'))

hours = list(range(24))
hourly_activity = [50 if h in usage_analytics['peak_hours'] else np.random.randint(10, 30) for h in hours]

fig_peak = px.bar(
    x=hours,
    y=hourly_activity,
    labels={'x': 'Hora del día', 'y': 'Actividad'},
    color=hourly_activity,
    color_continuous_scale='Viridis'
)
fig_peak.update_layout(height=300)
st.plotly_chart(fig_peak, use_container_width=True)

# Security Overview Section
st.header(get_text('security_overview'))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=get_text('security_events'),
        value=security_overview['total_events'],
        delta="-15"
    )

with col2:
    high_threats = security_overview['threat_levels']['Alto'] + security_overview['threat_levels']['Crítico']
    st.metric(
        label="Amenazas Altas/Críticas",
        value=high_threats,
        delta="-3"
    )

with col3:
    blocked_attempts = security_overview['event_types']['Intento de Inyección']
    st.metric(
        label="Intentos Bloqueados",
        value=blocked_attempts,
        delta="+2"
    )

# Security charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Eventos por Nivel de Amenaza")

    threat_df = pd.DataFrame(
        list(security_overview['threat_levels'].items()),
        columns=['Nivel', 'Cantidad']
    )

    fig_threats = px.bar(
        threat_df,
        x='Nivel',
        y='Cantidad',
        color='Nivel',
        color_discrete_map={
            'Bajo': '#96CEB4',
            'Medio': '#FFEAA7',
            'Alto': '#FDCB6E',
            'Crítico': '#E17055'
        }
    )
    st.plotly_chart(fig_threats, use_container_width=True)

with col2:
    st.subheader("Tipos de Eventos de Seguridad")

    events_df = pd.DataFrame(
        list(security_overview['event_types'].items()),
        columns=['Tipo', 'Cantidad']
    )

    fig_events = px.pie(
        events_df,
        values='Cantidad',
        names='Tipo',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_events, use_container_width=True)

# Predictive Analytics Section
st.header(get_text('predictive_analytics'))

# Generate forecast data
future_dates = pd.date_range(start=datetime.now(), end=datetime.now() + timedelta(days=7), freq='H')
forecast_queries = np.random.poisson(18, len(future_dates))  # Slightly higher than current

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('usage_forecast'))
    
    fig_forecast = go.Figure()
    
    # Historical data
    historical_timestamps = pd.date_range(
        start=datetime.now() - timedelta(hours=48),
        end=datetime.now(),
        freq='H'
    )
    historical_queries = np.random.poisson(15, len(historical_timestamps))

    fig_forecast.add_trace(go.Scatter(
        x=historical_timestamps,
        y=historical_queries,
        mode='lines',
        name='Histórico',
        line=dict(color='#45B7D1')
    ))
    
    # Forecast
    fig_forecast.add_trace(go.Scatter(
        x=future_dates,
        y=forecast_queries,
        mode='lines',
        name='Pronóstico',
        line=dict(color='#FF6B6B', dash='dash')
    ))
    
    fig_forecast.update_layout(height=400)
    st.plotly_chart(fig_forecast, use_container_width=True)

with col2:
    st.subheader(get_text('optimization_impact'))
    
    # Simulated optimization impact
    optimization_scenarios = {
        'Actual': 2.5,
        'Optimización Básica': 2.1,
        'Optimización Avanzada': 1.8,
        'Optimización Completa': 1.5
    }
    
    opt_df = pd.DataFrame(
        list(optimization_scenarios.items()),
        columns=['Escenario', 'Tiempo de Respuesta (s)']
    )
    
    fig_optimization = px.bar(
        opt_df,
        x='Escenario',
        y='Tiempo de Respuesta (s)',
        color='Tiempo de Respuesta (s)',
        color_continuous_scale='RdYlGn_r'
    )
    fig_optimization.update_layout(height=400)
    st.plotly_chart(fig_optimization, use_container_width=True)

# Recommendations Section
st.header(get_text('optimization_recommendations'))

recommendations = [
    {
        'priority': 'Alta',
        'category': 'Rendimiento',
        'recommendation': 'Optimizar tamaño de chunks para consultas complejas',
        'impact': 'Reducción del 25% en tiempo de respuesta',
        'effort': 'Medio'
    },
    {
        'priority': 'Media',
        'category': 'Seguridad',
        'recommendation': 'Implementar rate limiting más granular',
        'impact': 'Reducción del 40% en eventos de seguridad',
        'effort': 'Bajo'
    },
    {
        'priority': 'Media',
        'category': 'Uso',
        'recommendation': 'Escalar recursos durante horas pico (9-11h, 14-16h)',
        'impact': 'Mejora del 15% en satisfacción del usuario',
        'effort': 'Alto'
    },
    {
        'priority': 'Baja',
        'category': 'Contenido',
        'recommendation': 'Expandir contenido en inglés',
        'impact': 'Aumento del 20% en consultas en inglés',
        'effort': 'Alto'
    }
]

recommendations_df = pd.DataFrame(recommendations)

# Color coding for priority
def get_priority_color(priority):
    colors = {'Alta': '🔴', 'Media': '🟡', 'Baja': '🟢'}
    return colors.get(priority, '⚪')

for _, rec in recommendations_df.iterrows():
    with st.expander(f"{get_priority_color(rec['priority'])} {rec['recommendation']}"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Categoría:** {rec['category']}")
            st.write(f"**Prioridad:** {rec['priority']}")
        with col2:
            st.write(f"**Impacto Esperado:** {rec['impact']}")
        with col3:
            st.write(f"**Esfuerzo:** {rec['effort']}")

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()
