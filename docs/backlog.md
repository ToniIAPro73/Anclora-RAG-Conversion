# Backlog de Roadmap — Anclora AI RAG

Este documento consolida las épicas y tareas priorizadas para evolucionar la plataforma. Cada fase deriva del análisis recogido en [CODEX_PLAN_IMPLEMENTACION_MEJORAS.md](./CODEX_PLAN_IMPLEMENTACION_MEJORAS.md) y vincula las entregas con los módulos que deben actualizarse en `app/` y los artefactos de infraestructura.

## Fase 0 · Estabilización Crítica
Objetivo: reducir fallos inmediatos del flujo RAG y garantizar una experiencia consistente tras el arranque.

#### Tarea 0.1 — Cachear pipeline RAG y eliminar dependencias de CLI
- **Módulos clave:** [`app/common/langchain_module.py`](../app/common/langchain_module.py), [`app/common/chroma_db_settings.py`](../app/common/chroma_db_settings.py), [`app/Inicio.py`](../app/Inicio.py).
- **Criterios de aceptación:**
  - La inicialización de embeddings, cliente de Chroma y plantilla del LLM se realiza una única vez por sesión de Streamlit (uso de `st.cache_resource` o patrón equivalente).
  - Se elimina el uso de `argparse` y cualquier parsing de argumentos de línea de comandos dentro del ciclo de respuesta.
  - El chat en [`app/Inicio.py`](../app/Inicio.py) sigue funcionando sin excepciones, reutilizando el pipeline cacheado.
- **Dependencias principales:**
  - Servicios de `ollama` y `chromadb` definidos en `docker-compose*.yml` deben estar disponibles para validar la carga diferida.
  - Coordinación con la Tarea 0.2 para evitar regresiones en el contrato de la función `response`.

#### Tarea 0.2 — Clarificar la API del asistente en la UI
- **Módulos clave:** [`app/Inicio.py`](../app/Inicio.py), [`app/common/langchain_module.py`](../app/common/langchain_module.py).
- **Criterios de aceptación:**
  - La función expuesta por `langchain_module` se renombra de forma explícita (por ejemplo `generate_response`) y se actualizan todas las llamadas.
  - Se documenta mediante docstring la firma soportada (manejo opcional del idioma) y se cubren errores controlados en la UI.
  - El historial de conversación en `st.session_state` persiste tras múltiples llamadas y renombrados.
- **Dependencias principales:**
  - Debe ejecutarse tras la Tarea 0.1 para usar la versión cacheada del pipeline.
  - Requiere coordinación con las traducciones en [`app/common/translations.py`](../app/common/translations.py) para mantener mensajes coherentes.

#### Tarea 0.3 — Normalizar rutas y metadatos de archivos
- **Módulos clave:** [`app/common/ingest_file.py`](../app/common/ingest_file.py), [`app/pages/Archivos.py`](../app/pages/Archivos.py).
- **Criterios de aceptación:**
  - Se emplean utilidades de `os.path`/`pathlib` para crear rutas compatibles con Windows, Linux y macOS.
  - La detección de duplicados y eliminación en `delete_file_from_vectordb` funciona con rutas relativas desde la colección `vectordb`.
  - Las pruebas manuales cargando/eliminando archivos en los tres principales sistemas operativos no generan errores de normalización.
- **Dependencias principales:**
  - Requiere acceso a la colección Chroma creada en la Tarea 0.1.
  - Depende de la estructura definida en `docker-compose` para montar volúmenes consistentes.

## Fase 1 · Configuración y Portabilidad
Objetivo: facilitar despliegues reproducibles sin editar código fuente.

#### Tarea 1.1 — Externalizar configuración de servicios
- **Módulos clave:** [`app/common/constants.py`](../app/common/constants.py), [`app/pages/Archivos.py`](../app/pages/Archivos.py), [`app/common/chroma_db_settings.py`](../app/common/chroma_db_settings.py).
- **Criterios de aceptación:**
  - Host y puerto de Chroma, así como parámetros de Ollama, se leen desde variables de entorno o archivo `.env` documentado.
  - Los valores por defecto permiten ejecutar la app en Docker Desktop y en entornos Linux sin modificaciones manuales.
  - README actualizado con instrucciones para configurar dichas variables.
