"""Dashboard de Inteligencia Empresarial para Conversión Documental - Anclora RAG."""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time

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
    import sys
    import os

    # Add the app directory to the path if not already there
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from analytics.conversion_dashboard_service import ConversionDashboardService
    dashboard_service = ConversionDashboardService()
    DASHBOARD_SERVICE_AVAILABLE = True
except ImportError as e:
    DASHBOARD_SERVICE_AVAILABLE = False
    dashboard_service = None
    st.info(f"ℹ️ Servicio de dashboard no disponible: {e}. Usando datos simulados de conversión.")

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
        'title': '📊 Dashboard de Conversión Documental',
        'subtitle': 'Análisis avanzado del sistema de conversión orquestada por agentes',
        'conversion_metrics': 'Métricas de Conversión',
        'agent_performance': 'Rendimiento de Agentes',
        'security_analysis': 'Análisis de Seguridad',
        'quality_insights': 'Insights de Calidad',
        'predictive_analytics': 'Análisis Predictivo',
        'optimization_recommendations': 'Recomendaciones de Optimización',
        'conversion_volume': 'Volumen de Conversiones',
        'conversion_time': 'Tiempo de Conversión',
        'success_rate': 'Tasa de Éxito',
        'user_satisfaction': 'Satisfacción del Usuario',
        'complex_conversions': 'Conversiones Complejas',
        'batch_conversions': 'Conversiones por Lotes',
        'format_distribution': 'Distribución por Formato',
        'agent_utilization': 'Utilización de Agentes',
        'security_events': 'Eventos de Seguridad',
        'malware_detected': 'Malware Detectado',
        'files_quarantined': 'Archivos en Cuarentena',
        'threat_level': 'Nivel de Amenaza',
        'conversion_trend': 'Tendencia de Conversiones',
        'quality_score': 'Puntuación de Calidad',
        'error_analysis': 'Análisis de Errores',
        'usage_forecast': 'Pronóstico de Uso',
        'optimization_impact': 'Impacto de Optimizaciones',
        'recommendations': 'Recomendaciones',
        'last_24h': 'Últimas 24 horas',
        'last_7d': 'Últimos 7 días',
        'last_30d': 'Últimos 30 días',
        'real_time': 'Tiempo Real',
        'peak_hours': 'Horas Pico',
        'performance_trend': 'Tendencia de Rendimiento'
    },
    'en': {
        'title': '📊 Document Conversion Dashboard',
        'subtitle': 'Advanced analysis of agent-orchestrated conversion system',
        'conversion_metrics': 'Conversion Metrics',
        'agent_performance': 'Agent Performance',
        'security_analysis': 'Security Analysis',
        'quality_insights': 'Quality Insights',
        'predictive_analytics': 'Predictive Analytics',
        'optimization_recommendations': 'Optimization Recommendations',
        'conversion_volume': 'Conversion Volume',
        'conversion_time': 'Conversion Time',
        'success_rate': 'Success Rate',
        'user_satisfaction': 'User Satisfaction',
        'complex_conversions': 'Complex Conversions',
        'batch_conversions': 'Batch Conversions',
        'format_distribution': 'Format Distribution',
        'agent_utilization': 'Agent Utilization',
        'security_events': 'Security Events',
        'malware_detected': 'Malware Detected',
        'files_quarantined': 'Files Quarantined',
        'threat_level': 'Threat Level',
        'conversion_trend': 'Conversion Trend',
        'quality_score': 'Quality Score',
        'error_analysis': 'Error Analysis',
        'usage_forecast': 'Usage Forecast',
        'optimization_impact': 'Optimization Impact',
        'recommendations': 'Recommendations',
        'last_24h': 'Last 24 hours',
        'last_7d': 'Last 7 days',
        'last_30d': 'Last 30 days',
        'real_time': 'Real Time',
        'peak_hours': 'Peak Hours',
        'performance_trend': 'Performance Trend'
    }
}

def get_text(key):
    # Ensure language is set in session state
    if 'language' not in st.session_state:
        st.session_state.language = 'es'

    # Get the language, fallback to 'es' if not found
    language = st.session_state.get('language', 'es')

    # Return translation or key if not found
    return translations.get(language, translations['es']).get(key, key)

# Get real data from dashboard service
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dashboard_data(time_range: str):
    """Get real data from the dashboard service."""

    # Check if dashboard service is available
    if not DASHBOARD_SERVICE_AVAILABLE or dashboard_service is None:
        return get_fallback_data()

    try:
        # Get real metrics from conversion dashboard service
        conversion_metrics = dashboard_service.get_conversion_metrics(time_range)
        agent_performance = dashboard_service.get_agent_performance()
        security_analysis = dashboard_service.get_security_analysis()
        predictive_insights = dashboard_service.get_predictive_insights()

        # Get time series data for conversion metrics
        time_series_data = {}
        for metric in ['conversion_time', 'conversion_volume', 'success_rate', 'user_satisfaction', 'quality_score']:
            time_series_data[metric] = dashboard_service.get_time_series_data(metric, time_range)

        return {
            'conversion_metrics': conversion_metrics,
            'agent_performance': agent_performance,
            'security_analysis': security_analysis,
            'predictive_insights': predictive_insights,
            'time_series_data': time_series_data
        }

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        # Fallback to mock data
        return get_fallback_data()


