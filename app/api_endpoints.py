"""API REST para acceso de agentes IA al sistema Anclora RAG."""

from __future__ import annotations

import json  # Used by UTF8JSONResponse.render for proper UTF-8 output
import logging
import os
import secrets
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.agents.base import AgentResponse, AgentTask
from app.agents.orchestrator import OrchestratorService, create_default_orchestrator
from common.privacy import PrivacyManager

try:  # pragma: no cover - compatibilidad con httpx 0.28+
    import httpx
    from inspect import signature

    _original_httpx_init = httpx.Client.__init__

    if "app" not in signature(httpx.Client.__init__).parameters:
        def _patched_httpx_init(self, *args, **kwargs):  # type: ignore[override]
            kwargs.pop("app", None)
            return _original_httpx_init(self, *args, **kwargs)

        httpx.Client.__init__ = _patched_httpx_init  # type: ignore[assignment]
except Exception:  # pragma: no cover - si httpx no está disponible
    httpx = None

# Configurar logging
logger = logging.getLogger(__name__)


class UTF8JSONResponse(JSONResponse):
    """JSONResponse que mantiene caracteres multilingües sin escapar."""

    def render(self, content) -> bytes:  # type: ignore[override]
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# Configurar FastAPI
app = FastAPI(
    title="Anclora RAG API",
    description=(
        "API REST bilingüe para consultar y administrar el sistema Anclora RAG.\n\n"
        "This bilingual REST API allows you to query and manage the Anclora RAG system."
    ),
    version="1.0.0",
    default_response_class=UTF8JSONResponse,
)

# Seguridad básica
security = HTTPBearer()
privacy_manager = PrivacyManager()


_ORCHESTRATOR: OrchestratorService | None = None


def get_orchestrator() -> OrchestratorService:
    """Return a lazily initialised orchestrator instance."""

    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = create_default_orchestrator()
    return _ORCHESTRATOR


def _normalise_language(language: Optional[str]) -> str:
    """Normalise the language parameter to the supported values."""

    candidate = (language or "es").lower()
    return candidate if candidate in {"es", "en"} else "es"


