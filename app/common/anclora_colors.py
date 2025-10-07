"""Anclora RAG color theme configuration"""
import streamlit as st

ANCLORA_RAG_COLORS = {
    "primary_deep": "#1a365d",
    "primary_medium": "#2a4a7f",
    "primary_light": "#3b5998",
    "secondary": "#6c757d",
    "success": "#28a745",
    "warning": "#ffc107",
    "error": "#dc3545",
    "neutral_light": "#f8f9fa",
    "neutral_medium": "#e9ecef",
    "neutral_dark": "#343a40",
    "text_primary": "#212529",
    "text_secondary": "#6c757d",
    "text_inverse": "#ffffff",
    "accent_blue": "#007bff",
    "accent_green": "#20c997",
    "accent_orange": "#fd7e14"
}

# Chart colors for consistent theming across all visualizations
CHART_COLORS = {
    "primary": ANCLORA_RAG_COLORS["primary_medium"],
    "secondary": ANCLORA_RAG_COLORS["secondary"],
    "success": ANCLORA_RAG_COLORS["success"],
    "warning": ANCLORA_RAG_COLORS["warning"],
    "error": ANCLORA_RAG_COLORS["error"],
    "accent_blue": ANCLORA_RAG_COLORS["accent_blue"],
    "accent_green": ANCLORA_RAG_COLORS["accent_green"],
    "text_primary": ANCLORA_RAG_COLORS["text_primary"],
    "grid_lines": "#e0e0e0",
    "background": ANCLORA_RAG_COLORS["neutral_light"]
}

GRADIENTS = {
    "primary": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['primary_medium']}, {ANCLORA_RAG_COLORS['primary_deep']})",
    "secondary": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['secondary']}, {ANCLORA_RAG_COLORS['neutral_dark']})",
    "success": f"linear-gradient(135deg, {ANCLORA_RAG_COLORS['success']}, {ANCLORA_RAG_COLORS['accent_green']})"
}

def _inject_theme_css(css_content: str) -> None:
    """Inject theme CSS content properly into Streamlit app."""
    try:
        # Try using components.html for CSS injection (most reliable method)
        from streamlit.components.v1 import html
        html(f"<style>{css_content}</style>")
    except Exception:
        # Fallback to markdown if components.html fails
        try:
            st.markdown(f"<style>{css_content}</style>")
        except Exception:
            # Final fallback - just write the CSS (will show as text)
            st.code(css_content, language='css')

def apply_anclora_theme():
    """Apply Anclora RAG color theme to Streamlit"""
    css = f"""
    /* 🎨 Tema principal Anclora RAG */
    .stApp {{
        background-color: {ANCLORA_RAG_COLORS['neutral_light']};
    }}

    /* 📊 Métricas con fondo de gradiente */
    .stMetric {{
        background: {GRADIENTS['primary']};
        border-radius: 12px;
        padding: 15px;
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']};
    }}

    .stMetric label {{
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        font-weight: 600 !important;
    }}

    .stMetric value {{
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        font-weight: 700 !important;
    }}

    /* 📋 Tabs con estilo Anclora */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {ANCLORA_RAG_COLORS['neutral_light']};
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {ANCLORA_RAG_COLORS['neutral_medium']};
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        color: {ANCLORA_RAG_COLORS['text_primary']};
        border: 2px solid {ANCLORA_RAG_COLORS['neutral_medium']};
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        background: {GRADIENTS['primary']} !important;
        border-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }}

    /* 📂 Expander con degradado sutil */
    .streamlit-expanderHeader {{
        background: {GRADIENTS['primary']} !important;
        border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
        border-radius: 12px !important;
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        font-weight: 600 !important;
    }}

    /* 📋 Dataframes con bordes elegantes */
    .stDataFrame {{
        border: 2px solid {ANCLORA_RAG_COLORS['primary_light']} !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }}

    /* 📁 File uploader con degradado atractivo pero legible */
    .stFileUploader > div {{
        border: 3px dashed {ANCLORA_RAG_COLORS['primary_medium']} !important;
        border-radius: 16px !important;
        background: {GRADIENTS['primary']} !important;
        color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}

    /* 🎯 Botones con estilo Anclora */
    .stButton > button {{
        background: {GRADIENTS['primary']};
        color: {ANCLORA_RAG_COLORS['text_inverse']};
        border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}

    .stButton > button:hover {{
        background: {ANCLORA_RAG_COLORS['primary_deep']};
        border-color: {ANCLORA_RAG_COLORS['primary_deep']};
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    /* ✅ Mensajes de éxito */
    .stAlert [data-baseweb="notification"] {{
        background-color: {ANCLORA_RAG_COLORS['success']}15;
        border: 2px solid {ANCLORA_RAG_COLORS['success']};
        border-radius: 8px;
        color: {ANCLORA_RAG_COLORS['text_primary']};
    }}

    /* ⚠️ Mensajes de advertencia */
    .stWarning [data-baseweb="notification"] {{
        background-color: {ANCLORA_RAG_COLORS['warning']}15;
        border: 2px solid {ANCLORA_RAG_COLORS['warning']};
        border-radius: 8px;
        color: {ANCLORA_RAG_COLORS['text_primary']};
    }}

    /* ❌ Mensajes de error */
    .stError [data-baseweb="notification"] {{
        background-color: {ANCLORA_RAG_COLORS['error']}15;
        border: 2px solid {ANCLORA_RAG_COLORS['error']};
        border-radius: 8px;
        color: {ANCLORA_RAG_COLORS['text_primary']};
    }}
    """
    # Use safe CSS injection function to properly inject CSS
    _inject_theme_css(css)

def create_colored_alert(message: str, alert_type: str = "info") -> str:
    """Create a colored alert box"""
    color_map = {
        "info": ANCLORA_RAG_COLORS["primary_medium"],
        "success": ANCLORA_RAG_COLORS["success"],
        "warning": ANCLORA_RAG_COLORS["warning"],
        "error": ANCLORA_RAG_COLORS["error"]
    }
    
    color = color_map.get(alert_type, ANCLORA_RAG_COLORS["neutral_medium"])
    
    return f"""
    <div style="
        background-color: {color}15;
        border: 2px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: {ANCLORA_RAG_COLORS['text_primary']};
    ">
        {message}
    </div>
    """