def get_fallback_data():
    """Fallback data when real data is not available - specialized for document conversion."""

    # Generate fallback time series for conversion metrics
    dates = pd.date_range(start=datetime.now() - timedelta(days=1), end=datetime.now(), freq='h')

    time_series_data = {
        'conversion_time': [{'timestamp': d, 'value': 45 + np.random.normal(0, 8)} for d in dates],
        'conversion_volume': [{'timestamp': d, 'value': 8 + np.random.poisson(3)} for d in dates],
        'success_rate': [{'timestamp': d, 'value': 0.92 + np.random.normal(0, 0.03)} for d in dates],
        'user_satisfaction': [{'timestamp': d, 'value': 0.88 + np.random.normal(0, 0.04)} for d in dates],
        'quality_score': [{'timestamp': d, 'value': 0.85 + np.random.normal(0, 0.05)} for d in dates]
    }

    return {
        'conversion_metrics': {
            'avg_conversion_time': 45.2,
            'total_conversions': 847,
            'success_rate': 0.92,
            'user_satisfaction': 0.88,
            'complex_conversions': 156,
            'batch_conversions': 89,
            'avg_quality_score': 0.85
        },
        'agent_performance': {
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'format_distribution': {
                'PDF → DOCX': 28,
                'DOCX → PDF': 22,
                'PDF → EPUB': 18,
                'HTML → PDF': 12,
                'TXT → DOCX': 8,
                'Otros': 12
            },
            'agent_utilization': {
                'DocumentAgent': 85,
                'CodeAgent': 67,
                'MediaAgent': 43,
                'ArchiveAgent': 29,
                'OrchestratorAgent': 92
            },
            'complex_conversion_types': {
                'Documentos Técnicos con Diagramas': 45,
                'Documentos Legales Estructurados': 38,
                'Presentaciones Multimedia': 28,
                'Documentos Científicos': 25,
                'Archivos Comprimidos': 20
            }
        },
        'security_analysis': {
            'total_events': 89,
            'files_quarantined': 12,
            'malware_detected': 5,
            'suspicious_files': 18,
            'threat_levels': {
                'Bajo': 62,
                'Medio': 19,
                'Alto': 6,
                'Crítico': 2
            },
            'security_events': {
                'Malware Detectado': 5,
                'Archivo Corrupto': 23,
                'Formato Sospechoso': 18,
                'Tamaño Excesivo': 15,
                'Extensión Prohibida': 12,
                'Contenido Encriptado': 8,
                'Otros': 8
            },
            'scan_results': {
                'Archivos Escaneados': 2847,
                'Archivos Limpios': 2758,
                'Archivos Sospechosos': 77,
                'Archivos Bloqueados': 12
            }
        },
        'predictive_insights': {
            'conversion_forecast': [8, 12, 15, 13, 10, 9, 11],
            'quality_trend': [0.85, 0.87, 0.86, 0.88, 0.89, 0.87, 0.90],
            'optimization_recommendations': [
                {
                    'type': 'conversion_performance',
                    'description': 'Optimizar pipeline de conversión PDF→DOCX',
                    'impact': '30% reducción en tiempo de conversión',
                    'priority': 'Alta'
                },
                {
                    'type': 'security',
                    'description': 'Implementar escaneo antimalware avanzado',
                    'impact': '95% reducción en archivos maliciosos',
                    'priority': 'Crítica'
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

conversion_metrics = dashboard_data['conversion_metrics']
agent_performance = dashboard_data['agent_performance']
security_analysis = dashboard_data['security_analysis']
predictive_insights = dashboard_data['predictive_insights']
time_series_data = dashboard_data['time_series_data']

# Conversion Metrics Section
st.header(get_text('conversion_metrics'))

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_conversions = int(conversion_metrics['total_conversions'])
    st.metric(
        label=get_text('conversion_volume'),
        value=f"{total_conversions:,}",
        delta=f"+{int(total_conversions * 0.08)}"
    )

with col2:
    avg_conversion_time = conversion_metrics['avg_conversion_time']
    st.metric(
        label=get_text('conversion_time'),
        value=f"{avg_conversion_time:.1f}s",
        delta=f"{(avg_conversion_time - 50):.1f}s"
    )

with col3:
    success_rate = conversion_metrics['success_rate']
    st.metric(
        label=get_text('success_rate'),
        value=f"{success_rate:.1%}",
        delta=f"{(success_rate - 0.90):.1%}"
    )

with col4:
    user_satisfaction = conversion_metrics['user_satisfaction']
    st.metric(
        label=get_text('user_satisfaction'),
        value=f"{user_satisfaction:.1%}",
        delta=f"{(user_satisfaction - 0.85):.1%}"
    )

# Additional conversion-specific metrics
col1, col2, col3 = st.columns(3)

with col1:
    complex_conversions = int(conversion_metrics['complex_conversions'])
    st.metric(
        label=get_text('complex_conversions'),
        value=f"{complex_conversions:,}",
        delta=f"+{int(complex_conversions * 0.12)}"
    )

with col2:
    batch_conversions = int(conversion_metrics['batch_conversions'])
    st.metric(
        label=get_text('batch_conversions'),
        value=f"{batch_conversions:,}",
        delta=f"+{int(batch_conversions * 0.15)}"
    )

with col3:
    avg_quality_score = conversion_metrics['avg_quality_score']
    st.metric(
        label=get_text('quality_score'),
        value=f"{avg_quality_score:.1%}",
        delta=f"{(avg_quality_score - 0.80):.1%}"
    )

# Conversion Trends
st.subheader(get_text('conversion_trend'))

fig_performance = make_subplots(
    rows=2, cols=2,
    subplot_titles=[
        get_text('conversion_time'),
        get_text('conversion_volume'),
        get_text('success_rate'),
        get_text('quality_score')
    ]
)

# Conversion time trend
conversion_time_data = time_series_data.get('conversion_time', [])
if conversion_time_data:
    timestamps = [d['timestamp'] for d in conversion_time_data]
    values = [d['value'] for d in conversion_time_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('conversion_time'),
            line=dict(color='#FF6B6B')
        ),
        row=1, col=1
    )

# Conversion volume trend
conversion_volume_data = time_series_data.get('conversion_volume', [])
if conversion_volume_data:
    timestamps = [d['timestamp'] for d in conversion_volume_data]
    values = [d['value'] for d in conversion_volume_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('conversion_volume'),
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

# Quality score trend
quality_score_data = time_series_data.get('quality_score', [])
if quality_score_data:
    timestamps = [d['timestamp'] for d in quality_score_data]
    values = [d['value'] for d in quality_score_data]
    fig_performance.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode='lines',
            name=get_text('quality_score'),
            line=dict(color='#96CEB4')
        ),
        row=2, col=2
    )

fig_performance.update_layout(height=600, showlegend=False)
st.plotly_chart(fig_performance, use_container_width=True)

# Agent Performance Section
st.header(get_text('agent_performance'))

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('agent_utilization'))

    agent_util_df = pd.DataFrame(
        list(agent_performance['agent_utilization'].items()),
        columns=['Agent', 'Utilization']
    )

    fig_agents = px.pie(
        agent_util_df,
        values='Utilization',
        names='Agent',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_agents.update_layout(height=400)
    st.plotly_chart(fig_agents, use_container_width=True)

with col2:
    st.subheader(get_text('format_distribution'))

    format_df = pd.DataFrame(
        list(agent_performance['format_distribution'].items()),
        columns=['Conversion Type', 'Count']
    )

    fig_formats = px.bar(
        format_df,
        x='Conversion Type',
        y='Count',
        color='Count',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_formats.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_formats, use_container_width=True)

# Peak Hours Analysis
st.subheader(get_text('peak_hours'))

hours = list(range(24))
hourly_activity = [50 if h in agent_performance['peak_hours'] else np.random.randint(10, 30) for h in hours]

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
        value=security_analysis['total_events'],
        delta="-15"
    )

with col2:
    malware_detected = security_analysis['malware_detected']
    st.metric(
        label="Malware Detectado",
        value=malware_detected,
        delta="-3"
    )

with col3:
    files_quarantined = security_analysis['files_quarantined']
    st.metric(
        label="Archivos en Cuarentena",
        value=files_quarantined,
        delta="+2"
    )

# Security charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resultados de Escaneo")

    scan_df = pd.DataFrame(
        list(security_analysis['scan_results'].items()),
        columns=['Resultado', 'Cantidad']
    )

    fig_scan = px.bar(
        scan_df,
        x='Resultado',
        y='Cantidad',
        color='Resultado',
        color_discrete_map={
            'Archivos Limpios': '#96CEB4',
            'Archivos Sospechosos': '#FFEAA7',
            'Archivos Bloqueados': '#E17055'
        }
    )
    st.plotly_chart(fig_scan, use_container_width=True)

with col2:
    st.subheader("Tipos de Eventos de Seguridad")

    events_df = pd.DataFrame(
        list(security_analysis['security_events'].items()),
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
future_dates = pd.date_range(start=datetime.now(), end=datetime.now() + timedelta(days=7), freq='h')
forecast_queries = np.random.poisson(18, len(future_dates))  # Slightly higher than current

col1, col2 = st.columns(2)

with col1:
    st.subheader(get_text('usage_forecast'))
    
    fig_forecast = go.Figure()
    
    # Historical data
    historical_timestamps = pd.date_range(
        start=datetime.now() - timedelta(hours=48),
        end=datetime.now(),
        freq='h'
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