- **Dependencias principales:**
  - Depende de la normalización de rutas (Tarea 0.3) para asegurar que los volúmenes mapeados respeten la configuración externa.
  - Coordinar con `docker-compose*.yml` para propagar las variables.

#### Tarea 1.2 — Revisar `docker-compose` y documentación de modelos
- **Artefactos clave:** [`docker-compose.yml`](../docker-compose.yml), [`docker-compose_sin_gpu.yml`](../docker-compose_sin_gpu.yml), [`docs/AUGMENT_SOLUCION_PROBLEMAS_RAG.md`](./AUGMENT_SOLUCION_PROBLEMAS_RAG.md).
- **Criterios de aceptación:**
  - Se actualizan los servicios con límites de recursos explícitos, volúmenes persistentes y comentarios sobre selección de modelo (`llama3` vs `phi3`).
  - La documentación menciona pasos para cambiar de modelo y explica las implicaciones de GPU/CPU.
  - Pruebas de arranque (`docker compose up`) funcionan en Windows y Linux siguiendo la guía.
- **Dependencias principales:**
  - Requiere la configuración externa de la Tarea 1.1 para evitar valores hardcodeados.
  - Coordinación con scripts `open_rag.*` para reflejar nombres de servicios actualizados.

#### Tarea 1.3 — Saneamiento de dependencias Python
- **Módulos/archivos clave:** [`app/requirements.txt`](../app/requirements.txt), [`pyrightconfig.json`](../pyrightconfig.json).
- **Criterios de aceptación:**
  - Se eliminan paquetes no utilizados y se alinea la versión de `langchain` con `pydantic`/`chromadb` compatibles.
  - Se documenta en README la secuencia de instalación local cuando no se usa Docker.
  - `pyright` o chequeo equivalente pasa sin errores de tipado.
- **Dependencias principales:**
  - Depende de la Tarea 0.1 para conocer los módulos efectivamente requeridos por el pipeline.
  - Coordinar con la Tarea 1.2 para asegurar que las imágenes Docker instalen el lock actualizado.

## Fase 2 · Experiencia y Mantenibilidad
Objetivo: mejorar la operatividad diaria y reducir deuda técnica.

#### Tarea 2.1 — Feedback consistente en la UI
- **Módulos clave:** [`app/Inicio.py`](../app/Inicio.py), [`app/pages/Archivos.py`](../app/pages/Archivos.py), [`app/common/streamlit_style.py`](../app/common/streamlit_style.py).
- **Criterios de aceptación:**
  - Se añaden indicadores de estado (`st.spinner`, `st.toast`, etc.) para ingesta y respuestas.
  - Los mensajes de error/éxito utilizan el sistema de traducciones y cubren fallos de red.
  - Tests manuales muestran que no hay mensajes duplicados ni bloqueos de la UI.
- **Dependencias principales:**
  - Requiere la API estable de la Tarea 0.2 y la configuración externa de la Tarea 1.1.

#### Tarea 2.2 — Instrumentación y logging estructurado
- **Módulos clave:** [`app/common/langchain_module.py`](../app/common/langchain_module.py), [`app/common/ingest_file.py`](../app/common/ingest_file.py), [`app/api_endpoints.py`](../app/api_endpoints.py).
- **Criterios de aceptación:**
  - Se introduce un módulo de logging compartido con niveles configurables mediante variables de entorno.
  - Eventos críticos (ingesta, eliminación, fallos del LLM) se registran con metadatos (usuario, documento, duración).
  - Logs accesibles desde contenedores Docker mediante volúmenes o `docker logs`.
