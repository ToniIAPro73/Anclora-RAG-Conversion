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

    # Intentar cargar la imagen bg2.png
    image_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'bg2.png')
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

            /* Estilos para el título centrado */
            .main-title-container {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 1000;
                width: 100%;
                max-width: 800px;
                padding: 0 20px;
            }}

            .main-title {{
                font-size: 4rem !important;
                font-weight: 700 !important;
                color: #ffffff !important;
                text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7) !important;
                margin-bottom: 1rem !important;
                letter-spacing: 2px !important;
                line-height: 1.2 !important;
            }}

            .main-subtitle {{
                font-size: 1.2rem !important;
                font-weight: 300 !important;
                color: #ffffff !important;
                text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.5) !important;
                margin-top: 0.5rem !important;
                letter-spacing: 1px !important;
            }}

            /* Ocultar el título original de Streamlit */
            .stTitle {{
                display: none !important;
            }}

            /* Responsive para el título */
            @media (max-width: 768px) {{
                .main-title {{
                    font-size: 2.5rem !important;
                }}
                .main-subtitle {{
                    font-size: 1rem !important;
                }}
            }}

            @media (max-width: 480px) {{
                .main-title {{
                    font-size: 2rem !important;
                }}
                .main-subtitle {{
                    font-size: 0.9rem !important;
                }}
            }}
        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)