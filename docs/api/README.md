# Documentación de la API Anclora RAG

Esta guía resume cómo iniciar la API localmente, consultar la documentación interactiva y probar los endpoints más importantes con ejemplos en español e inglés.

## Requisitos previos

- Python 3.12 o superior.
- Dependencias instaladas (ver `app/requirements.txt`).
- Variables de entorno opcionales:
  - `MODEL`: nombre del modelo Ollama para respuestas RAG (por defecto usa el modelo configurado en el servidor Ollama).
  - `EMBEDDINGS_MODEL_NAME`: modelo de *sentence transformers* para embeddings (por defecto `all-MiniLM-L6-v2`).

## Inicio rápido

```bash
cd /workspace/Anclora-AI-RAG
PYTHONPATH=app uvicorn api_endpoints:app --host 0.0.0.0 --port 8000
```

> **Nota:** La variable `PYTHONPATH=app` es necesaria para que los módulos del directorio `app/common` se resuelvan correctamente.

Una vez iniciado el servidor:

- Documentación interactiva (Swagger UI): <http://127.0.0.1:8000/docs>
- Esquema OpenAPI en JSON: <http://127.0.0.1:8000/openapi.json>

También se incluye una copia estática del esquema en `docs/api/openapi.json` para referencia offline.

## Autenticación

Todos los endpoints protegidos requieren el encabezado `Authorization` con un token Bearer. Por defecto se valida contra la cadena `your-api-key-here`.

```http
Authorization: Bearer your-api-key-here
```

## Endpoints principales

### 1. `/health` — Health check / Verificación de estado

- **Método:** `GET`
- **Descripción ES:** Verifica el estado de la API y los servicios críticos.
- **Descripción EN:** Checks API status, version and dependent services.
- **Respuesta de ejemplo:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "chroma_db": "healthy",
    "ollama": "healthy",
    "rag_system": "healthy"
  }
}
```

### 2. `/chat` — Conversación con el RAG / Chat with RAG

- **Método:** `POST`
- **Autenticación:** requerida.
- **Descripción ES:** Envía una consulta al motor RAG y recibe una respuesta contextualizada.
- **Descripción EN:** Sends a query to the RAG engine and returns a contextualised answer.
- **Cuerpo de ejemplo (ES):**

```json
{
  "message": "¿Cuál es la política de respaldo de datos?",
  "max_length": 800,
  "language": "es"
}
```

- **Cuerpo de ejemplo (EN):**

```json
{
  "message": "Provide a summary of the onboarding process.",
  "max_length": 600,
  "language": "en"
}
```

- **Respuesta típica:**

```json
{
  "response": "La política de respaldo realiza copias incrementales cada 24 horas...",
  "status": "success",
  "timestamp": "2024-05-12T14:32:10.456789"
}
```

### 3. `/upload` — Subir documento / Upload document

- **Método:** `POST`
- **Autenticación:** requerida.
- **Contenido:** `multipart/form-data` con el archivo en el campo `file`.
- **Descripción ES:** Ingresa un documento válido al sistema RAG.
- **Descripción EN:** Uploads a supported document to the RAG knowledge base.
- **Ejemplo de llamada con `curl`:**

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@/ruta/al/documento.pdf"
```

### 4. `/documents` — Listar documentos / List documents

- **Método:** `GET`
- **Autenticación:** requerida.
- **Descripción ES:** Devuelve los nombres de archivo presentes en la base vectorial.
- **Descripción EN:** Lists stored document names in the vector database.

### 5. `/documents/{filename}` — Eliminar documento / Delete document

- **Método:** `DELETE`
- **Autenticación:** requerida.
- **Descripción ES:** Elimina la referencia de un documento.
- **Descripción EN:** Removes a document reference from the knowledge base.

## Consejos de uso

- **Idiomas soportados:** español (`es`) e inglés (`en`). Si se envía otro código se usará `es` por defecto.
- **Límites de entrada:** `max_length` controla la longitud máxima del mensaje; se puede ajustar por petición.
- **Estados y errores:** todas las respuestas siguen el modelo `status` + `response/message`; consulte Swagger UI para detalles de códigos HTTP.
- **Regenerar esquema:** después de cambios en la API, reinicie el servidor y ejecute:
  ```bash
  curl -s http://127.0.0.1:8000/openapi.json > docs/api/openapi.json
  ```

Con estos pasos podrá probar la API rápidamente y explorar toda la documentación en Swagger UI.
