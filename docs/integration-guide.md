# Guía de Integración / Integration Guide

## Descripción general / Overview

**ES:** Este documento explica cómo integrar aplicaciones externas, agentes y asistentes con Anclora AI RAG. Se cubre tanto el consumo directo de la API REST como el uso del cliente Python incluido en el repositorio, con recomendaciones específicas para manejar caracteres Unicode y codificaciones multilingües.

**EN:** This guide walks through integrating external applications, agents, and assistants with Anclora AI RAG. It covers both the REST API and the bundled Python client, and it includes best practices for working with Unicode characters and multilingual encodings.

## Requisitos previos / Prerequisites

- **ES:** Acceso a la instancia de Anclora AI RAG (por defecto en `http://localhost:8081`).
- **EN:** Access to a running Anclora AI RAG instance (default `http://localhost:8081`).
- **ES:** Una clave de API válida configurada en `verify_token` o en el proxy que delegue la autenticación.
- **EN:** A valid API key configured in `verify_token` or the authentication proxy that fronts the service.
- **ES:** Python 3.11+ para ejecutar los ejemplos y el cliente oficial.
- **EN:** Python 3.11+ to execute the samples and the official client.

## Integración vía API REST / REST API Integration

### Autenticación / Authentication

**ES:** Todos los endpoints requieren un encabezado `Authorization: Bearer <API_KEY>`. Sustituye `your-api-key-here` por la clave configurada en el backend.

**EN:** Every endpoint expects an `Authorization: Bearer <API_KEY>` header. Replace `your-api-key-here` with the key configured on the backend.

### Endpoints principales / Core Endpoints

| Método / Method | Ruta / Path          | Descripción ES / Description EN |
|-----------------|----------------------|---------------------------------|
| GET             | `/health`            | **ES:** Estado general del sistema.  |
| POST            | `/chat`              | **ES:** Consulta al motor RAG (`message`, `max_length`, `language`).  **EN:** Ask the RAG engine (`message`, `max_length`, `language`). |
| GET             | `/documents`         | **ES:** Lista archivos disponibles.  |
| DELETE          | `/documents/{name}`  | **ES:** Elimina un archivo de la base.  **EN:** Remove a document from the knowledge base. |
| POST            | `/upload`            | **ES:** Ingresa documentos (multipart, campo `file`).  **EN:** Ingest documents (multipart `file`). |
| GET             | `/documents`         | **ES:** Lista archivos disponibles. / **EN:** List available documents. |
| DELETE          | `/documents/{name}`  | **ES:** Elimina un archivo de la base. / **EN:** Remove a document from the knowledge base. |

### Ejemplo de consulta / Query Example

```bash
curl -X POST "http://localhost:8081/chat" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
        "message": "¿Qué políticas cubre el manual corporativo?",
        "language": "es",
        "max_length": 800
      }'
```

**ES:** La respuesta incluye `response`, `status` y `timestamp`. Cambia el campo `language` a `en` para inglés; otros valores caen por defecto en español.

**EN:** The response returns `response`, `status`, and `timestamp`. Set `language` to `en` for English; unsupported values fall back to Spanish.

### Subida de archivos / Uploading Files

```bash
curl -X POST "http://localhost:8081/upload" \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@/ruta/contrato_📝.pdf"
```

**ES:** Los nombres y contenidos de archivo pueden incluir caracteres Unicode; FastAPI los preserva cuando el cliente envía datos en UTF-8.

**EN:** File names and contents may include Unicode characters; FastAPI preserves them when the client submits UTF-8 encoded data.

### Manejo de Unicode y respuestas / Unicode Handling and Responses

- **ES:** El servidor serializa JSON usando UTF-8. Asegúrate de que tu cliente defina `Content-Type: application/json; charset=utf-8` cuando envíe payloads.
- **EN:** The server serializes JSON in UTF-8. Make sure your client sets `Content-Type: application/json; charset=utf-8` when sending payloads.
- **ES:** Si tu aplicación consume texto en otros alfabetos (p. ej., árabe, japonés), mantén la cadena en Unicode nativa de tu lenguaje de programación; evita convertirla a ASCII.
- **EN:** If your app consumes non-Latin text (e.g., Arabic, Japanese), keep strings in your language's native Unicode representation; avoid ASCII coercion.
- **ES:** Cuando proceses la respuesta, usa librerías que respeten UTF-8; en Python, `response.encoding = "utf-8"` garantiza la decodificación correcta.
- **EN:** When parsing responses, rely on UTF-8 aware libraries; in Python you can force `response.encoding = "utf-8"` to ensure proper decoding.

## Cliente Python oficial / Official Python Client

### Instalación rápida / Quick Setup

```bash
# Dentro del repositorio
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**ES:** Importa `AncloraRAGClient` o `AIAgentRAGInterface` desde `anclora_rag_client.py`.

**EN:** Import `AncloraRAGClient` or `AIAgentRAGInterface` from `anclora_rag_client.py`.

### Uso básico / Basic Usage

```python
from anclora_rag_client import AncloraRAGClient

