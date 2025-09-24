# Plan de Implementación de Mejoras - Anclora AI RAG

## Propósito del Repositorio

- Plataforma RAG que permite consultar documentos propios mediante una interfaz Streamlit.
- Despliegue con Docker Compose: servicios para Ollama (LLM), ChromaDB (almacen vectorial) y la UI.
- Scripts auxiliares (open_rag.*, chromadb_test.py) simplifican el arranque y diagnóstico local.

## Arquitectura y Flujo Actual

- pp/Inicio.py: chat en Streamlit con historial en sesión y llamadas al pipeline RAG.
- pp/pages/Archivos.py: página de administración para ingestar, listar y solicitar eliminación de archivos.
- pp/common/langchain_module.py: construye Retriever, prompt y LLM (Ollama) por cada consulta.
- pp/common/ingest_file.py: soporta múltiples formatos, aplica RecursiveCharacterTextSplitter y persiste en la colección ectordb de Chroma.
- pp/common/assistant_prompt.py: prompt en español que define el rol "Bastet" y el tono de respuesta.
- docker-compose*.yml: variantes GPU/CPU que configuran el modelo (llama3 o phi3) y servicios requeridos.

## Funcionalidades Clave

- Chat persistente con respuestas contextuales basadas en embeddings HuggingFace ll-MiniLM-L6-v2.
- Gestión de documentos desde la UI: carga, verificación de duplicados y marcación para eliminación.
- Scripts de diagnóstico para verificar dependencias (streamlit_test.py, chromadb_test.py).
- Configuración Pyright con stubs personalizados de Streamlit para mejorar la experiencia en el IDE.

## Hallazgos y Riesgos Detectados

- Dependencia rígida de host.docker.internal que falla fuera de Docker Desktop o en Linux (pp/common/constants.py:8, pp/pages/Archivos.py:40).
- Normalización de rutas y metadatos con separador / y prefijo /tmp/ impide detectar duplicados/eliminar en Windows (pp/common/ingest_file.py:109, pp/common/ingest_file.py:159).
- Uso de rgparse dentro de Streamlit y recreación de embeddings/cliente en cada request añade latencia y puede chocar con flags propios (pp/common/langchain_module.py:47, pp/common/langchain_module.py:62).
- Variable
esponse se reutiliza tanto para la función como para la cadena devuelta, dificultando depuración (pp/Inicio.py:50).
-

equirements.txt mezcla versiones antiguas o redundantes (por ejemplo pydantic==1.10.13 con langchain==0.1.16) afectando reproducibilidad.

## Plan de Mejora por Fases

### Fase 0 · Estabilización Crítica

- Eliminar rgparse del flujo de respuesta; cachear embeddings, retriever y cliente Chroma para reuso eficiente.
- Renombrar la variable de retorno en el chat para evitar sombras (ssistant_reply, etc.).
- Normalizar rutas y metadatos de archivos con os.path y separar la lógica de duplicados/eliminación para soportar Windows/Linux.

### Fase 1 · Configuración y Portabilidad

- Parametrizar host/puerto de Chroma y otros servicios vía variables de entorno o configuración común.
- Revisar docker-compose para GPU/CPU, incluyendo volúmenes y límites coherentes y documentación clara de selección de modelo.
- Depurar
equirements.txt, fijar versiones compatibles y remover dependencias no usadas.

### Fase 2 · Experiencia y Mantenibilidad

- Mejorar feedback en la UI (spinners, mensajes de error/success consistentes, controles de estado).
- Registrar acciones clave (ingesta, eliminación, fallos) con logging estructurado.
- Centralizar utilidades compartidas (get_unique_sources_df, formateo de rutas) y cubrirlas con pruebas unitarias básicas.

### Fase 3 · Evolución

- Añadir opciones de ingesta continua (carpetas vigiladas, API) y mecanismos de autenticación básica.
- Evaluar soporte para modelos alternativos o búsqueda híbrida (densa + keyword) según necesidades futuras.
- Documentar guías de operación y monitorización para despliegues en producción.
