"""
🎨 PALETA EXCLUSIVA ANCLORA RAG
Combinación única de las paletas oficiales de Anclora adaptada específicamente para RAG
Basada en: NEXUS, PRESS, KAIRON, RENDER, GUARDIAN + Paleta Visual Principal
"""

# 🎯 COLORES PRINCIPALES ANCLORA RAG (Basados en paletas oficiales)
ANCLORA_RAG_COLORS = {
    # 🔵 AZULES PRINCIPALES (De NEXUS + Paleta Visual)
    "primary_deep": "#23436B",       # Azul profundo NEXUS (Color principal RAG)
    "primary_medium": "#2EAFC4",     # Azul claro/Teal NEXUS (Acento principal)
    "primary_light": "#E8F4F8",      # Versión muy clara del teal
    "primary_ultra_light": "#F0F9FB", # Versión ultra clara para fondos

    # 🟢 VERDES INTELIGENTES (De KAIRON + GUARDIAN)
    "success_deep": "#37B5A4",       # Verde teal KAIRON (Éxito principal)
    "success_medium": "#4DF8E3",     # Verde claro KAIRON (Acento éxito)
    "success_light": "#E8F8F6",      # Verde muy claro
    "success_ultra_light": "#F0FBF9", # Verde ultra claro para fondos

    # 🟡 ÁMBAR SUAVE (De PRESS + GUARDIAN + Paleta Visual)
    "warning_deep": "#FFC979",       # Ámbar PRESS/GUARDIAN (Advertencia principal)
    "warning_medium": "#FFE4B8",     # Ámbar claro
    "warning_light": "#FFF4E6",      # Ámbar muy claro
    "warning_ultra_light": "#FFFAF2", # Ámbar ultra claro para fondos

    # 🌸 ROSA CORAL SUAVE (Reemplazo del rojo - Inspirado en paletas)
    "error_deep": "#FF9A9E",         # Rosa coral suave (NO rojo agresivo)
    "error_medium": "#FFCCCB",       # Rosa coral claro
    "error_light": "#FFF0F0",        # Rosa muy claro
    "error_ultra_light": "#FFF8F8",  # Rosa ultra claro para fondos

    # ⚫ GRISES SOFISTICADOS (De todas las paletas)
    "neutral_darkest": "#162032",    # Negro-azulado NEXUS/RENDER (Texto principal)
    "neutral_dark": "#F6F7F9",       # Gris claro oficial (Fondos secundarios)
    "neutral_medium": "#FFFFFF",     # Blanco puro (Fondos principales)
    "neutral_light": "#F8F9FA",      # Gris ultra claro

    # 🎨 COLORES ESPECIALES RAG
    "ai_accent": "#4DF8E3",          # Color especial para elementos de IA (teal brillante)
    "data_accent": "#2EAFC4",        # Color para datos y métricas (azul teal)
    "premium_accent": "#37B5A4",     # Color premium para funciones avanzadas

    # 📝 TEXTO OPTIMIZADO
    "text_primary": "#162032",       # Negro-azulado para máxima legibilidad
    "text_secondary": "#546E7A",     # Gris medio para texto secundario
    "text_muted": "#9CA3AF",         # Gris claro para texto deshabilitado
    "text_inverse": "#FFFFFF",       # Texto blanco para fondos oscuros
}

