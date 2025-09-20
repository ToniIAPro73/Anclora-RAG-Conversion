import streamlit as st
import base64
import os


def hide_streamlit_style():
    """Oculta los estilos por defecto de Streamlit y aplica fondo de pantalla."""

    # Hide menu items using page config (modern approach)
    st.set_page_config(
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Función para convertir imagen a base64
    def get_base64_image(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except Exception as e:
            st.warning(f"Could not load background image {image_path}: {e}. Using gradient fallback.")
            return None

    # Intentar cargar la imagen bg5.png
    image_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'bg5.png')
    base64_image = get_base64_image(image_path)

    if base64_image:
        # Usar imagen en base64
        background_css = f"""
            background-image: url('data:image/png;base64,{base64_image}');
        """
    else:
        # Fallback a gradiente si no se puede cargar la imagen
        background_css = """
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        """


    hide_st_style = f"""
        <style>

            /* Modern Streamlit selectors */
            .stMainMenu {{visibility: hidden;}}
            .stDeployButton {{display:none;}}
            .stFooter {{visibility: hidden;}}
            .stDecoration {{display:none;}}

            /* Fondo de pantalla con imagen responsive */
            .stApp {{
                {background_css}
                background-size: cover;
                background-position: center center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                min-height: 100vh;
                width: 100%;
            }}

            /* Asegurar que el body y html también tengan el fondo */
            html, body {{
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
                {background_css}
                background-size: cover;
                background-position: center center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}

            /* Responsive design para diferentes tamaños de pantalla */
            @media (max-width: 768px) {{
                .stApp {{
                    background-size: cover;
                    background-position: center center;
                }}
            }}

            @media (max-width: 480px) {{
                .stApp {{
                    background-position: center top;
                }}
            }}



            /* Ocultar el título original de Streamlit */
            .stTitle {{
                display: none !important;
            }}

            /* Make chat message boxes completely opaque with black background */
            .stChatMessage {{
                background-color: rgba(0, 0, 0, 0.9) !important;
                backdrop-filter: blur(10px) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 8px !important;
                padding: 16px !important;
                margin: 8px 0 !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
                color: white !important;
            }}

            .stChatMessage * {{
                color: white !important;
            }}

            .stChatInput {{
                background-color: rgba(0, 0, 0, 0.9) !important;
                backdrop-filter: blur(10px) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 8px !important;
                color: white !important;
            }}

            .stChatInput * {{
                color: white !important;
            }}

            .stChatInput input {{
                background-color: transparent !important;
                color: white !important;
            }}

            .stChatInput textarea {{
                background-color: transparent !important;
                color: white !important;
            }}

            /* Adaptive background based on sidebar state */
            .stApp {{
                {background_css}
                background-size: cover;
                background-position: center center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                min-height: 100vh;
                width: 100%;
                position: relative;
                overflow: hidden;
            }}

            /* Overlay sutil para reducir la prominencia del fondo */
            .stApp::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.2);
                backdrop-filter: blur(0.5px);
                z-index: -1;
                pointer-events: none;
            }}

            /* Main content area */
            .stMain {{
                padding: 20px !important;
                min-height: calc(100vh - 40px) !important;
                position: relative;
                z-index: auto;
            }}

            /* Background positioning based on sidebar state */
            .stSidebar[aria-expanded="true"] ~ .stMain {{
                background-position: right center;
            }}

            .stSidebar[aria-expanded="false"] ~ .stMain {{
                background-position: center center;
            }}

            /* Fallback for browsers that don't support :has() */
            @supports not selector(:has(*)) {{
                .stMain {{
                    background-position: center center;
                }}
            }}

            /* Ensure proper layering */
            .stApp > div:first-child {{
                position: relative;
                z-index: 0;
            }}

            /* Ensure all Streamlit elements are visible */
            [data-testid="stApp"] {{
                z-index: auto !important;
            }}

            [data-testid="stMain"] {{
                z-index: auto !important;
            }}

            [data-testid="stSidebar"] {{
                z-index: auto !important;
            }}

            /* Reset any problematic styles */
            .stApp * {{
                z-index: auto !important;
                visibility: visible !important;
                opacity: 1 !important;
            }}

            /* Responsive adjustments */
            @media (max-width: 768px) {{
                .stMain {{
                    padding: 15px !important;
                }}
            }}

            @media (max-width: 480px) {{
                .stMain {{
                    padding: 10px !important;
                }}
            }}


        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)