client = AncloraRAGClient(
    base_url="http://localhost:8081",
    api_key="your-api-key-here"
)

answer = client.query("List the latest compliance updates", max_length=600)
print(answer["response"])
```

**ES:** El método `query` envía cadenas Unicode sin transformación adicional. Para especificar idioma, extiende el payload: `client.session.post(..., json={"message": mensaje, "language": "es"})`.

**EN:** The `query` method forwards Unicode strings as-is. To force a language, extend the payload: `client.session.post(..., json={"message": message, "language": "en"})`.

```python
# Subir documentos con nombres Unicode
client.upload_document("./docs/póliza_seguros_2024.pdf")
```

**ES:** El cliente elimina el encabezado `Content-Type` durante uploads para que `requests` gestione correctamente multipart y codificaciones.

**EN:** The client removes the `Content-Type` header during uploads so `requests` can set the correct multipart boundary and encoding.

### Buenas prácticas de encoding / Encoding Good Practices

- **ES:** Configura `PYTHONUTF8=1` o `PYTHONIOENCODING=utf-8` en entornos Windows para forzar UTF-8 en la consola.
- **EN:** Set `PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8` on Windows environments to force UTF-8 in the console.
- **ES:** Cuando serialices JSON manualmente, usa `json.dumps(obj, ensure_ascii=False)` para preservar acentos y emojis.
- **EN:** When manually serializing JSON, call `json.dumps(obj, ensure_ascii=False)` to preserve accents and emoji characters.
- **ES:** Si consumes archivos de texto externos, abre con `open(path, encoding="utf-8")` y normaliza con `str.normalize` si debes comparar.
- **EN:** When reading external text files, call `open(path, encoding="utf-8")` and normalize with `str.normalize` if comparisons are needed.

## Integración con frameworks de agentes / Integrating with Agent Frameworks

### LangChain

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from anclora_rag_client import AncloraRAGClient

rag_client = AncloraRAGClient(api_key="your-api-key-here")

rag_tool = Tool(
    name="anclora_rag_search",
    func=lambda question: rag_client.query(question).get("response", ""),
    description=(
        "ES: Usa este tool para responder preguntas basadas en la base de conocimientos. "
        "EN: Use this tool to answer questions grounded on the knowledge base."
    )
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = initialize_agent(
    tools=[rag_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
)

result = agent.run("ES: Resume las últimas políticas de RRHH. EN: Summarize the latest HR policies.")
print(result)
```

**ES:** Para escenarios multilingües, pasa prompts bilingües como en el ejemplo o controla el idioma enviando el parámetro `language` directamente con `rag_client.session.post`.

**EN:** For multilingual scenarios, send bilingual prompts as in the example or call `rag_client.session.post` directly to set the `language` parameter.

### AutoGen

```python
from autogen import ConversableAgent
from anclora_rag_client import AIAgentRAGInterface

rag_interface = AIAgentRAGInterface(api_key="your-api-key-here")

assistant = ConversableAgent(
    name="rag_assistant",
    system_message=(
        "ES: Usa la base de conocimientos interna para responder. "
        "EN: Use the internal knowledge base when responding."
    ),
)

@assistant.register_for_llm("rag_search")
def rag_search(task: str) -> str:
    return rag_interface.ask_question(task)

conversation = assistant.generate_reply(
    messages=[{"role": "user", "content": "Analiza el contrato de servicio y resalta cláusulas críticas."}]
)
print(conversation)
```

**ES:** `AIAgentRAGInterface` maneja `health_check`, consulta y listado de documentos; úsalo para validar la disponibilidad del sistema antes de orquestar agentes colaborativos.

**EN:** `AIAgentRAGInterface` offers `health_check`, querying, and document listing; use it to validate system availability before orchestrating collaborative agents.

## Solución de problemas / Troubleshooting

- **ES:** Error 401 → revisa la clave de API y que el proxy no elimine el encabezado `Authorization`.
- **EN:** 401 errors → check the API key and ensure no proxy strips the `Authorization` header.
- **ES:** Unicode corrupto → confirma que el cliente envía `charset=utf-8` o normaliza el texto con `unicodedata.normalize('NFC', texto)`.
- **EN:** Garbled Unicode → ensure the client sends `charset=utf-8` or normalize text with `unicodedata.normalize('NFC', text)`.
- **ES:** Documentos que no aparecen → verifica `list_documents` para confirmar la ingesta y revisa los logs de `ingest_file`.
- **EN:** Missing documents → call `list_documents` to confirm ingestion and inspect `ingest_file` logs.

## Recursos adicionales / Additional Resources

- **ES:** Consulta el archivo `docs/backlog.md` para planes futuros y dependencias.
- **EN:** Review `docs/backlog.md` for roadmap plans and dependencies.
- **ES:** El código fuente de la API se encuentra en `app/api_endpoints.py`; el cliente oficial en `anclora_rag_client.py`.
- **EN:** API source lives in `app/api_endpoints.py`; the official client is `anclora_rag_client.py`.