# 🎨 CONFIGURACIONES POR CONTEXTO ANCLORA RAG
CONTEXT_COLORS = {
    "success": {
        "background": ANCLORA_RAG_COLORS["success_light"],
        "border": ANCLORA_RAG_COLORS["success_medium"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["success_deep"],
        "icon": "✅"
    },
    "warning": {
        "background": ANCLORA_RAG_COLORS["warning_light"],
        "border": ANCLORA_RAG_COLORS["warning_medium"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["warning_deep"],
        "icon": "⚠️"
    },
    "error": {
        "background": ANCLORA_RAG_COLORS["error_light"],
        "border": ANCLORA_RAG_COLORS["error_medium"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["error_deep"],
        "icon": "💝"  # Corazón suave en lugar de X rojo agresivo
    },
    "info": {
        "background": ANCLORA_RAG_COLORS["primary_light"],
        "border": ANCLORA_RAG_COLORS["primary_medium"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["primary_deep"],
        "icon": "ℹ️"
    },
    "ai": {
        "background": ANCLORA_RAG_COLORS["primary_ultra_light"],
        "border": ANCLORA_RAG_COLORS["ai_accent"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["ai_accent"],
        "icon": "🤖"
    },
    "data": {
        "background": ANCLORA_RAG_COLORS["success_ultra_light"],
        "border": ANCLORA_RAG_COLORS["data_accent"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["data_accent"],
        "icon": "📊"
    },
    "premium": {
        "background": ANCLORA_RAG_COLORS["warning_ultra_light"],
        "border": ANCLORA_RAG_COLORS["premium_accent"],
        "text": ANCLORA_RAG_COLORS["text_primary"],
        "accent": ANCLORA_RAG_COLORS["premium_accent"],
        "icon": "⭐"
    }
}

# 🌈 GRADIENTES EXCLUSIVOS ANCLORA RAG
GRADIENTS = {
    "primary": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['primary_deep']} 0%, {ANCLORA_RAG_COLORS['primary_medium']} 100%)",
    "success": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['success_deep']} 0%, {ANCLORA_RAG_COLORS['success_medium']} 100%)",
    "warning": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['warning_deep']} 0%, {ANCLORA_RAG_COLORS['warning_medium']} 100%)",
    "error": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['error_deep']} 0%, {ANCLORA_RAG_COLORS['error_medium']} 100%)",
    "ai": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['primary_medium']} 0%, {ANCLORA_RAG_COLORS['ai_accent']} 100%)",
    "data": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['data_accent']} 0%, {ANCLORA_RAG_COLORS['success_deep']} 100%)",
    "premium": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['premium_accent']} 0%, {ANCLORA_RAG_COLORS['warning_deep']} 100%)"
}

# 📊 COLORES PARA GRÁFICOS ANCLORA RAG (Plotly)
CHART_COLORS = [
    ANCLORA_RAG_COLORS["primary_medium"],    # Azul teal principal
    ANCLORA_RAG_COLORS["success_deep"],      # Verde teal
    ANCLORA_RAG_COLORS["warning_deep"],      # Ámbar
    ANCLORA_RAG_COLORS["ai_accent"],         # Teal brillante
    ANCLORA_RAG_COLORS["primary_deep"],      # Azul profundo
    ANCLORA_RAG_COLORS["success_medium"],    # Verde claro
    ANCLORA_RAG_COLORS["premium_accent"],    # Verde premium
    ANCLORA_RAG_COLORS["data_accent"]        # Azul datos
]

def get_color(color_name: str) -> str:
    """Obtiene un color de la paleta Anclora RAG"""
    return ANCLORA_RAG_COLORS.get(color_name, ANCLORA_RAG_COLORS["neutral_medium"])

def get_context_colors(context: str) -> dict:
    """Obtiene los colores para un contexto específico"""
    return CONTEXT_COLORS.get(context, CONTEXT_COLORS["info"])

def get_gradient(gradient_name: str) -> str:
    """Obtiene un gradiente de la paleta"""
    return GRADIENTS.get(gradient_name, GRADIENTS["primary"])