def _serialise_agent_response(
    agent_response: AgentResponse,
    *,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert an :class:`AgentResponse` into a JSON-ready dictionary."""

    payload = asdict(agent_response)
    data = payload.get("data")
    if data is None:
        payload.pop("data", None)

    metadata = payload.get("metadata") or {}
    if extra_metadata:
        for key, value in extra_metadata.items():
            if value is not None and key not in metadata:
                metadata[key] = value
    if metadata:
        payload["metadata"] = metadata
    else:
        payload.pop("metadata", None)

    if payload.get("error") is None:
        payload.pop("error", None)

    return payload


_ERROR_STATUS_MAP = {
    "question_missing": 400,
    "media_reference_missing": 400,
}


def _agent_error_status(error: Optional[str]) -> int:
    """Map agent-level error codes to HTTP status codes."""

    if not error:
        return 200
    if error in _ERROR_STATUS_MAP:
        return _ERROR_STATUS_MAP[error]
    if error.startswith("no_agent_for_"):
        return 501
    return 500


def _build_agent_http_response(
    agent_response: AgentResponse,
    *,
    extra_metadata: Optional[Dict[str, Any]] = None,
    log_context: str,
) -> UTF8JSONResponse:
    """Serialise ``agent_response`` and wrap it into an HTTP response."""

    payload = _serialise_agent_response(agent_response, extra_metadata=extra_metadata)
    status_code = 200 if agent_response.success else _agent_error_status(agent_response.error)
    if not agent_response.success:
        logger.warning("%s failed with agent error: %s", log_context, agent_response.error)
    return UTF8JSONResponse(content=payload, status_code=status_code)

# Modelos Pydantic
class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description=(
            "Mensaje de la consulta o pregunta que se enviará al motor RAG.\n"
            "Query message or question that will be processed by the RAG engine."
        ),
        example="¿Cuál es la política de respaldo de datos?"
    )
    max_length: Optional[int] = Field(
        1000,
        description=(
            "Longitud máxima permitida para el mensaje. Ajusta el límite si necesitas respuestas extensas.\n"
            "Maximum number of characters allowed in the message. Increase the limit for longer prompts."
        ),
        example=800
    )
    language: Optional[str] = Field(
        'es',
        description=(
            "Idioma preferido para la respuesta (`es` o `en`).\n"
            "Preferred response language (`es` or `en`)."
        ),
        example="en"
    )

    class Config:
        schema_extra = {
            "example": {
                "message": "Provide a summary of the onboarding process.",
                "max_length": 600,
                "language": "en"
            },
            "examples": [
                {
                    "message": "¿Cuál es el estado del informe trimestral?",
                    "max_length": 800,
                    "language": "es",
                },
                {
                    "message": "What's the status of the quarterly report?",
                    "max_length": 800,
                    "language": "en",
                },
            ]
        }

class AgentResponseModel(BaseModel):
    success: bool = Field(
        ...,
        description=(
            "Indica si la tarea fue atendida exitosamente por un agente especializado.\n"
            "Whether the orchestrated agent completed the task successfully."
        ),
        example=True,
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Carga útil retornada por el agente cuando la operación es exitosa.\n"
            "Payload returned by the agent for successful operations."
        ),
        example={"answer": "La política de respaldo realiza copias incrementales cada 24 horas."},
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Metadatos auxiliares (idioma, marca temporal, tipo de tarea) útiles para la interfaz.\n"
            "Auxiliary metadata (language, timestamp, task type) useful for clients."
        ),
        example={"language": "es", "timestamp": "2024-05-12T14:32:10.456789", "task_type": "document_query"},
    )
    error: Optional[str] = Field(
        default=None,
        description=(
            "Código de error retornado por el agente cuando `success` es `False`.\n"
            "Agent-specific error code when `success` is `False`."
        ),
        example="question_missing",
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"answer": "La base de conocimiento contiene 12 documentos."},
                "metadata": {
                    "language": "es",
                    "timestamp": "2024-05-04T12:00:00",
                    "task_type": "document_query",
                },
            },
            "examples": [
                {
                    "success": False,
                    "error": "question_missing",
                    "metadata": {"task_type": "document_query", "language": "es"},
                },
                {
                    "success": True,
                    "data": {"answer": "Transcripción disponible."},
                    "metadata": {"task_type": "media_transcription", "language": "en"},
                },
            ],
        }


class MediaTranscriptionRequest(BaseModel):
    media: str = Field(
        ...,
        description=(
            "Identificador o ruta del recurso multimedia a transcribir.\n"
            "Identifier or path of the media resource to transcribe."
        ),
        example="s3://datasets/anclora/reuniones/standup-2024-05-01.mp3",
    )
    language: Optional[str] = Field(
        default=None,
        description=(
            "Idioma sugerido para la transcripción o resumen resultante.\n"
            "Preferred language for the generated transcription or summary."
        ),
        example="es",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Metadatos adicionales (ej. tipo de reunión, participante principal).\n"
            "Optional metadata such as meeting type or main speaker."
        ),
        example={"meeting": "daily", "speaker": "analyst"},
    )

    class Config:
        schema_extra = {
            "example": {
                "media": "https://storage.example.com/audios/demo.wav",
                "language": "en",
                "metadata": {"department": "marketing"},
            }
        }


class ForgetRequest(BaseModel):
    filename: str = Field(
        ...,
        description="Nombre exacto del archivo que debe eliminarse de la base de conocimiento.",
        example="informe_trimestral.pdf",
    )
    subject_id: Optional[str] = Field(
        default=None,
        description="Identificador del titular de los datos que solicita el borrado.",
        example="cliente-123",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Motivo o referencia interna asociada a la solicitud del derecho al olvido.",
        example="Solicitud formal recibida el 2024-05-20",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metadatos adicionales que deban registrarse en la auditoría (se anonimizarán automáticamente).",
        example={"canal": "portal_privacidad", "ticket": "GDPR-77"},
    )


class ForgetResponse(BaseModel):
    status: str = Field(..., description="Resultado general de la operación.")
    message: str = Field(..., description="Detalle resumido del resultado del proceso.")
    audit_id: str = Field(..., description="Identificador único del registro de auditoría generado.")
    removed_collections: List[str] = Field(
        default_factory=list,
        description="Colecciones de ChromaDB donde se localizaron y eliminaron referencias al archivo.",
    )
    removed_files: List[str] = Field(
        default_factory=list,
        description="Rutas de artefactos temporales eliminados durante la solicitud.",
    )


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Compatibility helper to serialise Pydantic models across versions."""

    dump_method = getattr(model, "model_dump", None)
    if callable(dump_method):
        return dump_method()
    return model.dict()


class FileInfo(BaseModel):
    filename: str = Field(
        ...,
        description=(
            "Nombre del archivo almacenado en la base de conocimiento.\n"
            "Filename stored in the knowledge base."
        ),
        example="politica_seguridad.pdf"
    )
    status: str = Field(
        ...,
        description=(
            "Estado del procesamiento del archivo.\n"
            "Processing status for the uploaded file."
        ),
        example="indexed"
    )

    class Config:
        schema_extra = {
            "example": {
                "filename": "manual_instalacion.docx",
                "status": "indexed"
            }
        }

class HealthResponse(BaseModel):
    status: str = Field(
        ...,
        description=(
            "Estado global del sistema.\n"
            "Overall health status of the system."
        ),
        example="healthy"
    )
    version: str = Field(
        ...,
        description=(
            "Versión desplegada de la API.\n"
            "Deployed API version."
        ),
        example="1.0.0"
    )
    services: dict = Field(
        ...,
        description=(
            "Mapa de servicios críticos y su estado operativo.\n"
            "Mapping of critical services and their operational status."
        ),
        example={"chroma_db": "healthy", "ollama": "healthy"}
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "services": {
                    "chroma_db": "healthy",
                    "ollama": "healthy",
                    "rag_system": "healthy"
                }
            }
        }