- **Dependencias principales:**
  - Basado en la Tarea 1.1 para definir variables de entorno.
  - Dependiente de la refactorización de rutas de la Tarea 0.3 para reportar ubicaciones correctas.

#### Tarea 2.3 — Unificación de utilidades y pruebas básicas
- **Módulos/archivos clave:** [`app/common/ingest_file.py`](../app/common/ingest_file.py), [`app/common/chroma_db_settings.py`](../app/common/chroma_db_settings.py), `tests/` (nuevo módulo).
- **Criterios de aceptación:**
  - Se extraen funciones repetidas (normalización de rutas, acceso a colecciones) a utilidades compartidas.
  - Se añaden pruebas unitarias que cubren la manipulación de rutas y la creación de colecciones.
  - Integración con un flujo de CI simple (GitHub Actions o script de `make test`).
- **Dependencias principales:**
  - Debe ejecutarse tras la Tarea 0.3 para heredar la lógica de normalización.
  - Requiere la curación de dependencias (Tarea 1.3) para definir el entorno de pruebas.

## Fase 3 · Evolución
Objetivo: extender capacidades y preparar el terreno para escenarios empresariales.

#### Tarea 3.1 — Ingesta continua y APIs externas
- **Módulos/artefactos objetivo:** Nuevo servicio en `app/common/` o `app/api_endpoints.py`, scripts en `open_rag.*`.
- **Criterios de aceptación:**
  - Existe un proceso opcional de watch de carpetas o endpoint REST que agrega documentos automáticamente.
  - La seguridad mínima (token o API key) protege las operaciones remotas.
  - Documentación en `docs/` con ejemplos de uso.
- **Dependencias principales:**
  - Requiere logging estructurado (Tarea 2.2) para auditar acciones remotas.
  - Depende de la normalización de rutas (Tarea 0.3) para escribir archivos desde fuentes externas.

#### Tarea 3.2 — Búsqueda híbrida y soporte de modelos alternativos
- **Módulos clave:** [`app/common/langchain_module.py`](../app/common/langchain_module.py), [`app/common/chroma_db_settings.py`](../app/common/chroma_db_settings.py), [`docker-compose.yml`](../docker-compose.yml).
- **Criterios de aceptación:**
  - Se habilita la combinación de recuperación densa y basada en palabras clave configurables.
  - Se documenta cómo añadir nuevos modelos en Ollama (p. ej. `mistral`, `nomic-embed`) y se automatiza su descarga inicial.
  - Se reutiliza el `EmbeddingsManager` para orquestar modelos por dominio (MiniLM/mpnet/e5) y registrar su desempeño.
  - Pruebas exploratorias confirman que la selección de modelo puede cambiarse sin reiniciar todo el stack.
- **Dependencias principales:**
  - Requiere la limpieza de dependencias (Tarea 1.3) y la externalización de configuración (Tarea 1.1).
  - Necesita la instrumentación (Tarea 2.2) para medir calidad de respuesta al cambiar de modelo.

#### Tarea 3.3 — Guías operativas y monitorización
- **Artefactos clave:** `docs/` (nuevas guías), `docker-compose*.yml`, scripts de despliegue.
- **Criterios de aceptación:**
  - Se documentan procedimientos de backup/restauración de Chroma, rotación de tokens y escalado horizontal.
  - Se definen métricas mínimas (disponibilidad del LLM, latencia del retriever) y se sugieren integraciones con Prometheus o servicios equivalentes.
  - Existe una checklist de soporte para incidentes.
- **Dependencias principales:**
  - Basado en toda la instrumentación y mejoras previas.
  - Requiere coordinación con la comunidad/usuarios para validar las guías.

---

### Seguimiento y estados sugeridos
Se recomienda utilizar etiquetas como `fase-0`, `fase-1`, etc., y estados `por-hacer`, `en-progreso`, `bloqueado` y `hecho`. Cada tarea puede convertirse en issue y vincularse a Pull Requests que modifiquen los módulos señalados.