# 🎨 CSS PERSONALIZADO ANCLORA RAG
ANCLORA_RAG_CSS = f"""
<style>
/* 🎯 Variables CSS exclusivas de Anclora RAG */
:root {{
    --anclora-rag-primary: {ANCLORA_RAG_COLORS["primary_deep"]};
    --anclora-rag-secondary: {ANCLORA_RAG_COLORS["primary_medium"]};
    --anclora-rag-success: {ANCLORA_RAG_COLORS["success_deep"]};
    --anclora-rag-warning: {ANCLORA_RAG_COLORS["warning_deep"]};
    --anclora-rag-error: {ANCLORA_RAG_COLORS["error_deep"]};
    --anclora-rag-ai: {ANCLORA_RAG_COLORS["ai_accent"]};
    --anclora-rag-data: {ANCLORA_RAG_COLORS["data_accent"]};
    --anclora-rag-text: {ANCLORA_RAG_COLORS["text_primary"]};
    --anclora-rag-bg: {ANCLORA_RAG_COLORS["neutral_medium"]};
    --anclora-rag-bg-secondary: {ANCLORA_RAG_COLORS["neutral_light"]};
}}

/* 🎨 Personalización exclusiva de elementos Streamlit para Anclora RAG */
.stAlert > div {{
    border-radius: 12px;
    border: 2px solid;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}}

/* ✅ Alertas de éxito - Verde teal suave */
.stAlert[data-baseweb="notification"] div[data-testid="stNotificationContentSuccess"] {{
    background-color: {ANCLORA_RAG_COLORS["success_light"]} !important;
    border-color: {ANCLORA_RAG_COLORS["success_deep"]} !important;
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
}}

/* ⚠️ Alertas de advertencia - Ámbar suave */
.stAlert[data-baseweb="notification"] div[data-testid="stNotificationContentWarning"] {{
    background-color: {ANCLORA_RAG_COLORS["warning_light"]} !important;
    border-color: {ANCLORA_RAG_COLORS["warning_deep"]} !important;
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
}}

/* 💝 Alertas de error - Rosa coral suave (NO rojo agresivo) */
.stAlert[data-baseweb="notification"] div[data-testid="stNotificationContentError"] {{
    background-color: {ANCLORA_RAG_COLORS["error_light"]} !important;
    border-color: {ANCLORA_RAG_COLORS["error_deep"]} !important;
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
}}

/* ℹ️ Alertas de información - Azul teal suave */
.stAlert[data-baseweb="notification"] div[data-testid="stNotificationContentInfo"] {{
    background-color: {ANCLORA_RAG_COLORS["primary_light"]} !important;
    border-color: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
}}

/* 🔘 Botones principales con estilo Anclora RAG */
.stButton > button {{
    background: {GRADIENTS["primary"]} !important;
    border: 2px solid {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    border-radius: 12px !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}}

.stButton > button:hover {{
    background: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    border-color: {ANCLORA_RAG_COLORS["ai_accent"]} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important;
}}

/* 📊 Métricas con estilo RAG */
.metric-container {{
    background: {ANCLORA_RAG_COLORS["neutral_light"]} !important;
    border: 2px solid {ANCLORA_RAG_COLORS["primary_light"]} !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
}}

/* 🎨 Sidebar con gradiente RAG */
.css-1d391kg {{
    background: {GRADIENTS["primary"]} !important;
}}

/* 📝 Títulos con color RAG */
h1, h2, h3 {{
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
    font-weight: 700 !important;
}}

h1 {{
    color: {ANCLORA_RAG_COLORS["primary_deep"]} !important;
}}

/* 🎛️ Selectbox y otros inputs con bordes RAG */
.stSelectbox > div > div {{
    border-color: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}}

.stSelectbox > div > div:focus-within {{
    border-color: {ANCLORA_RAG_COLORS["ai_accent"]} !important;
    box-shadow: 0 0 0 2px {ANCLORA_RAG_COLORS["primary_light"]} !important;
}}

/* 📊 Progress bars con degradado sutil */
.stProgress > div > div {{
    background: {GRADIENTS["success"]} !important;
    border-radius: 10px !important;
}}

/* 📑 Tabs con degradados suaves y alta legibilidad */
.stTabs [data-baseweb="tab-list"] {{
    background: {ANCLORA_RAG_COLORS["neutral_light"]} !important;
    border-radius: 12px 12px 0 0 !important;
    padding: 0.5rem !important;
}}

.stTabs [data-baseweb="tab"] {{
    background-color: transparent !important;
    border: 2px solid transparent !important;
    border-radius: 8px !important;
    color: {ANCLORA_RAG_COLORS["text_secondary"]} !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background: {ANCLORA_RAG_COLORS["primary_ultra_light"]} !important;
    color: {ANCLORA_RAG_COLORS["text_primary"]} !important;
}}

.stTabs [aria-selected="true"] {{
    background: {GRADIENTS["primary"]} !important;
    border-color: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}}

/* 📂 Expander con degradado sutil */
.streamlit-expanderHeader {{
    background: {GRADIENTS["primary"]} !important;
    border: 2px solid {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    border-radius: 12px !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    font-weight: 600 !important;
}}

/* 📋 Dataframes con bordes elegantes */
.stDataFrame {{
    border: 2px solid {ANCLORA_RAG_COLORS["primary_light"]} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
}}

/* 📁 File uploader con degradado atractivo pero legible */
.stFileUploader > div {{
    border: 3px dashed {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    border-radius: 16px !important;
    background: {GRADIENTS["primary"]} !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}}

.stFileUploader > div:hover {{
    border-color: {ANCLORA_RAG_COLORS["ai_accent"]} !important;
    background: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.1) !important;
}}

/* ⏳ Spinner con colores RAG */
.stSpinner > div {{
    border-top-color: {ANCLORA_RAG_COLORS["ai_accent"]} !important;
    border-right-color: {ANCLORA_RAG_COLORS["primary_medium"]} !important;
}}

/* 🎨 Elementos especiales con degradados para Landing/MVP */
.anclora-hero-section {{
    background: {GRADIENTS["primary"]} !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    padding: 3rem 2rem !important;
    border-radius: 20px !important;
    text-align: center !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1) !important;
}}

.anclora-feature-card {{
    background: {ANCLORA_RAG_COLORS["neutral_medium"]} !important;
    border: 2px solid {ANCLORA_RAG_COLORS["primary_light"]} !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.05) !important;
}}

.anclora-feature-card:hover {{
    background: {GRADIENTS["primary"]} !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 32px rgba(0,0,0,0.15) !important;
}}

.anclora-cta-button {{
    background: {GRADIENTS["success"]} !important;
    border: none !important;
    border-radius: 12px !important;
    color: {ANCLORA_RAG_COLORS["text_inverse"]} !important;
    font-weight: 700 !important;
    padding: 1rem 2rem !important;
    font-size: 1.1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
}}

.anclora-cta-button:hover {{
    background: {ANCLORA_RAG_COLORS["success_deep"]} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
}}
</style>
"""

