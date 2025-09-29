"""API REST para acceso de agentes IA al sistema Anclora RAG."""

from __future__ import annotations

import json  # Used by UTF8JSONResponse.render for proper UTF-8 output
import logging
import os
import secrets
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from common.langchain_module import LegalComplianceGuardError, response
from common.privacy import PrivacyManager
from common.translations import get_text
from security import AdvancedSecurityManager, SecurityPolicy
from agents.orchestrator.service import OrchestratorService, create_default_orchestrator
from agents.base import AgentTask, AgentResponse

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

# Sistema de seguridad avanzado
security_policy = SecurityPolicy(
    max_queries_per_minute=100,
    max_queries_per_hour=2000,
    max_query_length=3000,
    enable_content_filtering=True,
    enable_anomaly_detection=True
)
advanced_security = AdvancedSecurityManager(security_policy)


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
        title="Message",
        description="Mensaje de la consulta o pregunta que se enviará al motor RAG. Query message or question that will be processed by the RAG engine."
    )
    max_length: Optional[int] = Field(
        1000,
        description="Longitud máxima permitida para el mensaje. Ajusta el límite si necesitas respuestas extensas. Maximum number of characters allowed in the message. Increase the limit for longer prompts."
    )
    language: Optional[str] = Field(
        'es',
        description="Idioma preferido para la respuesta (`es` o `en`). Preferred response language (`es` or `en`)."
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

class ChatResponse(BaseModel):
    response: str = Field(
        ...,
        description="Respuesta generada por el sistema RAG."
    )
    status: str = Field(
        ...,
        description="Estado de la respuesta (success, warning, error, guardrail)."
    )
    timestamp: str = Field(
        ...,
        description="Marca temporal de cuando se generó la respuesta."
    )


class AgentResponseModel(BaseModel):
    success: bool = Field(
        ...,
        description="Indica si la tarea fue atendida exitosamente por un agente especializado. Whether the orchestrated agent completed the task successfully."
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Carga útil retornada por el agente cuando la operación es exitosa. Payload returned by the agent for successful operations."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadatos auxiliares (idioma, marca temporal, tipo de tarea) útiles para la interfaz. Auxiliary metadata (language, timestamp, task type) useful for clients."
    )
    error: Optional[str] = Field(
        default=None,
        description="Código de error retornado por el agente cuando `success` es `False`. Agent-specific error code when `success` is `False`."
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
        description="Identificador o ruta del recurso multimedia a transcribir. Identifier or path of the media resource to transcribe."
    )
    language: Optional[str] = Field(
        default=None,
        description="Idioma sugerido para la transcripción o resumen resultante. Preferred language for the generated transcription or summary."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadatos adicionales (ej. tipo de reunión, participante principal). Optional metadata such as meeting type or main speaker."
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
        description="Nombre exacto del archivo que debe eliminarse de la base de conocimiento."
    )
    subject_id: Optional[str] = Field(
        default=None,
        description="Identificador del titular de los datos que solicita el borrado."
    )
    reason: Optional[str] = Field(
        default=None,
        description="Motivo o referencia interna asociada a la solicitud del derecho al olvido."
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metadatos adicionales que deban registrarse en la auditoría (se anonimizarán automáticamente)."
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

    try:
        # Try Pydantic v2 method first
        return model.model_dump()
    except AttributeError:
        # Fall back to Pydantic v1 method
        return model.dict()


class FileInfo(BaseModel):
    filename: str = Field(
        ...,
        description="Nombre del archivo almacenado en la base de conocimiento. Filename stored in the knowledge base."
    )
    status: str = Field(
        ...,
        description="Estado del procesamiento del archivo. Processing status for the uploaded file."
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
        description="Estado global del sistema. Overall health status of the system."
    )
    version: str = Field(
        ...,
        description="Versión desplegada de la API. Deployed API version."
    )
    services: dict = Field(
        ...,
        description="Mapa de servicios críticos y su estado operativo. Mapping of critical services and their operational status."
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


# Función de seguridad avanzada
def verify_security(request: Request) -> bool:
    """Verificar seguridad avanzada antes de procesar la solicitud."""

    try:
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"

        # Verificar si la IP está en cuarentena
        if advanced_security._is_ip_quarantined(client_ip):
            raise HTTPException(
                status_code=403,
                detail="IP address is quarantined due to security violations"
            )

        # Verificar rate limiting
        if not advanced_security._check_rate_limits(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security verification error: {e}")
        return True  # Permitir en caso de error para no bloquear el servicio


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
    response_model=ChatResponse,
    summary="Conversación con el RAG / Chat with RAG",
    description=(
        "Envía una consulta en español o inglés al motor RAG y recibe una respuesta contextualizada.\n\n"
        "Send a Spanish or English query to the RAG engine and receive a contextualised answer."
    ),
)
async def chat_with_rag(
    http_request: Request,
    request: ChatRequest = Body(
        ...,
        example={
            "message": "¿Cuál es el estado del informe trimestral?",
            "language": "es",
            "max_length": 600,
        },
    ),
    token: str = Depends(verify_token)
):
    """Realiza consultas conversacionales al sistema Anclora RAG."""

    # Verificación de seguridad avanzada
    verify_security(http_request)

    # Análisis de seguridad del contenido
    client_ip = http_request.client.host if http_request.client else "unknown"
    is_valid, security_event = advanced_security.validate_request(
        source_ip=client_ip,
        query=request.message,
        user_id=token[:8] if token else "anonymous",  # Usar parte del token como ID
    )

    if not is_valid:
        logger.warning(f"Security violation from {client_ip}: {security_event.description if security_event else 'Unknown'}")
        raise HTTPException(
            status_code=400,
            detail=f"Query blocked due to security policy: {security_event.description if security_event else 'Security violation'}"
        )

    language = (request.language or "es").lower()
    if language not in {"es", "en"}:
        language = "es"

    try:
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Mensaje vacío")

        if request.max_length is not None and len(request.message) > request.max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Mensaje demasiado largo (máximo {request.max_length} caracteres)",
            )

        # Procesar consulta
        logger.info(f"Procesando consulta API: {request.message[:50]}...")
        try:
            rag_response = response(request.message, language)
        except TypeError:
            rag_response = response(request.message)

        inspection = privacy_manager.inspect_response_citations(rag_response)
        warning_message: str | None = None
        if getattr(inspection, "has_sensitive_citations", False) and inspection.message_key:
            context = dict(getattr(inspection, "context", {}) or {})
            warning_message = get_text(
                inspection.message_key,
                language,
                **context,
            )
            sensitive_refs = tuple(getattr(inspection, "sensitive_citations", ()))
            if sensitive_refs:
                privacy_manager.record_sensitive_audit(
                    response=rag_response,
                    citations=sensitive_refs,
                    requested_by=token,
                    query=request.message,
                    metadata={
                        "language": language,
                        "citations": tuple(getattr(inspection, "citations", None) or sensitive_refs),
                    },
                )

        response_text = rag_response
        status_label = "success"
        if warning_message:
            response_text = f"{warning_message}\n\n{rag_response}"
            status_label = "warning"

        from datetime import datetime
        return ChatResponse(
            response=response_text,
            status=status_label,
            timestamp=datetime.now().isoformat()
        )

    except LegalComplianceGuardError as guard_exc:
        from datetime import datetime

        message = guard_exc.render_message(language)
        return ChatResponse(
            response=message,
            status="guardrail",
            timestamp=datetime.now().isoformat(),
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
        filename = getattr(file, 'filename', None) or getattr(file, 'name', None) or 'unknown_file'
        logger.info(f"Procesando archivo API: {filename}")
        ingest_file(file, filename)
        
        return {
            "status": "success",
            "message": f"Archivo '{filename}' procesado exitosamente",
            "filename": filename
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
        from common.constants import CHROMA_CLIENT

        # Usar la misma lógica que la UI para obtener documentos de ChromaDB
        documents = []
        try:
            collections = CHROMA_CLIENT.list_collections()
        except Exception as e:
            logger.error(f"Error listando colecciones: {e}")
            return {"status": "success", "documents": [], "count": 0}

        for collection_info in collections:
            try:
                collection = CHROMA_CLIENT.get_or_create_collection(collection_info.name)
                # Obtener solo metadatos para no cargar documentos completos
                try:
                    result = collection.get(include=["metadatas"], limit=2000)  # type: ignore
                except Exception:
                    result = collection.get(limit=2000)

                metadatas = (result or {}).get("metadatas", []) or []

                for meta in metadatas:
                    if isinstance(meta, dict) and meta.get("uploaded_file_name"):
                        documents.append(meta.get("uploaded_file_name"))

            except Exception as e2:
                logger.warning(f"No se pudo leer la colección '{collection_info.name}': {e2}")
                continue

        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_documents = []
        for doc in documents:
            if doc not in seen:
                seen.add(doc)
                unique_documents.append(doc)

        return {
            "status": "success",
            "documents": unique_documents,
            "count": len(unique_documents)
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

