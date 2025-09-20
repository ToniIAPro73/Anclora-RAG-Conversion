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

    # Intentar cargar la imagen bg4.png
    image_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'bg4.png')
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


        </style>
    """
    st.markdown(hide_st_style, unsafe_allow_html=True)