def apply_anclora_theme():
    """🎨 Aplica el tema exclusivo de colores Anclora RAG a Streamlit"""
    import streamlit as st
    st.markdown(ANCLORA_RAG_CSS, unsafe_allow_html=True)

# Funciones de utilidad para crear elementos con colores Anclora
def create_colored_metric(title: str, value: str, delta: str = None, color_context: str = "info"):
    """Crea una métrica con colores Anclora"""
    colors = get_context_colors(color_context)
    
    return f"""
    <div style="
        background: {colors['background']};
        border: 1px solid {colors['border']};
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    ">
        <h3 style="color: {colors['text']}; margin: 0; font-size: 1.2rem;">{title}</h3>
        <h2 style="color: {colors['accent']}; margin: 0.5rem 0; font-size: 2rem;">{value}</h2>
        {f'<p style="color: {colors["text"]}; margin: 0; font-size: 0.9rem;">{delta}</p>' if delta else ''}
    </div>
    """

def create_colored_alert(message: str, alert_type: str = "info"):
    """Crea una alerta con colores Anclora"""
    colors = get_context_colors(alert_type)
    
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "💗",  # Corazón en lugar de X rojo
        "info": "ℹ️",
        "premium": "⭐"
    }
    
    icon = icons.get(alert_type, "ℹ️")
    
    return f"""
    <div style="
        background: {colors['background']};
        border: 1px solid {colors['border']};
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid {colors['accent']};
    ">
        <p style="color: {colors['text']}; margin: 0;">
            <strong>{icon} {message}</strong>
        </p>
    </div>
    """
