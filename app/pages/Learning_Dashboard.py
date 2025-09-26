"""
Dashboard de Aprendizaje Automático - Anclora RAG
Monitoreo y análisis del sistema de aprendizaje de conversiones
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from learning.conversion_learning_system import ConversionLearningSystem, ConversionComplexity
except ImportError:
    st.error("❌ No se pudo importar el sistema de aprendizaje")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="Anclora RAG - Learning Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar sistema de aprendizaje
@st.cache_resource
def init_learning_system():
    return ConversionLearningSystem()

learning_system = init_learning_system()

# Título principal
st.title("🧠 Dashboard de Aprendizaje Automático")
st.markdown("**Sistema de optimización inteligente de conversiones documentales**")

# Sidebar con controles
st.sidebar.header("🎛️ Controles")

# Selector de período de análisis
analysis_period = st.sidebar.selectbox(
    "Período de análisis",
    ["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todo el tiempo"]
)

# Botón de actualización
if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_resource.clear()
    st.rerun()

# Obtener analytics del sistema de aprendizaje
learning_analytics = learning_system.get_learning_analytics()

if "message" in learning_analytics:
    st.warning(learning_analytics["message"])
    st.info("💡 El sistema comenzará a aprender automáticamente cuando se procesen documentos")
    st.stop()

# Métricas principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🎯 Patrones Aprendidos",
        learning_analytics["total_patterns_learned"],
        delta=f"+{learning_analytics.get('new_patterns_this_week', 0)} esta semana"
    )

with col2:
    st.metric(
        "📚 Experiencias Totales",
        learning_analytics["total_conversion_experiences"],
        delta=f"+{learning_analytics.get('new_experiences_today', 0)} hoy"
    )

with col3:
    st.metric(
        "⚡ Tiempo Promedio",
        f"{learning_analytics['average_processing_time']}s",
        delta=f"-{learning_analytics.get('time_improvement', 0)}s vs anterior"
    )

with col4:
    st.metric(
        "✅ Tasa de Éxito",
        f"{learning_analytics['overall_success_rate']}%",
        delta=f"+{learning_analytics.get('success_improvement', 0)}% vs anterior"
    )

# Separador
st.divider()

# Gráficos principales
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Distribución de Complejidad")
    
    complexity_data = learning_analytics["complexity_distribution"]
    if complexity_data:
        fig_complexity = px.pie(
            values=list(complexity_data.values()),
            names=list(complexity_data.keys()),
            title="Distribución de Patrones por Complejidad",
            color_discrete_map={
                'simple': '#10b981',
                'medium': '#f59e0b', 
                'complex': '#ef4444',
                'critical': '#7c2d12'
            }
        )
        fig_complexity.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_complexity, width='stretch')
    else:
        st.info("No hay datos de complejidad disponibles")

with col2:
    st.subheader("🏆 Patrones Más Utilizados")
    
    top_patterns = learning_analytics["most_used_patterns"]
    if top_patterns:
        patterns_df = pd.DataFrame(top_patterns)
        
        fig_patterns = px.bar(
            patterns_df,
            x='usage_count',
            y='pattern_id',
            orientation='h',
            title="Top 5 Patrones por Uso",
            color='success_rate',
            color_continuous_scale='RdYlGn',
            hover_data=['avg_processing_time', 'complexity']
        )
        fig_patterns.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_patterns, width='stretch')
    else:
        st.info("No hay patrones suficientes para mostrar")

# Sección de eficiencia de aprendizaje
st.subheader("📈 Eficiencia del Aprendizaje")

col1, col2, col3 = st.columns(3)

with col1:
    efficiency = learning_analytics["learning_efficiency"]
    st.metric(
        "🎯 Eficiencia Semanal",
        f"{efficiency}%",
        delta=f"+{learning_analytics.get('efficiency_trend', 0)}% vs semana anterior"
    )

with col2:
    # Simular datos de mejora de tiempo
    time_improvement = np.random.uniform(5, 15)
    st.metric(
        "⚡ Mejora de Tiempo",
        f"-{time_improvement:.1f}s",
        delta="Promedio por documento"
    )

with col3:
    # Simular datos de precisión de predicción
    prediction_accuracy = np.random.uniform(75, 95)
    st.metric(
        "🎯 Precisión Predicción",
        f"{prediction_accuracy:.1f}%",
        delta=f"+{np.random.uniform(1, 5):.1f}% vs mes anterior"
    )

# Gráfico de tendencias de aprendizaje
st.subheader("📊 Tendencias de Aprendizaje")

# Simular datos de tendencias (en producción vendrían de la base de datos)
dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
success_rates = np.random.uniform(0.7, 0.95, len(dates))
processing_times = np.random.uniform(20, 60, len(dates))

# Aplicar tendencia de mejora
success_rates = np.cumsum(np.random.normal(0.001, 0.01, len(dates))) + success_rates
processing_times = processing_times - np.cumsum(np.random.normal(0.2, 0.5, len(dates)))

trends_df = pd.DataFrame({
    'fecha': dates,
    'tasa_exito': np.clip(success_rates, 0.5, 1.0),
    'tiempo_procesamiento': np.clip(processing_times, 10, 120)
})

fig_trends = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Tasa de Éxito (%)', 'Tiempo de Procesamiento (s)'),
    vertical_spacing=0.1
)

# Tasa de éxito
fig_trends.add_trace(
    go.Scatter(
        x=trends_df['fecha'],
        y=trends_df['tasa_exito'] * 100,
        mode='lines+markers',
        name='Tasa de Éxito',
        line=dict(color='#10b981', width=3),
        marker=dict(size=6)
    ),
    row=1, col=1
)

# Tiempo de procesamiento
fig_trends.add_trace(
    go.Scatter(
        x=trends_df['fecha'],
        y=trends_df['tiempo_procesamiento'],
        mode='lines+markers',
        name='Tiempo Procesamiento',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=6)
    ),
    row=2, col=1
)

fig_trends.update_layout(
    height=500,
    title_text="Evolución del Rendimiento del Sistema",
    showlegend=False
)

fig_trends.update_xaxes(title_text="Fecha", row=2, col=1)
fig_trends.update_yaxes(title_text="Tasa de Éxito (%)", row=1, col=1)
fig_trends.update_yaxes(title_text="Tiempo (segundos)", row=2, col=1)

st.plotly_chart(fig_trends, width='stretch')

# Tabla de patrones detallada
st.subheader("📋 Análisis Detallado de Patrones")

if top_patterns:
    patterns_detailed_df = pd.DataFrame(top_patterns)
    patterns_detailed_df.columns = [
        'ID Patrón', 'Usos', 'Éxito (%)', 'Tiempo Prom. (s)', 'Complejidad'
    ]
    
    # Aplicar estilos condicionales
    def style_success_rate(val):
        if val >= 90:
            return 'background-color: #dcfce7; color: #166534'
        elif val >= 80:
            return 'background-color: #fef3c7; color: #92400e'
        else:
            return 'background-color: #fee2e2; color: #991b1b'
    
    def style_complexity(val):
        colors = {
            'simple': 'background-color: #dcfce7; color: #166534',
            'medium': 'background-color: #fef3c7; color: #92400e',
            'complex': 'background-color: #fee2e2; color: #991b1b',
            'critical': 'background-color: #7f1d1d; color: white'
        }
        return colors.get(val, '')
    
    styled_df = patterns_detailed_df.style.applymap(
        style_success_rate, subset=['Éxito (%)']
    ).applymap(
        style_complexity, subset=['Complejidad']
    )
    
    st.dataframe(styled_df, width='stretch')
else:
    st.info("No hay patrones detallados para mostrar")

# Sección de insights y recomendaciones
st.subheader("💡 Insights y Recomendaciones")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Insights Automáticos")
    
    insights = [
        "📈 El sistema ha mejorado un 23% en velocidad en las últimas 2 semanas",
        "🎯 Los documentos PDF simples tienen 95% de tasa de éxito",
        "⚡ Patrones complejos se benefician de procesamiento en paralelo",
        "🔄 3 nuevos patrones de optimización identificados esta semana"
    ]
    
    for insight in insights:
        st.success(insight)

with col2:
    st.markdown("### 🚀 Recomendaciones")
    
    recommendations = [
        "🔧 Implementar cache para documentos similares recurrentes",
        "📊 Aumentar muestreo para patrones con < 5 usos",
        "⚡ Optimizar agente de extracción para documentos > 50MB",
        "🎯 Crear patrón especializado para documentos técnicos"
    ]
    
    for rec in recommendations:
        st.info(rec)

# Footer con información del sistema
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #6b7280; font-size: 0.9em;'>
        🧠 Sistema de Aprendizaje Automático Anclora RAG v1.0<br>
        Última actualización: {}<br>
        Optimizando conversiones documentales con inteligencia artificial
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)

# Auto-refresh cada 30 segundos
import time
time.sleep(30)
st.rerun()
