"""
API REST para acceso de agentes IA al sistema Anclora RAG
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
from common.langchain_module import response
from common.ingest_file import ingest_file, validate_uploaded_file
from common.chroma_db_settings import get_unique_sources_df
from common.constants import CHROMA_SETTINGS

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar FastAPI
app = FastAPI(
    title="Anclora RAG API",
    description="API para acceso de agentes IA al sistema RAG",
    version="1.0.0"
)

# Seguridad básica
security = HTTPBearer()

# Modelos Pydantic
class ChatRequest(BaseModel):
    message: str
    max_length: Optional[int] = 1000
    language: Optional[str] = 'es'

class ChatResponse(BaseModel):
    response: str
    status: str
    timestamp: str

class FileInfo(BaseModel):
    filename: str
    status: str

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict

# Función de autenticación simple
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verificar token de acceso (implementar según necesidades)
    """
    # TODO: Implementar verificación real de tokens
    if credentials.credentials != "your-api-key-here":
        raise HTTPException(status_code=401, detail="Token inválido")
    return credentials.credentials

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint de salud del sistema
    """
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

@app.post("/chat", response_model=ChatResponse)
async def chat_with_rag(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """
    Endpoint principal para consultas al RAG
    """
    try:
        # Validar entrada
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(status_code=400, detail="Mensaje vacío")
        
        if len(request.message) > request.max_length:
            raise HTTPException(
                status_code=400, 
                detail=f"Mensaje demasiado largo (máximo {request.max_length} caracteres)"
            )
        
        # Procesar consulta
        logger.info(f"Procesando consulta API: {request.message[:50]}...")
        language = (request.language or "es").lower()
        if language not in {"es", "en"}:
            language = "es"

        try:
            rag_response = response(request.message, language)
        except TypeError:
            rag_response = response(request.message)
        
        from datetime import datetime
        return ChatResponse(
            response=rag_response,
            status="success",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en chat API: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    """
    Endpoint para subir documentos al RAG
    """
    try:
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

@app.get("/documents")
async def list_documents(token: str = Depends(verify_token)):
    """
    Listar documentos en la base de conocimiento
    """
    try:
        files_df = get_unique_sources_df(CHROMA_SETTINGS)
        documents = files_df['Archivo'].tolist() if not files_df.empty else []
        
        return {
            "status": "success",
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error al listar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener documentos")

@app.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    token: str = Depends(verify_token)
):
    """
    Eliminar documento de la base de conocimiento
    """
    try:
        from common.ingest_file import delete_file_from_vectordb
        delete_file_from_vectordb(filename)
        
        return {
            "status": "success",
            "message": f"Documento '{filename}' eliminado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error al eliminar documento: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al eliminar documento")

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

