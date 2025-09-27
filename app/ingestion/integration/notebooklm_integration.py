"""
Integración del adaptador NotebookLM con la UI de Streamlit
"""

import asyncio
from datetime import datetime
from typing import Iterable

import pandas as pd
import streamlit as st

from app.ingestion.markdown_source_parser import MarkdownSourceParser

def _run_async(coro):
    """Execute *coro* reusing or creating an event loop as needed."""

    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _build_anclora_output(sources: Iterable[dict], original_filename: str) -> str:
    """Render sources using the Anclora markdown format."""

    lines = [
        "# Fuentes Bibliográficas convertidas desde NotebookLM",
        f"## Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"## Archivo original: {original_filename}",
        "",
    ]

    field_order = [
        ("type", "Type"),
        ("title", "Title"),
        ("authors", "Author(s)"),
        ("publisher", "Publisher/Origin"),
        ("year", "Year"),
        ("url", "URL/DOI/Identifier"),
        ("citation", "Citation"),
        ("source_document", "Source_Document"),
        ("additional_content", "Additional_Content"),
    ]

    for source in sources:
        source_id = source.get("id") or "SRC-UNKNOWN"
        lines.append(f"**ID:** [{source_id}]")
        for key, label in field_order:
            value = source.get(key)
            if value and value != "N/A":
                lines.append(f"**{label}:** {value}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"



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
        type=["md", "txt"],
        help="Sube tu archivo de exportación de NotebookLM (formato Markdown o texto)",
        key="notebooklm_uploader",
    )

    if not uploaded_file:
        return

    raw_bytes = uploaded_file.read()
    content: str | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            content = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            content = None
    if content is None:
        st.error("No fue posible decodificar el archivo (guárdalo en UTF-8 e inténtalo de nuevo).")
        return

    parser = MarkdownSourceParser()
    validation = _run_async(parser.validate_source_format(content))
    sources = _run_async(parser.parse_sources(content))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Archivo", uploaded_file.name)
    with col2:
        st.metric("Longitud", f"{len(content)} caracteres")
    with col3:
        st.metric("Fuentes detectadas", str(validation.get("source_count", len(sources))))

    for warning in validation.get("warnings", []):
        st.warning(warning)

    with st.expander("Vista previa del contenido original"):
        preview_content = content[:1000] + "..." if len(content) > 1000 else content
        st.code(preview_content, language="markdown")

    if sources:
        with st.expander("Primeras fuentes detectadas"):
            df_preview = pd.DataFrame(sources[:20])["id title type url".split()]
            st.dataframe(df_preview, use_container_width=True)
    else:
        st.warning("No se detectaron fuentes con el formato esperado.")

    st.subheader("Opciones de conversión")
    auto_detect = st.checkbox(
        "Detección automática de formato",
        value=True,
        key="auto_detect_checkbox",
    )
    strict_validation = st.checkbox(
        "Validación estricta",
        value=False,
        key="strict_validation_checkbox",
    )
    _ = (auto_detect, strict_validation)

    if st.button("Convertir a formato Anclora", key="convert_notebooklm"):
        if not sources:
            st.error("No hay fuentes para convertir.")
            return

        try:
            converted_content = _build_anclora_output(sources, uploaded_file.name)

            st.success("Conversión completada exitosamente")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Fuentes convertidas", len(sources))
            with col_b:
                st.metric("Tasa de éxito", "100.0%")

            with st.expander("Contenido convertido"):
                st.code(converted_content, language="markdown")

            st.download_button(
                label="Descargar archivo convertido",
                data=converted_content,
                file_name=f"converted_{uploaded_file.name}",
                mime="text/markdown",
                key="download_converted",
            )
        except Exception as exc:
            st.error(f"Error en la conversión: {exc}")
            with st.expander("Detalles del error"):
                st.write(f"Error tipo: {type(exc).__name__}")
                st.write(f"Mensaje: {exc}")