try:  # pragma: no cover - la dependencia es opcional
    import jwt
    from jwt import PyJWTError
except Exception:  # pragma: no cover - entorno sin PyJWT
    jwt = None
    PyJWTError = Exception


def _get_allowed_tokens() -> List[str]:
    """Obtener los tokens válidos definidos en variables de entorno."""

    tokens: List[str] = []
    raw_tokens = os.getenv("ANCLORA_API_TOKENS")
    if raw_tokens:
        tokens.extend(
            token.strip() for token in raw_tokens.split(",") if token.strip()
        )

    single_token = os.getenv("ANCLORA_API_TOKEN")
    if single_token and single_token.strip():
        tokens.append(single_token.strip())

    if not tokens:
        default_token = os.getenv("ANCLORA_DEFAULT_API_TOKEN", "your-api-key-here")
        if default_token:
            tokens.append(default_token)

    # Mantener el orden pero eliminar duplicados
    seen = set()
    ordered_tokens: List[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered_tokens.append(token)

    return ordered_tokens


def _verify_jwt_token(token: str, secret: str) -> None:
    """Validar un JWT empleando la configuración del entorno."""

    if jwt is None:
        logger.error(
            "ANCLORA_JWT_SECRET está configurado pero PyJWT no está instalado"
        )
        raise HTTPException(
            status_code=500,
            detail="Configuración de autenticación inválida",
        )

    algorithms_env = os.getenv("ANCLORA_JWT_ALGORITHMS", "HS256")
    algorithms = [alg.strip() for alg in algorithms_env.split(",") if alg.strip()]
    if not algorithms:
        algorithms = ["HS256"]

    audience = os.getenv("ANCLORA_JWT_AUDIENCE")
    issuer = os.getenv("ANCLORA_JWT_ISSUER")

    decode_kwargs = {
        "algorithms": algorithms,
        "audience": audience or None,
        "issuer": issuer or None,
        "options": {"verify_aud": bool(audience)},
    }

    try:
        jwt.decode(token, secret, **decode_kwargs)
    except PyJWTError as exc:  # pragma: no cover - depende del contenido del token
        logger.warning("JWT inválido: %s", exc)
        raise HTTPException(status_code=401, detail="Token inválido") from exc


# Función de autenticación basada en variables de entorno / JWT
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar que el token recibido coincide con la configuración del entorno."""

    provided_token = credentials.credentials
    allowed_tokens = _get_allowed_tokens()

    for allowed in allowed_tokens:
        if secrets.compare_digest(provided_token, allowed):
            return provided_token

    jwt_secret = os.getenv("ANCLORA_JWT_SECRET")
    if jwt_secret:
        _verify_jwt_token(provided_token, jwt_secret)
        return provided_token

    if allowed_tokens:
        logger.warning("Intento de acceso con token no autorizado")
        raise HTTPException(status_code=401, detail="Token inválido")

    logger.error("No se configuraron credenciales de acceso para la API")
    raise HTTPException(status_code=500, detail="Autenticación no configurada")

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check / Verificación de estado",
    description=(
        "Verifica el estado general de la API, reporta la versión y el estado de los servicios críticos.\n\n"
        "Checks the overall API health, the deployed version, and reports the status of critical services."
    )
)
async def health_check():
    """Verifica la disponibilidad del sistema / Check system availability."""
    try:
        # Verificar servicios
        services_status = {
            "chroma_db": "healthy",
            "ollama": "healthy",
            "rag_system": "healthy"
        }
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            services=services_status
        )
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=503, detail="Servicio no disponible")

@app.post(
    "/chat",
    response_model=AgentResponseModel,
    summary="Conversación con el RAG / Chat with RAG",
    description=(
        "Envía una consulta en español o inglés al motor RAG y recibe una respuesta contextualizada.\n\n"
        "Send a Spanish or English query to the RAG engine and receive a contextualised answer."
    ),
)
async def chat_with_rag(
    request: ChatRequest = Body(
        ...,
        examples={
            "consulta_es": {
                "summary": "Consulta en español",
                "description": "Solicitud con caracteres acentuados para validar soporte UTF-8.",
                "value": {
                    "message": "¿Cuál es el estado del informe trimestral?",
                    "language": "es",
                    "max_length": 600,
                },
            },
            "query_en": {
                "summary": "Request in English",
                "description": "English request that showcases ñ/accents in the payload.",
                "value": {
                    "message": "Please summarize the jalapeño market update.",
                    "language": "en",
                    "max_length": 600,
                },
            },
        },
    ),
    token: str = Depends(verify_token)
):
    """Realiza consultas conversacionales al sistema Anclora RAG."""
    try:
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Mensaje vacío")

        if len(request.message) > request.max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Mensaje demasiado largo (máximo {request.max_length} caracteres)",
            )

        logger.info("Procesando consulta API: %s...", request.message[:50])
        language = _normalise_language(request.language)

        orchestrator = get_orchestrator()
        task = AgentTask(
            task_type="document_query",
            payload={
                "question": request.message,
                "language": language,
                "max_length": request.max_length,
            },
        )
        agent_response = orchestrator.execute(task)

        metadata = {
            "language": language,
            "task_type": task.task_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return _build_agent_http_response(
            agent_response,
            extra_metadata=metadata,
            log_context="chat_document_query",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error en chat API: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno del servidor") from exc


@app.post(
    "/media/transcription",
    response_model=AgentResponseModel,
    summary="Transcribir contenido multimedia / Media transcription",
    description=(
        "Envía un recurso multimedia para obtener una transcripción resumida.\n\n"
        "Submit a media resource and obtain a summarised transcription."
    ),
)
async def media_transcription(
    request: MediaTranscriptionRequest,
    token: str = Depends(verify_token),
):
    """Orquesta una solicitud de transcripción multimedia mediante el orquestador."""

    del token  # La autenticación se valida mediante el dependency injector.

    if not request.media or len(request.media.strip()) == 0:
        raise HTTPException(status_code=400, detail="Referencia multimedia vacía")

    try:
        orchestrator = get_orchestrator()
        language = _normalise_language(request.language)
        task = AgentTask(
            task_type="media_transcription",
            payload={
                "media": request.media,
                "language": language,
                "context": request.metadata or {},
                "source": "api_media_transcription",
            },
        )
        agent_response = orchestrator.execute(task)

        metadata = {
            "language": language,
            "task_type": task.task_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return _build_agent_http_response(
            agent_response,
            extra_metadata=metadata,
            log_context="media_transcription",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error en media transcription API: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno del servidor") from exc


@app.post(
    "/upload",
    summary="Subir documento / Upload document",
    description=(
        "Permite cargar un documento válido para que se procese e indexe en la base de conocimiento del RAG.\n\n"
        "Upload a valid document so it can be processed and indexed into the RAG knowledge base."
    )
)
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):

    """Carga un documento y lo envía al pipeline de ingesta / Uploads a document to the ingestion pipeline."""
    try:
        from common.ingest_file import ingest_file, validate_uploaded_file

        # Validar archivo
        is_valid, message = validate_uploaded_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Procesar archivo
        logger.info(f"Procesando archivo API: {file.filename}")
        ingest_file(file, file.filename)
        
        return {
            "status": "success",
            "message": f"Archivo '{file.filename}' procesado exitosamente",
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload API: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar archivo")

@app.get(
    "/documents",
    summary="Listar documentos / List documents",
    description=(
        "Devuelve la lista de fuentes únicas presentes en la base vectorial del RAG.\n\n"
        "Returns the list of unique sources available in the RAG vector database."
    )
)
async def list_documents(token: str = Depends(verify_token)):
    """Obtiene el catálogo de documentos actualmente indexados."""
    try:
        from common.constants import CHROMA_SETTINGS
        from common.ingest_file import get_unique_sources_df

        files_df = get_unique_sources_df(CHROMA_SETTINGS)
        documents = files_df['uploaded_file_name'].tolist() if not files_df.empty else []
        
        return {
            "status": "success",
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error al listar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener documentos")

@app.delete(
    "/documents/{filename}",
    summary="Eliminar documento / Delete document",
    description=(
        "Elimina la referencia del documento indicado de la base de conocimiento RAG.\n\n"
        "Deletes the specified document reference from the RAG knowledge base."
    )
)
async def delete_document(
    filename: str,
    token: str = Depends(verify_token)
):
    """Elimina un documento indexado / Delete an indexed document."""
    try:
        summary = privacy_manager.forget_document(
            filename,
            requested_by=token,
            reason="delete_document_endpoint",
        )

        payload = ForgetResponse(
            status="success" if summary.status == "deleted" else "not_found",
            message=summary.message,
            audit_id=summary.audit_id,
            removed_collections=list(summary.removed_collections),
            removed_files=[str(path) for path in summary.removed_files],
        )

        if summary.status != "deleted":
            logger.warning("No se encontraron coincidencias para eliminar el documento %s", filename)

        return _model_to_dict(payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar documento: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al eliminar documento")


@app.post(
    "/privacy/forget",
    response_model=ForgetResponse,
    summary="Derecho al olvido / Right to be forgotten",
    description=(
        "Ejecuta el proceso completo de derecho al olvido, eliminando registros del RAG y "
        "dejando constancia de la auditoría correspondiente.\n\n"
        "Executes the full right-to-be-forgotten workflow, purging RAG data and registering the audit trail."
    ),
)
async def execute_right_to_be_forgotten(
    payload: ForgetRequest,
    token: str = Depends(verify_token),
):
    """Procesa una solicitud formal del derecho al olvido / Process a right-to-be-forgotten request."""

    try:
        summary = privacy_manager.forget_document(
            payload.filename,
            requested_by=token,
            subject_id=payload.subject_id,
            reason=payload.reason,
            extra_metadata=payload.metadata or {},
        )

        response = ForgetResponse(
            status="success" if summary.status == "deleted" else "not_found",
            message=summary.message,
            audit_id=summary.audit_id,
            removed_collections=list(summary.removed_collections),
            removed_files=[str(path) for path in summary.removed_files],
        )

        if summary.status != "deleted":
            logger.info(
                "Solicitud de olvido procesada sin coincidencias para el archivo %s",
                payload.filename,
            )

        return _model_to_dict(response)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error al ejecutar el derecho al olvido: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="No fue posible completar la solicitud de olvido",
        )

# Middleware para CORS (si es necesario)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar según necesidades
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

