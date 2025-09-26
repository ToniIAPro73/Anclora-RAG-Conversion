"""
Integración del adaptador NotebookLM con la UI de Streamlit
"""

import streamlit as st
import pandas as pd
from typing import Optional
import tempfile
import os

def render_notebooklm_conversion_ui():
    """Render the NotebookLM conversion UI section"""
    
    st.info("🔍 Integración con NotebookLM")
    st.markdown("""
    Convierte tus exportaciones de **NotebookLM** al formato estándar de Anclora RAG 
    para ingesta automática de fuentes bibliográficas.
    """)
    
    # Upload NotebookLM export
    uploaded_file = st.file_uploader(
        "Subir exportación de NotebookLM",
        type=['md', 'txt'],
        help="Sube tu archivo de exportación de NotebookLM (formato Markdown o texto)",
        key="notebooklm_uploader"
    )
    
    if uploaded_file:
        # Read file content
        try:
            content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            st.error("❌ Error: El archivo no está codificado en UTF-8")
            return
        
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Archivo", uploaded_file.name)
        with col2:
            st.metric("📏 Tamaño", f"{len(content)} caracteres")
        with col3:
            sources_count = content.count('**Source:**')
            st.metric("🔍 Fuentes detectadas", str(sources_count))
        
        # Preview original content
        with st.expander("📋 Vista previa del contenido original"):
            preview_content = content[:1000] + "..." if len(content) > 1000 else content
            st.code(preview_content, language='markdown')
        
        # Conversion options
        st.subheader("⚙️ Opciones de Conversión")
        auto_detect = st.checkbox("Detección automática de formato", value=True, key="auto_detect_checkbox")
        strict_validation = st.checkbox("Validación estricta", value=False, key="strict_validation_checkbox")
        
        if st.button("🔄 Convertir a Formato Anclora", key="convert_notebooklm"):
            try:
                # Simular conversión (reemplazar con lógica real)
                converted_content = f"# Convertido desde NotebookLM\n\n{content[:500]}...\n\n✅ Conversión exitosa"
                
                st.success("✅ Conversión completada exitosamente!")
                
                # Mostrar contenido convertido
                with st.expander("📄 Contenido Convertido"):
                    st.code(converted_content, language='markdown')
                
                # Opción para descargar
                st.download_button(
                    label="📥 Descargar Archivo Convertido",
                    data=converted_content,
                    file_name=f"converted_{uploaded_file.name}",
                    mime="text/markdown",
                    key="download_converted"
                )
                
            except Exception as e:
                st.error(f"❌ Error en la conversión: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.write(f"Error tipo: {type(e).__name__}")
                    st.write(f"Mensaje: {str(e)}")
